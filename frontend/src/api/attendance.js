import apiClient from './client'

export const attendanceApi = {
  // 打卡上班
  punchIn: (data = {}) => apiClient.post('/v1/attendance/punch-in', data),
  
  // 打卡下班
  punchOut: (data = {}) => apiClient.post('/v1/attendance/punch-out', data),
  
  // 外出打卡 (WP-11-07 Phase 3B)
  breakOut: (data = {}) => apiClient.post('/v1/attendance/break-out', data),
  
  // 返回打卡 (WP-11-07 Phase 3B)
  breakIn: (data = {}) => apiClient.post('/v1/attendance/break-in', data),
  
  // 獲取今日狀態
  getCurrentStatus: () => apiClient.get('/v1/attendance/current-status'),
  
  // 獲取打卡記錄
  getHistory: (params) => apiClient.get('/v1/attendance/history', { params }),
  
  // 獲取最近記錄
  getRecentLogs: (limit = 10) => apiClient.get('/v1/attendance/history', { 
    params: { limit, offset: 0 } 
  }),
  
  // WP-11-11: OUT Checkpoint API
  // 創建 OUT checkpoint
  createOutCheckpoint: (data) => apiClient.post('/v1/attendance/out-checkpoint', data),
  
  // 獲取 OUT checkpoints 列表
  listOutCheckpoints: (params = {}) => apiClient.get('/v1/attendance/out-checkpoints', { params })
}
