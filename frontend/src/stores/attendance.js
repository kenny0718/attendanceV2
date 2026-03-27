import { defineStore } from 'pinia'
import dayjs from 'dayjs'
import { attendanceApi } from '@/api/attendance'
import { useLocation } from '@/composables/useLocation'

export const useAttendanceStore = defineStore('attendance', {
  state: () => ({
    // 今日狀態
    todayStatus: {
      punch_in: null,
      punch_out: null,
      break_out: null,
      break_in: null,
      is_punched_in: false,
      is_on_break: false,
      session_id: null
    },
    
    // 最近打卡記錄
    recentLogs: [],
    
    breakPunches: [],  // 今日外出打卡記錄
    
    // 外出原因管理
    reasonPresets: ['拜訪客戶', '外出洽公', '外出開會', '銀行辦事'],
    reasonCustoms: [],  // 自訂原因（從 localStorage 載入）
    
    // 狀態管理
    isLoading: false,
    error: null,
    lastAction: null
  }),
  
  getters: {
    canPunchIn: (state) => !state.todayStatus.is_punched_in,
    canPunchOut: (state) => state.todayStatus.is_punched_in && !state.todayStatus.punch_out,
    canBreakOut: (state) => state.todayStatus.is_punched_in && !state.todayStatus.punch_out, // WP-11-XX: 允許連續外出打卡
    canBreakIn: (state) => state.todayStatus.is_on_break,
    
    // WP-11-11: 可以創建 OUT checkpoint（不需要 open session）
    
    formattedTodayStatus: (state) => ({
      punch_in: state.todayStatus.punch_in ? dayjs(state.todayStatus.punch_in).format('HH:mm') : '-',
      punch_out: state.todayStatus.punch_out ? dayjs(state.todayStatus.punch_out).format('HH:mm') : '-',
      break_out: state.todayStatus.break_out ? dayjs(state.todayStatus.break_out).format('HH:mm') : '-',
      break_in: state.todayStatus.break_in ? dayjs(state.todayStatus.break_in).format('HH:mm') : '-'
    })
  },
  
  actions: {
    // 打卡（真實 API - WP-11-07 Phase 3B: 支援外出/返回）
    async punch(type, notes = '') {
      // 防止重複點擊
      if (this.isLoading) {
        console.warn('操作進行中，請稍候...')
        return
      }
      
      this.isLoading = true
      this.error = null
      this.lastAction = type
      
      try {
        let response
        
        switch (type) {
          case 'IN':
            response = await attendanceApi.punchIn({ notes: notes || '' })
            this.todayStatus.punch_in = response.punch_in_time
            this.todayStatus.is_punched_in = true
            this.todayStatus.session_id = response.session_id
            this.todayStatus.is_on_break = false
            localStorage.removeItem('is_on_break')
            break
            
          case 'OUT':
            response = await attendanceApi.punchOut({ notes: notes || '' })
            this.todayStatus.punch_out = response.punch_out_time
            this.todayStatus.is_punched_in = false
            this.todayStatus.is_on_break = false
            localStorage.removeItem('is_on_break')
            break
            
          case 'BREAK_OUT':
            response = await attendanceApi.breakOut({ notes: notes || '' })
            this.todayStatus.break_out = response.punch_time
            this.todayStatus.is_on_break = true
            localStorage.setItem('is_on_break', 'true')
            // 打卡成功後刷新外出打卡記錄
            await this.loadBreakPunches()
            break
            
          case 'BREAK_IN':
            response = await attendanceApi.breakIn({ notes: notes || '' })
            this.todayStatus.break_in = response.punch_time
            this.todayStatus.is_on_break = false
            localStorage.setItem('is_on_break', 'false')
            // 打卡成功後刷新外出打卡記錄
            await this.loadBreakPunches()
            break
            
          default:
            throw new Error('未知的打卡類型')
        }
        
        // 打卡成功後刷新狀態和記錄，確保 UI 完全同步
        await this.fetchTodayStatus()
        await this.fetchRecentLogs()
        
        // 如果是外出或返回打卡，刷新外出打卡記錄
        if (type === 'BREAK_OUT' || type === 'BREAK_IN') {
          await this.loadBreakPunches()
        }
        
        return { success: true, data: response }
      } catch (error) {
        // 統一錯誤處理
        this.error = this.handleError(error)
        
        // 發生錯誤時刷新狀態，確保 UI 與後端同步
        try {
          await this.fetchTodayStatus()
        } catch (refreshError) {
          console.error('刷新狀態失敗:', refreshError)
        }
        
        throw this.error
      } finally {
        // 確保 isLoading 一定會被重置
        this.isLoading = false
        console.log('[DEBUG] isLoading 已重置為 false')
      }
    },
    
    // WP-11-12: 接收 location 作為參數的打卡方法
    // UI 層負責取得 location，store 層負責業務邏輯
    async punchWithLocation(type, payload) {
      // 防止重複點擊
      if (this.isLoading) {
        console.warn('操作進行中，請稍候...')
        return
      }
      
      this.isLoading = true
      this.error = null
      this.lastAction = type
      
      try {
        let response
        
        switch (type) {
          case 'BREAK_OUT':
            // 直接使用傳入的 payload（包含 notes 和 gps）
            response = await attendanceApi.breakOut(payload)
            this.todayStatus.break_out = response.punch_time
            this.todayStatus.is_on_break = true
            localStorage.setItem('is_on_break', 'true')
            // 打卡成功後刷新外出打卡記錄
            await this.loadBreakPunches()
            break
            
          case 'BREAK_IN':
            // 未來可以用相同方式處理返回打卡
            response = await attendanceApi.breakIn(payload)
            this.todayStatus.break_in = response.punch_time
            this.todayStatus.is_on_break = false
            localStorage.setItem('is_on_break', 'false')
            await this.loadBreakPunches()
            break
            
          default:
            throw new Error('未知的打卡類型')
        }
        
        // 打卡成功後刷新記錄
        await this.fetchRecentLogs()
        
        return { success: true, data: response }
        
      } catch (error) {
        // 統一錯誤處理
        this.error = this.handleError(error)
        
        // 發生錯誤時刷新狀態，確保 UI 與後端同步
        try {
          await this.fetchTodayStatus()
        } catch (refreshError) {
          console.error('刷新狀態失敗:', refreshError)
        }
        
        throw this.error
        
      } finally {
        // 確保 isLoading 一定會被重置
        this.isLoading = false
        console.log('[DEBUG] isLoading 已重置為 false')
      }
    },
    
    
    // 載入今日外出打卡記錄
    async loadBreakPunches() {
      try {
        const data = await attendanceApi.getBreakPunches({ limit: 50 })
        this.breakPunches = data.punches || []
      } catch (error) {
        console.error('載入外出打卡記錄失敗:', error)
        this.breakPunches = []
      }
    },
    
    
    // @deprecated WP-11-12: 請使用 useLocation composable
    // 保留此方法僅供向後相容，未來將移除
    // @deprecated WP-11-12: 請使用 useLocation composable
    // 保留此方法僅供向後相容，未來將移除
    // WP-11-11: 偵測裝置類型
    detectDeviceType() {
      const userAgent = navigator.userAgent || ''
      const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
      return isMobile ? 'mobile' : 'pc'
    },
    
    // @deprecated WP-11-12: 請使用 useLocation composable
    // 保留此方法僅供向後相容，未來將移除
    // @deprecated WP-11-12: 請使用 useLocation composable
    // 保留此方法僅供向後相容，未來將移除
    // WP-11-11: 獲取 GPS 位置
    async getGPSLocation() {
      return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error('此裝置不支援定位功能'))
          return
        }
        
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy,
              captured_at: new Date().toISOString(),
              provider: 'gps'
            })
          },
          (error) => {
            let errorMessage = '無法獲取定位'
            switch (error.code) {
              case error.PERMISSION_DENIED:
                errorMessage = '請開啟定位權限後再外出打點'
                break
              case error.POSITION_UNAVAILABLE:
                errorMessage = '定位資訊無法取得'
                break
              case error.TIMEOUT:
                errorMessage = '定位請求逾時'
                break
            }
            reject(new Error(errorMessage))
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
          }
        )
      })
    },
    
    
    
    
    
    // 獲取今日狀態（真實 API）- WP-11-07 Phase 3B: 從 localStorage 恢復狀態
    async fetchTodayStatus() {
      try {
        const data = await attendanceApi.getCurrentStatus()
        
        if (data.has_open_session && data.session) {
          // 有 open session，更新狀態
          const isOnBreak = data.is_on_break || false
          
          localStorage.setItem('is_on_break', isOnBreak ? 'true' : 'false')
          
          this.todayStatus = {
            punch_in: data.session.punch_in_time,
            punch_out: data.session.punch_out_time,
            break_out: this.todayStatus.break_out,
            break_in: this.todayStatus.break_in,
            is_punched_in: data.session.status === 'open',
            is_on_break: isOnBreak,
            session_id: data.session.session_id
          }
        } else if (data.session) {
          // 沒有 open session 但有 session（已下班），保留時間顯示
          localStorage.removeItem('is_on_break')
          this.todayStatus = {
            punch_in: data.session.punch_in_time,
            punch_out: data.session.punch_out_time,  // 關鍵修復：確保 punch_out_time 被正確設置
            break_out: this.todayStatus.break_out,
            break_in: this.todayStatus.break_in,
            is_punched_in: false,
            is_on_break: false,
            session_id: data.session.session_id
          }
        } else {
          // 完全沒有 session，重置狀態
          // 但保留當日已知的 punch_in / punch_out（避免下班後閃現問題）
          const preservedPunchIn = this.todayStatus.punch_in
          const preservedPunchOut = this.todayStatus.punch_out
          localStorage.removeItem('is_on_break')
          this.todayStatus = {
            punch_in: preservedPunchIn,
            punch_out: preservedPunchOut,
            break_out: null,
            break_in: null,
            is_punched_in: false,
            is_on_break: false,
            session_id: null
          }
        }
      } catch (error) {
        console.error('獲取狀態失敗:', error)
        // 不拋出錯誤，避免影響頁面載入
      }
    },
    // 獲取最近記錄（真實 API）
    async fetchRecentLogs() {
      try {
        const data = await attendanceApi.getHistory({ limit: 10, offset: 0 })
        
        // 只顯示上班/下班記錄（不包含外出/返回）
        this.recentLogs = data.sessions.map(session => {
          // 判斷是上班還是下班
          const isPunchIn = session.punch_in_time && !session.punch_out_time
          const isPunchOut = session.punch_out_time
          
          return {
            id: session.session_id,
            timestamp: isPunchOut ? session.punch_out_time : session.punch_in_time,
            attendance_type: isPunchOut ? 'OUT' : 'IN',
            status: 'success',
            is_late: false,
            duration_minutes: session.duration_minutes
          }
        })
      } catch (error) {
        console.error('獲取記錄失敗:', error)
      }
    },
    
    // 統一錯誤處理
    handleError(error) {
      let errorMessage = '操作失敗'
      let errorCode = null
      
      if (error.status) {
        errorCode = error.status
        
        switch (error.status) {
          case 409:
            if (error.data?.detail?.error_code === 'DUPLICATE_CHECKPOINT') {
              errorMessage = '請勿重複打點（短時間/近距離）'
            } else if (error.data?.detail?.error_code === 'ALREADY_ON_BREAK') {
              errorMessage = '已經在外出狀態，請先返回打卡' // WP-11-XX: 此錯誤已廢棄（允許連續外出）
            } else if (error.data?.detail?.error_code === 'NOT_ON_BREAK') {
              errorMessage = '目前不在外出狀態，請先外出打卡'
            } else if (error.data?.detail?.error_code === 'ALREADY_OPEN_SESSION') {
              errorMessage = '今天已打上班卡，請勿重複打卡'
            } else {
              errorMessage = error.message || '已有打開的打卡記錄，請勿重複打卡'
            }
            break
            
          case 422:
            if (error.data?.detail?.error_code === 'GPS_REQUIRED') {
              errorMessage = '請開啟定位後再外出打點'
            } else {
              errorMessage = error.message || '請求參數錯誤'
            }
            break
            
          case 404:
            if (error.data?.detail?.error_code === 'NO_OPEN_SESSION') {
              errorMessage = '找不到開啟中的打卡記錄，請先打上班卡'
            } else {
              errorMessage = error.message || '找不到打開的打卡記錄，請先打上班卡'
            }
            break
            
          case 403:
            errorMessage = '無權限/租戶無效，請重新登入或確認公司'
            break
            
          case 400:
            errorMessage = error.message || '請求參數錯誤'
            break
            
          case 500:
          case 502:
          case 503:
            errorMessage = '伺服器或網路異常，請稍後重試'
            break
            
          default:
            errorMessage = error.message || '未知錯誤'
        }
      } else if (error.message) {
        if (error.message.includes('網絡') || error.message.includes('Network') || error.message.includes('網路')) {
          errorMessage = '網路連線失敗，請檢查網路設定'
        } else {
          errorMessage = error.message
        }
      }
      
      return {
        message: errorMessage,
        code: errorCode,
        originalError: error
      }
    },
    
    
    // 外出原因管理
    addCustomReason(reason) {
      const trimmed = reason.trim()
      if (!trimmed) return
      
      // 避免重複
      if (this.reasonCustoms.includes(trimmed) || this.reasonPresets.includes(trimmed)) {
        return
      }
      
      this.reasonCustoms.push(trimmed)
      this.saveReasonsToLocalStorage()
    },
    
    removeCustomReason(reason) {
      const index = this.reasonCustoms.indexOf(reason)
      if (index > -1) {
        this.reasonCustoms.splice(index, 1)
        this.saveReasonsToLocalStorage()
      }
    },
    
    saveReasonsToLocalStorage() {
      try {
        localStorage.setItem('customBreakReasons', JSON.stringify(this.reasonCustoms))
      } catch (error) {
        console.error('保存自訂原因失敗:', error)
      }
    },
    
    hydrateReasonsFromLocalStorage() {
      try {
        const saved = localStorage.getItem('customBreakReasons')
        if (saved) {
          this.reasonCustoms = JSON.parse(saved)
        }
      } catch (error) {
        console.error('載入自訂原因失敗:', error)
        this.reasonCustoms = []
      }
    },
    
    // 清除錯誤
    clearError() {
      this.error = null
    },
    
    // 手動重置 isLoading 狀態（用於調試）
    resetLoadingState() {
      console.log('[DEBUG] 手動重置 isLoading 狀態')
      this.isLoading = false
    }
  }
})
