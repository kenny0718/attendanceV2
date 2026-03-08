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
          <span v-else-if="todayStatus.is_on_break">目前外出中（可繼續外出打卡或返回打卡）</span>
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
      <Card title="外出位置記錄（選用）" class="mb-6">
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
          <span>{{ outCheckpointLoading ? '提交中...' : '記錄當前位置' }}</span>
        </button>
        
        <!-- 今日外出打卡記錄 -->
        <div v-if="breakPunches.length > 0" class="checkpoint-list mt-4 pt-4 border-t border-gray-200">
          <h4 class="text-sm font-medium text-text-primary mb-2">今日外出打卡記錄</h4>
          <div class="space-y-2">
            <div
              v-for="punch in breakPunches.slice(0, 10)"
              :key="punch.punch_id"
              class="checkpoint-item flex items-center justify-between p-2 bg-bg-main rounded text-sm hover:bg-gray-50 cursor-pointer transition-colors"
              @click="editPunchNote(punch)"
            >
              <div class="flex items-center gap-2 flex-1">
                <svg v-if="punch.punch_type === 'break_start'" class="w-4 h-4 text-warning flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd" />
                </svg>
                <svg v-else class="w-4 h-4 text-success flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <!-- 只顯示原因，如果沒有原因則顯示類型 -->
                <span v-if="punch.notes" class="text-text-primary font-medium">{{ punch.notes }}</span>
                <span v-else class="text-text-secondary italic">{{ punch.punch_type === 'break_start' ? '外出' : '返回' }}</span>
                <!-- 編輯提示 -->
                <svg class="w-3 h-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-text-secondary text-xs">{{ formatTime(punch.punch_time) }}</span>
                <span v-if="punch.location_lat && punch.location_lng" class="text-xs text-success">📍</span>
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

    <!-- 編輯備註對話框 -->
    <div v-if="showEditDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="cancelEdit">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-text-primary mb-4">編輯外出原因</h3>
        
        <div class="mb-4">
          <label class="block text-sm font-medium text-text-secondary mb-2">
            原因說明
          </label>
          <input
            v-model="editingNote"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            placeholder="例如：拜訪客戶-A客戶"
            @keyup.enter="saveEditedNote"
            @keyup.esc="cancelEdit"
          />
          <p class="mt-1 text-xs text-text-secondary">
            提示：可以在原因後面加上詳細說明，例如「拜訪客戶-A客戶」
          </p>
        </div>
        
        <div class="flex gap-3 justify-end">
          <button
            @click="cancelEdit"
            class="px-4 py-2 text-sm font-medium text-text-secondary bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            取消
          </button>
          <button
            @click="saveEditedNote"
            class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-dark transition-colors"
          >
            保存
          </button>
        </div>
      </div>
    </div>

  </template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAttendanceStore } from '@/stores/attendance'
import { attendanceApi } from '@/api/attendance'
import dayjs from 'dayjs'
import { detectDeviceType } from '@/utils/locationAdapter'
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
  breakPunches,
  outCheckpointLoading,
  reasonPresets,
  reasonCustoms,
  lastSelectedReason
} = storeToRefs(attendanceStore)

// Getters 直接從 store 訪問
const canPunchIn = computed(() => attendanceStore.canPunchIn)
const canPunchOut = computed(() => attendanceStore.canPunchOut)
const canBreakOut = computed(() => attendanceStore.canBreakOut)
const canBreakIn = computed(() => attendanceStore.canBreakIn)
const formattedTodayStatus = computed(() => attendanceStore.formattedTodayStatus)
const canCreateOutCheckpoint = computed(() => attendanceStore.canCreateOutCheckpoint)
const allReasons = computed(() => attendanceStore.allReasons)

const showSuccessMessage = ref(false)
const showErrorMessage = ref(false)
const errorMessage = ref('')
const successMessage = ref('打卡成功')

// WP-11-11: OUT Checkpoint 狀態
const selectedReason = ref('')
const editingPunch = ref(null)
const editingNote = ref('')
const showEditDialog = ref(false)
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
    // 如果是外出打卡，使用選擇的原因
    let notes = ''
    if (type === 'BREAK_OUT' && selectedReason.value) {
      notes = selectedReason.value
    }
    
    await attendanceStore.punch(type, notes)
    
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

// 編輯打卡備註
const editPunchNote = (punch) => {
  // 只允許編輯外出記錄（break_start）
  if (punch.punch_type !== 'break_start') {
    return
  }
  
  editingPunch.value = punch
  editingNote.value = punch.notes || ''
  showEditDialog.value = true
}

// 保存編輯的備註
const saveEditedNote = async () => {
  if (!editingPunch.value) return
  
  try {
    // 調用 API 更新備註
    await attendanceApi.updatePunchNote(editingPunch.value.punch_id, {
      notes: editingNote.value
    })
    
    // 更新本地數據
    const index = breakPunches.value.findIndex(p => p.punch_id === editingPunch.value.punch_id)
    if (index !== -1) {
      breakPunches.value[index].notes = editingNote.value
    }
    
    // 關閉對話框
    showEditDialog.value = false
    editingPunch.value = null
    editingNote.value = ''
    
    // 顯示成功訊息
    successMessage.value = '備註已更新'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 2000)
  } catch (error) {
    console.error('更新備註失敗:', error)
    errorMessage.value = '更新失敗，請稍後再試'
    showErrorMessage.value = true
    setTimeout(() => {
      showErrorMessage.value = false
    }, 3000)
  }
}

// 取消編輯
const cancelEdit = () => {
  showEditDialog.value = false
  editingPunch.value = null
  editingNote.value = ''
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
    successMessage.value = '位置記錄成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
    
    // 不清除選擇的原因，方便下次使用
  } catch (error) {
    console.error('外出打點失敗:', error)
    
    // 顯示友善的錯誤訊息
    errorMessage.value = error.message || '位置記錄失敗，請稍後再試'
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
  attendanceStore.loadBreakPunches()
  attendanceStore.hydrateReasonsFromLocalStorage()
  
  // 設定裝置類型
  deviceType.value = detectDeviceType()
  
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
