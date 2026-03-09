<template>
  <div class="home-page">
    <Navbar />
    
    <div class="container">
      <!-- 今日狀態 - 簡化為只顯示上班/下班 -->
      <Card title="今日狀態" class="status-section">
        <div class="status-grid-simple">
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
        </div>
      </Card>

      <!-- 打卡操作 - 只有上班/下班 -->
      <div class="section-title">
        <h2>打卡操作</h2>
      </div>
      <div class="punch-grid-main">
        <!-- 上班打卡 -->
        <div 
          @click="handlePunch('IN')"
          :class="[
            'punch-card',
            { 'disabled': !canPunchIn || isLoading },
            { 'completed': todayStatus.punch_in }
          ]"
        >
          <div class="card-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          </div>
          <div class="card-label">上班打卡</div>
          <div v-if="todayStatus.punch_in" class="status-badge completed">✓</div>
        </div>

        <!-- 下班打卡 -->
        <div 
          @click="handlePunch('OUT')"
          :class="[
            'punch-card',
            { 'disabled': !canPunchOut || isLoading },
            { 'completed': todayStatus.punch_out }
          ]"
        >
          <div class="card-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </div>
          <div class="card-label">下班打卡</div>
          <div v-if="todayStatus.punch_out" class="status-badge completed">✓</div>
        </div>
      </div>

      <!-- 最近打卡記錄 - 可收合 -->
      <div class="records-collapsible">
        <div 
          class="records-header"
          @click="toggleRecentLogs"
        >
          <h2>最近打卡記錄</h2>
          <div class="header-right">
            <span v-if="recentLogs.length > 0" class="count-badge">
              {{ recentLogs.length }} 筆
            </span>
            <svg 
              class="expand-icon"
              :class="{ 'expanded': isRecentLogsExpanded }"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
        
        <div v-show="isRecentLogsExpanded" class="records-content">
          <div v-if="recentLogs.length === 0" class="empty-state">
            <p>尚無打卡記錄</p>
          </div>
          <div v-else class="log-list">
            <div 
              v-for="log in recentLogs" 
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

      <!-- 外出原因輸入 -->
      <div class="section-title">
        <h2>外出原因</h2>
      </div>
      <Card class="reason-section">
        <div class="reason-input-area">
          <label class="input-label">
            外出原因
          </label>
          
          <!-- 常用原因快速選擇 -->
          <div class="reason-chips">
            <button
              v-for="reason in reasonPresets"
              :key="reason"
              @click="selectReason(reason)"
              :class="[
                'reason-chip',
                { 'selected': breakOutReason === reason }
              ]"
            >
              {{ reason }}
            </button>
          </div>
          
          <!-- 自訂原因 -->
          <div v-if="reasonCustoms.length > 0" class="custom-reasons">
            <button
              v-for="reason in reasonCustoms"
              :key="reason"
              @click="selectReason(reason)"
              :class="[
                'reason-chip custom',
                { 'selected': breakOutReason === reason }
              ]"
            >
              {{ reason }}
              <span 
                @click.stop="removeCustomReason(reason)"
                class="remove-btn"
              >
                ✕
              </span>
            </button>
          </div>
          
          <!-- 原因輸入欄 -->
          <input
            v-model="breakOutReason"
            type="text"
            class="reason-input"
            placeholder="請輸入外出原因"
            maxlength="50"
          />
          
          <!-- 新增自訂原因 -->
          <div class="add-custom-reason">
            <input
              v-model="newCustomReason"
              @keyup.enter="addCustomReason"
              type="text"
              placeholder="新增常用原因..."
              class="custom-input"
              maxlength="20"
            />
            <button
              @click="addCustomReason"
              :disabled="!newCustomReason.trim()"
              class="add-btn"
            >
              ＋新增
            </button>
          </div>
        </div>
      </Card>

      <!-- 外出 / 返回打卡 - 移到外出原因下方 -->
      <div class="section-title">
        <h2>外出 / 返回</h2>
      </div>
      <div class="punch-grid-break">
        <!-- 外出打卡 -->
        <div 
          @click="handleBreakOutPunch"
          :class="[
            'punch-card',
            { 'disabled': !canBreakOut || isLoading }
          ]"
        >
          <div class="card-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </div>
          <div class="card-label">外出打卡</div>
          <div v-if="todayStatus.is_on_break" class="status-badge active">外出中</div>
        </div>

        <!-- 返回打卡 -->
        <div 
          @click="handleBreakInPunch"
          :class="[
            'punch-card',
            { 'disabled': !canBreakIn || isLoading }
          ]"
        >
          <div class="card-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 16l-4-4m0 0l4-4m-4 4h18" />
            </svg>
          </div>
          <div class="card-label">返回打卡</div>
        </div>
      </div>

      <!-- 今日外出/返回記錄 - 可收合 -->
      <div v-if="breakPunches.length > 0" class="records-collapsible">
        <div 
          class="records-header"
          @click="toggleBreakLogs"
        >
          <h2>今日外出 / 返回紀錄</h2>
          <div class="header-right">
            <span class="count-badge">
              {{ breakPunches.length }} 筆
            </span>
            <svg 
              class="expand-icon"
              :class="{ 'expanded': isBreakLogsExpanded }"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
        
        <div v-show="isBreakLogsExpanded" class="records-content">
          <div class="break-list">
            <div
              v-for="punch in breakPunches.slice(0, 10)"
              :key="punch.punch_id"
              class="break-item"
            >
              <div class="break-icon">
                <svg v-if="punch.punch_type === 'break_start'" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd" />
                </svg>
                <svg v-else fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
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
                <div v-if="punch.notes" class="break-notes">
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
                  <svg fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
                  </svg>
                  <span>地圖</span>
                </a>
                
                <button
                  v-if="punch.punch_type === 'break_start'"
                  @click="editPunchNote(punch)"
                  class="edit-btn"
                  title="編輯原因"
                >
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷功能 -->
      <div class="section-title">
        <h2>快捷功能</h2>
      </div>
      <div class="shortcut-grid">
        <div class="shortcut-card disabled">
          <div class="card-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div class="card-label">個人資料</div>
        </div>

        <div class="shortcut-card disabled">
          <div class="card-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div class="card-label">請假申請</div>
        </div>

        <div class="shortcut-card disabled">
          <div class="card-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="card-label">補打卡申請</div>
        </div>
      </div>

      <!-- Toast 提示 -->
      <div 
        v-if="showSuccessMessage" 
        class="toast success"
      >
        ✓ {{ successMessage }}
      </div>

      <div 
        v-if="showErrorMessage" 
        class="toast error"
      >
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <span>{{ errorMessage }}</span>
      </div>
    </div>

    <!-- 編輯外出原因對話框 -->
    <div v-if="showEditDialog" class="dialog-overlay" @click.self="cancelEdit">
      <div class="dialog-content">
        <h3 class="dialog-title">編輯外出原因</h3>
        
        <div class="dialog-body">
          <label class="dialog-label">
            原因說明
          </label>
          <input
            v-model="editingNote"
            type="text"
            class="dialog-input"
            placeholder="例如：拜訪客戶-A客戶"
            @keyup.enter="saveEditedNote"
            @keyup.esc="cancelEdit"
          />
          <p class="dialog-hint">
            提示：可以在原因後面加上詳細說明
          </p>
        </div>
        
        <div class="dialog-actions">
          <button
            @click="cancelEdit"
            class="dialog-btn cancel"
          >
            取消
          </button>
          <button
            @click="saveEditedNote"
            class="dialog-btn confirm"
          >
            保存
          </button>
        </div>
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
import { useLocation } from '@/composables/useLocation'
import Card from '@/components/Card.vue'
import StatusCard from '@/components/StatusCard.vue'

