<template>
  <PageShell max-width="1120px">
    <Navbar />

    <PageIntroCard
      :eyebrow="currentPage.eyebrow"
      :title="currentPage.title"
      :description="currentPage.description"
    >
      <div class="admin-tabs" role="tablist" aria-label="Admin sections">
        <router-link
          v-for="item in visibleTabs"
          :key="item.to"
          :to="item.to"
          class="admin-tab"
          :class="{ 'admin-tab--active': isActive(item) }"
        >
          <span class="admin-tab-label">{{ item.label }}</span>
          <span class="admin-tab-hint">{{ item.hint }}</span>
        </router-link>
      </div>
    </PageIntroCard>

    <section class="admin-content-shell">
      <router-view />
    </section>
  </PageShell>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import Navbar from '@/components/Navbar.vue'
import PageShell from '@/components/PageShell.vue'
import PageIntroCard from '@/components/PageIntroCard.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const tabItems = [
  {
    to: '/admin',
    label: '總覽',
    hint: '管理入口',
    eyebrow: 'ADMIN PORTAL',
    title: '平台管理',
    description: '在同一個 admin 框架下切換各管理模組，維持穩定且連續的操作節奏。',
  },
  {
    to: '/admin/companies',
    label: '公司管理',
    hint: '公司與成員',
    eyebrow: 'ADMIN COMPANIES',
    title: '公司管理',
    description: '查看公司列表、編輯公司資料，並管理公司成員。',
  },
  {
    to: '/admin/users',
    label: '使用者 / 成員',
    hint: '帳號與資格',
    eyebrow: 'ADMIN USERS',
    title: '使用者 / 成員查看',
    description: '依公司查看成員名單、建立新成員，並管理成員基本資料與帳號狀態。',
  },
  {
    to: '/admin/attendance',
    label: '打卡管理',
    hint: '出勤查詢',
    eyebrow: 'ADMIN ATTENDANCE',
    title: '打卡管理',
    description: '依日期區間查詢公司全體員工打卡紀錄，維持 admin 內部切換的穩定體感。',
  },
  {
    to: '/admin/onboarding',
    label: '新公司開通',
    hint: 'super_admin',
    eyebrow: 'ADMIN ONBOARDING',
    title: '新公司開通',
    description: '建立新租戶與初始管理者帳號，在同一個 admin 框架中完成開通流程。',
    superAdminOnly: true,
  },
]

const visibleTabs = computed(() =>
  tabItems.filter((item) => !item.superAdminOnly || authStore.isSuperAdmin)
)

const currentPage = computed(() => {
  const matched = tabItems.find((item) => item.to === route.path)
  return matched || tabItems[0]
})

function isActive(item) {
  return route.path === item.to
}
</script>

<style scoped>
.admin-tabs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.admin-tab {
  min-width: 150px;
  padding: 14px 16px;
  border-radius: 18px;
  text-decoration: none;
  color: inherit;
  background: rgba(248, 250, 252, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.18);
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease, background-color 0.16s ease;
  display: grid;
  gap: 2px;
}

.admin-tab:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
  border-color: rgba(74, 111, 165, 0.26);
}

.admin-tab--active {
  background: linear-gradient(135deg, rgba(74, 111, 165, 0.14), rgba(123, 163, 209, 0.2));
  border-color: rgba(74, 111, 165, 0.34);
  box-shadow: 0 14px 28px rgba(74, 111, 165, 0.12);
}

.admin-tab-label {
  font-size: 14px;
  font-weight: 800;
  color: #163a63;
}

.admin-tab-hint {
  font-size: 11px;
  color: #64748b;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.admin-content-shell {
  min-height: 420px;
}

@media (max-width: 720px) {
  .admin-tabs {
    display: grid;
    grid-template-columns: 1fr;
  }

  .admin-tab {
    min-width: 0;
  }
}
</style>
