<template>
  <div class="login-page min-h-screen flex items-center justify-center bg-bg-main">
    <div class="login-card bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
      <h1 class="text-3xl font-bold text-heading text-center mb-2">
        考勤打卡系統
      </h1>
      <p class="text-center text-text-secondary mb-8">
        請登入以繼續使用
      </p>
      
      <!-- 錯誤提示 -->
      <div v-if="error" class="mb-4 p-3 bg-error-bg border border-red-300 rounded-lg text-error text-sm">
        {{ error }}
      </div>
      
      <!-- 登入表單 -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <!-- 公司 ID -->
        <div>
          <label for="company_id" class="block text-sm font-medium text-text-primary mb-1">
            公司 ID
          </label>
          <input
            id="company_id"
            v-model="form.company_id"
            type="text"
            required
            placeholder="例如: company-a"
            class="w-full px-4 py-2 border border-border-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            :disabled="isLoading"
          />
        </div>
        
        <!-- 用戶名 -->
        <div>
          <label for="username" class="block text-sm font-medium text-text-primary mb-1">
            用戶名
          </label>
          <input
            id="username"
            v-model="form.login_username"
            type="text"
            required
            placeholder="請輸入用戶名"
            class="w-full px-4 py-2 border border-border-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            :disabled="isLoading"
          />
        </div>
        
        <!-- 密碼 -->
        <div>
          <label for="password" class="block text-sm font-medium text-text-primary mb-1">
            密碼
          </label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            placeholder="請輸入密碼"
            class="w-full px-4 py-2 border border-border-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            :disabled="isLoading"
          />
        </div>
        
        <!-- 登入按鈕 -->
        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-primary hover:bg-primary-hover text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="!isLoading">登入</span>
          <span v-else>登入中...</span>
        </button>
      </form>
      
      <!-- 測試帳號提示 -->
      <div class="mt-6 p-4 bg-primary-lightest rounded-lg">
        <p class="text-sm text-text-secondary mb-2">測試帳號：</p>
        <p class="text-xs text-text-hint">公司 ID: company-a</p>
        <p class="text-xs text-text-hint">用戶名: testuser</p>
        <p class="text-xs text-text-hint">密碼: (請聯繫管理員)</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  company_id: 'company-a',
  login_username: '',
  password: ''
})

const isLoading = ref(false)
const error = ref('')

const handleLogin = async () => {
  error.value = ''
  isLoading.value = true
  
  try {
    await authStore.login(form.value)
    
    // 登入成功，跳轉到首頁
    router.push('/')
  } catch (err) {
    error.value = err.message || '登入失敗，請檢查帳號密碼'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  background: linear-gradient(135deg, var(--primary-lightest) 0%, var(--bg-main) 100%);
}
</style>
