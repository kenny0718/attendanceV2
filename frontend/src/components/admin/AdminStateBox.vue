<template>
  <div
    class="state-box"
    :class="variantClass"
  >
    <svg
      v-if="iconPath"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      stroke-width="2"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        :d="iconPath"
      />
    </svg>
    <div>
      <p
        v-if="title"
        class="state-title"
      >
        {{ title }}
      </p>
      <p
        v-if="message"
        class="state-msg"
      >
        {{ message }}
      </p>
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default',
  },
  title: {
    type: String,
    default: '',
  },
  message: {
    type: String,
    default: '',
  },
  iconPath: {
    type: String,
    default: '',
  },
})

const variantClass = computed(() => ({
  'state-error': props.variant === 'error',
  'state-empty': props.variant === 'empty',
  'state-notice': props.variant === 'notice',
  'state-success': props.variant === 'success',
}))
</script>

<style scoped>
.state-box {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  text-align: center;
}

.state-box svg {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  opacity: 0.45;
}

.state-title {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 700;
}

.state-msg {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
}

.state-error {
  color: #b91c1c;
}

.state-error svg {
  opacity: 1;
}

.state-success {
  color: #15803d;
}

.state-success svg {
  opacity: 1;
}
</style>
