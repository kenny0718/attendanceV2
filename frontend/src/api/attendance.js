import apiClient from './client'

export const attendanceApi = {
  // 打卡上班
  punchIn: (data = {}) => apiClient.post('/v1/attendance/punch-in', data),
  
  // 打卡下班
  punchOut: (data = {}) => apiClient.post('/v1/attendance/punch-out', data),
  
  // 獲取今日狀態
  getCurrentStatus: () => apiClient.get('/v1/attendance/current-status'),
  
  // 獲取打卡記錄
  getHistory: (params) => apiClient.get('/v1/attendance/history', { params }),
  
  // 獲取最近記錄
  getRecentLogs: (limit = 10) => apiClient.get('/v1/attendance/history', { 
    params: { limit, offset: 0 } 
  })
}

// 注意：後端目前沒有獨立的外出/返回 endpoints
// Phase 2 暫時只實作上班/下班
// 外出/返回功能留待後端新增 API 後再實作
