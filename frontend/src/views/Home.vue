<template>
  <div class="home-page">
    <Navbar />
    
    <div class="container mx-auto px-4 py-8 max-w-6xl">
      <!-- 今日狀態 -->
      <Card title="今日狀態" class="mb-6">
        <div class="status-grid grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusCard 
            label="上班時間" 
            :value="formattedTodayStatus.punch_in"
            :valueClass="todayStatus.punch_in ? 'active' : 'empty'"
          />
          <StatusCard 
            label="下班時間" 
            :value="formattedTodayStatus.punch_out"
            :valueClass="todayStatus.punch_out ? 'active' : 'empty'"
          />
          <StatusCard 
            label="外出時間" 
            :value="formattedTodayStatus.break_out"
            :valueClass="todayStatus.break_out ? 'active' : 'empty'"
          />
          <StatusCard 
            label="返回時間" 
            :value="formattedTodayStatus.break_in"
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
            :disabled="!canPunchIn || isLoading"
            @click="handlePunch('IN')"
          />
          <PunchButton 
            label="下班打卡"
            variant="primary"
            icon="logout"
            :disabled="!canPunchOut || isLoading"
            @click="handlePunch('OUT')"
          />
          <PunchButton 
            label="外出打卡"
            variant="secondary"
            icon="break"
            :disabled="!canBreakOut || isLoading"
            @click="handlePunch('BREAK_OUT')"
          />
          <PunchButton 
            label="返回打卡"
            variant="secondary"
            icon="check"
            :disabled="!canBreakIn || isLoading"
            @click="handlePunch('BREAK_IN')"
          />
        </div>

        <!-- 提示訊息 -->
        <div class="punch-hint text-center text-sm text-text-secondary mt-4">
          <span v-if="!todayStatus.punch_in">請先打上班卡</span>
          <span v-else-if="todayStatus.is_on_break">目前外出中，請返回打卡</span>
          <span v-else-if="!todayStatus.punch_out">已上班打卡</span>
          <span v-else>今日打卡已完成</span>
        </div>

        <!-- Loading 狀態 -->
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <p class="text-text-secondary mt-2">打卡中...</p>
        </div>
      </Card>

      <!-- WP-11-11: OUT Checkpoint 區塊 -->
      <Card title="外出打點" class="mb-6">
        <!-- 原因選擇器 -->
        <div class="reason-picker mb-4">
          <label class="block text-sm font-medium text-text-primary mb-2">
            選擇外出原因
            <span v-if="deviceType === 'pc'" class="text-xs text-text-hint ml-2">(PC 不記錄定位)</span>
            <span v-else class="text-xs text-text-hint ml-2">(需要定位權限)</span>
          </label>
          
          <!-- Preset 原因 -->
          <div class="reason-chips flex flex-wrap gap-2 mb-3">
            <button
              v-for="reason in reasonPresets"
              :key="reason"
              @click="selectReason(reason)"
              :class="[
                'reason-chip px-4 py-2 rounded-full text-sm transition-all',
                selectedReason === reason 
                  ? 'bg-primary text-white shadow-md' 
                  : 'bg-white text-text-primary border border-gray-300 hover:border-primary hover:text-primary'
              ]"
            >
              {{ reason }}
            </button>
          </div>
          
          <!-- Custom 原因 -->
          <div v-if="reasonCustoms.length > 0" class="custom-reasons mb-3">
            <div class="flex flex-wrap gap-2">
              <button
                v-for="reason in reasonCustoms"
                :key="reason"
                @click="selectReason(reason)"
                :class="[
                  'reason-chip px-4 py-2 rounded-full text-sm transition-all flex items-center gap-2',
                  selectedReason === reason 
                    ? 'bg-primary text-white shadow-md' 
                    : 'bg-white text-text-primary border border-gray-300 hover:border-primary hover:text-primary'
                ]"
              >
                {{ reason }}
                <span 
                  @click.stop="removeCustomReason(reason)"
                  class="remove-btn text-xs opacity-70 hover:opacity-100"
                >
                  ✕
                </span>
              </button>
            </div>
          </div>
          
          <!-- 新增自訂原因 -->
          <div class="add-custom-reason flex gap-2">
            <input
              v-model="newCustomReason"
              @keyup.enter="addCustomReason"
              type="text"
              placeholder="輸入自訂原因..."
              class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-primary text-sm"
              maxlength="20"
            />
            <button
              @click="addCustomReason"
              :disabled="!newCustomReason.trim()"
              class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              ＋新增
            </button>
          </div>
        </div>
        
        <!-- OUT Checkpoint 按鈕 -->
        <button
          @click="handleOutCheckpoint"
          :disabled="!canCreateOutCheckpoint || outCheckpointLoading"
          class="w-full py-3 bg-secondary text-white rounded-lg font-medium hover:bg-secondary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          <svg v-if="!outCheckpointLoading" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
          </svg>
          <div v-else class="loading-spinner-small"></div>
          <span>{{ outCheckpointLoading ? '提交中...' : '外出打點' }}</span>
        </button>
        
        <!-- OUT Checkpoints 列表 -->
        <div v-if="outCheckpointList.length > 0" class="checkpoint-list mt-4 pt-4 border-t border-gray-200">
          <h4 class="text-sm font-medium text-text-primary mb-2">今日外出記錄</h4>
          <div class="space-y-2">
            <div
              v-for="checkpoint in outCheckpointList.slice(0, 5)"
              :key="checkpoint.checkpoint_id"
              class="checkpoint-item flex items-center justify-between p-2 bg-bg-main rounded text-sm"
            >
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-secondary" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
                </svg>
                <span class="text-text-primary">{{ checkpoint.notes || '外出' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-text-secondary text-xs">{{ formatTime(checkpoint.punch_time) }}</span>
                <span v-if="checkpoint.device_type === 'mobile'" class="text-xs text-success">📍</span>
                <span v-else class="text-xs text-text-hint">💻</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <!-- 快速功能 -->
      <div class="quick-actions grid grid-cols-3 gap-4 mb-6">
        <button class="action-btn bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow" disabled>
          <svg class="action-icon w-8 h-8 mx-auto mb-2 text-primary" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm text-text-primary">個人資料</span>
        </button>

        <button class="action-btn bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow" disabled>
          <svg class="action-icon w-8 h-8 mx-auto mb-2 text-primary" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm text-text-primary">請假申請</span>
        </button>

        <button class="action-btn bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow" disabled>
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
        class="success-toast fixed bottom-8 right-8 bg-success text-white px-6 py-3 rounded-lg shadow-xl z-50"
      >
        ✓ {{ successMessage }}
      </div>

      <!-- 錯誤提示 -->
      <div 
        v-if="showErrorMessage" 
        class="error-toast fixed bottom-8 right-8 bg-error text-white px-6 py-3 rounded-lg shadow-xl z-50 max-w-md"
      >
        <div class="flex items-start gap-2">
          <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <span>{{ errorMessage }}</span>
        </div>
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
const { 
  todayStatus, 
  recentLogs, 
  isLoading,
  outCheckpointList,
  outCheckpointLoading,
  reasonPresets,
  reasonCustoms,
  lastSelectedReason
} = storeToRefs(attendanceStore)

const { 
  canPunchIn, 
  canPunchOut, 
  canBreakOut, 
  canBreakIn, 
  formattedTodayStatus,
  canCreateOutCheckpoint,
  allReasons
} = storeToRefs(attendanceStore)

const showSuccessMessage = ref(false)
const showErrorMessage = ref(false)
const errorMessage = ref('')
const successMessage = ref('打卡成功')

// WP-11-11: OUT Checkpoint 狀態
const selectedReason = ref('')
const newCustomReason = ref('')
const deviceType = ref('pc')

// 格式化日期時間
const formatDateTime = (timestamp) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

// 格式化時間（僅時分）
const formatTime = (timestamp) => {
  return dayjs(timestamp).format('HH:mm')
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
  // 清除之前的錯誤
  attendanceStore.clearError()
  
  try {
    await attendanceStore.punch(type)
    
    // 顯示成功訊息
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('打卡失敗:', error)
    
    // 顯示友善的錯誤訊息
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
    showErrorMessage.value = true
    
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}

// WP-11-11: 選擇原因
const selectReason = (reason) => {
  selectedReason.value = reason
}

// WP-11-11: 新增自訂原因
const addCustomReason = () => {
  if (!newCustomReason.value.trim()) return
  
  attendanceStore.addCustomReason(newCustomReason.value)
  selectedReason.value = newCustomReason.value
  newCustomReason.value = ''
}

// WP-11-11: 移除自訂原因
const removeCustomReason = (reason) => {
  attendanceStore.removeCustomReason(reason)
  if (selectedReason.value === reason) {
    selectedReason.value = ''
  }
}

// WP-11-11: 處理 OUT checkpoint
const handleOutCheckpoint = async () => {
  // 驗證是否選擇原因
  if (!selectedReason.value) {
    errorMessage.value = '請先選擇原因'
    showErrorMessage.value = true
    setTimeout(() => {
      showErrorMessage.value = false
    }, 3000)
    return
  }
  
  attendanceStore.clearError()
  
  try {
    await attendanceStore.outCheckpointSubmit(selectedReason.value)
    
    // 顯示成功訊息
    successMessage.value = '外出打點成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
    
    // 不清除選擇的原因，方便下次使用
  } catch (error) {
    console.error('外出打點失敗:', error)
    
    // 顯示友善的錯誤訊息
    errorMessage.value = error.message || '外出打點失敗，請稍後再試'
    showErrorMessage.value = true
    
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}

// 頁面載入時獲取狀態
onMounted(() => {
  attendanceStore.fetchTodayStatus()
  attendanceStore.fetchRecentLogs()
  
  // WP-11-11: 載入 OUT checkpoints 和原因
  attendanceStore.loadOutCheckpoints()
  attendanceStore.hydrateReasonsFromLocalStorage()
  
  // 設定裝置類型
  deviceType.value = attendanceStore.detectDeviceType()
  
  // 恢復最後選擇的原因
  if (lastSelectedReason.value) {
    selectedReason.value = lastSelectedReason.value
  }
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
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--primary-lighter);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.success-toast,
.error-toast {
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

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reason-chip {
  cursor: pointer;
  user-select: none;
}

.reason-chip:active {
  transform: scale(0.95);
}

.remove-btn {
  cursor: pointer;
  transition: opacity 0.2s;
}

.checkpoint-item {
  transition: background-color 0.2s;
}

.checkpoint-item:hover {
  background-color: var(--bg-hover);
}
</style>
