<template>
  <div class="home-page">
    <Navbar />
    
    <div class="container mx-auto px-4 py-8 max-w-6xl">
      <!-- 今日狀態 -->
      <Card title="今日狀態" class="mb-6">
        <div class="status-grid grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusCard 
            label="上班時間" 
            :value="formattedStatus.punch_in"
            :valueClass="todayStatus.punch_in ? 'active' : 'empty'"
          />
          <StatusCard 
            label="下班時間" 
            :value="formattedStatus.punch_out"
            :valueClass="todayStatus.punch_out ? 'active' : 'empty'"
          />
          <StatusCard 
            label="外出時間" 
            :value="formattedStatus.break_out"
            :valueClass="todayStatus.break_out ? 'active' : 'empty'"
          />
          <StatusCard 
            label="返回時間" 
            :value="formattedStatus.break_in"
            :valueClass="todayStatus.break_in ? 'active' : 'empty'"
          />
        </div>
      </Card>

      <!-- 打卡操作 -->
      <Card title="打卡操作" class="mb-6">
        <div class="punch-grid grid grid-cols-2 gap-4 mb-4">
          <PunchButton 
            label="上班打卡"
            variant="primary"
            icon="check"
            :disabled="!canPunchIn"
            @click="handlePunch('IN')"
          />
          <PunchButton 
            label="下班打卡"
            variant="primary"
            icon="logout"
            :disabled="!canPunchOut"
            @click="handlePunch('OUT')"
          />
          <PunchButton 
            label="外出打卡"
            variant="secondary"
            icon="break"
            :disabled="!canBreakOut"
            @click="handlePunch('BREAK_OUT')"
          />
          <PunchButton 
            label="返回打卡"
            variant="secondary"
            icon="check"
            :disabled="!canBreakIn"
            @click="handlePunch('BREAK_IN')"
          />
        </div>

        <!-- 提示訊息 -->
        <div class="punch-hint text-center text-sm text-text-secondary mt-4">
          <span v-if="!todayStatus.punch_in">請先打上班卡</span>
          <span v-else-if="!todayStatus.punch_out">已上班打卡</span>
          <span v-else>今日打卡已完成</span>
        </div>

        <!-- Loading 狀態 -->
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <p class="text-text-secondary mt-2">打卡中...</p>
        </div>
      </Card>

      <!-- 快速功能 -->
      <div class="quick-actions grid grid-cols-3 gap-4 mb-6">
        <button class="action-btn bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
          <svg class="action-icon w-8 h-8 mx-auto mb-2 text-primary" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm text-text-primary">個人資料</span>
        </button>

        <button class="action-btn bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
          <svg class="action-icon w-8 h-8 mx-auto mb-2 text-primary" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm text-text-primary">請假申請</span>
        </button>

        <button class="action-btn bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
          <svg class="action-icon w-8 h-8 mx-auto mb-2 text-primary" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm text-text-primary">補打卡申請</span>
        </button>
      </div>

      <!-- 最近打卡記錄 -->
      <Card title="最近打卡記錄">
        <div v-if="recentLogs.length === 0" class="empty-state text-center py-8 text-text-hint">
          <p>尚無打卡記錄</p>
        </div>
        <div v-else class="log-list space-y-3">
          <div 
            v-for="log in recentLogs" 
            :key="log.id"
            class="log-item flex items-center justify-between p-3 bg-bg-main rounded-lg hover:bg-bg-hover transition-colors"
          >
            <div class="log-time text-text-secondary">
              {{ formatDateTime(log.timestamp) }}
            </div>
            <div class="log-type font-medium text-text-primary">
              {{ getTypeLabel(log.attendance_type) }}
            </div>
            <div 
              class="log-status px-3 py-1 rounded-full text-sm"
              :class="getStatusClass(log)"
            >
              {{ getStatusLabel(log) }}
            </div>
          </div>
        </div>
      </Card>

      <!-- 成功提示 -->
      <div 
        v-if="showSuccessMessage" 
        class="success-toast fixed bottom-8 right-8 bg-success text-white px-6 py-3 rounded-lg shadow-xl"
      >
        ✓ 打卡成功
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAttendanceStore } from '@/stores/attendance'
import dayjs from 'dayjs'
import Navbar from '@/components/Navbar.vue'
import Card from '@/components/Card.vue'
import StatusCard from '@/components/StatusCard.vue'
import PunchButton from '@/components/PunchButton.vue'

const attendanceStore = useAttendanceStore()
const { todayStatus, recentLogs, isLoading } = storeToRefs(attendanceStore)
const { canPunchIn, canPunchOut, canBreakOut, canBreakIn, formattedTodayStatus } = storeToRefs(attendanceStore)

const showSuccessMessage = ref(false)

// 格式化日期時間
const formatDateTime = (timestamp) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

// 獲取打卡類型標籤
const getTypeLabel = (type) => {
  const labels = {
    'IN': '上班',
    'OUT': '下班',
    'BREAK_OUT': '外出',
    'BREAK_IN': '返回'
  }
  return labels[type] || type
}

// 獲取狀態標籤
const getStatusLabel = (log) => {
  if (log.is_late) {
    return `⚠ 遲到 ${log.late_minutes} 分鐘`
  }
  return '✓ 正常'
}

// 獲取狀態樣式
const getStatusClass = (log) => {
  if (log.is_late) {
    return 'bg-warning-bg text-warning'
  }
  return 'bg-success-bg text-success'
}

// 處理打卡
const handlePunch = async (type) => {
  try {
    await attendanceStore.punch(type)
    
    // 顯示成功訊息
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('打卡失敗:', error)
    alert('打卡失敗：' + (error.message || '未知錯誤'))
  }
}

// 頁面載入時獲取狀態
onMounted(() => {
  attendanceStore.fetchTodayStatus()
  attendanceStore.fetchRecentLogs()
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background-color: var(--bg-main);
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--primary-lighter);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.success-toast {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
}
</style>
