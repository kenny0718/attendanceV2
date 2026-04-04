import apiClient from './client'

export const scheduleApi = {
  // ── Shift Templates ──────────────────────────────────────────────

  // 列出班別模板
  listTemplates: (params = {}) =>
    apiClient.get('/v1/schedule/shift-templates', { params }),

  // 取得單一班別模板
  getTemplate: (id) =>
    apiClient.get(`/v1/schedule/shift-templates/${id}`),

  // 建立班別模板
  createTemplate: (data) =>
    apiClient.post('/v1/schedule/shift-templates', data),

  // 更新班別模板（部分更新）
  updateTemplate: (id, data) =>
    apiClient.patch(`/v1/schedule/shift-templates/${id}`, data),

  // 啟用班別模板
  activateTemplate: (id) =>
    apiClient.post(`/v1/schedule/shift-templates/${id}/activate`),

  // 停用班別模板
  deactivateTemplate: (id) =>
    apiClient.post(`/v1/schedule/shift-templates/${id}/deactivate`),

  // ── Shift Assignments ────────────────────────────────────────────

  // 列出班別指派
  listAssignments: (params = {}) =>
    apiClient.get('/v1/schedule/shift-assignments', { params }),

  // 取得單一班別指派
  getAssignment: (id) =>
    apiClient.get(`/v1/schedule/shift-assignments/${id}`),

  // 建立班別指派
  createAssignment: (data) =>
    apiClient.post('/v1/schedule/shift-assignments', data),

  // 取消班別指派
  cancelAssignment: (id) =>
    apiClient.post(`/v1/schedule/shift-assignments/${id}/cancel`),
}
