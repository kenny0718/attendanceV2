<template>
  <div class="summary-card">
    <div class="summary-label">{{ label }}</div>
    <div :class="['summary-value', { empty: value === null || value === undefined || value === '—' }]">
      {{ displayValue }}
    </div>
    <div v-if="sub" class="summary-sub">{{ sub }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
  sub:   { type: String, default: '' }
})

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined) return '—'
  return props.value
})
</script>

<style scoped>
.summary-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: var(--shadow-sm);
  transition: var(--transition-base);
}

.summary-card:hover {
  box-shadow: var(--shadow-md);
}

.summary-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.summary-value {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--heading);
  line-height: 1.2;
}

.summary-value.empty {
  font-size: 1.2rem;
  color: var(--text-hint);
}

.summary-sub {
  font-size: 0.75rem;
  color: var(--text-hint);
}
</style>
