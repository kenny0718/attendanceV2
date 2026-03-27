import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// WP-S1-08B: Route access policy
// /schedule  → company_admin only   (tenant-level admin)
// /admin     → super_admin OR company_admin OR hr_manager (S1-11C)
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
  // ── Admin (WP-S1-08B / WP-S1-10A) — super_admin only ──────────────
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: { requiresAuth: true, requiresAdminAccess: true }
  },
  {
    path: '/admin/companies',
    name: 'AdminCompanies',
    component: () => import('@/views/admin/AdminCompaniesView.vue'),
    meta: { requiresAuth: true, requiresAdminAccess: true }
  },
  {
    path: '/admin/onboarding',
    name: 'AdminOnboarding',
    component: () => import('@/views/admin/AdminOnboardingView.vue'),
    meta: { requiresAuth: true, requiresAdminAccess: true, requiresSuperAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/admin/AdminUsersView.vue'),
    meta: { requiresAuth: true, requiresAdminAccess: true }
  },
  // S1-12: Admin Attendance View (read-only)
  {
    path: '/admin/attendance',
    name: 'AdminAttendance',
    component: () => import('@/views/admin/AdminAttendanceView.vue'),
    meta: { requiresAuth: true, requiresAdminAccess: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // S1-11E.3 fix: restore session if token exists but state is not fully hydrated.
  // Covers the edge case where main.js restoreSession() ran on a different pinia
  // instance before app.use(router) completed, leaving state.role as null.
  if (localStorage.getItem('token') && (!authStore.isAuthenticated || !authStore.userRole)) {
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

  // 4. /admin onboarding — super_admin only
  if (to.meta.requiresSuperAdmin) {
    if (!authStore.isSuperAdmin) {
      next('/admin')
      return
    }
  }

  // 5. /admin — S1-11C: super_admin OR company_admin OR hr_manager
  //    Deny: employee, unauthenticated
  //    Allow: super_admin, company_admin, hr_manager
  if (to.meta.requiresAdminAccess) {
    if (!authStore.isSuperAdmin && !authStore.isAdminAccess) {
      next('/')
      return
    }
  }

  next()
})

export default router
