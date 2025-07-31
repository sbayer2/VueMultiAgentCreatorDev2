import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/utils/api'
import type { User, LoginCredentials, RegisterData, AuthResponse } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Router instance
  const router = useRouter()

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const currentUser = computed(() => user.value)

  // Actions
  const login = async (credentials: LoginCredentials) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.post<AuthResponse>('/auth/login', credentials)
      
      if (response.success && response.data) {
        // Validate token before storing
        if (!response.data.token || response.data.token === 'undefined' || response.data.token === 'null') {
          error.value = 'Invalid authentication token received'
          return { success: false, error: error.value }
        }
        
        // Set state first
        token.value = response.data.token
        user.value = response.data.user
        
        // Store token in localStorage immediately
        localStorage.setItem('auth_token', response.data.token)
        
        // Return success and let the component handle navigation
        return { success: true }
      } else {
        error.value = response.error?.message || 'Login failed'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const register = async (data: RegisterData) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.post<AuthResponse>('/auth/register', data)
      
      if (response.success && response.data) {
        // Validate token before storing
        if (!response.data.token || response.data.token === 'undefined' || response.data.token === 'null') {
          error.value = 'Invalid authentication token received'
          return { success: false, error: error.value }
        }
        
        // Set state first
        token.value = response.data.token
        user.value = response.data.user
        
        // Store token in localStorage immediately
        localStorage.setItem('auth_token', response.data.token)
        
        // Return success and let the component handle navigation
        return { success: true }
      } else {
        error.value = response.error?.message || 'Registration failed'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout')
    } catch {
      // Ignore logout errors
    }

    // Clear auth state
    user.value = null
    token.value = null
    localStorage.removeItem('auth_token')
    
    await router.push('/login')
  }

  const checkAuth = async () => {
    console.log('[AUTH DEBUG] checkAuth() called')
    const storedToken = localStorage.getItem('auth_token')
    console.log('[AUTH DEBUG] Token from localStorage in checkAuth:', storedToken ? storedToken.substring(0, 20) + '...' : 'null')
    
    // Check for invalid tokens
    if (!storedToken || storedToken === 'undefined' || storedToken === 'null' || storedToken.trim() === '') {
      console.log('[AUTH DEBUG] No valid token found, returning false')
      // Clean up invalid tokens
      if (storedToken === 'undefined' || storedToken === 'null') {
        localStorage.removeItem('auth_token')
        console.log('[AUTH DEBUG] Removed invalid token from localStorage')
      }
      return false
    }

    token.value = storedToken
    isLoading.value = true

    try {
      console.log('[AUTH DEBUG] Making GET /auth/me request')
      const response = await apiClient.get<User>('/auth/me')
      console.log('[AUTH DEBUG] /auth/me response:', response)
      
      if (response.success && response.data) {
        user.value = response.data
        console.log('[AUTH DEBUG] checkAuth successful, user set')
        return true
      } else {
        console.log('[AUTH DEBUG] checkAuth failed, calling logout')
        // Invalid token, clear auth state
        logout()
        return false
      }
    } catch (error) {
      console.log('[AUTH DEBUG] checkAuth error, calling logout:', error)
      logout()
      return false
    } finally {
      isLoading.value = false
    }
  }

  const updateProfile = async (updates: Partial<User>) => {
    if (!user.value) return { success: false, error: 'Not authenticated' }

    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.patch<User>('/auth/profile', updates)
      
      if (response.success && response.data) {
        user.value = response.data
        return { success: true }
      } else {
        error.value = response.error?.message || 'Update failed'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/auth/change-password', {
        currentPassword,
        newPassword,
      })
      
      if (response.success) {
        return { success: true }
      } else {
        error.value = response.error?.message || 'Password change failed'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    user,
    token,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    currentUser,
    
    // Actions
    login,
    register,
    logout,
    checkAuth,
    updateProfile,
    changePassword,
  }
}, {
  persist: {
    paths: ['token', 'user'], // Persist both token and user
  },
})