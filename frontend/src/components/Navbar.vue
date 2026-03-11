<template>
  <nav class="navbar bg-white shadow-md">
    <div class="container mx-auto px-4 py-2 max-w-6xl flex items-center justify-between">
      <!-- Logo / Title -->
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
          </svg>
        </div>
        <div>
          <h1 class="text-lg font-bold text-heading leading-tight">考勤打卡系統</h1>
          <p class="text-xs text-text-secondary leading-tight">{{ companyName }}</p>
        </div>
      </div>
      
      <!-- User Info -->
      <div class="flex items-center space-x-3">
        <div class="text-right">
          <p class="text-sm font-medium text-text-primary leading-tight">{{ userName }}</p>
          <p class="text-xs text-text-secondary leading-tight">{{ userRole }}</p>
        </div>
        
        <!-- Logout Button -->
        <button
          @click="handleLogout"
          class="px-3 py-2 text-sm text-text-secondary hover:text-error hover:bg-error-bg rounded-lg transition-colors"
          title="登出"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userName = computed(() => authStore.currentUser?.display_name || '訪客')
const companyName = computed(() => authStore.company?.name || '未知公司')
const userRole = computed(() => authStore.role?.name || '未知角色')

const handleLogout = async () => {
  if (confirm('確定要登出嗎？')) {
    await authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
}
</style>
