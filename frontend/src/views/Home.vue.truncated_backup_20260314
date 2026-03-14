<template>
  <div class="home-page">
    <Navbar />

    <div class="container">
      <div class="main-grid">

        <!-- ===== Card 1: 今日打卡 ===== -->
        <div class="section-card">
          <h2 class="card-section-title">今日打卡</h2>

          <div class="today-status-row">
            <div class="status-item">
              <span class="status-label">上班時間</span>
              <span :class="['status-value', todayStatus.punch_in ? 'active' : 'empty']">{{ formattedTodayStatus.punch_in }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">下班時間</span>
              <span :class="['status-value', todayStatus.punch_out ? 'active' : 'empty']">{{ formattedTodayStatus.punch_out }}</span>
            </div>
          </div>

          <div class="punch-grid">
            <div @click="handlePunch('IN')" :class="['punch-card', { disabled: !canPunchIn || isLoading }, { completed: !!todayStatus.punch_in }]">
              <div class="punch-card-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
              </div>
              <div class="punch-card-label">上班打卡</div>
              <div v-if="todayStatus.punch_in" class="status-badge completed">✓</div>
            </div>
            <div @click="handlePunch('OUT')" :class="['punch-card', { disabled: !canPunchOut || isLoading }, { completed: !!todayStatus.punch_out }]">
              <div class="punch-card-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </div>
              <div class="punch-card-label">下班打卡</div>
              <div v-if="todayStatus.punch_out" class="status-badge completed">✓</div>
            </div>
          </div>

          <div class="subsection">
            <div class="subsection-header" @click="toggleRecentLogs">
              <span class="subsection-title">最近打卡記錄</span>
              <div class="header-right">
                <span v-if="recentLogs.length > 0" class="count-badge">{{ recentLogs.length }} 筆</span>
                <svg class="expand-icon" :class="{ expanded: isRecentLogsExpanded }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <div v-show="isRecentLogsExpanded" class="subsection-content">
              <div v-if="recentLogs.length === 0" class="empty-state">尚無打卡記錄</div>
              <div v-else class="log-list">
                <div v-for="log in recentLogs" :key="log.id" class="log-item">
                  <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
                  <span class="log-type">{{ getTypeLabel(log.attendance_type) }}</span>
                  <span :class="['log-status', getStatusClass(log)]">{{ getStatusLabel(log) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== Card 2: 外出管理 ===== -->
        <div class="section-card">
          <h2 class="card-section-title">外出管理</h2>

          <div class="subsection border-bottom">
            <span class="subsection-title">外出原因</span>
            <div class="reason-input-area">
              <div class="reason-chips">
                <button v-for="reason in reasonPresets" :key="reason" @click="selectReason(reason)" :class="['reason-chip', { selected: breakOutReason === reason }]">{{ reason }}</button>
              </div>
              <div v-if="reasonCustoms.length > 0" class="reason-chips">
                <button v-for="reason in reasonCustoms" :key="reason" @click="selectReason(reason)" :class="['reason-chip custom', { selected: breakOutReason === reason }]">
                  {{ reason }}
                  <span @click.stop="removeCustomReason(reason)" class="remove-btn">✕</span>
                </button>
              </div>
              <input v-model="breakOutReason" type="text" class="reason-input" placeholder="請輸入外出原因" maxlength="50" />
              <div class="add-custom-reason">
                <input v-model="newCustomReason" @keyup.enter="addCustomReason" type="text" placeholder="新增常用原因..." class="custom-input" maxlength="20" />
                <button @click="addCustomReason" :disabled="!newCustomReason.trim()" class="add-btn">＋新增</button>
              </div>
            </div>
          </div>

          <div class="subsection border-bottom">
            <span class="subsection-title">外出 / 返回</span>
            <div class="punch-grid">
              <div @click="handleBreakOutPunch" :class="['punch-card', { disabled: !canBreakOut || isLoading }]">
                <div class="punch-card-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </div>
                <div class="punch-card-label">外出打卡</div>
                <div v-if="todayStatus.is_on_break" class="status-badge active">外出中</div>
              </div>
              <div @click="handleBreakInPunch" :class="['punch-card', { disabled: !canBreakIn || isLoading }]">
                <div class="punch-card-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                  </svg>
                </div>
                <div class="punch-card-label">返回打卡</div>
              </div>
            </div>
          </div>

          <!-- 外出記錄 - 始終顯示，含空狀態 -->
          <div class="subsection">
            <div class="subsection-header" @click="toggleBreakLogs">
              <span class="subsection-title">今日外出記錄</span>
              <div class="header-right">
                <span v-if="breakPunches.length > 0" class="count-badge">{{ breakPunches.length }} 筆</span>
                <svg class="expand-icon" :class="{ expanded: isBreakLogsExpanded }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <div v-show="isBreakLogsExpanded" class="subsection-content">
              <div v-if="breakPunches.length === 0" class="empty-state">尚無外出記錄</div>
              <div v-else class="break-list">
                <div v-for="punch in breakPunches.slice(0, 10)" :key="punch.punch_id" class="break-item">
                  <div class="break-icon">
                    <svg v-if="punch.punch_type === 'break_start'" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd" /></svg>
                    <svg v-else fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
                  </div>
                  <div class="break-info">
                    <div class="break-type-time">
                      <span class="break-type">{{ punch.punch_type === 'break_start' ? '外出' : '返回' }}</span>
                      <span class="break-time">{{ formatTime(punch.punch_time) }}</span>
                    </div>
                    <div v-if="punch.notes" class="break-notes">{{ punch.notes }}</div>
                  </div>
                  <div class="break-actions">
                    <a v-if="punch.location_lat && punch.location_lng" :href="`https://www.google.com/maps?q=${punch.location_lat},${punch.location_lng}`" target="_blank" rel="noopener noreferrer" class="map-link" title="在 Google Maps 開啟">
                      <svg fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" /></svg>
                      <span>地圖</span>
                    </a>
                    <button v-if="punch.punch_type === 'break_start'" @click="editPunchNote(punch)" class="edit-btn" title="編輯原因">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== Card 3: 申請服務 ===== -->
        <div class="section-card">
          <h2 class="card-section-title">申請服務</h2>
          <div class="service-grid">
            <div class="service-item disabled">
              <div class="service-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div class="service-label">個人資料</div>
            </div>
            <div class="service-item disabled">
              <div class="service-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="service-label">請假申請</div>
            </div>
            <div class="service-item disabled">
              <div class="service-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div class="service-label">補打卡申請</div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Toast 提示 -->
    <div v-if="showSuccessMessage" class="toast success">✓ {{ successMessage }}</div>
    <div v-if="showErrorMessage" class="toast error">
      <svg fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- 編輯外出原因對話框 -->
    <div v-if="showEditDialog" class="dialog-overlay" @click.self="cancelEdit">
      <div class="dialog-content">
        <h3 class="dialog-title">編輯外出原因</h3>
        <div class="dialog-body">
          <label class="dialog-label">原因說明</label>
          <input v-model="editingNote" type="text" class="dialog-input" placeholder="例如：拜訪客戶-A客戶" @keyup.enter="saveEditedNote" @keyup.esc="cancelEdit" />
          <p class="dialog-hint">提示：可以在原因後面加上詳細說明</p>
        </div>
        <div class="dialog-actions">
          <button @click="cancelEdit" class="dialog-btn cancel">取消</button>
          <button @click="saveEditedNote" class="dialog-btn confirm">保存</button>
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
import AttendanceOverviewCard from '@/components/attendance/AttendanceOverviewCard.vue'
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
const isBreakLogsExpanded = ref(true)

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
  return dayjs(timestamp).tz('Asia/Taipei').format('YYYY-MM-DD HH:mm:ss')
}

const formatTime = (timestamp) => {
  return dayjs(timestamp).tz('Asia/Taipei').format('HH:mm')
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
  return '✓ 