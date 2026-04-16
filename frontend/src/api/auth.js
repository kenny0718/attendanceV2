import apiClient from './client'

export const authApi = {
  login: (credentials) => apiClient.post('/internal/auth/login', credentials),
  refresh: () => apiClient.post('/internal/auth/refresh'),
  logout: () => apiClient.post('/internal/auth/logout'),

  getCurrentUser: () => {
    const user = localStorage.getItem('user')
    const company = localStorage.getItem('company')
    const membership = localStorage.getItem('membership')
    const role = localStorage.getItem('role')
    return user && company ? {
      user: JSON.parse(user),
      company: JSON.parse(company),
      membership: membership ? JSON.parse(membership) : null,
      role: role ? JSON.parse(role) : null,
    } : null
  }
}
