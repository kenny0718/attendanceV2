<template>
  <div class="sessions-page">
    <div class="page-container">
      <Navbar />

      <section class="intro-card">
        <p class="eyebrow">ATTENDANCE SESSIONS</p>
        <h1>出勤紀錄</h1>
        <p>依月份、日期區間與狀態查詢自己的出勤 Session，維持與請假頁相同的頁面骨架與卡片語言。</p>
      </section>

      <section class="filter-card">
        <div class="filter-grid">
          <div class="field-block">
            <p class="field-title">月份快速篩選</p>
            <MonthPicker @select="onMonthSelect" />
          </div>

          <div class="field-block wide">
            <p class="field-title">日期區間</p>
            <DateRangeFilter @change="onDateRangeChange" />
          </div>

          <div class="field-block status-block">
            <label class="field-title" for="session-status">狀態篩選</label>
            <select id="session-status" v-model="filterStatus" class="select-input" @change="applyFilters">
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
      </section>

      <section v-if="store.sessionsLoading" class="state-card">
        <div class="spinner"></div>
        <span>載入中...</span>
      </section>

      <section v-else-if="store.sessionsError" class="state-card error">
        <span>⚠ {{ store.sessionsError }}</span>
      </section>

      <section v-else-if="store.sessions.length === 0" class="state-card empty">
        <span>本期間無出勤記錄</span>
      </section>

      <section v-else class="table-card">
        <div class="table-card-header">
          <div>
            <h2>查詢結果</h2>
            <p>共 {{ store.sessionsTotal }} 筆出勤 Session</p>
          </div>
        </div>

        <div class="table-scroll">
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
        </div>

        <PaginationBar
          :total="store.sessionsTotal"
          :limit="pageLimit"
          :offset="pageOffset"
          @change="onPageChange"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import Navbar from '@/components/Navbar.vue'
import MonthPicker from '@/components/MonthPicker.vue'
import DateRangeFilter from '@/components/DateRangeFilter.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { useReportingStore } from '@/stores/reporting'

const store = useReportingStore()

const filterStatus = ref('')
const pageLimit = ref(20)
const pageOffset = ref(0)

let currentDateRange = { start_date: null, end_date: null }

function buildParams() {
  const params = { limit: pageLimit.value, offset: pageOffset.value }
  if (currentDateRange.start_date) params.start_date = currentDateRange.start_date
  if (currentDateRange.end_date) params.end_date = currentDateRange.end_date
  if (filterStatus.value) params.status = filterStatus.value
  return params
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
  pageLimit.value = limit
  load()
}

function formatTime(value) {
  if (!value) return '—'
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

function formatDuration(minutes) {
  if (minutes === null || minutes === undefined) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h} 小時 ${m} 分` : `${m} 分`
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.sessions-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.page-container {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px 16px 48px;
  display: grid;
  gap: 18px;
}

.intro-card,
.filter-card,
.state-card,
.table-card {
  background: rgba(255, 255, 255, 0.84);
  border-radius: 24px;
  padding: 24px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: #c2410c;
}

h1,
h2 {
  margin: 0;
  color: #0f172a;
}

.intro-card p:last-child,
.table-card-header p {
  margin: 10px 0 0;
  color: #475569;
  line-height: 1.7;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 16px;
}

.field-block {
  grid-column: span 4;
  display: grid;
  gap: 10px;
}

.field-block.wide {
  grid-column: span 5;
}

.field-block.status-block {
  grid-column: span 3;
}

.field-title {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #334155;
}

.select-input {
  width: 100%;
  min-height: 44px;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.32);
  padding: 0 14px;
  font-size: 0.95rem;
  color: #0f172a;
  background: rgba(255, 255, 255, 0.92);
  outline: none;
}

.select-input:focus {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.25);
}

.state-card {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
}

.state-card.error {
  color: #b91c1c;
}

.state-card.empty {
  color: #94a3b8;
}

.spinner {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 3px solid rgba(148, 163, 184, 0.28);
  border-top-color: #0ea5e9;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.table-card {
  overflow: hidden;
}

.table-card-header {
  margin-bottom: 18px;
}

.table-scroll {
  overflow-x: auto;
  margin: 0 -4px 18px;
  padding: 0 4px;
}

.sessions-table {
  width: 100%;
  min-width: 620px;
  border-collapse: collapse;
}

.sessions-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #64748b;
  text-transform: uppercase;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(248, 250, 252, 0.92);
}

.sessions-table td {
  padding: 16px;
  color: #0f172a;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.sessions-table tbody tr:last-child td {
  border-bottom: none;
}

.sessions-table tbody tr:hover {
  background: rgba(248, 250, 252, 0.92);
}

@media (max-width: 900px) {
  .field-block,
  .field-block.wide,
  .field-block.status-block {
    grid-column: 1 / -1;
  }
}

@media (max-width: 720px) {
  .page-container {
    padding: 20px 14px 40px;
    gap: 16px;
  }

  .intro-card,
  .filter-card,
  .state-card,
  .table-card {
    padding: 20px;
    border-radius: 20px;
  }
}
</style>
