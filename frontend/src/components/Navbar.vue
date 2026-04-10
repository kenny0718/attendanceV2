<template>
  <header class="navbar-shell">
    <div class="navbar container">
      <router-link to="/" class="brand">
        <div class="brand-mark">A</div>
        <div class="brand-copy">
          <strong>Attendance</strong>
          <span>Workstream</span>
        </div>
      </router-link>

      <div class="account-actions">
        <div class="account-box">
          <div class="account-name">{{ displayName }}</div>
          <div class="account-meta">{{ roleLabel }}</div>
        </div>

        <button class="logout-btn" @click="handleLogout">登出</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useStreamingStore } from '@/stores/streaming'

const router = useRouter()
const authStore = useAuthStore()
const streamingStore = useStreamingStore()

const displayName = computed(() => authStore.currentUser?.name || authStore.currentUser?.email || '使用者')
const roleLabel = computed(() => authStore.role?.name || authStore.role?.id || 'authenticated')

async function handleLogout() {
  await authStore.logout()
  streamingStore.disconnect()
  router.push('/login')
}
</script>

<style scoped>
.navbar-shell {
  position: sticky;
  top: 0;
  z-index: 30;
  backdrop-filter: blur(18px);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.88));
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.14);
}

.container {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 16px;
}

.navbar {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding-top: 12px;
  padding-bottom: 12px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  color: white;
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: 0 10px 22px rgba(239, 68, 68, 0.28);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  color: #e2e8f0;
  line-height: 1.05;
}

.brand-copy strong {
  font-size: 0.98rem;
}

.brand-copy span {
  font-size: 0.72rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.account-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.account-box {
  text-align: right;
  color: #e2e8f0;
}

.account-name {
  font-size: 0.88rem;
  font-weight: 700;
}

.account-meta {
  font-size: 0.72rem;
  color: #94a3b8;
}

.logout-btn {
  border: none;
  border-radius: 999px;
  padding: 9px 14px;
  background: linear-gradient(135deg, #ef4444, #f97316);
  color: white;
  font-weight: 700;
  cursor: pointer;
}

@media (max-width: 900px) {
  .navbar {
    align-items: flex-start;
  }

  .account-actions {
    justify-content: flex-start;
  }
}
</style>
