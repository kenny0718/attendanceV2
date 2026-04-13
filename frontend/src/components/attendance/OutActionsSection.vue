<template>
  <div class="break-actions-section">
    <h3 class="subsection-title">
      外出 / 返回
    </h3>
    <div class="punch-grid-break">
      <!-- 外出打卡 -->
      <div 
        :class="[
          'punch-card',
          { 'disabled': !canBreakOut || isLoading }
        ]"
        @click="$emit('break-out')"
      >
        <div class="card-icon">
          <svg
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            stroke-width="2.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M17 8l4 4m0 0l-4 4m4-4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
        </div>
        <div class="card-label">
          外出打卡
        </div>
        <div
          v-if="isOnBreak"
          class="status-badge active"
        >
          外出中
        </div>
      </div>

      <!-- 返回打卡 -->
      <div 
        :class="[
          'punch-card',
          { 'disabled': !canBreakIn || isLoading }
        ]"
        @click="$emit('break-in')"
      >
        <div class="card-icon">
          <svg
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            stroke-width="2.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
            />
          </svg>
        </div>
        <div class="card-label">
          返回打卡
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Props - 只接收狀態數據
const props = defineProps({
  canBreakOut: {
    type: Boolean,
    default: false
  },
  canBreakIn: {
    type: Boolean,
    default: false
  },
  isOnBreak: {
    type: Boolean,
    default: false
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

// Emits - 只發送事件
defineEmits(['break-out', 'break-in'])
</script>

<style scoped>
.break-actions-section {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--heading);
  margin-bottom: 12px;
}

.punch-grid-break {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 0;
}

.punch-card {
  background: var(--bg-card);
  border-radius: 18px;
  padding: 16px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  border: 2px solid transparent;
}

.punch-card:active {
  transform: scale(0.98);
}

.punch-card:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.punch-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--bg-main);
}

.punch-card.disabled:hover {
  transform: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.punch-card.disabled .card-icon {
  color: #9CA3AF;
}

.card-icon svg {
  width: 32px;
  height: 32px;
}

.card-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
}

.punch-card.disabled .card-label {
  color: #9CA3AF;
}

.status-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 10px;
  font-weight: 600;
  line-height: 1;
}

.status-badge.active {
  background: var(--warning);
  color: white;
}
</style>
