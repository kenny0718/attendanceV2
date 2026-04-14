import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 創建 Axios 實例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器
apiClient.interceptors.request.use(
  (config) => {
    // 自動添加 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 響應攔截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 未授權，清除 token 並跳轉登入
          console.error('Token 無效或已過期，請重新登入')
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          localStorage.removeItem('company')
          localStorage.removeItem('role')
          
          const authStore = useAuthStore()
          authStore.logout()
          
          // 如果不是在登入頁，則跳轉
          if (router.currentRoute.value.path !== '/login') {
            router.push('/login')
          }
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
    } else if (error.request) {
      return Promise.reject({
        message: '網絡連接失敗，請檢查網絡設定'
      })
    } else {
      return Promise.reject({
        message: error.message || '未知錯誤'
      })
    }
  }
)

export default apiClient
