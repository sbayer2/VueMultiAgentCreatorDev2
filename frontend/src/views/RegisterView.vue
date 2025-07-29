<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Create your account
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Or
          <RouterLink to="/login" class="font-medium text-primary-600 hover:text-primary-500">
            sign in to existing account
          </RouterLink>
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit="handleSubmit">
        <div class="space-y-4">
          <BaseInput
            v-model="fields.name.value"
            type="text"
            label="Full name"
            placeholder="John Doe"
            required
            :error="fields.name.error"
            @blur="touchField('name')"
            :icon="UserIcon"
          />

          <BaseInput
            v-model="fields.email.value"
            type="email"
            label="Email address"
            placeholder="john@example.com"
            required
            :error="fields.email.error"
            @blur="touchField('email')"
            :icon="EnvelopeIcon"
          />

          <BaseInput
            v-model="fields.password.value"
            type="password"
            label="Password"
            placeholder="••••••••"
            required
            :error="fields.password.error"
            @blur="touchField('password')"
            :icon="LockClosedIcon"
            hint="At least 8 characters with uppercase, lowercase, and number"
          />

          <BaseInput
            v-model="fields.confirmPassword.value"
            type="password"
            label="Confirm password"
            placeholder="••••••••"
            required
            :error="fields.confirmPassword.error"
            @blur="touchField('confirmPassword')"
            :icon="LockClosedIcon"
          />
        </div>

        <div class="flex items-center">
          <input
            id="agree-terms"
            name="agree-terms"
            type="checkbox"
            required
            class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
          />
          <label for="agree-terms" class="ml-2 block text-sm text-gray-900">
            I agree to the
            <a href="#" class="font-medium text-primary-600 hover:text-primary-500">
              Terms and Conditions
            </a>
          </label>
        </div>

        <div>
          <BaseButton
            type="submit"
            :loading="isSubmitting"
            :disabled="!isValid"
            full-width
            size="lg"
          >
            Create account
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
import { 
  UserIcon, 
  EnvelopeIcon, 
  LockClosedIcon, 
  ExclamationCircleIcon 
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()

const { fields, isValid, isSubmitting, submitError, touchField, handleSubmit } = useForm({
  initialValues: {
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  },
  rules: {
    name: [validationRules.required, validationRules.minLength(2)],
    email: [validationRules.required, validationRules.email],
    password: [validationRules.required, validationRules.password],
    confirmPassword: [validationRules.required],
  },
  onSubmit: async (values) => {
    // Additional validation
    if (values.password !== values.confirmPassword) {
      throw new Error('Passwords do not match')
    }

    const result = await authStore.register({
      name: values.name,
      email: values.email,
      password: values.password,
      confirmPassword: values.confirmPassword,
    })
    
    if (!result.success) {
      throw new Error(result.error)
    }
  },
})

// Add custom validation for confirm password
fields.confirmPassword.rules?.push(
  validationRules.confirmPassword(fields.password.value)
)
</script>