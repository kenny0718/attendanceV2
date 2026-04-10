import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Route access policy
// /my-schedule → authenticated user with uses_schedule=true
// /schedule    → company_admin with uses_schedule=true (management UI)
// /admin       → super_admin OR company_admin OR hr_manager
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
  {
    path: '/my-schedule',
    name: 'MySchedule',
    component: () => import('@/views/schedule/MySchedulePage.vue'),
    meta: { requiresAuth: true, requiresUsesSchedule: true }
  },
  {
    path: '/schedule',
    name: 'Schedule',
    component: () => import('@/views/schedule/SchedulePage.vue'),
    meta: { requiresAuth: true, requiresCompanyAdmin: true }
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdminAccess: true },
    children: [
      {
        path: '',
        name: 'Admin',
        component: () => import('@/views/Admin.vue'),
        meta: { requiresAuth: true, requiresAdminAccess: true }
      },
      {
        path: 'companies',
        name: 'AdminCompanies',
        component: () => import('@/views/admin/AdminCompaniesView.vue'),
        meta: { requiresAuth: true, requiresAdminAccess: true }
      },
      {
        path: 'onboarding',
        name: 'AdminOnboarding',
        component: () => import('@/views/admin/AdminOnboardingView.vue'),
        meta: { requiresAuth: true, requiresAdminAccess: true, requiresSuperAdmin: true }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsersView.vue'),
        meta: { requiresAuth: true, requiresAdminAccess: true }
      },
      {
        path: 'attendance',
        name: 'AdminAttendance',
        component: () => import('@/views/admin/AdminAttendanceView.vue'),
        meta: { requiresAuth: true, requiresAdminAccess: true }
      }
    ]
  },
  {
    path: '/leave',
    name: 'LeaveRequest',
    component: () => import('@/views/LeaveRequestView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (localStorage.getItem('token') && (!authStore.isAuthenticated || !authStore.userRole)) {
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

  if (to.meta.requiresUsesSchedule) {
    if (!authStore.usesSchedule) {
      next('/')
      return
    }
  }

  if (to.meta.requiresCompanyAdmin) {
    if (!authStore.isCompanyAdmin || !authStore.usesSchedule) {
      next('/')
      return
    }
  }

  if (to.meta.requiresSuperAdmin) {
    if (!authStore.isSuperAdmin) {
      next('/admin')
      return
    }
  }

  if (to.meta.requiresAdminAccess) {
    if (!authStore.isSuperAdmin && !authStore.isAdminAccess) {
      next('/')
      return
    }
  }

  next()
})

export default router
