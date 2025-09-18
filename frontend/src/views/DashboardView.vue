<template>
  <div>
    <div class="md:flex md:items-center md:justify-between">
      <div class="min-w-0 flex-1">
        <h2 class="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
          Welcome back, {{ authStore.currentUser?.name }}!
        </h2>
      </div>
    </div>

    <!-- Stats -->
    <div class="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="stat in stats" :key="stat.name" class="card">
        <div class="card-body">
          <dt class="text-sm font-medium text-gray-500 truncate">
            {{ stat.name }}
          </dt>
          <dd class="mt-1 text-2xl font-semibold text-primary-600">
            {{ stat.value }}
          </dd>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="mt-8">
      <h3 class="text-lg font-medium leading-6 text-gray-900">Recent Activity</h3>
      <div class="mt-4 card">
        <div class="card-body">
          <div v-if="isLoading" class="text-center py-8">
            <LoadingSpinner size="lg" />
          </div>
          <div v-else-if="recentActivity.length === 0" class="text-center py-8 text-gray-500">
            No recent activity
          </div>
          <ul v-else role="list" class="divide-y divide-gray-200">
            <li v-for="activity in recentActivity" :key="activity.id" class="py-4">
              <div class="flex space-x-3">
                <div class="flex-1 space-y-1">
                  <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium">{{ activity.title }}</h3>
                    <p class="text-sm text-gray-500">{{ formatDate(activity.timestamp, 'relative') }}</p>
                  </div>
                  <p class="text-sm text-gray-500">{{ activity.description }}</p>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="mt-8">
      <h3 class="text-lg font-medium leading-6 text-gray-900">Quick Actions</h3>
      <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <RouterLink
          v-for="action in quickActions"
          :key="action.name"
          :to="action.href"
          class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
        >
          <div class="flex-shrink-0">
            <component :is="action.icon" class="h-10 w-10 text-primary-600" aria-hidden="true" />
          </div>
          <div class="flex-1 min-w-0">
            <span class="absolute inset-0" aria-hidden="true" />
            <p class="text-sm font-medium text-gray-900">{{ action.name }}</p>
            <p class="text-sm text-gray-500 truncate">{{ action.description }}</p>
          </div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/formatters'
import { apiClient } from '@/utils/api'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { 
  PlusIcon,
  ChatBubbleLeftRightIcon,
  CogIcon,
} from '@heroicons/vue/24/outline'
import type { ApiError } from '@/types'

interface DashboardStats {
  totalAssistants: number;
  activeChats: number;
  messagesToday: number;
  apiUsage: string;
}

interface Activity {
  id: string;
  title: string;
  description: string;
  timestamp: string;
}

const authStore = useAuthStore()
const isLoading = ref(true)
const error = ref<ApiError | null>(null)
const dashboardData = ref<{ stats: DashboardStats; recentActivity: Activity[] } | null>(null)

const stats = computed(() => {
  if (!dashboardData.value) {
    return [
      { name: 'Total Assistants', value: '...' },
      { name: 'Active Chats', value: '...' },
      { name: 'Messages Today', value: '...' },
      { name: 'API Usage', value: '...' },
    ]
  }
  return [
    { name: 'Total Assistants', value: dashboardData.value.stats.totalAssistants },
    { name: 'Active Chats', value: dashboardData.value.stats.activeChats },
    { name: 'Messages Today', value: dashboardData.value.stats.messagesToday },
    { name: 'API Usage', value: dashboardData.value.stats.apiUsage },
  ]
})

const recentActivity = computed(() => dashboardData.value?.recentActivity || [])

const quickActions = [
  {
    name: 'Create Assistant',
    description: 'Build a new AI assistant',
    href: '/dashboard/assistants/create',
    icon: PlusIcon,
  },
  {
    name: 'Start Chat',
    description: 'Begin a new conversation',
    href: '/dashboard/chat',
    icon: ChatBubbleLeftRightIcon,
  },
  {
    name: 'Manage Profile',
    description: 'Update your settings',
    href: '/dashboard/profile',
    icon: CogIcon,
  },
]

async function fetchDashboardData() {
  isLoading.value = true
  error.value = null
  const response = await apiClient.get<{ stats: DashboardStats; recentActivity: Activity[] }>('/dashboard/stats')
  if (response.success) {
    dashboardData.value = response.data
  } else {
    error.value = response.error
    console.error('Error loading dashboard data:', response.error)
  }
  isLoading.value = false
}

onMounted(fetchDashboardData);
</script>