/**
 * Leave Request API client (S1-14A)
 *
 * Base URL: /v1/leave
 * All endpoints require Bearer token (JWT with active_company_id)
 */
import apiClient from './client'

export const leaveApi = {
  /**
   * S1-14A: 建立請假申請
   * POST /v1/leave/requests
   *
   * @param {Object} payload
   * @param {string} payload.leave_type_id  - Leave Type UUID
   * @param {string} payload.start_date     - YYYY-MM-DD
   * @param {string} payload.end_date       - YYYY-MM-DD
   * @param {string} payload.reason         - Required, 1-1000 chars
   * @param {boolean} [payload.is_half_day] - Optional, default false
   * @returns {Promise<LeaveRequestResponse>}
   */
  createLeaveRequest: (payload) =>
    apiClient.post('/v1/leave/requests', payload),

  /**
   * 取得自己的請假列表
   * GET /v1/leave/my-requests
   */
  getMyLeaveRequests: ({ status, limit = 20, offset = 0 } = {}) => {
    const params = { limit, offset }
    if (status) params.status = status
    return apiClient.get('/v1/leave/my-requests', { params })
  },
}