const attendanceStore = useAttendanceStore()
const { 
  todayStatus, 
  recentLogs, 
  isLoading,
  breakPunches,
  reasonPresets,
  reasonCustoms,
} = storeToRefs(attendanceStore)

const canPunchIn = computed(() => attendanceStore.canPunchIn)
const canPunchOut = computed(() => attendanceStore.canPunchOut)
const canBreakOut = computed(() => attendanceStore.canBreakOut)
const canBreakIn = computed(() => attendanceStore.canBreakIn)
const formattedTodayStatus = computed(() => attendanceStore.formattedTodayStatus)

const showSuccessMessage = ref(false)
const showErrorMessage = ref(false)
const errorMessage = ref('')
const successMessage = ref('打卡成功')

const breakOutReason = ref('')
const newCustomReason = ref('')

const showEditDialog = ref(false)
const editingPunch = ref(null)
const editingNote = ref('')

const isRecentLogsExpanded = ref(false)
const isBreakLogsExpanded = ref(false)

const deviceType = ref('pc')

const {
  location: currentLocation,
  error: locationError,
  isLoading: locationLoading,
  deviceType: detectedDeviceType,
  isGPSRequired,
  getLocationIfRequired
} = useLocation()

const toggleRecentLogs = () => {
  isRecentLogsExpanded.value = !isRecentLogsExpanded.value
}

