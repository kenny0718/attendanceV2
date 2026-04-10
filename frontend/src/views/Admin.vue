<template>
  <div class="nav-grid">
    <router-link to="/admin/companies" class="nav-card">
      <div class="nav-card-icon nav-card-icon--blue">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      </div>
      <div class="nav-card-body">
        <h2 class="nav-card-title">公司管理</h2>
        <p class="nav-card-desc">查看與管理已建立的公司</p>
      </div>
      <svg class="nav-card-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </router-link>

    <router-link v-if="authStore.isSuperAdmin" to="/admin/onboarding" class="nav-card">
      <div class="nav-card-icon nav-card-icon--green">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 21h18M9 8h6M9 12h6M9 16h6M4 21V7a1 1 0 011-1h3l2-2h4l2 2h3a1 1 0 011 1v14" />
        </svg>
      </div>
      <div class="nav-card-body">
        <h2 class="nav-card-title">新公司開通</h2>
        <p class="nav-card-desc">一次建立公司、初始管理者帳號與 Membership</p>
      </div>
      <svg class="nav-card-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </router-link>

    <router-link to="/admin/attendance" class="nav-card">
      <div class="nav-card-icon nav-card-icon--orange">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div class="nav-card-body">
        <h2 class="nav-card-title">打卡管理</h2>
        <p class="nav-card-desc">查看公司所有員工的打卡紀錄</p>
      </div>
      <svg class="nav-card-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </router-link>

    <router-link to="/admin/users" class="nav-card">
      <div class="nav-card-icon nav-card-icon--purple">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
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
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.nav-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.nav-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  text-decoration: none;
  color: inherit;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.nav-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 44px rgba(15, 23, 42, 0.12);
  border-color: rgba(148, 163, 184, 0.28);
}

.nav-card-icon {
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  color: white;
}

.nav-card-icon--blue { background: linear-gradient(135deg, #7BA3D1, #4A6FA5); }
.nav-card-icon--green { background: linear-gradient(135deg, #86efac, #16a34a); }
.nav-card-icon--purple { background: linear-gradient(135deg, #c4b5fd, #7c3aed); }
.nav-card-icon--orange { background: linear-gradient(135deg, #fb923c, #ea580c); }

.nav-card-icon svg {
  width: 26px;
  height: 26px;
}

.nav-card-body {
  flex: 1;
}

.nav-card-title {
  margin: 0 0 6px;
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}

.nav-card-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
}

.nav-card-arrow {
  width: 20px;
  height: 20px;
  color: #94a3b8;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .nav-grid {
    grid-template-columns: 1fr;
  }
}
</style>
