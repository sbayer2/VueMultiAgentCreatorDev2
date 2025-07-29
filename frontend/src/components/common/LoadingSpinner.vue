<template>
  <div class="flex items-center justify-center" :class="containerClass">
    <svg
      class="animate-spin"
      :class="spinnerClass"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
    <span v-if="text" class="ml-2" :class="textClass">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'white' | 'gray'
  text?: string
  fullScreen?: boolean
}

const props = withDefaults(defineProps<LoadingSpinnerProps>(), {
  size: 'md',
  color: 'primary',
  fullScreen: false,
})

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
}

const colorClasses = {
  primary: 'text-primary-600',
  white: 'text-white',
  gray: 'text-gray-400',
}

const spinnerClass = computed(() => [
  sizeClasses[props.size],
  colorClasses[props.color],
])

const textClass = computed(() => [
  colorClasses[props.color],
  props.size === 'sm' ? 'text-sm' : '',
  props.size === 'xl' ? 'text-lg' : '',
])

const containerClass = computed(() => {
  if (props.fullScreen) {
    return 'fixed inset-0 bg-white bg-opacity-75 z-50'
  }
  return ''
})
</script>