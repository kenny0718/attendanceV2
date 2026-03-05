import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    company: null,
    role: null,
    token: localStorage.getItem('token'),
    isLoading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    currentUser: (state) => state.user,
    companyId: (state) => state.company?.id,
    userId: (state) => state.user?.id,
    userRole: (state) => state.role?.id
  },
  
  actions: {
    // 登入
    async login(credentials) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await authApi.login(credentials)
        
        // 保存 token
        this.token = response.access_token
        localStorage.setItem('token', response.access_token)
        
        // 保存用戶資訊
        this.user = response.user
        this.company = response.company
        this.role = response.role
        
        localStorage.setItem('user', JSON.stringify(response.user))
        localStorage.setItem('company', JSON.stringify(response.company))
        localStorage.setItem('role', JSON.stringify(response.role))
        
        return { success: true }
      } catch (error) {
        console.error('登入失敗:', error)
        this.error = error.message || '登入失敗，請檢查帳號密碼'
        throw error
      } finally {
        this.isLoading = false
      }
    },
    
    // 登出
    async logout() {
      await authApi.logout()
      
      this.user = null
      this.company = null
      this.role = null
      this.token = null
      this.error = null
    },
    
    // 從 localStorage 恢復登入狀態
    restoreSession() {
      const token = localStorage.getItem('token')
      const user = localStorage.getItem('user')
      const company = localStorage.getItem('company')
      const role = localStorage.getItem('role')
      
      if (token && user && company) {
        this.token = token
        this.user = JSON.parse(user)
        this.company = JSON.parse(company)
        this.role = role ? JSON.parse(role) : null
      }
    },
    
    // 清除錯誤
    clearError() {
      this.error = null
    }
  }
})
