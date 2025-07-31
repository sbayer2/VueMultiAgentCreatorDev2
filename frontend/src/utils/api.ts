import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import type { ApiResponse, ApiError } from '@/types'

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Note: Interceptors are set up in main.ts after Pinia initialization
// to avoid circular dependency issues

// Helper function to handle API errors
export function handleApiError(error: any): ApiError {
  if (error.response?.data?.error) {
    return error.response.data.error
  }

  if (error.response) {
    return {
      code: `HTTP_${error.response.status}`,
      message: error.response.statusText || 'An error occurred',
      details: error.response.data,
    }
  }

  if (error.request) {
    return {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server. Please check your internet connection.',
    }
  }

  return {
    code: 'UNKNOWN_ERROR',
    message: error.message || 'An unexpected error occurred',
  }
}

// Generic request wrapper with error handling
export async function apiRequest<T = any>(
  config: AxiosRequestConfig
): Promise<ApiResponse<T>> {
  try {
    const response = await api.request<any>(config)
    
    // The backend returns { success: boolean, data?: any, error?: any }
    // We need to check if this is the backend's response format
    if (response.data && typeof response.data === 'object' && 'success' in response.data) {
      return response.data as ApiResponse<T>
    }
    
    // Otherwise wrap the response
    return {
      success: true,
      data: response.data as T,
    }
  } catch (error) {
    return {
      success: false,
      error: handleApiError(error),
    }
  }
}

// Convenience methods
export const apiClient = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'GET', url }),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'POST', url, data }),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'PUT', url, data }),

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'PATCH', url, data }),

  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'DELETE', url }),
}

export default api