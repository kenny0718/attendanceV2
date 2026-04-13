<template>
  <div class="page-root">
    <Navbar />

    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">
          個人出勤摘要
        </h1>
        <p class="page-sub">
          個人出勤統計數字
        </p>
      </div>

      <!-- 篩選區 -->
      <div class="filter-card">
        <MonthPicker @select="onMonthSelect" />
      </div>

      <!-- 載入中 -->
      <div
        v-if="store.userSummaryLoading"
        class="state-box"
      >
        <div class="spinner" />
        <span>載入中...</span>
      </div>

      <!-- 錯誤 -->
      <div
        v-else-if="store.userSummaryError"
        class="state-box error"
      >
        <span>⚠ {{ store.userSummaryError }}</span>
      </div>

      <!-- 空結果 -->
      <div
        v-else-if="store.userSummary && store.userSummary.total_sessions === 0"
        class="state-box empty"
      >
        <span>本期間無出勤記錄</span>
      </div>

      <!-- 摘要卡片 -->
      <div
        v-else-if="store.userSummary"
        class="summary-section"
      >
        <div class="summary-grid">
          <SummaryCard
            label="總 Sessions"
            :value="store.userSummary.total_sessions"
          />
          <SummaryCard
            label="已完成"
            :value="store.userSummary.closed_sessions"
          />
          <SummaryCard
            label="進行中"
            :value="store.userSummary.open_sessions"
          />
          <SummaryCard
            label="總工時"
            :value="formatDuration(store.userSummary.total_work_minutes)"
          />
          <SummaryCard
            label="平均每次工時"
            :value="formatAvg(store.userSummary.average_session_minutes)"
          />
        </div>

        <div class="time-range-row">
          <div class="time-item">
            <span class="time-label">最早打卡時間</span>
            <span class="time-value">{{ formatDate(store.userSummary.first_session_time) }}</span>
          </div>
          <div class="time-item">
            <span class="time-label">最近打卡時間</span>
            <span class="time-value">{{ formatDate(store.userSummary.last_session_time) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import Navbar from '@/components/Navbar.vue'
import MonthPicker from '@/components/MonthPicker.vue'
import SummaryCard from '@/components/SummaryCard.vue'
import { useReportingStore } from '@/stores/reporting'

const TZ = 'Asia/Taipei'
const store = useReportingStore()

function onMonthSelect({ start_date, end_date }) {
  store.fetchUserSummary({ start_date, end_date })
}

function formatDuration(minutes) {
  if (!minutes && minutes !== 0) return '—'
  if (minutes === 0) return '0 分鐘'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h} 小時 ${m} 分` : `${m} 分`
}

function formatAvg(val) {
  if (val === null || val === undefined) return null
  const h = Math.floor(val / 60)
  const m = Math.round(val % 60)
  return h > 0 ? `${h} 小時 ${m} 分` : `${m} 分`
}

function formatDate(utcStr) {
  if (!utcStr) return '—'
  return dayjs(utcStr).tz(TZ).format('YYYY-MM-DD')
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
  box-shadow: var(--shadow-sm);
}

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

.summary-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.time-range-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 16px 20px;
  box-shadow: var(--shadow-sm);
}

.time-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.time-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--heading);
}
</style>
