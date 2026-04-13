<template>
  <Card
    title="今日打卡總覽"
    class="attendance-overview-card"
  >
    <!-- 區塊 A：今日狀態 -->
    <TodayStatusSection 
      :punch-in="todayStatus.punch_in"
      :punch-out="todayStatus.punch_out"
    />

    <!-- 區塊 B：打卡操作 -->
    <PunchActionsSection 
      :can-punch-in="canPunchIn"
      :can-punch-out="canPunchOut"
      :has-punched-in="!!todayStatus.punch_in"
      :has-punched-out="!!todayStatus.punch_out"
      :is-loading="isLoading"
      @punch-in="$emit('punch-in')"
      @punch-out="$emit('punch-out')"
    />

    <!-- 區塊 C：最近打卡記錄 -->
    <RecentPunchLogsSection 
      :logs="recentLogs"
      :initial-expanded="isRecentLogsExpanded"
    />
  </Card>
</template>

<script setup>
import Card from '@/components/Card.vue'
import TodayStatusSection from './TodayStatusSection.vue'
import PunchActionsSection from './PunchActionsSection.vue'
import RecentPunchLogsSection from './RecentPunchLogsSection.vue'

// Props - 從 Home.vue 接收數據
const props = defineProps({
  todayStatus: {
    type: Object,
    required: true
  },
  recentLogs: {
    type: Array,
    default: () => []
  },
  canPunchIn: {
    type: Boolean,
    default: false
  },
  canPunchOut: {
    type: Boolean,
    default: false
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  isRecentLogsExpanded: {
    type: Boolean,
    default: false
  }
})

// Emits - 向上傳遞事件
defineEmits(['punch-in', 'punch-out'])
</script>

<style scoped>
.attendance-overview-card {
  margin-bottom: 16px;
}
</style>