const toggleBreakLogs = () => {
  isBreakLogsExpanded.value = !isBreakLogsExpanded.value
}

const formatDateTime = (timestamp) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

const formatTime = (timestamp) => {
  return dayjs(timestamp).format('HH:mm')
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

const handlePunch = async (type) => {
  attendanceStore.clearError()
  
  try {
    // 呼叫 store 的 punch 方法，它會自動刷新狀態
    // store 會保留 punch_in 和 punch_out 時間
    await attendanceStore.punch(type, '')
    
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('打卡失敗:', error)
    
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
    showErrorMessage.value = true
    
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}

const handleBreakOutPunch = async () => {
  if (!breakOutReason.value.trim()) {
    errorMessage.value = '請先輸入外出原因'
    showErrorMessage.value = true
    setTimeout(() => {
      showErrorMessage.value = false
    }, 3000)
    return
  }

  attendanceStore.clearError()
  
  try {
    const gpsData = await getLocationIfRequired()
    
    const payload = {
      notes: breakOutReason.value.trim()
    }
    
    if (gpsData) {
      payload.location = {
        latitude: gpsData.latitude,
        longitude: gpsData.longitude
      }
    }
    
    await attendanceStore.punchWithLocation('BREAK_OUT', payload)
    
    breakOutReason.value = ""
    
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
    
  } catch (error) {
    console.error('外出打卡失敗:', error)
    
    if (error.response?.status === 403 && 
        error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION') {
      let message = error.response.data.detail.error || '不在允許的打卡範圍內'
      
      if (error.response.data.detail.nearest_location) {
        const nearest = error.response.data.detail.nearest_location
        message += `\n\n最近的允許地點：${nearest.name}\n距離：${nearest.distance_meters} 公尺`
      }
      
      errorMessage.value = message
    } else if (error.code === 'PERMISSION_DENIED') {
      errorMessage.value = '需要定位權限才能外出打卡\n請在瀏覽器設定中允許定位後重試'
    } else if (error.code === 'TIMEOUT') {
      errorMessage.value = '定位請求逾時\n請確認 GPS 訊號良好後重試'
    } else if (error.code === 'POSITION_UNAVAILABLE') {
      errorMessage.value = '無法取得定位資訊\n請確認已開啟定位服務'
    } else {
      errorMessage.value = error.message || '打卡失敗，請稍後再試'
    }
    
    showErrorMessage.value = true
    
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}

const handleBreakInPunch = async () => {
  attendanceStore.clearError()
  
  try {
    await attendanceStore.punch('BREAK_IN', '')
    
    breakOutReason.value = ''
    
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('返回打卡失敗:', error)
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
    showErrorMessage.value = true
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}

const selectReason = (reason) => {
  breakOutReason.value = reason
}

const addCustomReason = () => {
  if (!newCustomReason.value.trim()) return
  
  attendanceStore.addCustomReason(newCustomReason.value.trim())
  breakOutReason.value = newCustomReason.value.trim()
  newCustomReason.value = ''
}

const removeCustomReason = (reason) => {
  attendanceStore.removeCustomReason(reason)
  if (breakOutReason.value === reason) {
    breakOutReason.value = ''
  }
}

const editPunchNote = (punch) => {
  if (punch.punch_type !== 'break_start') {
    return
  }
  
  editingPunch.value = punch
  editingNote.value = punch.notes || ''
  showEditDialog.value = true
}

const saveEditedNote = async () => {
  if (!editingPunch.value) return
  
  try {
    await attendanceApi.updatePunchNote(editingPunch.value.punch_id, {
      notes: editingNote.value
    })
    
    const index = breakPunches.value.findIndex(p => p.punch_id === editingPunch.value.punch_id)
    if (index !== -1) {
      breakPunches.value[index].notes = editingNote.value
    }
    
    showEditDialog.value = false
    editingPunch.value = null
    editingNote.value = ''
    
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

const cancelEdit = () => {
  showEditDialog.value = false
  editingPunch.value = null
  editingNote.value = ''
}

onMounted(() => {
  attendanceStore.fetchTodayStatus()
  attendanceStore.fetchRecentLogs()
  attendanceStore.loadBreakPunches()
  attendanceStore.hydrateReasonsFromLocalStorage()
  
  deviceType.value = detectDeviceType()
})
</script>

<style scoped>
/* 移動優先設計 - 色彩系統 */
:root {
  --primary: #4A6FA5;
  --primary-hover: #3D5A8A;
  --primary-light: #7BA3D1;
  --secondary: #F2E8DF;
  --heading: #1C3B6B;
  --text-primary: #2D3A52;
  --text-secondary: #5A6C7D;
  --text-hint: #9CA3AF;
  --bg-main: #F4F7F9;
  --bg-card: #FFFFFF;
  --bg-hover: #F0F4F8;
  --success: #2E7D32;
  --success-bg: #E8F5E9;
  --error: #C62828;
  --error-bg: #FFEBEE;
  --warning: #F57C00;
  --warning-bg: #FFF3E0;
  --border: #E5E7EB;
}

.home-page {
  min-height: 100vh;
  background-color: var(--bg-main);
  padding-bottom: 24px;
}

/* 容器 - 移動優先 */
.container {
  padding: 16px;
  max-width: 480px;
  margin: 0 auto;
}

/* 區塊標題 */
.section-title {
  margin-bottom: 12px;
  margin-top: 16px;
}

.section-title h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--heading);
}

/* 狀態區塊 - 簡化為 2 欄 */
.status-section {
  margin-bottom: 16px;
}

.status-grid-simple {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* 打卡卡片 - 主要打卡（上班/下班）*/
.punch-grid-main {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

/* 打卡卡片 - 外出/返回 */
.punch-grid-break {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.punch-card {
  background: var(--bg-card);
  border-radius: 18px;
  padding: 16px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  border: 2px solid transparent;
}

.punch-card:active {
  transform: scale(0.98);
}

.punch-card:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.punch-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--bg-main);
}

.punch-card.disabled:hover {
  transform: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.punch-card.completed {
  background: var(--success-bg);
  border-color: var(--success);
}

/* 卡片 Icon - 清晰的線條風格 */
.punch-card .card-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.punch-card.disabled .card-icon {
  color: #9CA3AF;
}

.punch-card.completed .card-icon {
  color: var(--success);
}

.punch-card .card-icon svg {
  width: 32px;
  height: 32px;
}

/* 卡片標籤 */
.punch-card .card-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
}

.punch-card.disabled .card-label {
  color: #9CA3AF;
}

/* 狀態徽章 */
.status-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 10px;
  font-weight: 600;
  line-height: 1;
}

.status-badge.completed {
  background: var(--success);
  color: white;
}

.status-badge.active {
  background: var(--warning);
  color: white;
}

/* 可收合區塊 */
.records-collapsible {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-bottom: 16px;
}

.records-header {
  min-height: 50px;
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
  user-select: none;
}

.records-header:active {
  background-color: var(--bg-hover);
}

.records-header h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--heading);
  margin: 0;
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
  padding: 0 16px 16px 16px;
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

/* 記錄列表 */
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

/* 外出記錄列表 */
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

/* 原因輸入區 */
.reason-section {
  margin-bottom: 16px;
}

.reason-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.reason-chips,
.custom-reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.reason-chip {
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 13px;
  border: none;
  background: var(--bg-main);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.reason-chip:active {
  transform: scale(0.95);
}

.reason-chip.selected {
  background: var(--primary);
  color: white;
  box-shadow: 0 2px 6px rgba(74, 111, 165, 0.3);
}

.reason-chip.custom {
  background: #EFF6FF;
  display: flex;
  align-items: center;
  gap: 6px;
}

.reason-chip.custom.selected {
  background: var(--secondary);
}

.remove-btn {
  font-size: 14px;
  opacity: 0.7;
  cursor: pointer;
  transition: opacity 0.2s;
}

.remove-btn:hover {
  opacity: 1;
}

.reason-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.2s;
}

.reason-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.1);
}

.add-custom-reason {
  display: flex;
  gap: 8px;
}

.custom-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 13px;
  transition: all 0.2s;
}

