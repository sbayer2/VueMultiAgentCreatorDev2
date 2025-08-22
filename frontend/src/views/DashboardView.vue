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
          <dd class="mt-1 flex items-baseline justify-between md:block lg:flex">
            <div class="flex items-baseline text-2xl font-semibold text-primary-600">
              {{ stat.value }}
            </div>
            <div
              :class="[
                stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600',
                'ml-2 flex items-baseline text-sm font-semibold'
              ]"
            >
              <component
                :is="stat.changeType === 'increase' ? ArrowUpIcon : ArrowDownIcon"
                class="h-4 w-4 flex-shrink-0 self-center"
                aria-hidden="true"
              />
              <span class="ml-1">{{ stat.change }}</span>
            </div>
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
import { useAssistantsStore } from '@/stores/assistants'
import { useConversationsStore } from '@/stores/conversations'
import { formatDate } from '@/utils/formatters'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { 
  ArrowUpIcon, 
  ArrowDownIcon,
  PlusIcon,
  ChatBubbleLeftRightIcon,
  CogIcon,
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()
const assistantsStore = useAssistantsStore()
const conversationsStore = useConversationsStore()

const isLoading = ref(true)
const recentActivity = ref<any[]>([])

const stats = computed(() => [
  {
    name: 'Total Assistants',
    value: assistantsStore.assistantsCount,
    change: '+10%',
    changeType: 'increase',
  },
  {
    name: 'Active Chats',
    value: conversationsStore.conversationsCount,
    change: '+5%',
    changeType: 'increase',
  },
  {
    name: 'Messages Today',
    value: '127',
    change: '-3%',
    changeType: 'decrease',
  },
  {
    name: 'API Usage',
    value: '89%',
    change: '+12%',
    changeType: 'increase',
  },
])

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

onMounted(async () => {
  try {
    // Fetch initial data
    await Promise.all([
      assistantsStore.fetchAssistants(),
      conversationsStore.fetchConversations(),
    ])
    
    // Simulate fetching recent activity
    setTimeout(() => {
      recentActivity.value = [
        {
          id: '1',
          title: 'New assistant created',
          description: 'Created "Customer Support Bot" assistant',
          timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        },
        {
          id: '2',
          title: 'Chat session started',
          description: 'Started conversation with "Sales Assistant"',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        },
        {
          id: '3',
          title: 'Profile updated',
          description: 'Changed notification preferences',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
        },
      ]
      isLoading.value = false
    }, 1000)
  } catch (error) {
    console.error('Error loading dashboard data:', error)
    isLoading.value = false
  }
})
</script>