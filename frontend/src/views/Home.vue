<template>
  <div class="home-page">
    <div class="container">
      <Navbar />

      <AttendanceOverviewCard
        :today-status="todayStatus"
        :recent-logs="recentLogs"
        :can-punch-in="canPunchIn"
        :can-punch-out="canPunchOut"
        :is-loading="isLoading"
        :is-recent-logs-expanded="isRecentLogsExpanded"
        @punch-in="handlePunch('IN')"
        @punch-out="handlePunch('OUT')"
      />

      <OutingOverviewCard
        :reason-presets="reasonPresets"
        :reason-customs="reasonCustoms"
        :selected-reason="breakOutReason"
        :new-custom-reason="newCustomReason"
        :can-break-out="canBreakOut"
        :can-break-in="canBreakIn"
        :is-on-break="todayStatus.is_on_break"
        :is-loading="isLoading"
        :break-punches="breakPunches"
        :is-break-logs-expanded="isBreakLogsExpanded"
        @select-reason="selectReason"
        @remove-custom-reason="removeCustomReason"
        @add-custom-reason="addCustomReason"
        @update:selected-reason="breakOutReason = $event"
        @update:new-custom-reason="newCustomReason = $event"
        @break-out="handleBreakOutPunch"
        @break-in="handleBreakInPunch"
        @edit-note="editPunchNote"
      />

      <PersonalServiceCard />

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
        <svg
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clip-rule="evenodd"
          />
        </svg>
        <span>{{ errorMessage }}</span>
      </div>
    </div>

    <div
      v-if="showEditDialog"
      class="dialog-overlay"
      @click.self="cancelEdit"
    >
      <div class="dialog-content">
        <h3 class="dialog-title">
          編輯外出原因
        </h3>

        <div class="dialog-body">
          <label class="dialog-label">原因說明</label>
          <input
            v-model="editingNote"
            type="text"
            class="dialog-input"
            placeholder="例如：拜訪客戶-A客戶"
            @keyup.enter="saveEditedNote"
            @keyup.esc="cancelEdit"
          >
          <p class="dialog-hint">
            提示：可以在原因後面加上詳細說明
          </p>
        </div>

        <div class="dialog-actions">
          <button
            class="dialog-btn cancel"
            @click="cancelEdit"
          >
            取消
          </button>
          <button
            class="dialog-btn confirm"
            @click="saveEditedNote"
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
import { detectDeviceType } from '@/utils/locationAdapter'
import Navbar from '@/components/Navbar.vue'
import { useLocation } from '@/composables/useLocation'
import AttendanceOverviewCard from '@/components/attendance/AttendanceOverviewCard.vue'
import OutingOverviewCard from '@/components/attendance/OutingOverviewCard.vue'
import PersonalServiceCard from '@/components/attendance/PersonalServiceCard.vue'

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

const { getLocationIfRequired } = useLocation()

const handlePunch = async (type) => {
  attendanceStore.clearError()

  try {
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
    const payload = { notes: breakOutReason.value.trim() }

    if (gpsData) {
      payload.location = {
        latitude: gpsData.latitude,
        longitude: gpsData.longitude,
      }
    }

    await attendanceStore.punchWithLocation('BREAK_OUT', payload)
    breakOutReason.value = ''
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('外出打卡失敗:', error)

    if (
      error.response?.status === 403 &&
      error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION'
    ) {
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
  if (punch.punch_type !== 'break_start') return
  editingPunch.value = punch
  editingNote.value = punch.notes || ''
  showEditDialog.value = true
}

const saveEditedNote = async () => {
  if (!editingPunch.value) return

  try {
    await attendanceApi.updatePunchNote(editingPunch.value.punch_id, {
      notes: editingNote.value,
    })

    const index = breakPunches.value.findIndex((p) => p.punch_id === editingPunch.value.punch_id)
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
.home-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  padding-bottom: 24px;
}

.container {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px 16px 48px;
  display: grid;
  gap: 18px;
}

.toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  border-radius: 16px;
  color: white;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
}

.toast.success {
  background: #16a34a;
}

.toast.error {
  background: #dc2626;
  max-width: min(420px, calc(100vw - 32px));
  white-space: pre-line;
}

.toast.error svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 60;
}

.dialog-content {
  width: min(520px, 100%);
  background: rgba(255, 255, 255, 0.96);
  border-radius: 24px;
  padding: 24px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
}

.dialog-title {
  margin: 0 0 16px;
  font-size: 1.2rem;
  font-weight: 800;
  color: #0f172a;
}

.dialog-body {
  display: grid;
  gap: 10px;
}

.dialog-label {
  font-size: 0.9rem;
  font-weight: 700;
  color: #334155;
}

.dialog-input {
  width: 100%;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.36);
  padding: 12px 14px;
  font-size: 0.95rem;
  color: #0f172a;
  outline: none;
  box-sizing: border-box;
}

.dialog-input:focus {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.25);
}

.dialog-hint {
  margin: 0;
  color: #64748b;
  font-size: 0.85rem;
}

.dialog-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-btn {
  border: none;
  border-radius: 14px;
  padding: 10px 16px;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
}

.dialog-btn.cancel {
  background: #e2e8f0;
  color: #334155;
}

.dialog-btn.confirm {
  background: #0ea5e9;
  color: white;
}

@media (max-width: 720px) {
  .container {
    padding: 20px 14px 40px;
    gap: 16px;
  }

  .toast {
    left: 16px;
    right: 16px;
    bottom: 16px;
  }
}
</style>