.custom-input:focus {
  outline: none;
  border-color: var(--primary);
}

.add-btn {
  padding: 10px 16px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.add-btn:active {
  background: var(--primary-hover);
  transform: scale(0.98);
}

.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 快捷功能卡片 */
.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.shortcut-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 14px;
  height: 96px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
}

.shortcut-card:active {
  transform: scale(0.98);
}

.shortcut-card:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.shortcut-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--bg-main);
}

.shortcut-card.disabled:hover {
  transform: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.shortcut-card .card-icon {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.shortcut-card.disabled .card-icon {
  color: #9CA3AF;
}

.shortcut-card .card-icon svg {
  width: 30px;
  height: 30px;
}

.shortcut-card .card-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
}

.shortcut-card.disabled .card-label {
  color: #9CA3AF;
}

/* Toast 提示 */
.toast {
  position: fixed;
  bottom: 24px;
  right: 16px;
  left: 16px;
  max-width: 400px;
  margin: 0 auto;
  padding: 14px 16px;
  border-radius: 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 1000;
  animation: slideUp 0.3s ease-out;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.toast.success {
  background: var(--success);
  color: white;
}

.toast.error {
  background: var(--error);
  color: white;
}

.toast svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* 對話框 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.dialog-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.dialog-body {
  margin-bottom: 20px;
}

.dialog-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.dialog-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.2s;
}

.dialog-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.1);
}

.dialog-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.dialog-btn {
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.dialog-btn:active {
  transform: scale(0.98);
}

.dialog-btn.cancel {
  background: var(--bg-main);
  color: var(--text-secondary);
}

.dialog-btn.cancel:active {
  background: var(--bg-hover);
}

.dialog-btn.confirm {
  background: var(--primary);
  color: white;
}

.dialog-btn.confirm:active {
  background: var(--primary-hover);
}

/* 桌面版調整 */
@media (min-width: 768px) {
  .container {
    max-width: 1200px;
    padding: 24px 32px;
  }
  
  .status-grid-simple {
    grid-template-columns: repeat(2, 1fr);
    max-width: 600px;
  }
  
  .punch-grid-main,
  .punch-grid-break {
    grid-template-columns: repeat(2, 1fr);
    max-width: 600px;
  }
  
  .shortcut-grid {
    grid-template-columns: repeat(6, 1fr);
  }
  
  .toast {
    right: 24px;
    left: auto;
    max-width: 400px;
  }
}
</style>
