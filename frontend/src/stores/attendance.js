import { defineStore } from 'pinia'
import dayjs from 'dayjs'
import { attendanceApi } from '@/api/attendance'

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
    
    // WP-11-11: OUT Checkpoint 狀態
    outCheckpointList: [],
    breakPunches: [],  // 今日外出打卡記錄
    outCheckpointLoading: false,
    outCheckpointError: null,
    
    // WP-11-11: 原因選擇器
    lastSelectedReason: '',
    reasonPresets: [
      '外出洽公',
      '拜訪客戶',
      '銀行辦事',
      '郵局辦事',
      '採購物資',
      '用餐'
    ],
    reasonCustoms: [],
    
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
    canCreateOutCheckpoint: (state) => !state.outCheckpointLoading,
    
    // WP-11-11: 所有原因選項（preset + custom）
    allReasons: (state) => [...state.reasonPresets, ...state.reasonCustoms],
    
    formattedTodayStatus: (state) => ({
      punch_in: state.todayStatus.punch_in ? dayjs(state.todayStatus.punch_in).format('HH:mm') : '-',
      punch_out: state.todayStatus.punch_out ? dayjs(state.todayStatus.punch_out).format('HH:mm') : '-',
      break_out: state.todayStatus.break_out ? dayjs(state.todayStatus.break_out).format('HH:mm') : '-',
      break_in: state.todayStatus.break_in ? dayjs(state.todayStatus.break_in).format('HH:mm') : '-'
    })
  },
  
  actions: {
    // 打卡（真實 API - WP-11-07 Phase 3B: 支援外出/返回）
    async punch(type) {
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
            response = await attendanceApi.punchIn({ notes: '' })
            this.todayStatus.punch_in = response.punch_in_time
            this.todayStatus.is_punched_in = true
            this.todayStatus.session_id = response.session_id
            this.todayStatus.is_on_break = false
            localStorage.removeItem('is_on_break')
            break
            
          case 'OUT':
            response = await attendanceApi.punchOut({ notes: '' })
            this.todayStatus.punch_out = response.punch_out_time
            this.todayStatus.is_punched_in = false
            this.todayStatus.is_on_break = false
            localStorage.removeItem('is_on_break')
            break
            
          case 'BREAK_OUT':
            response = await attendanceApi.breakOut({ notes: '' })
            this.todayStatus.break_out = response.punch_time
            this.todayStatus.is_on_break = true
            localStorage.setItem('is_on_break', 'true')
            break
            
          case 'BREAK_IN':
            response = await attendanceApi.breakIn({ notes: '' })
            this.todayStatus.break_in = response.punch_time
            this.todayStatus.is_on_break = false
            localStorage.setItem('is_on_break', 'false')
            break
            
          default:
            throw new Error('未知的打卡類型')
        }
        
        // 打卡成功後只刷新記錄，不刷新狀態（避免覆蓋剛設置的 is_on_break）
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
        this.isLoading = false
      }
    },
    
    // WP-11-11: 提交 OUT checkpoint
    async outCheckpointSubmit(reasonText) {
      if (this.outCheckpointLoading) {
        console.warn('操作進行中，請稍候...')
        return
      }
      
      if (!reasonText || reasonText.trim() === '') {
        throw new Error('請先選擇原因')
      }
      
      this.outCheckpointLoading = true
      this.outCheckpointError = null
      
      try {
        // 偵測裝置類型
        const deviceType = this.detectDeviceType()
        
        // 準備 payload
        const payload = {
          device_type: deviceType,
          notes: reasonText.trim()
        }
        
        // Mobile 需要 GPS
        if (deviceType === 'mobile') {
          const gpsData = await this.getGPSLocation()
          payload.gps = gpsData
        }
        
        // 提交 checkpoint
        const response = await attendanceApi.createOutCheckpoint(payload)
        
        // 保存最後選擇的原因
        this.lastSelectedReason = reasonText
        localStorage.setItem('lastSelectedReason', reasonText)
        
        // 刷新 checkpoint 列表
        await this.loadOutCheckpoints()
        
        return { success: true, data: response }
      } catch (error) {
        this.outCheckpointError = this.handleError(error)
        
        // 即使錯誤也嘗試刷新列表（可能是 409 重複）
        try {
          await this.loadOutCheckpoints()
        } catch (refreshError) {
          console.error('刷新列表失敗:', refreshError)
        }
        
        throw this.outCheckpointError
      } finally {
        this.outCheckpointLoading = false
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
    
    // WP-11-11: 載入 OUT checkpoints 列表
    async loadOutCheckpoints() {
      try {
        const data = await attendanceApi.listOutCheckpoints({ limit: 50, offset: 0 })
        
        // 只顯示今天的記錄
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        
        this.outCheckpointList = (data.checkpoints || []).filter(checkpoint => {
          const checkpointDate = new Date(checkpoint.punch_time)
          checkpointDate.setHours(0, 0, 0, 0)
          return checkpointDate.getTime() === today.getTime()
        })
      } catch (error) {
        console.error('載入 OUT checkpoints 失敗:', error)
        this.outCheckpointList = []
      }
    },
    
    // WP-11-11: 偵測裝置類型
    detectDeviceType() {
      const userAgent = navigator.userAgent || ''
      const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
      return isMobile ? 'mobile' : 'pc'
    },
    
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
    
    // WP-11-11: 添加自訂原因
    addCustomReason(text) {
      const trimmed = text.trim()
      if (!trimmed) return
      
      // 避免重複
      if (this.reasonPresets.includes(trimmed) || this.reasonCustoms.includes(trimmed)) {
        return
      }
      
      this.reasonCustoms.push(trimmed)
      this.persistReasonsToLocalStorage()
    },
    
    // WP-11-11: 移除自訂原因
    removeCustomReason(text) {
      const index = this.reasonCustoms.indexOf(text)
      if (index > -1) {
        this.reasonCustoms.splice(index, 1)
        this.persistReasonsToLocalStorage()
      }
    },
    
    // WP-11-11: 從 localStorage 載入原因
    hydrateReasonsFromLocalStorage() {
      try {
        const saved = localStorage.getItem('customReasons')
        if (saved) {
          this.reasonCustoms = JSON.parse(saved)
        }
        
        const lastReason = localStorage.getItem('lastSelectedReason')
        if (lastReason) {
          this.lastSelectedReason = lastReason
        }
      } catch (error) {
        console.error('載入自訂原因失敗:', error)
      }
    },
    
    // WP-11-11: 保存原因到 localStorage
    persistReasonsToLocalStorage() {
      try {
        localStorage.setItem('customReasons', JSON.stringify(this.reasonCustoms))
      } catch (error) {
        console.error('保存自訂原因失敗:', error)
      }
    },
    
    // 獲取今日狀態（真實 API）- WP-11-07 Phase 3B: 從 localStorage 恢復狀態
    async fetchTodayStatus() {
      try {
        const data = await attendanceApi.getCurrentStatus()
        
        if (data.has_open_session && data.session) {
          // 使用後端返回的 is_on_break 狀態（優先於 localStorage）
          const isOnBreak = data.is_on_break || false
          
          // 同步到 localStorage
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
        } else {
          // 沒有 open session，重置狀態並清除 localStorage
          localStorage.removeItem('is_on_break')
          this.todayStatus = {
            punch_in: null,
            punch_out: null,
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
            errorMessage = error.message || '找不到打開的打卡記錄，請先打上班卡'
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
    
    // 清除錯誤
    clearError() {
      this.error = null
      this.outCheckpointError = null
    }
  }
})
