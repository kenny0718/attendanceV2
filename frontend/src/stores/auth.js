import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    company: null,
    role: null,
    membership: null,
    token: localStorage.getItem('token'),
    isLoading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    currentUser: (state) => state.user,
    companyId: (state) => state.company?.id,
    userId: (state) => state.user?.id,
    userRole: (state) => state.role?.id,
    usesSchedule: (state) => state.membership?.uses_schedule === true,
    isCompanyAdmin: (state) => state.role?.id === 'company_admin',
    isSuperAdmin: (state) => state.role?.id === 'super_admin',
    isAdminAccess: (state) => ['company_admin', 'hr_manager'].includes(state.role?.id)
  },

  actions: {
    async login(credentials) {
      this.isLoading = true
      this.error = null

      try {
        const response = await authApi.login(credentials)
        this.token = response.access_token
        localStorage.setItem('token', response.access_token)

        this.user = response.user
        this.company = response.company
        this.role = response.role
        this.membership = response.membership || null

        localStorage.setItem('user', JSON.stringify(response.user))
        localStorage.setItem('company', JSON.stringify(response.company))
        localStorage.setItem('role', JSON.stringify(response.role))
        localStorage.setItem('membership', JSON.stringify(response.membership || null))

        return { success: true }
      } catch (error) {
        console.error('登入失敗:', error)
        this.error = error.message || '登入失敗，請檢查帳號密碼'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async logout() {
      await authApi.logout()
      this.user = null
      this.company = null
      this.role = null
      this.membership = null
      this.token = null
      this.error = null
    },

    restoreSession() {
      const token = localStorage.getItem('token')
      const user = localStorage.getItem('user')
      const company = localStorage.getItem('company')
      const role = localStorage.getItem('role')
      const membership = localStorage.getItem('membership')

      if (token && user && company) {
        this.token = token
        this.user = JSON.parse(user)
        this.company = JSON.parse(company)
        this.role = role ? JSON.parse(role) : null
        this.membership = membership ? JSON.parse(membership) : null
      }
    },

    clearError() {
      this.error = null
    }
  }
})
