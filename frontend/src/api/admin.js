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
,

  // WP-S1-10B: List users + memberships for a company (read-only)
  // GET /api/admin/companies/{company_id}/members
  listCompanyMembers: (companyId) =>
    apiClient.get(`/admin/companies/${companyId}/members`)
,

  // WP-S1-10C: Toggle membership active state (super_admin only)
  // PATCH /api/admin/companies/{company_id}/members/{membership_id}/active
  toggleMembershipActive: (companyId, membershipId, isActive) =>
    apiClient.patch(`/admin/companies/${companyId}/members/${membershipId}/active`, { is_active: isActive }),

  // WP-S1-10D: Create a new member in a company (super_admin only)
  // POST /api/admin/companies/{company_id}/members
  createCompanyMember: (companyId, payload) =>
    apiClient.post(`/admin/companies/${companyId}/members`, payload)
}
