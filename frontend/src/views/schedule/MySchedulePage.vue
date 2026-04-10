<template>
  <div class="page-root">
    <div class="page-container">
      <Navbar />

      <div class="page-header">
        <div>
          <p class="eyebrow">PERSONAL SCHEDULE</p>
          <h1 class="page-title">我的班表</h1>
          <p class="page-sub">查看你近期的排班資訊與班次狀態。</p>
        </div>
        <div class="identity-chip">
          <span>{{ displayName }}</span>
          <small>{{ companyName }}</small>
        </div>
      </div>

      <div v-if="isLoading" class="state-box">
        <div class="spinner"></div>
        <span>載入班表中...</span>
      </div>

      <div v-else-if="error" class="state-box error">
        ⚠ {{ error }}
      </div>

      <div v-else class="content-stack">
        <section class="hero-card">
          <div class="hero-copy">
            <p class="hero-label">接下來 14 天</p>
            <h2>{{ assignments.length }} 筆班表</h2>
            <p>依登入會員資格顯示你的個人排班，不包含其他員工資料。</p>
          </div>
          <button class="refresh-btn" @click="loadAssignments">重新整理</button>
        </section>

        <section v-if="assignments.length === 0" class="empty-card">
          <h3>目前沒有可顯示的班表</h3>
          <p>若你已啟用排班制但尚未看到資料，請聯絡公司管理員確認是否已建立班別指派。</p>
        </section>

        <section v-else class="schedule-list">
          <article v-for="assignment in assignments" :key="assignment.id" class="schedule-card">
            <div class="schedule-main">
              <div class="schedule-date-block">
                <span class="weekday">{{ formatWeekday(assignment.work_date) }}</span>
                <strong>{{ formatDate(assignment.work_date) }}</strong>
              </div>

              <div class="schedule-body">
                <div class="schedule-headline">
                  <h3>{{ templateNameMap[assignment.shift_template_id] || '班別指派' }}</h3>
                  <span :class="statusClass(assignment.status)">{{ statusLabel(assignment.status) }}</span>
                </div>

                <p class="schedule-time">{{ templateTimeMap[assignment.shift_template_id] || '班別時間待確認' }}</p>
                <p class="schedule-note">{{ assignment.notes || '尚無備註' }}</p>
              </div>
            </div>
          </article>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import Navbar from '@/components/Navbar.vue'
import { scheduleApi } from '@/api/schedule'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const isLoading = ref(false)
const error = ref('')
const assignments = ref([])
const templates = ref([])

const displayName = computed(() => authStore.currentUser?.name || authStore.currentUser?.email || '使用者')
const companyName = computed(() => authStore.company?.display_name || authStore.company?.name || authStore.company?.id || '目前公司')

const templateNameMap = computed(() => Object.fromEntries(
  templates.value.map((item) => [item.id, item.name])
))

const templateTimeMap = computed(() => Object.fromEntries(
  templates.value.map((item) => [item.id, `${item.start_time} - ${item.end_time}`])
))

async function loadAssignments() {
  if (!authStore.userId) {
    error.value = '找不到目前登入者資料'
    return
  }

  isLoading.value = true
  error.value = ''

  const startDate = dayjs().format('YYYY-MM-DD')
  const endDate = dayjs().add(14, 'day').format('YYYY-MM-DD')

  try {
    const [assignmentRows, templateRows] = await Promise.all([
      scheduleApi.listAssignments({
        user_id: authStore.userId,
        start_date: startDate,
        end_date: endDate,
      }),
      scheduleApi.listTemplates({ active_only: false }),
    ])

    assignments.value = [...assignmentRows].sort((a, b) => a.work_date.localeCompare(b.work_date))
    templates.value = templateRows || []
  } catch (err) {
    console.error('載入個人班表失敗:', err)
    error.value = err?.response?.data?.detail?.message || err?.message || '載入個人班表失敗'
  } finally {
    isLoading.value = false
  }
}

function formatDate(value) {
  return dayjs(value).format('MM/DD')
}

function formatWeekday(value) {
  return dayjs(value).format('ddd')
}

function statusLabel(status) {
  const labels = {
    scheduled: '已排班',
    confirmed: '已確認',
    cancelled: '已取消'
  }
  return labels[status] || status
}

function statusClass(status) {
  return `status-pill status-pill--${status}`
}

onMounted(loadAssignments)
</script>

<style scoped>
.page-root {
  min-height: 100vh;
  background:
    radial-gradient(circle at top, rgba(14, 165, 233, 0.16), transparent 28%),
    linear-gradient(180deg, #f8fbff 0%, #eef4ff 52%, #f8fafc 100%);
}

.page-container {
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-top: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.18em;
  color: #0f766e;
  font-weight: 800;
}

.page-title {
  margin: 0;
  font-size: clamp(2rem, 3vw, 2.6rem);
  color: #0f172a;
}

.page-sub {
  margin: 8px 0 0;
  color: #475569;
}

.identity-chip {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  min-width: 220px;
}

.identity-chip span,
.identity-chip small {
  display: block;
}

.identity-chip span {
  font-weight: 700;
  color: #0f172a;
}

.identity-chip small {
  margin-top: 4px;
  color: #64748b;
}

.content-stack {
  display: grid;
  gap: 18px;
}

.hero-card,
.empty-card,
.schedule-card,
.state-box {
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.hero-card {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-label {
  margin: 0 0 6px;
  color: #0f766e;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.hero-card h2,
.empty-card h3 {
  margin: 0;
  color: #0f172a;
}

.hero-card p,
.empty-card p {
  margin: 8px 0 0;
  color: #475569;
}

.refresh-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  background: linear-gradient(135deg, #0ea5e9, #14b8a6);
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.empty-card,
.state-box {
  padding: 24px;
}

.state-box {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #0f172a;
}

.state-box.error {
  color: #b91c1c;
  background: rgba(254, 242, 242, 0.88);
  border-color: rgba(248, 113, 113, 0.28);
}

.spinner {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 2px solid rgba(14, 165, 233, 0.18);
  border-top-color: #0ea5e9;
  animation: spin 0.8s linear infinite;
}

.schedule-list {
  display: grid;
  gap: 14px;
}

.schedule-card {
  padding: 18px 20px;
}

.schedule-main {
  display: flex;
  align-items: center;
  gap: 18px;
}

.schedule-date-block {
  min-width: 90px;
  padding: 12px;
  border-radius: 18px;
  background: rgba(14, 165, 233, 0.08);
  text-align: center;
}

.schedule-date-block .weekday {
  display: block;
  font-size: 12px;
  color: #0f766e;
  margin-bottom: 4px;
  font-weight: 700;
}

.schedule-date-block strong {
  color: #0f172a;
  font-size: 1.1rem;
}

.schedule-body {
  flex: 1;
  min-width: 0;
}

.schedule-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.schedule-headline h3 {
  margin: 0;
  color: #0f172a;
}

.schedule-time,
.schedule-note {
  margin: 8px 0 0;
  color: #475569;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.status-pill--scheduled {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

.status-pill--confirmed {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.status-pill--cancelled {
  background: rgba(244, 63, 94, 0.12);
  color: #be123c;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 720px) {
  .page-container {
    padding: 12px 12px 40px;
  }

  .page-header {
    margin-top: 16px;
  }

  .identity-chip {
    width: 100%;
  }

  .schedule-main {
    flex-direction: column;
    align-items: flex-start;
  }

  .schedule-date-block {
    min-width: auto;
    width: 100%;
  }
}
</style>
