import type { AxiosInstance } from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

export function setupInterceptors(api: AxiosInstance) {
  // Request interceptor to add auth token
  api.interceptors.request.use(
    (config) => {
      // Get token directly from localStorage to avoid circular dependency
      const token = localStorage.getItem('auth_token')
      
      // Check for valid token (not null, not "undefined", not empty)
      if (token && token !== 'undefined' && token !== 'null' && token.trim() !== '') {
        config.headers.Authorization = `Bearer ${token}`
      } else {
        // Clean up invalid tokens
        if (token === 'undefined' || token === 'null') {
          localStorage.removeItem('auth_token')
        }
      }

      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor to handle errors
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        // Only logout if we're not already on the login page
        if (router.currentRoute.value.name !== 'login') {
          const authStore = useAuthStore()
          authStore.logout()
        }
      }

      return Promise.reject(error)
    }
  )
}