import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

const IDLE_ACTIVITY_EVENTS = ['mousedown', 'keydown', 'scroll', 'touchstart']

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    company: null,
    role: null,
    membership: null,
    token: localStorage.getItem('token'),
    idleTimeoutMinutes: Number(localStorage.getItem('idle_timeout_minutes') || 60),
    absoluteTimeoutHours: Number(localStorage.getItem('absolute_timeout_hours') || 12),
    lastActivityAt: Number(localStorage.getItem('last_activity_at') || Date.now()),
    refreshPromise: null,
    activityBound: false,
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
        this.applySessionPayload(response)
        this.bindActivityTracking()
        return { success: true }
      } catch (error) {
        console.error('登入失敗:', error)
        this.error = error.message || '登入失敗，請檢查帳號密碼'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async refreshSession() {
      if (this.refreshPromise) {
        return this.refreshPromise
      }

      this.refreshPromise = authApi.refresh()
        .then((response) => {
          this.token = response.access_token
          localStorage.setItem('token', response.access_token)
          this.idleTimeoutMinutes = response.idle_timeout_minutes
          this.absoluteTimeoutHours = response.absolute_timeout_hours
          localStorage.setItem('idle_timeout_minutes', String(response.idle_timeout_minutes))
          localStorage.setItem('absolute_timeout_hours', String(response.absolute_timeout_hours))
          this.recordActivity()
          return response.access_token
        })
        .catch(async (error) => {
          await this.logout({ remote: false })
          throw error
        })
        .finally(() => {
          this.refreshPromise = null
        })

      return this.refreshPromise
    },

    async logout({ remote = true } = {}) {
      if (remote) {
        authApi.logout().catch((error) => {
          console.warn('登出 API 失敗，已在本地清除 session', error)
        })
      }
      this.clearSessionState()
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
        this.idleTimeoutMinutes = Number(localStorage.getItem('idle_timeout_minutes') || 60)
        this.absoluteTimeoutHours = Number(localStorage.getItem('absolute_timeout_hours') || 12)
        this.lastActivityAt = Number(localStorage.getItem('last_activity_at') || Date.now())
        this.bindActivityTracking()
      }
    },

    applySessionPayload(response) {
      this.token = response.access_token
      this.user = response.user
      this.company = response.company
      this.role = response.role
      this.membership = response.membership || null
      this.idleTimeoutMinutes = response.idle_timeout_minutes || 60
      this.absoluteTimeoutHours = response.absolute_timeout_hours || 12

      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      localStorage.setItem('company', JSON.stringify(response.company))
      localStorage.setItem('role', JSON.stringify(response.role))
      localStorage.setItem('membership', JSON.stringify(response.membership || null))
      localStorage.setItem('idle_timeout_minutes', String(this.idleTimeoutMinutes))
      localStorage.setItem('absolute_timeout_hours', String(this.absoluteTimeoutHours))
      this.recordActivity()
    },

    updateCompanyProfile(company) {
      this.company = company
      localStorage.setItem('company', JSON.stringify(company))
    },

    recordActivity() {
      this.lastActivityAt = Date.now()
      localStorage.setItem('last_activity_at', String(this.lastActivityAt))
    },

    bindActivityTracking() {
      if (this.activityBound || typeof window === 'undefined') {
        return
      }
      const handler = () => this.recordActivity()
      IDLE_ACTIVITY_EVENTS.forEach((eventName) => {
        window.addEventListener(eventName, handler, { passive: true })
      })
      this._activityHandler = handler
      this.activityBound = true
    },

    unbindActivityTracking() {
      if (!this.activityBound || typeof window === 'undefined' || !this._activityHandler) {
        return
      }
      IDLE_ACTIVITY_EVENTS.forEach((eventName) => {
        window.removeEventListener(eventName, this._activityHandler)
      })
      this._activityHandler = null
      this.activityBound = false
    },

    clearSessionState() {
      this.unbindActivityTracking()
      this.user = null
      this.company = null
      this.role = null
      this.membership = null
      this.token = null
      this.idleTimeoutMinutes = 60
      this.absoluteTimeoutHours = 12
      this.lastActivityAt = Date.now()
      this.error = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('company')
      localStorage.removeItem('role')
      localStorage.removeItem('membership')
      localStorage.removeItem('idle_timeout_minutes')
      localStorage.removeItem('absolute_timeout_hours')
      localStorage.removeItem('last_activity_at')
    },

    clearError() {
      this.error = null
    }
  }
})
