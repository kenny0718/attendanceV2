/**
 * Admin API — WP-S1-09B / WP-S1-09D
 * Companies management endpoints (super_admin only)
 */
import apiClient from './client'

export const adminApi = {
  // WP-S1-09B: List all companies
  // GET /api/admin/companies
  listCompanies: () =>
    apiClient.get('/admin/companies'),

  // WP-S1-09B: Create a company
  // POST /api/admin/companies
  createCompany: (data) =>
    apiClient.post('/admin/companies', data),

  // WP-S1-09D: Onboarding — company + initial user + membership (atomic)
  // POST /api/admin/companies/onboarding
  onboardCompany: (data) =>
    apiClient.post('/admin/companies/onboarding', data)
}
