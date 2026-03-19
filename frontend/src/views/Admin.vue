<template>
  <div class="admin-page">
    <Navbar />
    
    <div class="container">
      <!-- 頁面標題 -->
      <div class="admin-header">
        <h1 class="admin-title">管理後台</h1>
        <p class="admin-description">
          管理系統佔位符頁面。此區域用於未來的管理功能開發。
        </p>
      </div>

      <!-- 佔位符模塊卡片 -->
      <div class="modules-grid">
        <!-- 排班管理 -->
        <div class="module-card">
          <div class="module-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="module-title">排班管理</h3>
          <p class="module-description">管理員工排班和班次安排</p>
          <div class="module-status">開發中</div>
        </div>

        <!-- 出勤報表 -->
        <div class="module-card">
          <div class="module-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 class="module-title">出勤報表</h3>
          <p class="module-description">查看和導出出勤統計報表</p>
          <div class="module-status">開發中</div>
        </div>

        <!-- GPS 地點設定 -->
        <div class="module-card">
          <div class="module-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 class="module-title">GPS 地點設定</h3>
          <p class="module-description">配置允許打卡的地理位置</p>
          <div class="module-status">開發中</div>
        </div>

        <!-- 補卡審核 -->
        <div class="module-card">
          <div class="module-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="module-title">補卡審核</h3>
          <p class="module-description">審核和批准員工的補卡申請</p>
          <div class="module-status">開發中</div>
        </div>

        <!-- 請假審核 -->
        <div class="module-card">
          <div class="module-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1m2-1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5" />
            </svg>
          </div>
          <h3 class="module-title">請假審核</h3>
          <p class="module-description">審核和批准員工的請假申請</p>
          <div class="module-status">開發中</div>
        </div>

        <!-- 員工管理 -->
        <div class="module-card">
          <div class="module-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 12H9m6 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="module-title">員工管理</h3>
          <p class="module-description">管理員工資訊和權限設定</p>
          <div class="module-status">開發中</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import Navbar from '@/components/Navbar.vue'
</script>

<style scoped>
:root {
  --primary: #4A6FA5;
  --primary-hover: #3D5A8A;
  --primary-light: #7BA3D1;
  --heading: #1C3B6B;
  --text-primary: #2D3A52;
  --text-secondary: #5A6C7D;
  --text-hint: #9CA3AF;
  --bg-main: #F4F7F9;
  --bg-card: #FFFFFF;
  --bg-hover: #F0F4F8;
  --border: #E5E7EB;
}

.admin-page {
  min-height: 100vh;
  background-color: var(--bg-main);
  padding-bottom: 24px;
}

.container {
  padding: 24px 16px;
  max-width: 1200px;
  margin: 0 auto;
}

.admin-header {
  margin-bottom: 32px;
}

.admin-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--heading);
  margin-bottom: 8px;
}

.admin-description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.module-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.module-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  border-radius: 12px;
  margin-bottom: 16px;
  color: white;
}

.module-icon svg {
  width: 28px;
  height: 28px;
}

.module-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--heading);
  margin-bottom: 8px;
}

.module-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
  flex-grow: 1;
}

.module-status {
  display: inline-block;
  padding: 6px 12px;
  background: #FFF3E0;
  color: #F57C00;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}

@media (min-width: 768px) {
  .container {
    padding: 32px;
  }

  .admin-title {
    font-size: 32px;
  }

  .modules-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 24px;
  }
}
</style>
