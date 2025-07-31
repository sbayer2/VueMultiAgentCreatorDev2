import type { AxiosInstance } from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
import { debugAuth, checkLocalStorage, checkAxiosHeaders } from '@/utils/debugAuth'

export function setupInterceptors(api: AxiosInstance) {
  // Request interceptor to add auth token
  api.interceptors.request.use(
    (config) => {
      // Get token directly from localStorage to avoid circular dependency
      const token = localStorage.getItem('auth_token')
      
      debugAuth('Interceptor - token from localStorage:', token ? `${token.substring(0, 20)}...` : 'null')
      
      // Check for valid token (not null, not "undefined", not empty)
      if (token && token !== 'undefined' && token !== 'null' && token.trim() !== '') {
        config.headers.Authorization = `Bearer ${token}`
        debugAuth('Interceptor - Added Authorization header')
      } else {
        debugAuth('Interceptor - No valid token found, skipping Authorization header')
        // Clean up invalid tokens
        if (token === 'undefined' || token === 'null') {
          localStorage.removeItem('auth_token')
          debugAuth('Interceptor - Removed invalid token from localStorage')
        }
      }
      
      checkAxiosHeaders(config)

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