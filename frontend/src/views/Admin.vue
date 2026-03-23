<template>
  <div class="admin-page">
    <Navbar />
    <div class="container">
      <div class="admin-header">
        <div class="admin-header-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h1 class="admin-title">平台管理</h1>
          <p class="admin-description">系統管理後台（依角色顯示可用功能）</p>
        </div>
      </div>

      <div class="nav-grid">
        <router-link to="/admin/companies" class="nav-card">
          <div class="nav-card-icon nav-card-icon--blue">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <div class="nav-card-body">
            <h2 class="nav-card-title">公司管理</h2>
            <p class="nav-card-desc">查看所有公司、快速建立新公司</p>
          </div>
          <svg class="nav-card-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>

        <router-link v-if="authStore.isSuperAdmin" to="/admin/onboarding" class="nav-card">
          <div class="nav-card-icon nav-card-icon--green">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M3 21h18M9 8h6M9 12h6M9 16h6M4 21V7a1 1 0 011-1h3l2-2h4l2 2h3a1 1 0 011 1v14" />
            </svg>
          </div>
          <div class="nav-card-body">
            <h2 class="nav-card-title">新公司開通</h2>
            <p class="nav-card-desc">一次建立公司 + 初始管理者帳號 + Membership</p>
          </div>
          <svg class="nav-card-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>

        <router-link to="/admin/users" class="nav-card">
          <div class="nav-card-icon nav-card-icon--purple">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div class="nav-card-body">
            <h2 class="nav-card-title">使用者 / 成員查看</h2>
            <p class="nav-card-desc">查看各公司的使用者帳號與 Membership</p>
          </div>
          <svg class="nav-card-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import Navbar from '@/components/Navbar.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.admin-page {
  --primary: #4A6FA5;
  --heading: #1C3B6B;
  --text-primary: #2D3A52;
  --text-secondary: #5A6C7D;
  --bg-main: #F4F7F9;
  --bg-card: #FFFFFF;
  --border: #E5E7EB;
  min-height: 100vh;
  background-color: var(--bg-main);
  padding-bottom: 48px;
}
.container { padding: 24px 16px; max-width: 960px; margin: 0 auto; }
@media (min-width: 768px) { .container { padding: 40px 32px; } }

.admin-header { display: flex; align-items: center; gap: 16px; margin-bottom: 40px; }
.admin-header-icon {
  width: 52px; height: 52px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #7BA3D1, var(--primary));
  border-radius: 14px; color: white;
}
.admin-header-icon svg { width: 28px; height: 28px; }
.admin-title { font-size: 26px; font-weight: 700; color: var(--heading); margin: 0 0 4px; }
.admin-description { font-size: 13px; color: var(--text-secondary); margin: 0; }

.nav-grid { display: flex; flex-direction: column; gap: 16px; }
@media (min-width: 640px) { .nav-grid { flex-direction: row; } }

.nav-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
}
.nav-card:hover {
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  transform: translateY(-2px);
  border-color: #C7D9EF;
}
.nav-card-icon {
  width: 52px; height: 52px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: 14px; color: white;
}
.nav-card-icon--blue { background: linear-gradient(135deg, #7BA3D1, #4A6FA5); }
.nav-card-icon--green { background: linear-gradient(135deg, #86efac, #16a34a); }
.nav-card-icon--purple { background: linear-gradient(135deg, #c4b5fd, #7c3aed); }
.nav-card-icon svg { width: 26px; height: 26px; }
.nav-card-body { flex: 1; }
.nav-card-title { font-size: 17px; font-weight: 600; color: var(--heading); margin: 0 0 6px; }
.nav-card-desc { font-size: 13px; color: var(--text-secondary); margin: 0; line-height: 1.5; }
.nav-card-arrow { width: 20px; height: 20px; color: #C0CADB; flex-shrink: 0; }
</style>
