<template>
  <div class="page-root">
    <Navbar />

    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">出勤記錄查詢</h1>
        <p class="page-sub">查詢個人出勤 Session 清單</p>
      </div>

      <!-- 篩選區 -->
      <div class="filter-card">
        <div class="filter-row">
          <MonthPicker @select="onMonthSelect" />
        </div>
        <div class="filter-row">
          <DateRangeFilter @change="onDateRangeChange" />
          <div class="status-filter">
            <label class="field-label">狀態篩選</label>
            <select v-model="filterStatus" class="select-input" @change="applyFilters">
              <option value="">全部</option>
              <option value="open">進行中</option>
              <option value="closed">已完成</option>
              <option value="pending">審核中</option>
              <option value="approved">已核准</option>
              <option value="rejected">已拒絕</option>
              <option value="missing_punch_out">缺下班卡</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 載入中 -->
      <div v-if="store.sessionsLoading" class="state-box">
        <div class="spinner"></div>
        <span>載入中...</span>
      </div>

      <!-- 錯誤 -->
      <div v-else-if="store.sessionsError" class="state-box error">
        <span>⚠ {{ store.sessionsError }}</span>
      </div>

      <!-- 空結果 -->
      <div v-else-if="store.sessions.length === 0" class="state-box empty">
        <span>本期間無出勤記錄</span>
      </div>

      <!-- 資料表格 -->
      <div v-else class="table-card">
        <table class="sessions-table">
          <thead>
            <tr>
              <th>上班時間</th>
              <th>下班時間</th>
              <th>工時</th>
              <th>狀態</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in store.sessions" :key="s.session_id">
              <td>{{ formatTime(s.punch_in_time) }}</td>
              <td>{{ s.punch_out_time ? formatTime(s.punch_out_time) : '進行中' }}</td>
              <td>{{ formatDuration(s.duration_minutes) }}</td>
              <td><StatusBadge :status="s.status" /></td>
            </tr>
          </tbody>
        </table>

        <PaginationBar
          :total="store.sessionsTotal"
          :limit="pageLimit"
          :offset="pageOffset"
          @change="onPageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import dayjs from 'dayjs'
import Navbar from '@/components/Navbar.vue'
import MonthPicker from '@/components/MonthPicker.vue'
import DateRangeFilter from '@/components/DateRangeFilter.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { useReportingStore } from '@/stores/reporting'

const TZ = 'Asia/Taipei'
const store = useReportingStore()

const filterStatus = ref('')
const pageLimit    = ref(20)
const pageOffset   = ref(0)

let currentDateRange = { start_date: null, end_date: null }

function buildParams() {
  const p = { limit: pageLimit.value, offset: pageOffset.value }
  if (currentDateRange.start_date) p.start_date = currentDateRange.start_date
  if (currentDateRange.end_date)   p.end_date   = currentDateRange.end_date
  if (filterStatus.value)          p.status     = filterStatus.value
  return p
}

function load() {
  store.fetchSessions(buildParams())
}

function onMonthSelect({ start_date, end_date }) {
  currentDateRange = { start_date, end_date }
  pageOffset.value = 0
  load()
}

function onDateRangeChange({ start_date, end_date }) {
  currentDateRange = { start_date, end_date }
  pageOffset.value = 0
  load()
}

function applyFilters() {
  pageOffset.value = 0
  load()
}

function onPageChange({ offset, limit }) {
  pageOffset.value = offset
  pageLimit.value  = limit
  load()
}

function formatTime(utcStr) {
  if (!utcStr) return '—'
  return dayjs(utcStr).tz(TZ).format('YYYY-MM-DD HH:mm')
}

function formatDuration(minutes) {
  if (minutes === null || minutes === undefined) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h} 小時 ${m} 分` : `${m} 分`
}
</script>

<style scoped>
.page-root {
  min-height: 100vh;
  background: var(--bg-main);
}

.page-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 28px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--heading);
}

.page-sub {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.filter-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--shadow-sm);
}

.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.status-filter {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.field-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.select-input {
  padding: 6px 10px;
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--text-primary);
  background: white;
  outline: none;
  cursor: pointer;
  transition: var(--transition-base);
}

.select-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-lighter);
}

/* State boxes */
.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 20px;
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.state-box.error { color: var(--error); }
.state-box.empty { color: var(--text-hint); }

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid var(--border-light);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Table */
.table-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.sessions-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.sessions-table th {
  background: var(--bg-main);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-light);
}

.sessions-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
}

.sessions-table tbody tr:last-child td {
  border-bottom: none;
}

.sessions-table tbody tr:hover {
  background: var(--bg-hover);
}
</style>
