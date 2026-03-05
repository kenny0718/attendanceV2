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
    
    // 狀態管理
    isLoading: false,
    error: null,
    lastAction: null
  }),
  
  getters: {
    canPunchIn: (state) => !state.todayStatus.is_punched_in,
    canPunchOut: (state) => state.todayStatus.is_punched_in && !state.todayStatus.punch_out,
    canBreakOut: (state) => state.todayStatus.is_punched_in && !state.todayStatus.is_on_break && !state.todayStatus.punch_out,
    canBreakIn: (state) => state.todayStatus.is_on_break,
    
    formattedTodayStatus: (state) => ({
      punch_in: state.todayStatus.punch_in ? dayjs(state.todayStatus.punch_in).format('HH:mm') : '-',
      punch_out: state.todayStatus.punch_out ? dayjs(state.todayStatus.punch_out).format('HH:mm') : '-',
      break_out: state.todayStatus.break_out ? dayjs(state.todayStatus.break_out).format('HH:mm') : '-',
      break_in: state.todayStatus.break_in ? dayjs(state.todayStatus.break_in).format('HH:mm') : '-'
    })
  },
  
  actions: {
    // 打卡（真實 API）
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
            break
            
          case 'OUT':
            response = await attendanceApi.punchOut({ notes: '' })
            this.todayStatus.punch_out = response.punch_out_time
            this.todayStatus.is_punched_in = false
            break
            
          case 'BREAK_OUT':
            // 暫時不支援（後端無此 endpoint）
            throw new Error('外出打卡功能開發中')
            
          case 'BREAK_IN':
            // 暫時不支援（後端無此 endpoint）
            throw new Error('返回打卡功能開發中')
            
          default:
            throw new Error('未知的打卡類型')
        }
        
        // 打卡成功後立即刷新狀態和記錄
        await Promise.all([
          this.fetchTodayStatus(),
          this.fetchRecentLogs()
        ])
        
        return { success: true, data: response }
      } catch (error) {
        // 統一錯誤處理
        this.error = this.handleError(error)
        
        // 發生錯誤時也要刷新狀態，確保 UI 與後端同步
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
    
    // 獲取今日狀態（真實 API）
    async fetchTodayStatus() {
      try {
        const data = await attendanceApi.getCurrentStatus()
        
        if (data.has_open_session && data.session) {
          this.todayStatus = {
            punch_in: data.session.punch_in_time,
            punch_out: data.session.punch_out_time,
            break_out: null, // 後端暫無此欄位
            break_in: null,  // 後端暫無此欄位
            is_punched_in: data.session.status === 'open',
            is_on_break: false, // 後端暫無此欄位
            session_id: data.session.session_id
          }
        } else {
          // 沒有 open session，重置狀態
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
        
        // 轉換後端數據格式為前端需要的格式
        this.recentLogs = data.sessions.map(session => {
          // 判斷是上班還是下班
          const isPunchIn = session.punch_in_time && !session.punch_out_time
          const isPunchOut = session.punch_out_time
          
          return {
            id: session.session_id,
            timestamp: isPunchOut ? session.punch_out_time : session.punch_in_time,
            attendance_type: isPunchOut ? 'OUT' : 'IN',
            status: 'success',
            is_late: false, // 後端 policy_evaluation 可能有此資訊
            duration_minutes: session.duration_minutes
          }
        })
      } catch (error) {
        console.error('獲取記錄失敗:', error)
        // 不拋出錯誤，避免影響頁面載入
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
            // 狀態衝突（例如已打上班卡）
            errorMessage = error.message || '已有打開的打卡記錄，請勿重複打卡'
            break
            
          case 404:
            // 資源不存在（例如沒有 open session）
            errorMessage = error.message || '找不到打開的打卡記錄，請先打上班卡'
            break
            
          case 403:
            // 無權限
            errorMessage = '無權限執行此操作，請檢查登入狀態或公司設定'
            break
            
          case 400:
            // 請求錯誤
            errorMessage = error.message || '請求參數錯誤'
            break
            
          case 500:
          case 502:
          case 503:
            // 伺服器錯誤
            errorMessage = '伺服器暫時無法處理請求，請稍後再試'
            break
            
          default:
            errorMessage = error.message || '未知錯誤'
        }
      } else if (error.message) {
        // 網路錯誤或其他錯誤
        if (error.message.includes('網絡') || error.message.includes('Network')) {
          errorMessage = '網絡連接失敗，請檢查網絡設定'
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
    }
  }
})
