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

  getBreakPunches: (params = {}) => apiClient.get('/v1/attendance/break-punches', { params }),

  // 更新打卡備註
  updatePunchNote: (punchId, data) => apiClient.patch(`/v1/attendance/punch/${punchId}/note`, data),

  // OUT Checkpoint
  createOutCheckpoint: (data = {}) => apiClient.post('/v1/attendance/out-checkpoint', data),
  listOutCheckpoints: (params = {}) => apiClient.get('/v1/attendance/out-checkpoints', { params }),

  // ── Reporting API (WP-REPORTING-UI) ──────────────────────────────

  // Reporting Step 1: Sessions List
  fetchSessions: (params = {}) =>
    apiClient.get('/v1/attendance/sessions', { params }),

  // Reporting Step 2: Company Summary
  fetchCompanySummary: (params = {}) =>
    apiClient.get('/v1/attendance/reports/company-summary', { params }),

  // Reporting Step 3: User Summary
  fetchUserSummary: (params = {}) =>
    apiClient.get('/v1/attendance/reports/user-summary', { params })
}
