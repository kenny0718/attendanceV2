<template>
  <div class="section-header" :class="{ 'section-header-between': align === 'between' }">
    <h2 class="section-title">
      <svg v-if="iconPath" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
      </svg>
      {{ title }}
    </h2>
      <div v-if="$slots.actions" class="section-actions">
        <slot name="actions" />
      </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  iconPath: {
    type: String,
    default: '',
  },
  align: {
    type: String,
    default: 'start',
  },
})
</script>

<style scoped>
.section-header {
  margin-bottom: 18px;
}

.section-header-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: #0f172a;
}

.section-title svg {
  width: 18px;
  height: 18px;
  color: #0ea5e9;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

@media (max-width: 720px) {
  .section-header-between,
  .section-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
