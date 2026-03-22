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

// 在 router 掛載前先 restoreSession，確保 beforeEach guard 可讀到正確的 role
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.restoreSession()

app.use(router)

app.mount('#app')
