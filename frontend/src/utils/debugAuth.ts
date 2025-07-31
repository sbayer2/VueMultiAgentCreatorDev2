// Debug helper to track auth flow
export function debugAuth(message: string, data?: any) {
  console.log(`[AUTH DEBUG] ${message}`, data || '')
}

export function checkLocalStorage() {
  const token = localStorage.getItem('auth_token')
  console.log('[AUTH DEBUG] Token in localStorage:', token ? `${token.substring(0, 20)}...` : 'null')
  return token
}

export function checkAxiosHeaders(config: any) {
  console.log('[AUTH DEBUG] Request config:', {
    url: config.url,
    method: config.method,
    headers: config.headers,
    hasAuthHeader: !!config.headers?.Authorization
  })
}