import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/styles/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 在應用啟動時恢復登入狀態
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.restoreSession()

app.mount('#app')
