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
    
    // 添加 tenant headers (從 auth store 取得)
    const authStore = useAuthStore()
    if (authStore.companyId) {
      config.headers['X-Company-ID'] = authStore.companyId
    }
    if (authStore.userId) {
      config.headers['X-User-ID'] = authStore.userId
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
          localStorage.removeItem('token')
          const authStore = useAuthStore()
          authStore.logout()
          router.push('/login')
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
        message: data?.detail || data?.message || '請求失敗',
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
