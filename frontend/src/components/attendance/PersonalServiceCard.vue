<template>
  <Card title="個人服務" class="personal-service-card">
    <div class="shortcut-grid">
      <div class="shortcut-card disabled">
        <div class="card-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <div class="card-label">個人資料</div>
        <div class="card-hint">規劃中</div>
      </div>

      <div class="shortcut-card disabled">
        <div class="card-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 1.343-3 3v1H7a1 1 0 000 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2v-1a1 1 0 112 0 1 1 0 102 0c0-1.657-1.343-3-3-3z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3a9 9 0 100 18 9 9 0 000-18z" />
          </svg>
        </div>
        <div class="card-label">加班申請</div>
        <div class="card-hint">規劃中</div>
      </div>

      <router-link to="/attendance/reports/sessions" class="shortcut-card">
        <div class="card-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2m5-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="card-label">出勤紀錄</div>
        <div class="card-hint">查看自己的打卡紀錄</div>
      </router-link>

      <div class="shortcut-card disabled">
        <div class="card-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="card-label">補打卡申請</div>
        <div class="card-hint">規劃中</div>
      </div>

      <router-link to="/leave" class="shortcut-card">
        <div class="card-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <div class="card-label">請假申請</div>
        <div class="card-hint">填寫並送出請假單</div>
      </router-link>
    </div>
  </Card>
</template>

<script setup>
import Card from '@/components/Card.vue'
</script>

<style scoped>
.personal-service-card {
  margin-bottom: 16px;
}

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.shortcut-card {
  background: var(--bg-card);
  border-radius: 18px;
  padding: 18px 16px;
  min-height: 132px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(148, 163, 184, 0.14);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  text-decoration: none;
}

.shortcut-card:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 16px 30px rgba(37, 99, 235, 0.12);
  border-color: rgba(59, 130, 246, 0.18);
}

.shortcut-card:active:not(.disabled) {
  transform: scale(0.985);
}

.shortcut-card.disabled {
  opacity: 0.58;
  cursor: not-allowed;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(241, 245, 249, 0.92));
}

.card-icon {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.card-icon svg {
  width: 34px;
  height: 34px;
}

.shortcut-card.disabled .card-icon {
  color: #94a3b8;
}

.card-label {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
}

.card-hint {
  font-size: 12px;
  line-height: 1.4;
  color: #64748b;
  text-align: center;
}

.shortcut-card.disabled .card-label,
.shortcut-card.disabled .card-hint {
  color: #94a3b8;
}

@media (max-width: 900px) {
  .shortcut-grid {
    grid-template-columns: 1fr;
  }
}
</style>
