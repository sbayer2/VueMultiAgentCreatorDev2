<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Reset your password
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Enter your email address and we'll send you a link to reset your password.
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit="handleSubmit">
        <div>
          <BaseInput
            v-model="fields.email.value"
            type="email"
            label="Email address"
            placeholder="Enter your email address"
            required
            :error="fields.email.error"
            @blur="touchField('email')"
            :icon="EnvelopeIcon"
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
            Send reset link
          </BaseButton>
        </div>

        <div class="text-center">
          <RouterLink to="/login" class="font-medium text-primary-600 hover:text-primary-500">
            Back to login
          </RouterLink>
        </div>

        <div v-if="submitSuccess" class="rounded-md bg-green-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <CheckCircleIcon class="h-5 w-5 text-green-400" aria-hidden="true" />
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-green-800">
                Check your email! If an account exists with that email, we've sent you a password reset link.
              </p>
            </div>
          </div>
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
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useForm } from '@/composables/useForm'
import { validationRules } from '@/utils/validators'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import { EnvelopeIcon, ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'
import api from '@/utils/api'

const submitSuccess = ref(false)

const { fields, isValid, isSubmitting, submitError, touchField, handleSubmit } = useForm({
  initialValues: {
    email: '',
  },
  rules: {
    email: [validationRules.required, validationRules.email],
  },
  onSubmit: async (values) => {
    try {
      const response = await api.post('/auth/forgot-password', {
        email: values.email,
      })

      if (response.data.success) {
        submitSuccess.value = true
        // Clear form
        fields.email.value = ''
      }
    } catch (error: any) {
      // Show success message even on error to prevent email enumeration
      submitSuccess.value = true
      fields.email.value = ''
    }
  },
})
</script>