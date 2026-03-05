<template>
  <div class="status-card bg-bg-card rounded-md p-4 text-center border border-border-light">
    <div class="status-label text-sm text-text-secondary mb-2">
      {{ label }}
    </div>
    <div 
      class="status-value text-2xl font-semibold"
      :class="valueClass"
    >
      {{ value }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: String,
    required: true
  },
  valueClass: {
    type: String,
    default: 'text-text-primary'
  }
})
</script>

<style scoped>
.status-card {
  transition: var(--transition-base);
}

.status-card:hover {
  background-color: var(--bg-hover);
}

.status-value.active {
  color: var(--primary);
}

.status-value.empty {
  color: var(--text-hint);
}
</style>
