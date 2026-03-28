<template>
  <div class="admin-page">
    <Navbar />
    <div class="container">
      <div class="admin-header">
        <div class="admin-header-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h1 class="admin-title">打卡管理</h1>
          <p class="admin-description"><router-link to="/admin" class="back-link">← 平台管理</router-link></p>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header"><h2 class="panel-title">查詢條件</h2></div>
        <div class="filter-body">
          <div class="filter-row">
            <div class="filter-group">
              <label class="filter-label">開始日期 <span class="required">*</span></label>
              <input v-model="filters.start_date" type="date" class="filter-input" />
            </div>
            <div class="filter-group">
              <label class="filter-label">結束日期 <span class="required">*</span></label>
              <input v-model="filters.end_date" type="date" class="filter-input" />
            </div>
            <div class="filter-group">
              <label class="filter-label">員工 ID（選填）</label>
              <input v-model="filters.user_id" type="text" class="filter-input" placeholder="輸入員工 ID" />
            </div>
            <div class="filter-group filter-group-action">
              <button class="btn-query" :disabled="loading || !filters.start_date || !filters.end_date" @click="loadSessions">
                <span v-if="loading" class="btn-spinner-sm"></span>
                <span v-else>查詢</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">打卡紀錄</h2>
          <button class="btn-refresh" :disabled="loading" @click="loadSessions" title="重新整理">
            <svg :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <!-- RISK-03 S1-12E: super_admin 無 company scope 限制提示 -->
        <div v-if="isSuperAdminNoScope" class="state-box state-notice">
          <div>
            <p class="state-title">需要公司範圍才能查詢</p>
            <p class="state-msg">目前帳號未選定公司範圍，無法查詢打卡資料。請先切換至特定公司後再使用此功能。</p>
          </div>
        </div>
        <div v-else-if="loading" class="state-box"><div class="spinner"></div><span>載入中…</span></div>
        <div v-else-if="error" class="state-box state-error"><div><p class="state-title">載入失敗</p><p class="state-msg">{{ error }}</p></div></div>
        <div v-else-if="!queried" class="state-box"><div><p class="state-title">請選擇日期範圍後查詢</p><p class="state-msg">設定開始與結束日期，按下「查詢」開始查看打卡紀錄。</p></div></div>
        <div v-else-if="sessions.length === 0" class="state-box"><div><p class="state-title">此期間無打卡紀錄</p><p class="state-msg">請調整日期範圍後重新查詢。</p></div></div>
        <div v-else class="table-wrapper">
          <table class="sessions-table">
            <thead><tr><th>員工名稱</th><th>日期</th><th>上班時間</th><th>下班時間</th><th>狀態</th></tr></thead>
            <tbody>
              <tr v-for="s in sessions" :key="s.session_id">
                <td class="cell-name">{{ s.display_name || s.user_id }}</td>
                <td class="cell-date">{{ formatDate(s.punch_in_time) }}</td>
                <td class="cell-time">{{ formatTime(s.punch_in_time) }}</td>
                <td class="cell-time">{{ formatTime(s.punch_out_time) }}</td>
                <td><span :class="statusClass(s)">{{ statusLabel(s) }}</span></td>
              </tr>
            </tbody>
          </table>
          <p class="total-count">共 {{ sessions.length }} 筆紀錄</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Navbar from '@/components/Navbar.vue'
import { attendanceApi } from '@/api/attendance'

// FIX-02 (S1-12C): 用 UTC+8 基準產生台北日期字串，避免跨日問題
function getTaipeiDateStr(offsetDays = 0) {
  const ms = Date.now() + 8 * 3600000 + offsetDays * 86400000
  return new Date(ms).toISOString().slice(0, 10)
}

const today = getTaipeiDateStr(0)
const sevenDaysAgo = getTaipeiDateStr(-6)

const authStore = useAuthStore()
// RISK-03 (S1-12E): super_admin 無 company scope 時顯示限制提示
const isSuperAdminNoScope = computed(() => authStore.isSuperAdmin && !authStore.companyId)

const filters = ref({ start_date: sevenDaysAgo, end_date: today, user_id: '' })
const sessions = ref([])
const loading = ref(false)
const error = ref(null)
const queried = ref(false)

// FIX-02 (S1-12C): 加 +08:00 offset 使 backend 能解析為 timezone-aware datetime
// backend GET /sessions 的 start_date/end_date 要求 timezone-aware（否則 422）
function toTaipeiISO(dateStr, isEnd = false) {
  if (!dateStr) return null
  return isEnd ? dateStr + 'T23:59:59+08:00' : dateStr + 'T00:00:00+08:00'
}

async function loadSessions() {
  if (!filters.value.start_date || !filters.value.end_date) return
  loading.value = true
  error.value = null
  try {
    const params = {
      start_date: toTaipeiISO(filters.value.start_date, false),
      end_date:   toTaipeiISO(filters.value.end_date,   true)
    }
    if (filters.value.user_id && filters.value.user_id.trim()) {
      params.user_id = filters.value.user_id.trim()
    }
    const data = await attendanceApi.getAdminAttendanceSessions(params)
    sessions.value = data.sessions || []
    queried.value = true
  } catch (err) {
    error.value = err.message || '載入打卡紀錄失敗，請稍後再試'
    queried.value = true
  } finally {
    loading.value = false
  }
}

