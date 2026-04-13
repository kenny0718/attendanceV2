<template>
  <div class="page-shell">
    <div
      class="page-container"
      :style="containerStyle"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  maxWidth: {
    type: String,
    default: '980px',
  },
})

const containerStyle = computed(() => ({
  maxWidth: props.maxWidth,
}))
</script>

<style scoped>
.page-shell {
  min-height: 100vh;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.page-container {
  margin: 0 auto;
  padding: 24px 16px 48px;
  display: grid;
  gap: 18px;
  width: 100%;
  box-sizing: border-box;
}

@media (max-width: 720px) {
  .page-container {
    padding: 20px 14px 40px;
    gap: 16px;
  }
}
</style>
