import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/styles/main.css'

// Day.js 時區支援 - 必須在應用啟動前完成
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)
// 設定 Asia/Taipei 為全域顯示基準時區
dayjs.tz.setDefault('Asia/Taipei')

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 在應用啟動時恢復登入狀態
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.restoreSession()

app.mount('#app')
