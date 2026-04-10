<template>
  <header>
    <div class="navbar surface-card">
      <router-link to="/" class="brand-block">
        <div v-if="companyLogo" class="brand-logo-wrap">
          <img :src="companyLogo" :alt="`${companyDisplayName} logo`" class="brand-logo">
        </div>
        <div v-else class="brand-text">{{ companyDisplayName }}</div>
      </router-link>

      <div class="actions-block">
        <div class="user-block">
          <p class="user-name">{{ userDisplayName }}</p>
        </div>

        <router-link v-if="showAdminEntry" to="/admin" class="action-btn admin-btn">
          後台管理
        </router-link>

        <button class="action-btn logout-btn" type="button" @click="handleLogout">
          登出
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const companyDisplayName = computed(
  () => authStore.company?.display_name || authStore.company?.name || '未指定公司'
)
const companyLogo = computed(() => authStore.company?.logo_url || '')
const userDisplayName = computed(
  () => authStore.currentUser?.display_name || authStore.currentUser?.name || authStore.currentUser?.email || '未登入使用者'
)
const showAdminEntry = computed(() => authStore.isSuperAdmin || authStore.isAdminAccess)

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  max-width: 1200px;
  margin: 0 auto;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-sizing: border-box;
}

.brand-block {
  min-width: 0;
  display: flex;
  align-items: center;
  color: inherit;
  text-decoration: none;
}

.brand-logo-wrap {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.brand-text {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
}

.actions-block {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.user-block {
  text-align: right;
}

.user-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #334155;
}

.action-btn {
  border: none;
  border-radius: 14px;
  padding: 10px 14px;
  font-size: 0.92rem;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.admin-btn {
  background: #e0f2fe;
  color: #0369a1;
}

.admin-btn:hover {
  background: #bae6fd;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.92);
  color: #475569;
  border: 1px solid rgba(203, 213, 225, 0.9);
}

.logout-btn:hover {
  background: #f8fafc;
  color: #0f172a;
}

@media (max-width: 720px) {
  .navbar {
    padding: 16px;
    align-items: flex-start;
    flex-direction: column;
  }

  .actions-block {
    width: 100%;
    justify-content: space-between;
  }

  .user-block {
    text-align: left;
  }
}
</style>
