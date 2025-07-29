import { ref, reactive, computed } from 'vue'
import { validateForm } from '@/utils/validators'

export interface FormField<T = any> {
  value: T
  error: string
  touched: boolean
  rules?: ((value: T) => string | true)[]
}

export interface UseFormOptions<T extends Record<string, any>> {
  initialValues: T
  rules?: Partial<Record<keyof T, ((value: any) => string | true)[]>>
  onSubmit?: (values: T) => Promise<void> | void
}

export function useForm<T extends Record<string, any>>(options: UseFormOptions<T>) {
  const { initialValues, rules = {}, onSubmit } = options

  // Create reactive form fields
  const fields = reactive<Record<keyof T, FormField>>(
    Object.entries(initialValues).reduce((acc, [key, value]) => {
      acc[key as keyof T] = {
        value,
        error: '',
        touched: false,
        rules: rules[key as keyof T] || [],
      }
      return acc
    }, {} as Record<keyof T, FormField>)
  )

  // Form state
  const isSubmitting = ref(false)
  const submitError = ref<string | null>(null)

  // Computed properties
  const values = computed(() => 
    Object.entries(fields).reduce((acc, [key, field]) => {
      acc[key as keyof T] = field.value
      return acc
    }, {} as T)
  )

  const errors = computed(() =>
    Object.entries(fields).reduce((acc, [key, field]) => {
      if (field.error) {
        acc[key as keyof T] = field.error
      }
      return acc
    }, {} as Partial<Record<keyof T, string>>)
  )

  const isValid = computed(() => {
    const fieldErrors = Object.values(fields).some(field => !!field.error)
    const untouchedRequired = Object.values(fields).some(
      field => field.rules?.some(rule => {
        const result = rule(field.value)
        return result !== true && result.includes('required')
      })
    )
    return !fieldErrors && !untouchedRequired
  })

  const isDirty = computed(() =>
    Object.entries(fields).some(([key, field]) => 
      field.value !== initialValues[key as keyof T]
    )
  )

  // Methods
  const validateField = (name: keyof T) => {
    const field = fields[name]
    if (!field.rules || field.rules.length === 0) {
      field.error = ''
      return true
    }

    for (const rule of field.rules) {
      const result = rule(field.value)
      if (result !== true) {
        field.error = result
        return false
      }
    }

    field.error = ''
    return true
  }

  const validateAllFields = () => {
    let valid = true
    Object.keys(fields).forEach((key) => {
      const isFieldValid = validateField(key as keyof T)
      if (!isFieldValid) {
        valid = false
      }
    })
    return valid
  }

  const touchField = (name: keyof T) => {
    fields[name].touched = true
    validateField(name)
  }

  const setFieldValue = (name: keyof T, value: any) => {
    fields[name].value = value
    if (fields[name].touched) {
      validateField(name)
    }
  }

  const setFieldError = (name: keyof T, error: string) => {
    fields[name].error = error
  }

  const setErrors = (errors: Partial<Record<keyof T, string>>) => {
    Object.entries(errors).forEach(([key, error]) => {
      if (key in fields) {
        fields[key as keyof T].error = error as string
      }
    })
  }

  const reset = () => {
    Object.entries(initialValues).forEach(([key, value]) => {
      fields[key as keyof T].value = value
      fields[key as keyof T].error = ''
      fields[key as keyof T].touched = false
    })
    submitError.value = null
  }

  const handleSubmit = async (e?: Event) => {
    if (e) {
      e.preventDefault()
    }

    // Touch all fields
    Object.keys(fields).forEach(key => {
      fields[key as keyof T].touched = true
    })

    // Validate all fields
    if (!validateAllFields()) {
      return
    }

    isSubmitting.value = true
    submitError.value = null

    try {
      if (onSubmit) {
        await onSubmit(values.value)
      }
    } catch (error: any) {
      submitError.value = error.message || 'An error occurred'
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    fields,
    values,
    errors,
    isValid,
    isDirty,
    isSubmitting,
    submitError,
    validateField,
    validateAllFields,
    touchField,
    setFieldValue,
    setFieldError,
    setErrors,
    reset,
    handleSubmit,
  }
}