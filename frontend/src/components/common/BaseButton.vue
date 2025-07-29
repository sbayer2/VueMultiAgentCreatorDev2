<template>
  <component
    :is="componentType"
    :type="type"
    :to="to"
    :href="href"
    :disabled="disabled || loading"
    :class="buttonClasses"
    v-bind="$attrs"
  >
    <LoadingSpinner
      v-if="loading"
      :size="size === 'lg' ? 'md' : 'sm'"
      :color="variant === 'primary' ? 'white' : 'gray'"
      class="mr-2"
    />
    <component
      v-if="icon && !iconRight"
      :is="icon"
      :class="iconClasses"
      aria-hidden="true"
    />
    <span>
      <slot />
    </span>
    <component
      v-if="icon && iconRight"
      :is="icon"
      :class="iconClasses"
      aria-hidden="true"
    />
  </component>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import { RouterLink } from 'vue-router'
import LoadingSpinner from './LoadingSpinner.vue'

export interface BaseButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  to?: string
  href?: string
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
  icon?: Component
  iconRight?: boolean
}

const props = withDefaults(defineProps<BaseButtonProps>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false,
  iconRight: false,
})

const componentType = computed(() => {
  if (props.to) return RouterLink
  if (props.href) return 'a'
  return 'button'
})

const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'

const variantClasses = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
  secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-primary-500',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-primary-500',
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

const buttonClasses = computed(() => [
  baseClasses,
  variantClasses[props.variant],
  sizeClasses[props.size],
  props.fullWidth ? 'w-full' : '',
  props.loading ? 'cursor-wait' : '',
])

const iconSizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
}

const iconClasses = computed(() => [
  iconSizeClasses[props.size],
  props.iconRight ? 'ml-2' : 'mr-2',
])
</script>