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
</style>
