<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'
import { storeToRefs } from 'pinia'

import { useAuthStore } from '@/stores/auth'
import { useStreamingStore } from '@/stores/streaming'

const authStore = useAuthStore()
const streamingStore = useStreamingStore()
const { isAuthenticated } = storeToRefs(authStore)

watch(
  isAuthenticated,
  (authed) => {
    if (authed) {
      streamingStore.connect()
      return
    }

    streamingStore.disconnect()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  streamingStore.disconnect()
})
</script>

<style scoped>
#app {
  min-height: 100vh;
}
</style>
