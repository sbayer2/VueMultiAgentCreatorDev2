<template>
  <div class="max-w-4xl mx-auto">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900">Profile Settings</h1>
      <p class="mt-2 text-gray-600">Manage your account information and preferences</p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center py-12">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Profile Content -->
    <div v-else class="space-y-6">
      <!-- User Information Section -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Personal Information</h2>
        </div>
        <div class="p-6">
          <form @submit.prevent="updateProfile" class="space-y-4">
            <div>
              <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
              <input
                id="username"
                v-model="profileForm.username"
                type="text"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                :disabled="!isEditingProfile"
              />
            </div>

            <div class="flex justify-between items-center pt-4">
              <div class="text-sm text-gray-500">
                Member since {{ formatDate(userProfile?.created_at) }}
              </div>
              <div class="space-x-3">
                <button
                  v-if="!isEditingProfile"
                  @click="isEditingProfile = true"
                  type="button"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Edit Profile
                </button>
                <template v-else>
                  <button
                    @click="cancelEdit"
                    type="button"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="isSaving"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {{ isSaving ? 'Saving...' : 'Save Changes' }}
                  </button>
                </template>
              </div>
            </div>
          </form>
        </div>
      </div>

      <!-- Password Change Section -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Change Password</h2>
        </div>
        <div class="p-6">
          <div v-if="!isChangingPassword">
            <button
              @click="isChangingPassword = true"
              class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Change Password
            </button>
          </div>
          <form v-else @submit.prevent="changePassword" class="space-y-4">
            <div>
              <label for="current-password" class="block text-sm font-medium text-gray-700">
                Current Password
              </label>
              <input
                id="current-password"
                v-model="passwordForm.currentPassword"
                type="password"
                required
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label for="new-password" class="block text-sm font-medium text-gray-700">
                New Password
              </label>
              <input
                id="new-password"
                v-model="passwordForm.newPassword"
                type="password"
                required
                minlength="6"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label for="confirm-password" class="block text-sm font-medium text-gray-700">
                Confirm New Password
              </label>
              <input
                id="confirm-password"
                v-model="passwordForm.confirmPassword"
                type="password"
                required
                minlength="6"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <p v-if="passwordError" class="mt-1 text-sm text-red-600">{{ passwordError }}</p>
            </div>

            <div class="flex justify-end space-x-3 pt-4">
              <button
                @click="cancelPasswordChange"
                type="button"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="isSavingPassword"
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {{ isSavingPassword ? 'Updating...' : 'Update Password' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Account Statistics Section -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Account Statistics</h2>
        </div>
        <div class="p-6">
          <div v-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-gray-50 p-4 rounded-lg">
              <dt class="text-sm font-medium text-gray-500">Total Assistants</dt>
              <dd class="mt-1 text-2xl font-semibold text-gray-900">{{ stats.total_assistants }}</dd>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
              <dt class="text-sm font-medium text-gray-500">Total Conversations</dt>
              <dd class="mt-1 text-2xl font-semibold text-gray-900">{{ stats.total_conversations }}</dd>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
              <dt class="text-sm font-medium text-gray-500">Total Messages</dt>
              <dd class="mt-1 text-2xl font-semibold text-gray-900">{{ stats.total_messages }}</dd>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
              <dt class="text-sm font-medium text-gray-500">Storage Used</dt>
              <dd class="mt-1 text-2xl font-semibold text-gray-900">{{ stats.storage_used_mb }} MB</dd>
            </div>
          </div>
          <div v-else class="text-center py-4 text-gray-500">
            Loading statistics...
          </div>
        </div>
      </div>

      <!-- API Keys Section (Future Enhancement) -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">API Configuration</h2>
        </div>
        <div class="p-6">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p class="text-blue-800">
              API key management is handled through environment variables for security.
            </p>
            <p class="text-blue-700 text-sm mt-2">
              Contact your administrator to update OpenAI API keys.
            </p>
          </div>
        </div>
      </div>

      <!-- Danger Zone Section -->
      <div class="bg-white shadow rounded-lg border border-red-300">
        <div class="px-6 py-4 border-b border-red-200 bg-red-50">
          <h2 class="text-lg font-semibold text-red-900">Danger Zone</h2>
        </div>
        <div class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-medium text-gray-900">Delete Account</h3>
              <p class="mt-1 text-sm text-gray-500">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
            </div>
            <button
              @click="showDeleteConfirmation = true"
              class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <TransitionRoot appear :show="showDeleteConfirmation" as="template">
      <Dialog as="div" @close="showDeleteConfirmation = false" class="relative z-10">
        <TransitionChild
          as="template"
          enter="duration-300 ease-out"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="duration-200 ease-in"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black bg-opacity-25" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4 text-center">
            <TransitionChild
              as="template"
              enter="duration-300 ease-out"
              enter-from="opacity-0 scale-95"
              enter-to="opacity-100 scale-100"
              leave="duration-200 ease-in"
              leave-from="opacity-100 scale-100"
              leave-to="opacity-0 scale-95"
            >
              <DialogPanel class="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <DialogTitle as="h3" class="text-lg font-medium leading-6 text-gray-900">
                  Delete Account
                </DialogTitle>
                <div class="mt-2">
                  <p class="text-sm text-gray-500">
                    Are you absolutely sure you want to delete your account? This action will permanently delete:
                  </p>
                  <ul class="mt-3 text-sm text-gray-500 list-disc list-inside">
                    <li>All your assistants</li>
                    <li>All conversations and messages</li>
                    <li>All uploaded files</li>
                    <li>Your profile information</li>
                  </ul>
                  <p class="mt-3 text-sm font-medium text-red-600">
                    This action cannot be undone!
                  </p>
                </div>

                <div class="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    @click="showDeleteConfirmation = false"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                    @click="deleteAccount"
                    :disabled="isDeletingAccount"
                  >
                    {{ isDeletingAccount ? 'Deleting...' : 'Delete My Account' }}
                  </button>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>

    <!-- Success Toast -->
    <Transition
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="successMessage"
        class="fixed bottom-4 right-4 max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden"
      >
        <div class="p-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <CheckCircleIcon class="h-6 w-6 text-green-400" aria-hidden="true" />
            </div>
            <div class="ml-3 w-0 flex-1 pt-0.5">
              <p class="text-sm font-medium text-gray-900">{{ successMessage }}</p>
            </div>
            <div class="ml-4 flex-shrink-0 flex">
              <button
                @click="successMessage = ''"
                class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <span class="sr-only">Close</span>
                <XMarkIcon class="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/utils/api'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { CheckCircleIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'

interface UserProfile {
  id: number
  username: string
  created_at: string
  updated_at?: string
}

interface UserStats {
  total_assistants: number
  total_conversations: number
  total_messages: number
  storage_used_mb: number
}

const router = useRouter()
const authStore = useAuthStore()

// State
const isLoading = ref(true)
const error = ref('')
const successMessage = ref('')
const userProfile = ref<UserProfile | null>(null)
const stats = ref<UserStats | null>(null)

// Profile editing
const isEditingProfile = ref(false)
const isSaving = ref(false)
const profileForm = reactive({
  username: ''
})

// Password change
const isChangingPassword = ref(false)
const isSavingPassword = ref(false)
const passwordError = ref('')
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// Account deletion
const showDeleteConfirmation = ref(false)
const isDeletingAccount = ref(false)

// Methods
async function fetchProfile() {
  try {
    isLoading.value = true
    error.value = ''

    const response = await apiClient.get<UserProfile>('/profile')
    if (response.success && response.data) {
      userProfile.value = response.data
      profileForm.username = response.data.username
    } else {
      error.value = response.error?.message || 'Failed to load profile'
    }
  } catch (err) {
    error.value = 'Failed to load profile information'
  } finally {
    isLoading.value = false
  }
}

async function fetchStats() {
  try {
    const response = await apiClient.get<UserStats>('/profile/stats')
    if (response.success && response.data) {
      stats.value = response.data
    }
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}

async function updateProfile() {
  try {
    isSaving.value = true
    error.value = ''

    const response = await apiClient.put<UserProfile>('/profile', {
      name: profileForm.name,
      email: profileForm.email
    })

    if (response.success && response.data) {
      userProfile.value = response.data
      isEditingProfile.value = false
      successMessage.value = 'Profile updated successfully'

      // Update auth store
      if (authStore.currentUser) {
        authStore.currentUser.name = response.data.name
        authStore.currentUser.email = response.data.email
      }

      // Clear success message after 3 seconds
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    } else {
      error.value = response.error?.message || 'Failed to update profile'
    }
  } catch (err) {
    error.value = 'Failed to update profile'
  } finally {
    isSaving.value = false
  }
}

async function changePassword() {
  // Validate passwords match
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordError.value = 'Passwords do not match'
    return
  }

  try {
    isSavingPassword.value = true
    passwordError.value = ''

    const response = await apiClient.post('/profile/change-password', {
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword,
      confirm_password: passwordForm.confirmPassword
    })

    if (response.success) {
      isChangingPassword.value = false
      successMessage.value = 'Password changed successfully'

      // Clear form
      passwordForm.currentPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''

      // Clear success message after 3 seconds
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    } else {
      passwordError.value = response.error?.message || 'Failed to change password'
    }
  } catch (err) {
    passwordError.value = 'Failed to change password'
  } finally {
    isSavingPassword.value = false
  }
}

async function deleteAccount() {
  try {
    isDeletingAccount.value = true

    const response = await apiClient.delete('/profile')

    if (response.success) {
      // Log out and redirect to login
      await authStore.logout()
      router.push('/login')
    } else {
      error.value = response.error?.message || 'Failed to delete account'
      showDeleteConfirmation.value = false
    }
  } catch (err) {
    error.value = 'Failed to delete account'
    showDeleteConfirmation.value = false
  } finally {
    isDeletingAccount.value = false
  }
}

function cancelEdit() {
  isEditingProfile.value = false
  if (userProfile.value) {
    profileForm.username = userProfile.value.username
  }
}

function cancelPasswordChange() {
  isChangingPassword.value = false
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordError.value = ''
}

function formatDate(dateString?: string) {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// Lifecycle
onMounted(() => {
  fetchProfile()
  fetchStats()
})
</script>