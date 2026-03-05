import apiClient from './client'

export const authApi = {
  // 登入
  login: (credentials) => apiClient.post('/internal/auth/login', credentials),
  
  // 登出（前端清除 token）
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('company')
    return Promise.resolve()
  },
  
  // 獲取當前用戶資訊（從 localStorage）
  getCurrentUser: () => {
    const user = localStorage.getItem('user')
    const company = localStorage.getItem('company')
    return user && company ? {
      user: JSON.parse(user),
      company: JSON.parse(company)
    } : null
  }
}
