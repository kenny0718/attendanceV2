<template>
  <div class="leave-page">
    <Navbar />
    <div class="container">
      <div class="page-header">
        <div class="page-header-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <div>
          <h1 class="page-title">請假申請</h1>
          <p class="page-desc">填寫請假資訊，送出後等待主管審核</p>
        </div>
      </div>

      <!-- Create Leave Form -->
      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">新增請假申請</h2>
        </div>
        <div class="panel-body">
          <!-- Success message -->
          <div v-if="successMsg" class="alert alert-success">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <span>{{ successMsg }}</span>
            <button class="alert-close" @click="successMsg = null">✕</button>
          </div>

          <!-- Error message -->
          <div v-if="errorMsg" class="alert alert-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ errorMsg }}</span>
            <button class="alert-close" @click="errorMsg = null">✕</button>
          </div>

          <form class="leave-form" @submit.prevent="submitLeave">
            <!-- Leave Type -->
            <div class="form-group">
              <label class="form-label">假別 <span class="required">*</span></label>
              <select v-model="form.leave_type" class="form-input" required>
                <option value="">— 請選擇假別 —</option>
                <option value="annual">特休</option>
                <option value="sick">病假</option>
                <option value="personal">事假</option>
                <option value="bereavement">喪假</option>
                <option value="marriage">婚假</option>
                <option value="maternity">產假</option>
                <option value="paternity">陪產假</option>
                <option value="other">其他</option>
              </select>
              <p class="form-hint">請依公司假別政策選擇</p>
            </div>

            <!-- Leave Type ID (UUID from company) -->
            <div class="form-group">
              <label class="form-label">假別代碼（UUID）<span class="required">*</span></label>
              <input
                v-model="form.leave_type_id"
                class="form-input font-mono"
                type="text"
                placeholder="請輸入公司提供的假別 UUID"
                pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
                required
              />
              <p class="form-hint">格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx（由管理員提供）</p>
            </div>

            <!-- Date range -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">開始日期 <span class="required">*</span></label>
                <input v-model="form.start_date" class="form-input" type="date" required />
              </div>
              <div class="form-group">
                <label class="form-label">結束日期 <span class="required">*</span></label>
                <input v-model="form.end_date" class="form-input" type="date" :min="form.start_date" required />
              </div>
            </div>

            <!-- Date validation hint -->
            <div v-if="dateError" class="field-error">{{ dateError }}</div>

            <!-- Half day -->
            <div class="form-group form-group-check">
              <label class="check-label">
                <input v-model="form.is_half_day" type="checkbox" class="check-input" />
                <span>半天假</span>
              </label>
            </div>

            <!-- Reason -->
            <div class="form-group">
              <label class="form-label">請假原因 <span class="required">*</span></label>
              <textarea
                v-model="form.reason"
                class="form-input form-textarea"
                placeholder="請說明請假原因（最多 1000 字）"
                maxlength="1000"
                rows="3"
                required
              ></textarea>
              <p class="form-hint">{{ form.reason.length }} / 1000</p>
            </div>

            <!-- Submit -->
            <div class="form-actions">
              <button type="submit" class="btn-submit" :disabled="loading || !!dateError">
                <span v-if="loading" class="btn-spinner"></span>
                <span v-else>送出申請</span>
              </button>
              <button type="button" class="btn-reset" @click="resetForm" :disabled="loading">清除</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Recent requests preview -->
      <div v-if="recentRequests.length" class="panel mt">
        <div class="panel-header">
          <h2 class="panel-title">最近申請</h2>
        </div>
        <div class="recent-list">
          <div v-for="req in recentRequests" :key="req.id" class="recent-item">
            <div class="recent-dates">{{ req.start_date }} ～ {{ req.end_date }}</div>
            <div class="recent-reason">{{ req.reason }}</div>
            <span class="status-badge" :class="'status-' + req.status">{{ statusLabel(req.status) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { leaveApi } from '@/api/leave'

const form = ref({
  leave_type: '',
  leave_type_id: '',
  start_date: '',
  end_date: '',
  reason: '',
  is_half_day: false,
})

const loading = ref(false)
const successMsg = ref(null)
const errorMsg = ref(null)
const recentRequests = ref([])

// Client-side date validation
const dateError = computed(() => {
  if (!form.value.start_date || !form.value.end_date) return null
  if (form.value.end_date < form.value.start_date) return '結束日期不能早於開始日期'
  return null
})

function resetForm() {
  form.value = {
    leave_type: '',
    leave_type_id: '',
    start_date: '',
    end_date: '',
    reason: '',
    is_half_day: false,
  }
  successMsg.value = null
  errorMsg.value = null
}

async function submitLeave() {
  if (dateError.value) return
  loading.value = true
  successMsg.value = null
  errorMsg.value = null
  try {
    const result = await leaveApi.createLeaveRequest({
      leave_type_id: form.value.leave_type_id,
      start_date: form.value.start_date,
      end_date: form.value.end_date,
      reason: form.value.reason.trim(),
      is_half_day: form.value.is_half_day,
    })
    successMsg.value = `請假申請已送出（${result.start_date} ～ ${result.end_date}），等待審核中。`
    recentRequests.value.unshift(result)
    resetForm()
    successMsg.value = `請假申請已送出（${result.start_date} ～ ${result.end_date}），等待審核中。`
  } catch (err) {
    const code = err?.data?.detail?.code
    const msg = err?.data?.detail?.message || err?.data?.detail
    if (code === 'FEATURE_DISABLED') {
      errorMsg.value = '您的公司尚未啟用請假功能，請聯繫管理員。'
    } else if (typeof msg === 'string') {
      errorMsg.value = msg
    } else {
      errorMsg.value = err.message || '送出失敗，請稍後再試'
    }
  } finally {
    loading.value = false
  }
}

async function loadRecentRequests() {
  try {
    const data = await leaveApi.getMyLeaveRequests({ limit: 5 })
    recentRequests.value = data.requests || []
  } catch {
    // silent fail — recent list is optional
  }
}

function statusLabel(status) {
  const map = { pending: '待審核', approved: '已核准', rejected: '已拒絕', cancelled: '已取消' }
  return map[status] || status
}

onMounted(loadRecentRequests)
</script>

<style scoped>
/* ── Page Layout ── */
.leave-page {
  --primary: #4A6FA5;
  --heading: #1C3B6B;
  --text: #2D3A52;
  --text-secondary: #5A6C7D;
  --border: #E5E7EB;
  --bg: #F4F7F9;
  --error: #dc2626;
  --success: #15803d;
  min-height: 100vh;
  background: var(--bg);
  padding-bottom: 48px;
}
.container { max-width: 720px; margin: 0 auto; padding: 24px 16px; }
@media (min-width: 768px) { .container { padding: 32px; } }

/* ── Header ── */
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 28px; }
.page-header-icon {
  width: 48px; height: 48px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #93c5fd, #3b82f6);
  border-radius: 12px; color: #fff;
}
.page-header-icon svg { width: 24px; height: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--heading); margin: 0 0 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin: 0; }

