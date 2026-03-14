import { defineStore } from 'pinia'
import { attendanceApi } from '@/api/attendance'

export const useReportingStore = defineStore('reporting', {
  state: () => ({
    // Sessions List
    sessions: [],
    sessionsTotal: 0,
    sessionsLimit: 20,
    sessionsOffset: 0,
    sessionsLoading: false,
    sessionsError: null,
    // sessionsFilters: 目前 View 層自行管理篩選參數，此 state 未被任何 action 寫入
    // 亦未被任何 View 讀取，依 Audit WARN-01 移除，避免 dead state 誤導。
    // 若 Step 2/3 需要跨元件共用篩選狀態時再行補回。

    // Company Summary
    companySummary: null,
    companySummaryLoading: false,
    companySummaryError: null,

    // User Summary
    userSummary: null,
    userSummaryLoading: false,
    userSummaryError: null
  }),

  actions: {
    // BUG-01 修正：api/client.js response interceptor 已 unwrap response.data，
    // attendanceApi.*() 回傳的直接是 body object，不可再取 .data。
    async fetchSessions(params = {}) {
      this.sessionsLoading = true
      this.sessionsError = null
      try {
        const data = await attendanceApi.fetchSessions(params)
        this.sessions = data.sessions
        this.sessionsTotal = data.total
        this.sessionsLimit = data.limit
        this.sessionsOffset = data.offset
      } catch (err) {
        this.sessionsError = err?.message || '載入失敗'
      } finally {
        this.sessionsLoading = false
      }
    },

    async fetchCompanySummary(params = {}) {
      this.companySummaryLoading = true
      this.companySummaryError = null
      try {
        this.companySummary = await attendanceApi.fetchCompanySummary(params)
      } catch (err) {
        this.companySummaryError = err?.message || '載入失敗'
      } finally {
        this.companySummaryLoading = false
      }
    },

    async fetchUserSummary(params = {}) {
      this.userSummaryLoading = true
      this.userSummaryError = null
      try {
        this.userSummary = await attendanceApi.fetchUserSummary(params)
      } catch (err) {
        this.userSummaryError = err?.message || '載入失敗'
      } finally {
        this.userSummaryLoading = false
      }
    }
  }
})
