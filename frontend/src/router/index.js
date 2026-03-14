import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  // ── Reporting UI (WP-REPORTING-UI) ────────────────────────────────
  {
    path: '/attendance/reports/sessions',
    name: 'AttendanceSessions',
    component: () => import('@/views/reports/AttendanceSessionsPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/attendance/reports/company-summary',
    name: 'CompanySummary',
    component: () => import('@/views/reports/CompanySummaryPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/attendance/reports/user-summary',
    name: 'UserSummary',
    component: () => import('@/views/reports/UserSummaryPage.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (!authStore.isAuthenticated && localStorage.getItem('token')) {
    authStore.restoreSession()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
    return
  }

  next()
})

export default router
