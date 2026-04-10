import apiClient from './client'

export const authApi = {
  login: (credentials) => apiClient.post('/internal/auth/login', credentials),

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('company')
    localStorage.removeItem('role')
    localStorage.removeItem('membership')
    return Promise.resolve()
  },

  getCurrentUser: () => {
    const user = localStorage.getItem('user')
    const company = localStorage.getItem('company')
    const membership = localStorage.getItem('membership')
    return user && company ? {
      user: JSON.parse(user),
      company: JSON.parse(company),
      membership: membership ? JSON.parse(membership) : null,
    } : null
  }
}
