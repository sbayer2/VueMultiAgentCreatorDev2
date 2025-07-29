<template>
  <RouterView />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(async () => {
  // Check if user is authenticated on app mount
  await authStore.checkAuth()
})
</script>

<style scoped>
/* App-level styles if needed */
</style>