onMounted(loadSessions)

function formatDate(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  return isNaN(d) ? isoStr : d.toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
function formatTime(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  return isNaN(d) ? isoStr : d.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', hour12: false })
}
function statusLabel(s) {
  if (s.punch_in_time && s.punch_out_time) return '已下班'
  if (s.punch_in_time && !s.punch_out_time) return '已上班'
  return '未完成'
}
function statusClass(s) {
  if (s.punch_in_time && s.punch_out_time) return 'badge badge-out'
  if (s.punch_in_time && !s.punch_out_time) return 'badge badge-in'
  return 'badge badge-incomplete'
}
</script>
<style scoped>
.admin-page {
  --primary:#4A6FA5;--heading:#1C3B6B;--text-primary:#2D3A52;
  --text-secondary:#5A6C7D;--bg-main:#F4F7F9;--bg-card:#fff;
  --border:#E5E7EB;--error:#dc2626;
  min-height:100vh;background:var(--bg-main);padding-bottom:48px;
}
.container{padding:24px 16px;max-width:1300px;margin:0 auto}
@media(min-width:768px){.container{padding:32px}}
.admin-header{display:flex;align-items:center;gap:16px;margin-bottom:32px}
.admin-header-icon{width:52px;height:52px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#fb923c,#ea580c);border-radius:14px;color:white}
.admin-header-icon svg{width:28px;height:28px}
.admin-title{font-size:26px;font-weight:700;color:var(--heading);margin:0 0 4px}
.admin-description{font-size:13px;color:var(--text-secondary);margin:0}
.back-link{color:var(--primary);text-decoration:none}
.back-link:hover{text-decoration:underline}
.panel{background:var(--bg-card);border-radius:16px;box-shadow:0 2px 8px rgba(0,0,0,.07);overflow:hidden;margin-bottom:24px}
.panel-header{display:flex;align-items:center;justify-content:space-between;padding:20px 24px 16px;border-bottom:1px solid var(--border)}
.panel-title{font-size:16px;font-weight:600;color:var(--heading);margin:0}
.filter-body{padding:20px 24px}
.filter-row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end}
.filter-group{display:flex;flex-direction:column;gap:6px;min-width:160px}
.filter-group-action{flex:0 0 auto;min-width:auto}
.filter-label{font-size:12px;font-weight:600;color:var(--text-secondary)}
.required{color:var(--error)}
.filter-input{padding:9px 12px;border:1px solid #D1D5DB;border-radius:8px;font-size:14px;color:var(--text-primary);background:#fff;outline:none;transition:border-color .2s,box-shadow .2s}
.filter-input:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(74,111,165,.12)}
.btn-query{display:inline-flex;align-items:center;justify-content:center;padding:9px 24px;background:var(--primary);color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity .15s;min-width:80px}
.btn-query:hover:not(:disabled){opacity:.88}
.btn-query:disabled{opacity:.55;cursor:not-allowed}
.btn-refresh{width:32px;height:32px;display:flex;align-items:center;justify-content:center;border:1px solid var(--border);border-radius:8px;background:transparent;color:var(--text-secondary);cursor:pointer;transition:all .2s}
.btn-refresh:hover:not(:disabled){background:#F0F4F8;color:var(--primary)}
.btn-refresh:disabled{opacity:.5;cursor:not-allowed}
.btn-refresh svg{width:16px;height:16px}
.spinning{animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.state-box{display:flex;align-items:center;justify-content:center;gap:12px;padding:48px 24px;color:var(--text-secondary);font-size:14px}
.state-error{color:var(--error)}
.state-notice{color:#92400e;background:#fffbeb;border-radius:12px;border:1px solid #fde68a}
.state-title{font-weight:600;margin:0 0 4px;font-size:15px}
.state-msg{margin:0;font-size:13px;opacity:.8}
.spinner{width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--primary);border-radius:50%;animation:spin .8s linear infinite;flex-shrink:0}
.table-wrapper{overflow-x:auto}
.sessions-table{width:100%;border-collapse:collapse;font-size:13px}
.sessions-table th{padding:10px 16px;text-align:left;font-size:11px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.05em;background:#F8FAFC;border-bottom:1px solid var(--border);white-space:nowrap}
.sessions-table td{padding:12px 16px;border-bottom:1px solid #F1F5F9;color:var(--text-primary);vertical-align:middle}
.sessions-table tbody tr:hover td{background:#F8FAFC}
.sessions-table tbody tr:last-child td{border-bottom:none}
.cell-name{font-weight:500}
.cell-date,.cell-time{white-space:nowrap;font-size:13px}
.cell-time{color:var(--text-secondary)}
.total-count{padding:10px 16px;font-size:12px;color:var(--text-secondary);text-align:right;margin:0;border-top:1px solid var(--border)}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600}
.badge-out{background:#dcfce7;color:#15803d}
.badge-in{background:#dbeafe;color:#1d4ed8}
.badge-incomplete{background:#fef9c3;color:#92400e}
.btn-spinner-sm{display:inline-block;width:12px;height:12px;border:2px solid currentColor;border-top-color:transparent;border-radius:50%;animation:spin .6s linear infinite}
</style>