/* ── Panel ── */
.panel { background: #fff; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; }
.mt { margin-top: 20px; }
.panel-header { padding: 18px 24px 14px; border-bottom: 1px solid var(--border); }
.panel-title { font-size: 15px; font-weight: 600; color: var(--heading); margin: 0; }
.panel-body { padding: 24px; }

/* ── Alerts ── */
.alert {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px 14px; border-radius: 10px; font-size: 13px; margin-bottom: 16px;
}
.alert svg { width: 16px; height: 16px; flex-shrink: 0; margin-top: 1px; }
.alert span { flex: 1; }
.alert-success { background: #f0fdf4; color: var(--success); border: 1px solid #bbf7d0; }
.alert-error { background: #fef2f2; color: var(--error); border: 1px solid #fecaca; }
.alert-close { background: none; border: none; cursor: pointer; color: inherit; font-size: 14px; padding: 0 2px; }

/* ── Form ── */
.leave-form { display: flex; flex-direction: column; gap: 16px; }
.form-row { display: flex; gap: 16px; flex-wrap: wrap; }
.form-group { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 6px; }
.form-group-check { flex-direction: row; align-items: center; }
.form-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.required { color: var(--error); }
.form-input {
  padding: 9px 12px; border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 14px; color: var(--text); background: #fff; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s; width: 100%; box-sizing: border-box;
}
.form-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.form-textarea { resize: vertical; min-height: 80px; font-family: inherit; }
.font-mono { font-family: monospace; font-size: 13px; }
.form-hint { font-size: 11px; color: var(--text-secondary); margin: 0; }
.field-error { font-size: 12px; color: var(--error); margin-top: -8px; }

/* ── Checkbox ── */
.check-label { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; color: var(--text); }
.check-input { width: 16px; height: 16px; cursor: pointer; }

/* ── Actions ── */
.form-actions { display: flex; gap: 12px; justify-content: flex-end; padding-top: 4px; }
.btn-submit {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 24px; background: var(--primary); color: #fff;
  border: none; border-radius: 8px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s; min-width: 100px;
}
.btn-submit:hover:not(:disabled) { opacity: 0.88; }
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-reset {
  padding: 10px 20px; border: 1px solid var(--border); border-radius: 8px;
  background: #fff; color: var(--text-secondary); font-size: 14px; cursor: pointer;
}
.btn-reset:hover:not(:disabled) { background: #F0F4F8; }
.btn-reset:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-spinner {
  display: inline-block; width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4); border-top-color: #fff;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Recent list ── */
.recent-list { padding: 8px 0; }
.recent-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 24px;
  border-bottom: 1px solid #F1F5F9; font-size: 13px;
}
.recent-item:last-child { border-bottom: none; }
.recent-dates { font-weight: 600; color: var(--heading); white-space: nowrap; }
.recent-reason { flex: 1; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.status-badge {
  display: inline-block; padding: 2px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 600; white-space: nowrap;
}
.status-pending { background: #fef9c3; color: #a16207; }
.status-approved { background: #dcfce7; color: #15803d; }
.status-rejected { background: #fee2e2; color: #dc2626; }
.status-cancelled { background: #f1f5f9; color: #64748b; }
</style>
