import { ref, watch, type Ref } from 'vue'

export function useDebounce<T>(value: Ref<T>, delay = 300) {
  const debouncedValue = ref<T>(value.value) as Ref<T>
  let timeout: NodeJS.Timeout

  const flush = () => {
    clearTimeout(timeout)
    debouncedValue.value = value.value
  }

  const cancel = () => {
    clearTimeout(timeout)
  }

  watch(value, (newValue) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      debouncedValue.value = newValue
    }, delay)
  })

  return {
    debouncedValue,
    flush,
    cancel,
  }
}

// Alternative implementation for functions
export function useDebounceFn<T extends (...args: any[]) => any>(
  fn: T,
  delay = 300
): T & { cancel: () => void; flush: () => void } {
  let timeout: NodeJS.Timeout
  let lastArgs: any[]

  const debouncedFn = ((...args: any[]) => {
    lastArgs = args
    clearTimeout(timeout)
    
    timeout = setTimeout(() => {
      fn(...args)
    }, delay)
  }) as T

  const cancel = () => {
    clearTimeout(timeout)
  }

  const flush = () => {
    clearTimeout(timeout)
    if (lastArgs) {
      fn(...lastArgs)
    }
  }

  return Object.assign(debouncedFn, { cancel, flush })
}