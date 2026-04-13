<template>
  <div
    v-if="breakPunches.length > 0"
    class="break-records-section"
  >
    <div 
      class="records-header-inline"
      @click="toggleExpanded"
    >
      <h3 class="subsection-title">
        今日外出 / 返回紀錄
      </h3>
      <div class="header-right">
        <span class="count-badge">
          {{ breakPunches.length }} 筆
        </span>
        <svg 
          class="expand-icon"
          :class="{ 'expanded': isExpanded }"
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>
    </div>
    
    <div
      v-show="isExpanded"
      class="records-content"
    >
      <div class="break-list">
        <div
          v-for="punch in breakPunches.slice(0, 10)"
          :key="punch.punch_id"
          class="break-item"
        >
          <div class="break-icon">
            <svg
              v-if="punch.punch_type === 'break_start'"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z"
                clip-rule="evenodd"
              />
            </svg>
            <svg
              v-else
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          
          <div class="break-info">
            <div class="break-type-time">
              <span class="break-type">
                {{ punch.punch_type === 'break_start' ? '外出' : '返回' }}
              </span>
              <span class="break-time">
                {{ formatTime(punch.punch_time) }}
              </span>
            </div>
            <div
              v-if="punch.notes"
              class="break-notes"
            >
              {{ punch.notes }}
            </div>
          </div>
          
          <div class="break-actions">
            <a
              v-if="punch.location_lat && punch.location_lng"
              :href="`https://www.google.com/maps?q=${punch.location_lat},${punch.location_lng}`"
              target="_blank"
              rel="noopener noreferrer"
              class="map-link"
              title="在 Google Maps 開啟"
            >
              <svg
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>地圖</span>
            </a>
            
            <button
              v-if="punch.punch_type === 'break_start'"
              class="edit-btn"
              title="編輯原因"
              @click="$emit('edit-note', punch)"
            >
              <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                />
              </svg>
            </button>
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
  breakPunches: {
    type: Array,
    default: () => []
  },
  initialExpanded: {
    type: Boolean,
    default: false
  }
})

// Emits
defineEmits(['edit-note'])

// Local state - 只管理展開/收合
const isExpanded = ref(props.initialExpanded)

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

// 格式化方法 - 以 Asia/Taipei 時區渲染，避免依賴瀏覽器本地時間
const formatTime = (timestamp) => {
  return dayjs(timestamp).tz(TZ).format('HH:mm')
}
</script>

<style scoped>
.break-records-section {
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

.break-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.break-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-main);
  border-radius: 12px;
  transition: background-color 0.2s;
}

.break-item:active {
  background: var(--bg-hover);
}

.break-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.break-icon svg {
  width: 20px;
  height: 20px;
}

.break-icon svg:first-child {
  color: var(--warning);
}

.break-icon svg:last-child {
  color: var(--success);
}

.break-info {
  flex: 1;
  min-width: 0;
}

.break-type-time {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.break-type {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.break-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.break-notes {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.break-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.map-link,
.edit-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 11px;
  transition: all 0.2s;
  border: none;
  background: transparent;
  cursor: pointer;
}

.map-link {
  color: var(--primary);
  text-decoration: none;
}

.map-link:active {
  background: var(--primary-light);
  color: white;
}

.edit-btn {
  color: var(--text-secondary);
}

.edit-btn:active {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.map-link svg,
.edit-btn svg {
  width: 14px;
  height: 14px;
}
</style>
