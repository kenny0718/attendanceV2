<template>
  <div class="month-picker">
    <button
      v-for="opt in options"
      :key="opt.key"
      :class="['month-btn', { active: activeKey === opt.key }]"
      @click="select(opt)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import dayjs from 'dayjs'

const TZ = 'Asia/Taipei'

const emit = defineEmits(['select'])

const now = dayjs().tz(TZ)

const options = computed(() => {
  const result = []
  for (let i = 0; i < 3; i++) {
    const m = now.subtract(i, 'month')
    const start = m.startOf('month')
    const end   = m.add(1, 'month').startOf('month')
    result.push({
      key:   `${m.year()}-${String(m.month() + 1).padStart(2, '0')}`,
      label: i === 0 ? '本月' : i === 1 ? '上月' : m.format('M月'),
      start_date: start.toISOString(),
      end_date:   end.toISOString()
    })
  }
  return result
})

const activeKey = ref(options.value[0].key)

function select(opt) {
  activeKey.value = opt.key
  emit('select', { start_date: opt.start_date, end_date: opt.end_date })
}

// 初始化時自動 emit 本月
select(options.value[0])
</script>

<style scoped>
.month-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.month-btn {
  padding: 5px 14px;
  border-radius: 6px;
  border: 1px solid var(--border-medium);
  background: white;
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-base);
}

.month-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-lightest);
}

.month-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}
</style>
