import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/dashboard',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'assistants',
          name: 'assistants',
          component: () => import('@/views/AssistantsView.vue'),
        },
        {
          path: 'assistants/create',
          name: 'assistant-create',
          component: () => import('@/views/AssistantCreateView.vue'),
        },
        {
          path: 'assistants/:id/edit',
          name: 'assistant-edit',
          component: () => import('@/views/AssistantEditView.vue'),
          props: true,
        },
        {
          path: 'chat/:sessionId?',
          name: 'chat',
          component: () => import('@/views/ChatView.vue'),
          props: true,
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  console.log('[ROUTER DEBUG] Navigation:', from.path, '->', to.path)
  const authStore = useAuthStore()
  
  const tokenInStorage = localStorage.getItem('auth_token')
  console.log('[ROUTER DEBUG] Token in localStorage:', tokenInStorage ? tokenInStorage.substring(0, 20) + '...' : 'null')
  console.log('[ROUTER DEBUG] isAuthenticated:', authStore.isAuthenticated)
  
  // Check authentication status if not already checked
  if (!authStore.isAuthenticated && tokenInStorage) {
    console.log('[ROUTER DEBUG] Calling checkAuth()')
    await authStore.checkAuth()
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)

  if (requiresAuth && !authStore.isAuthenticated) {
    console.log('[ROUTER DEBUG] Route requires auth but user not authenticated, redirecting to login')
    // Redirect to login if authentication is required
    next({
      name: 'login',
      query: { redirect: to.fullPath },
    })
  } else if (requiresGuest && authStore.isAuthenticated) {
    console.log('[ROUTER DEBUG] Route requires guest but user authenticated, redirecting to dashboard')
    // Redirect to dashboard if already authenticated
    next({ name: 'dashboard' })
  } else {
    console.log('[ROUTER DEBUG] Navigation allowed')
    next()
  }
})

export default router