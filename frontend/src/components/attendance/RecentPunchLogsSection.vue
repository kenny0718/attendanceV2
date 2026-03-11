<template>
  <div class="recent-logs-section">
    <div 
      class="records-header-inline"
      @click="toggleExpanded"
    >
      <h3 class="subsection-title">最近打卡記錄</h3>
      <div class="header-right">
        <span v-if="logs.length > 0" class="count-badge">
          {{ logs.length }} 筆
        </span>
        <svg 
          class="expand-icon"
          :class="{ 'expanded': isExpanded }"
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
    
    <div v-show="isExpanded" class="records-content">
      <div v-if="logs.length === 0" class="empty-state">
        <p>尚無打卡記錄</p>
      </div>
      <div v-else class="log-list">
        <div 
          v-for="log in logs" 
          :key="log.id"
          class="log-item"
        >
          <div class="log-time">
            {{ formatDateTime(log.timestamp) }}
          </div>
          <div class="log-type">
            {{ getTypeLabel(log.attendance_type) }}
          </div>
          <div 
            class="log-status"
            :class="getStatusClass(log)"
          >
            {{ getStatusLabel(log) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)
// Asia/Taipei 時區常數，所有顯示皆使用此值，避免依賴瀏覽器本地時間
const TZ = 'Asia/Taipei'

// Props - 只接收顯示數據
const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  },
  initialExpanded: {
    type: Boolean,
    default: false
  }
})

// Local state - 只管理展開/收合
const isExpanded = ref(props.initialExpanded)

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

// 格式化方法 - 以 Asia/Taipei 時區渲染，避免依賴瀏覽器本地時間
const formatDateTime = (timestamp) => {
  return dayjs(timestamp).tz(TZ).format('YYYY-MM-DD HH:mm:ss')
}

const getTypeLabel = (type) => {
  const labels = {
    'IN': '上班',
    'OUT': '下班',
    'BREAK_OUT': '外出',
    'BREAK_IN': '返回'
  }
  return labels[type] || type
}

const getStatusLabel = (log) => {
  if (log.is_late) {
    return `⚠ 遲到 ${log.late_minutes} 分鐘`
  }
  return '✓ 正常'
}

const getStatusClass = (log) => {
  if (log.is_late) {
    return 'late'
  }
  return 'normal'
}
</script>

<style scoped>
.recent-logs-section {
  border-bottom: none;
  padding-bottom: 0;
}

.records-header-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 8px 0;
  transition: background-color 0.2s;
  border-radius: 8px;
  margin: 0 -8px;
  padding: 8px;
}

.records-header-inline:active {
  background-color: var(--bg-hover);
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--heading);
  margin-bottom: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.count-badge {
  font-size: 12px;
  color: var(--text-secondary);
}

.expand-icon {
  width: 18px;
  height: 18px;
  color: var(--text-secondary);
  transition: transform 0.3s ease;
  flex-shrink: 0;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.records-content {
  padding: 0 0 16px 0;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--bg-main);
  border-radius: 12px;
  transition: background-color 0.2s;
}

.log-item:active {
  background: var(--bg-hover);
}

.log-time {
  font-size: 12px;
  color: var(--text-secondary);
  flex: 1;
}

.log-type {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 0 0 auto;
  margin: 0 12px;
}

.log-status {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 10px;
  flex: 0 0 auto;
}

.log-status.normal {
  background: var(--success-bg);
  color: var(--success);
}

.log-status.late {
  background: var(--error-bg);
  color: var(--error);
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-hint);
  font-size: 13px;
}
</style>
