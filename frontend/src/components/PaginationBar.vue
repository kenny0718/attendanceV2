<template>
  <div
    v-if="totalPages > 1"
    class="pagination-bar"
  >
    <button
      class="page-btn"
      :disabled="currentPage <= 1"
      @click="go(currentPage - 1)"
    >
      ‹ 上一頁
    </button>

    <div class="page-info">
      第 <strong>{{ currentPage }}</strong> / {{ totalPages }} 頁
      <span class="total-hint">（共 {{ total }} 筆）</span>
    </div>

    <button
      class="page-btn"
      :disabled="currentPage >= totalPages"
      @click="go(currentPage + 1)"
    >
      下一頁 ›
    </button>
  </div>
  <div
    v-else-if="total > 0"
    class="pagination-hint"
  >
    共 {{ total }} 筆
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total:  { type: Number, required: true },
  limit:  { type: Number, default: 20 },
  offset: { type: Number, default: 0 }
})

const emit = defineEmits(['change'])

const currentPage = computed(() => Math.floor(props.offset / props.limit) + 1)
const totalPages  = computed(() => Math.max(1, Math.ceil(props.total / props.limit)))

function go(page) {
  const newOffset = (page - 1) * props.limit
  emit('change', { offset: newOffset, limit: props.limit })
}
</script>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px 0;
}

.page-btn {
  padding: 6px 16px;
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  background: white;
  color: var(--text-primary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: var(--transition-base);
}

.page-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-lightest);
}

.page-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.page-info strong {
  color: var(--heading);
}

.total-hint {
  color: var(--text-hint);
  font-size: 0.78rem;
  margin-left: 4px;
}

.pagination-hint {
  text-align: center;
  padding: 10px 0;
  font-size: 0.82rem;
  color: var(--text-hint);
}
</style>
