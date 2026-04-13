<template>
  <section
    class="page-card"
    :class="customClass"
  >
    <slot />
  </section>
</template>

<script setup>
defineProps({
  customClass: {
    type: [String, Array, Object],
    default: '',
  },
})
</script>

<style scoped>
.page-card {
  background: rgba(255, 255, 255, 0.84);
  border-radius: 24px;
  padding: 24px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

@media (max-width: 720px) {
  .page-card {
    padding: 20px;
    border-radius: 20px;
  }
}
</style>
