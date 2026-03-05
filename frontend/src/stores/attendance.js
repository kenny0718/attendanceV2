import { defineStore } from 'pinia'
import dayjs from 'dayjs'

export const useAttendanceStore = defineStore('attendance', {
  state: () => ({
    // 今日狀態
    todayStatus: {
      punch_in: null,
      punch_out: null,
      break_out: null,
      break_in: null,
      is_punched_in: false,
      is_on_break: false
    },
    
    // 最近打卡記錄（Mock data）
    recentLogs: [
      {
        id: '1',
        timestamp: '2026-03-05T09:00:15',
        attendance_type: 'IN',
        status: 'success',
        is_late: false
      },
      {
        id: '2',
        timestamp: '2026-03-04T18:30:22',
        attendance_type: 'OUT',
        status: 'success',
        is_late: false
      },
      {
        id: '3',
        timestamp: '2026-03-04T09:02:10',
        attendance_type: 'IN',
        status: 'success',
        is_late: true,
        late_minutes: 2
      }
    ],
    
    isLoading: false,
    error: null
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
    // MVP: Mock punch action
    async punch(type) {
      this.isLoading = true
      this.error = null
      
      try {
        // TODO: 實際 API 呼叫
        // await attendanceApi.punch({ attendance_type: type })
        
        // Mock delay
        await new Promise(resolve => setTimeout(resolve, 500))
        
        const now = dayjs().format('YYYY-MM-DDTHH:mm:ss')
        
        // 更新狀態
        switch (type) {
          case 'IN':
            this.todayStatus.punch_in = now
            this.todayStatus.is_punched_in = true
            break
          case 'OUT':
            this.todayStatus.punch_out = now
            break
          case 'BREAK_OUT':
            this.todayStatus.break_out = now
            this.todayStatus.is_on_break = true
            break
          case 'BREAK_IN':
            this.todayStatus.break_in = now
            this.todayStatus.is_on_break = false
            break
        }
        
        // 新增到記錄
        this.recentLogs.unshift({
          id: Date.now().toString(),
          timestamp: now,
          attendance_type: type,
          status: 'success',
          is_late: false
        })
        
        // 只保留最近 10 筆
        if (this.recentLogs.length > 10) {
          this.recentLogs = this.recentLogs.slice(0, 10)
        }
        
        return { success: true }
      } catch (error) {
        this.error = error.message || '打卡失敗'
        throw error
      } finally {
        this.isLoading = false
      }
    },
    
    // MVP: Mock get status
    async fetchTodayStatus() {
      this.isLoading = true
      try {
        // TODO: 實際 API 呼叫
        // const data = await attendanceApi.getStatus()
        
        // Mock delay
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // Mock: 如果已經有打卡記錄就保持，否則重置
        // this.todayStatus = data
      } catch (error) {
        this.error = error.message || '獲取狀態失敗'
        console.error('獲取狀態失敗:', error)
      } finally {
        this.isLoading = false
      }
    },
    
    // MVP: Mock get logs
    async fetchRecentLogs() {
      this.isLoading = true
      try {
        // TODO: 實際 API 呼叫
        // const data = await attendanceApi.getLogs({ limit: 10 })
        
        // Mock delay
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // Mock: 使用預設資料
        // this.recentLogs = data
      } catch (error) {
        this.error = error.message || '獲取記錄失敗'
        console.error('獲取記錄失敗:', error)
      } finally {
        this.isLoading = false
      }
    }
  }
})
