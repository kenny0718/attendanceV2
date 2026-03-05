<template>
  <div class="card bg-white rounded-lg shadow-md p-6">
    <h2 v-if="title" class="card-title text-xl font-semibold text-heading mb-4">
      {{ title }}
    </h2>
    <div class="card-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.card {
  transition: var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}
</style>
