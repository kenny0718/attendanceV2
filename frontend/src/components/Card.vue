<template>
  <div class="card surface-card">
    <h2 v-if="title" class="card-title">
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
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

.card:hover {
  box-shadow: var(--surface-card-hover-shadow);
}

.card-title {
  margin: 0 0 18px;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}
</style>
