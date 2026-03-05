import apiClient from './client'

export const authApi = {
  // 登入
  login: (credentials) => apiClient.post('/auth/login', credentials),
  
  // 登出
  logout: () => apiClient.post('/auth/logout'),
  
  // 獲取個人資料
  getProfile: () => apiClient.get('/auth/profile'),
  
  // 更新個人資料
  updateProfile: (data) => apiClient.put('/auth/profile', data),
  
  // 修改密碼
  changePassword: (data) => apiClient.post('/auth/change-password', data)
}
