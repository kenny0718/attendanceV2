import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: false } // MVP 階段先不要求登入
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守衛（MVP 階段先註解掉）
// router.beforeEach((to, from, next) => {
//   const authStore = useAuthStore()
//   
//   if (to.meta.requiresAuth && !authStore.isAuthenticated) {
//     next('/login')
//     return
//   }
//   
//   next()
// })

export default router
