<template>
  <div class="today-status-section">
    <h3 class="subsection-title">
      今日狀態
    </h3>
    <div class="status-grid-simple">
      <StatusCard 
        label="上班時間" 
        :value="formattedPunchIn"
        :value-class="punchIn ? 'active' : 'empty'"
      />
      <StatusCard 
        label="下班時間" 
        :value="formattedPunchOut"
        :value-class="punchOut ? 'active' : 'empty'"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import StatusCard from '@/components/StatusCard.vue'

dayjs.extend(utc)
dayjs.extend(timezone)
// Asia/Taipei 時區常數，所有顯示皆使用此值，避免依賴瀏覽器本地時間
const TZ = 'Asia/Taipei'

// Props - 只接收必要的顯示數據
const props = defineProps({
  punchIn: {
    type: String,
    default: null
  },
  punchOut: {
    type: String,
    default: null
  }
})

// Computed - 格式化顯示（以 Asia/Taipei 時區渲染，避免依賴瀏覽器本地時間）
const formattedPunchIn = computed(() => {
  return props.punchIn ? dayjs(props.punchIn).tz(TZ).format('HH:mm') : '-'
})

const formattedPunchOut = computed(() => {
  return props.punchOut ? dayjs(props.punchOut).tz(TZ).format('HH:mm') : '-'
})
</script>

<style scoped>
.today-status-section {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--heading);
  margin-bottom: 12px;
}

.status-grid-simple {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
</style>
