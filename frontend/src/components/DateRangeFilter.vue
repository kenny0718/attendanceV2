<template>
  <div class="date-range-filter">
    <div class="date-field">
      <label class="field-label">開始日期</label>
      <input
        type="date"
        class="date-input"
        :value="localStart"
        @change="onStartChange"
      />
    </div>
    <span class="range-sep">～</span>
    <div class="date-field">
      <label class="field-label">結束日期</label>
      <input
        type="date"
        class="date-input"
        :value="localEnd"
        @change="onEndChange"
      />
    </div>
    <button class="clear-btn" @click="clear" title="清除日期篩選">✕ 清除</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import dayjs from 'dayjs'

const TZ = 'Asia/Taipei'

const emit = defineEmits(['change'])

const localStart = ref('')
const localEnd   = ref('')

function toISO(dateStr, isEnd = false) {
  if (!dateStr) return null
  const d = dayjs.tz(dateStr, TZ)
  return isEnd ? d.add(1, 'day').startOf('day').toISOString() : d.startOf('day').toISOString()
}

function onStartChange(e) {
  localStart.value = e.target.value
  emitChange()
}

function onEndChange(e) {
  localEnd.value = e.target.value
  emitChange()
}

function emitChange() {
  emit('change', {
    start_date: toISO(localStart.value, false),
    end_date:   toISO(localEnd.value, true)
  })
}

function clear() {
  localStart.value = ''
  localEnd.value   = ''
  emit('change', { start_date: null, end_date: null })
}
</script>

<style scoped>
.date-range-filter {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.date-field {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.field-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.date-input {
  padding: 6px 10px;
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--text-primary);
  background: white;
  outline: none;
  transition: var(--transition-base);
}

.date-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-lighter);
}

.range-sep {
  color: var(--text-hint);
  font-size: 1rem;
  padding-bottom: 6px;
}

.clear-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  background: white;
  color: var(--text-secondary);
  font-size: 0.82rem;
  cursor: pointer;
  transition: var(--transition-base);
}

.clear-btn:hover {
  border-color: var(--error);
  color: var(--error);
  background: var(--error-bg);
}
</style>
