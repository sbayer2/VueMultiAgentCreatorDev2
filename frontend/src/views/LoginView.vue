<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to your account
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Or
          <RouterLink to="/register" class="font-medium text-primary-600 hover:text-primary-500">
            create a new account
          </RouterLink>
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit="handleSubmit">
        <div class="rounded-md shadow-sm -space-y-px">
          <div>
            <BaseInput
              v-model="fields.email.value"
              type="email"
              label="Email address"
              placeholder="Email address"
              required
              :error="fields.email.error"
              @blur="touchField('email')"
              :icon="EnvelopeIcon"
            />
          </div>
          <div class="mt-4">
            <BaseInput
              v-model="fields.password.value"
              type="password"
              label="Password"
              placeholder="Password"
              required
              :error="fields.password.error"
              @blur="touchField('password')"
              :icon="LockClosedIcon"
            />
          </div>
        </div>

        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label for="remember-me" class="ml-2 block text-sm text-gray-900">
              Remember me
            </label>
          </div>

          <div class="text-sm">
            <RouterLink to="/forgot-password" class="font-medium text-primary-600 hover:text-primary-500">
              Forgot your password?
            </RouterLink>
          </div>
        </div>

        <div>
          <BaseButton
            type="submit"
            :loading="isSubmitting"
            :disabled="!isValid"
            full-width
            size="lg"
          >
            Sign in
          </BaseButton>
        </div>

        <div v-if="submitError" class="rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <ExclamationCircleIcon class="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                {{ submitError }}
              </h3>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useForm } from '@/composables/useForm'
import { validationRules } from '@/utils/validators'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import { EnvelopeIcon, LockClosedIcon, ExclamationCircleIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()

const { fields, isValid, isSubmitting, submitError, touchField, handleSubmit } = useForm({
  initialValues: {
    email: '',
    password: '',
  },
  rules: {
    email: [validationRules.required, validationRules.email],
    password: [validationRules.required],
  },
  onSubmit: async (values) => {
    const result = await authStore.login({
      email: values.email,
      password: values.password,
    })
    
    if (result.success) {
      // Navigate to dashboard after successful login
      await router.push('/dashboard')
    } else {
      throw new Error(result.error)
    }
  },
})
</script>