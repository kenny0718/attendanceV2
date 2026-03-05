<template>
  <div class="login-page min-h-screen flex items-center justify-center bg-bg-main">
    <div class="login-card bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
      <h1 class="text-2xl font-bold text-heading text-center mb-6">
        考勤打卡系統
      </h1>
      
      <div class="text-center text-text-secondary mb-6">
        <p>MVP 階段 - 登入功能開發中</p>
        <p class="text-sm mt-2">請直接訪問首頁</p>
      </div>
      
      <button 
        @click="goToHome"
        class="w-full bg-primary hover:bg-primary-hover text-white font-semibold py-3 rounded-lg transition-colors"
      >
        前往首頁
      </button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToHome = () => {
  router.push('/')
}
</script>

<style scoped>
.login-page {
  background: linear-gradient(135deg, var(--primary-lightest) 0%, var(--bg-main) 100%);
}
</style>
