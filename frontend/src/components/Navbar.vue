<template>
  <nav class="navbar bg-primary text-white shadow-md">
    <div class="container mx-auto px-4 py-4 flex items-center justify-between">
      <div class="navbar-brand flex items-center">
        <h1 class="text-xl font-semibold">考勤打卡系統</h1>
      </div>
      
      <div class="navbar-menu flex items-center gap-6">
        <router-link 
          to="/" 
          class="nav-link hover:text-primary-lighter transition-colors"
        >
          首頁
        </router-link>
        
        <div class="user-info flex items-center gap-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
          </svg>
          <span>{{ userName }}</span>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const userName = computed(() => authStore.currentUser?.name || '使用者')
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-link {
  text-decoration: none;
  font-weight: 500;
}
</style>
