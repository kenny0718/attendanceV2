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
    apiClient.post('/admin/companies/onboarding', data),

  // Companies v3: Lookup company registration data by tax id
  // POST /api/admin/companies/lookup-by-tax-id
  lookupCompanyByTaxId: (taxId) =>
    apiClient.post('/admin/companies/lookup-by-tax-id', { tax_id: taxId }),

  // WP-S1-10B: List users + memberships for a company (read-only)
  // GET /api/admin/companies/{company_id}/members
  listCompanyMembers: (companyId) =>
    apiClient.get(`/admin/companies/${companyId}/members`),

  // WP-S1-10C: Toggle membership active state (super_admin only)
  // PATCH /api/admin/companies/{company_id}/members/{membership_id}/active
  toggleMembershipActive: (companyId, membershipId, isActive) =>
    apiClient.patch(`/admin/companies/${companyId}/members/${membershipId}/active`, { is_active: isActive }),

  // S1-13A1: Update member display_name / email / role_id
  // PATCH /api/admin/companies/{company_id}/members/{membership_id}
  updateMember: (companyId, membershipId, payload) =>
    apiClient.patch(`/admin/companies/${companyId}/members/${membershipId}`, payload),

  // S1-13A3: Admin reset member password
  // PATCH /api/admin/companies/{company_id}/members/{membership_id}/password
  resetMemberPassword: (companyId, membershipId, newPassword) =>
    apiClient.patch(`/admin/companies/${companyId}/members/${membershipId}/password`, { new_password: newPassword }),

  // WP-S1-10D: Create a new member in a company (super_admin only)
  // POST /api/admin/companies/{company_id}/members
  createCompanyMember: (companyId, payload) =>
    apiClient.post(`/admin/companies/${companyId}/members`, payload),

  // Companies v3: Get single company detail + member summary
  // GET /api/admin/companies/{company_id}
  getCompany: (companyId) =>
    apiClient.get(`/admin/companies/${companyId}`),

  // S1-11A: Update company basic info
  // PATCH /api/admin/companies/{company_id}
  updateCompany: (companyId, payload) =>
    apiClient.patch(`/admin/companies/${companyId}`, payload),
}
