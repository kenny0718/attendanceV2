import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// WP-S1-08B: Route access policy
// /schedule  → company_admin only   (tenant-level admin)
// /admin     → super_admin only      (system-level, NOT equivalent to company_admin)
// All other requiresAuth routes → any authenticated user

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
  // ── Reporting UI (WP-REPORTING-UI) ─────────────────────────────────────
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
  },
  // ── Schedule (WP-S1-07) — company_admin only ────────────────────────
  {
    path: '/schedule',
    name: 'Schedule',
    component: () => import('@/views/schedule/SchedulePage.vue'),
    meta: { requiresAuth: true, requiresCompanyAdmin: true }
  },
  // ── Admin (WP-S1-08B) — super_admin only ───────────────────────────
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: { requiresAuth: true, requiresSuperAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Restore session from localStorage if token exists but state is not hydrated
  if (!authStore.isAuthenticated && localStorage.getItem('token')) {
    authStore.restoreSession()
  }

  // 1. Unauthenticated → /login
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 2. Already logged in, trying to visit /login → /
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
    return
  }

  // 3. /schedule — requires exact company_admin role
  //    Deny: employee, unauthenticated, super_admin (no tenant context)
  //    Allow: company_admin only
  if (to.meta.requiresCompanyAdmin) {
    if (!authStore.isCompanyAdmin) {
      next('/')
      return
    }
  }

  // 4. /admin — requires exact super_admin role
  //    Deny: company_admin, employee, unauthenticated
  //    Allow: super_admin only
  if (to.meta.requiresSuperAdmin) {
    if (!authStore.isSuperAdmin) {
      next('/')
      return
    }
  }

  next()
})

export default router
