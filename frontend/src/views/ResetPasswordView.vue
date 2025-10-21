<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Create new password
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Enter your new password below.
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit="handleSubmit">
        <div class="space-y-4">
          <BaseInput
            v-model="fields.password.value"
            type="password"
            label="New Password"
            placeholder="Enter new password"
            required
            :error="fields.password.error"
            @blur="touchField('password')"
            :icon="LockClosedIcon"
          />

          <BaseInput
            v-model="fields.confirmPassword.value"
            type="password"
            label="Confirm New Password"
            placeholder="Confirm new password"
            required
            :error="fields.confirmPassword.error"
            @blur="touchField('confirmPassword')"
            :icon="LockClosedIcon"
          />
        </div>

        <div>
          <BaseButton
            type="submit"
            :loading="isSubmitting"
            :disabled="!isValid"
            full-width
            size="lg"
          >
            Reset password
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
import { useRoute, useRouter } from 'vue-router'
import { useForm } from '@/composables/useForm'
import { validationRules } from '@/utils/validators'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import { LockClosedIcon, ExclamationCircleIcon } from '@heroicons/vue/24/outline'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()

const { fields, isValid, isSubmitting, submitError, touchField, handleSubmit } = useForm({
  initialValues: {
    password: '',
    confirmPassword: '',
  },
  rules: {
    password: [validationRules.required, validationRules.minLength(8)],
    confirmPassword: [
      validationRules.required,
      (value: string) => value === fields.password.value || 'Passwords must match',
    ],
  },
  onSubmit: async (values) => {
    const token = route.query.token as string

    if (!token) {
      throw new Error('Invalid or missing reset token')
    }

    try {
      const response = await api.post('/auth/reset-password', {
        token,
        password: values.password,
      })

      if (response.data.success) {
        // Redirect to login with success message
        await router.push({
          name: 'login',
          query: { message: 'Password reset successfully. Please login with your new password.' }
        })
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to reset password. The link may have expired.')
    }
  },
})
</script>