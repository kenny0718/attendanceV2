import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

let refreshPromise = null

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    if (error.response) {
      const { status, data, config } = error.response
      const originalRequest = error.config || config || {}

      if (status === 401 && !originalRequest._retry && !String(originalRequest.url || '').includes('/internal/auth/login') && !String(originalRequest.url || '').includes('/internal/auth/refresh')) {
        originalRequest._retry = true
        try {
          const authStore = useAuthStore()
          refreshPromise = refreshPromise || authStore.refreshSession()
          const newToken = await refreshPromise
          refreshPromise = null
          originalRequest.headers = originalRequest.headers || {}
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return apiClient(originalRequest)
        } catch (refreshError) {
          refreshPromise = null
          const authStore = useAuthStore()
          await authStore.logout({ remote: false })
          if (router.currentRoute.value.path !== '/login') {
            router.push('/login')
          }
          return Promise.reject(refreshError)
        }
      }

      switch (status) {
        case 401:
          console.error('登入狀態失效，請重新登入')
          break
        case 403:
          console.error('無權限訪問')
          break
        case 404:
          console.error('資源不存在')
          break
        case 500:
          console.error('伺服器錯誤')
          break
      }
      
      return Promise.reject({
        status,
        message: typeof data?.detail === 'string'
          ? data.detail
          : (data?.detail?.message || data?.detail?.error || data?.message || '請求失敗'),
        data
      })
    }

    if (error.request) {
      return Promise.reject({
        message: '網絡連接失敗，請檢查網絡設定'
      })
    }

      return Promise.reject({
        message: error.message || '未知錯誤'
      })
  }
)

export default apiClient
