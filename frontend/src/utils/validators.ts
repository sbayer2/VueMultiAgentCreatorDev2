// Email validation
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Password validation
export const isValidPassword = (password: string): boolean => {
  // At least 8 characters, one uppercase, one lowercase, one number
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/
  return passwordRegex.test(password)
}

// Form validation rules
export const validationRules = {
  required: (value: any) => !!value || 'This field is required',
  
  email: (value: string) => isValidEmail(value) || 'Please enter a valid email address',
  
  password: (value: string) => 
    isValidPassword(value) || 
    'Password must be at least 8 characters with uppercase, lowercase, and number',
  
  confirmPassword: (password: string) => (value: string) => 
    value === password || 'Passwords do not match',
  
  minLength: (min: number) => (value: string) => 
    value.length >= min || `Must be at least ${min} characters`,
  
  maxLength: (max: number) => (value: string) => 
    value.length <= max || `Must be no more than ${max} characters`,
  
  numeric: (value: string) => 
    /^\d+$/.test(value) || 'Must contain only numbers',
  
  alphanumeric: (value: string) => 
    /^[a-zA-Z0-9]+$/.test(value) || 'Must contain only letters and numbers',
}

// Form validation helper
export interface ValidationResult {
  isValid: boolean
  errors: Record<string, string>
}

export const validateForm = (
  data: Record<string, any>,
  rules: Record<string, ((value: any) => string | true)[]>
): ValidationResult => {
  const errors: Record<string, string> = {}
  let isValid = true

  Object.entries(rules).forEach(([field, fieldRules]) => {
    const value = data[field]
    
    for (const rule of fieldRules) {
      const result = rule(value)
      if (result !== true) {
        errors[field] = result
        isValid = false
        break
      }
    }
  })

  return { isValid, errors }
}

// File validation
export const isValidFileType = (file: File, acceptedTypes: string[]): boolean => {
  return acceptedTypes.some(type => {
    if (type.startsWith('.')) {
      return file.name.toLowerCase().endsWith(type.toLowerCase())
    }
    if (type.endsWith('/*')) {
      const category = type.split('/')[0]
      return file.type.startsWith(category)
    }
    return file.type === type
  })
}

export const isValidFileSize = (file: File, maxSizeInMB: number): boolean => {
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024
  return file.size <= maxSizeInBytes
}