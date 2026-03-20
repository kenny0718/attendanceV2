/**
 * Admin API — WP-S1-09B
 * Companies management endpoints (super_admin only)
 */
import apiClient from './client'

export const adminApi = {
  /**
   * GET /api/admin/companies
   * List all companies. Returns { companies: [...], total: N }
   */
  listCompanies: () =>
    apiClient.get('/admin/companies'),

  /**
   * POST /api/admin/companies
   * Create a new company.
   * @param {{ id: string, name: string, timezone?: string }} data
   */
  createCompany: (data) =>
    apiClient.post('/admin/companies', data)
}
