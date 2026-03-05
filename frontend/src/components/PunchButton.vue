<template>
  <button
    class="punch-button"
    :class="[variantClass, { 'disabled': disabled }]"
    :disabled="disabled"
    @click="handleClick"
  >
    <div class="button-content">
      <svg v-if="icon" class="button-icon" viewBox="0 0 24 24" fill="currentColor">
        <path :d="iconPath" />
      </svg>
      <span class="button-text">{{ label }}</span>
    </div>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  variant: {
    type: String,
    default: 'primary', // primary, secondary
    validator: (value) => ['primary', 'secondary'].includes(value)
  },
  icon: {
    type: String,
    default: 'check'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const variantClass = computed(() => {
  return props.variant === 'primary' ? 'btn-primary' : 'btn-secondary'
})

const iconPath = computed(() => {
  const icons = {
    check: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z',
    logout: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11H7v-2h10v2z',
    break: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z'
  }
  return icons[props.icon] || icons.check
})

const handleClick = () => {
  if (!props.disabled) {
    emit('click')
  }
}
</script>

<style scoped>
.punch-button {
  width: 100%;
  padding: 1.5rem;
  border-radius: 12px;
  border: none;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.punch-button:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.punch-button:active:not(.disabled) {
  transform: translateY(0);
}

.punch-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-primary:hover:not(.disabled) {
  background-color: var(--primary-hover);
}

.btn-secondary {
  background-color: var(--secondary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(.disabled) {
  background-color: var(--secondary-hover);
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.button-icon {
  width: 2.5rem;
  height: 2.5rem;
}

.button-text {
  font-size: 1rem;
}
</style>
