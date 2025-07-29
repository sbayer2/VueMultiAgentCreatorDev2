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
        user.value = response.data.user
        token.value = response.data.token
        
        // Store token in localStorage for persistence
        localStorage.setItem('auth_token', response.data.token)
        
        await router.push('/dashboard')
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
        user.value = response.data.user
        token.value = response.data.token
        
        localStorage.setItem('auth_token', response.data.token)
        
        await router.push('/dashboard')
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
    const storedToken = localStorage.getItem('auth_token')
    
    if (!storedToken) {
      return false
    }

    token.value = storedToken
    isLoading.value = true

    try {
      const response = await apiClient.get<User>('/auth/me')
      
      if (response.success && response.data) {
        user.value = response.data
        return true
      } else {
        // Invalid token, clear auth state
        logout()
        return false
      }
    } catch {
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
    paths: ['token'], // Only persist the token
  },
})