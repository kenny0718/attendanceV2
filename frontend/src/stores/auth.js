import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token'),
    isLoading: false,
    // MVP: Mock user data (使用真實數據庫中的用戶 ID)
    mockUser: {
      id: '11bda10d-7541-4230-b1f3-842afab2cea5',
      name: '測試員工',
      company_id: 'company-a',
      role: 'employee'
    }
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token || !!state.mockUser,
    currentUser: (state) => state.user || state.mockUser,
    companyId: (state) => state.mockUser?.company_id || state.user?.company_id,
    userId: (state) => state.mockUser?.id || state.user?.id
  },
  
  actions: {
    // MVP: Mock login
    async login(credentials) {
      this.isLoading = true
      try {
        // TODO: 實際 API 呼叫
        // const data = await authApi.login(credentials)
        
        // Mock response
        await new Promise(resolve => setTimeout(resolve, 500))
        this.token = 'mock-token-123'
        this.user = this.mockUser
        localStorage.setItem('token', this.token)
        return { success: true }
      } catch (error) {
        console.error('登入失敗:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },
    
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
    }
  }
})
