# 考勤打卡系統 - 頁面設計詳細規格

---

## 📱 頁面佈局設計

### 1. 首頁 - 打卡頁面 (Home.vue)

#### 佈局結構

```
┌─────────────────────────────────────────┐
│ Navbar (導航欄)                          │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 今日狀態                         │   │
│  │ ┌─────┬─────┬─────┬─────┐      │   │
│  │ │上班 │下班 │外出 │返回 │      │   │
│  │ │09:00│  -  │  -  │  -  │      │   │
│  │ └─────┴─────┴─────┴─────┘      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 打卡操作                         │   │
│  │ ┌──────────┐  ┌──────────┐     │   │
│  │ │上班打卡  │  │下班打卡  │     │   │
│  │ │  [圖示]  │  │  [圖示]  │     │   │
│  │ └──────────┘  └──────────┘     │   │
│  │                                 │   │
│  │ ┌──────────┐  ┌──────────┐     │   │
│  │ │外出打卡  │  │返回打卡  │     │   │
│  │ │  [圖示]  │  │  [圖示]  │     │   │
│  │ └──────────┘  └──────────┘     │   │
│  │                                 │   │
│  │ 打卡原因（外部打卡需填寫）       │   │
│  │ [文字輸入框]                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 快速功能                         │   │
│  │ [個人資料] [請假申請] [補打卡]  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 最近打卡記錄                     │   │
│  │ 2026-03-05 09:00:15 上班 ✓      │   │
│  │ 2026-03-04 18:30:22 下班 ✓      │   │
│  │ 2026-03-04 09:02:10 上班 ⚠遲到  │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

#### Vue 組件實作

```vue
<template>
  <div class="home-page">
    <Navbar />
    
    <div class="container">
      <!-- 今日狀態 -->
      <Card title="今日狀態" class="status-section">
        <div class="status-grid">
          <StatusCard 
            label="上班時間" 
            :value="todayStatus.punch_in || '-'"
            :valueClass="todayStatus.punch_in ? 'active' : 'empty'"
          />
          <StatusCard 
            label="下班時間" 
            :value="todayStatus.punch_out || '-'"
            :valueClass="todayStatus.punch_out ? 'active' : 'empty'"
          />
          <StatusCard 
            label="外出時間" 
            :value="todayStatus.break_out || '-'"
            :valueClass="todayStatus.break_out ? 'active' : 'empty'"
          />
          <StatusCard 
            label="返回時間" 
            :value="todayStatus.break_in || '-'"
            :valueClass="todayStatus.break_in ? 'active' : 'empty'"
          />
        </div>
      </Card>

      <!-- 打卡操作 -->
      <Card title="打卡操作" class="punch-section">
        <div class="punch-grid">
          <button 
            class="punch-btn punch-in"
            :disabled="!canPunchIn"
            @click="handlePunch('IN')"
          >
            <svg class="punch-icon" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <span>上班打卡</span>
          </button>

          <button 
            class="punch-btn punch-out"
            :disabled="!canPunchOut"
            @click="handlePunch('OUT')"
          >
            <svg class="punch-icon" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11H7v-2h10v2z"/>
            </svg>
            <span>下班打卡</span>
          </button>

          <button 
            class="punch-btn punch-break-out"
            :disabled="!canBreakOut"
            @click="handlePunch('BREAK_OUT')"
          >
            <svg class="punch-icon" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/>
            </svg>
            <span>外出打卡</span>
          </button>

          <button 
            class="punch-btn punch-break-in"
            :disabled="!canBreakIn"
            @click="handlePunch('BREAK_IN')"
          >
            <svg class="punch-icon" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <span>返回打卡</span>
          </button>
        </div>

        <!-- 打卡原因（外部打卡時顯示） -->
        <div v-if="isExternalPunch" class="punch-reason">
          <label>打卡原因（外部打卡需填寫）</label>
          <textarea 
            v-model="punchReason"
            placeholder="例如：在家辦公、外出洽公..."
            rows="3"
          ></textarea>
        </div>

        <!-- 提示訊息 -->
        <div class="punch-hint">
          <span v-if="!todayStatus.punch_in">請先打上班卡</span>
          <span v-else-if="!todayStatus.punch_out">已上班打卡</span>
          <span v-else>今日打卡已完成</span>
        </div>
      </Card>

      <!-- 快速功能 -->
      <div class="quick-actions">
        <router-link to="/profile" class="action-btn">
          <svg class="action-icon" viewBox="0 0 24 24">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
          <span>個人資料</span>
        </router-link>

        <router-link to="/leave-request" class="action-btn">
          <svg class="action-icon" viewBox="0 0 24 24">
            <path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"/>
          </svg>
          <span>請假申請</span>
        </router-link>

        <router-link to="/missed-punch" class="action-btn">
          <svg class="action-icon" viewBox="0 0 24 24">
            <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
          </svg>
          <span>補打卡申請</span>
        </router-link>
      </div>

      <!-- 最近打卡記錄 -->
      <Card title="最近打卡記錄" class="recent-logs">
        <div v-if="recentLogs.length === 0" class="empty-state">
          <p>尚無打卡記錄</p>
        </div>
        <div v-else class="log-list">
          <div 
            v-for="log in recentLogs" 
            :key="log.id"
            class="log-item"
          >
            <div class="log-time">{{ formatDateTime(log.timestamp) }}</div>
            <div class="log-type">{{ getTypeLabel(log.attendance_type) }}</div>
            <div class="log-status" :class="getStatusClass(log)">
              {{ getStatusLabel(log) }}
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- 打卡成功彈窗 -->
    <Modal v-model="showSuccessModal" title="打卡成功">
      <div class="success-content">
        <svg class="success-icon" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
        <h3>{{ successMessage }}</h3>
        <p class="success-time">{{ successTime }}</p>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { attendanceApi } from '@/api/attendance';
import { useAuthStore } from '@/stores/auth';
import Navbar from '@/components/Navbar.vue';
import Card from '@/components/Card.vue';
import StatusCard from '@/components/StatusCard.vue';
import Modal from '@/components/Modal.vue';

const authStore = useAuthStore();

// 狀態
const todayStatus = ref({
  punch_in: null,
  punch_out: null,
  break_out: null,
  break_in: null,
});

const recentLogs = ref([]);
const isExternalPunch = ref(false);
const punchReason = ref('');
const showSuccessModal = ref(false);
const successMessage = ref('');
const successTime = ref('');

// 計算屬性 - 判斷可否打卡
const canPunchIn = computed(() => !todayStatus.value.punch_in);
const canPunchOut = computed(() => todayStatus.value.punch_in && !todayStatus.value.punch_out);
const canBreakOut = computed(() => todayStatus.value.punch_in && !todayStatus.value.punch_out && !todayStatus.value.break_out);
const canBreakIn = computed(() => todayStatus.value.break_out && !todayStatus.value.break_in);

// 打卡處理
const handlePunch = async (type) => {
  try {
    // 獲取 GPS 位置
    const location = await getLocation();
    
    // 檢查是否為外部打卡
    const isExternal = await checkIsExternal();
    
    if (isExternal && !punchReason.value.trim()) {
      alert('外部打卡需填寫原因');
      return;
    }

    // 發送打卡請求
    const response = await attendanceApi.punch({
      attendance_type: type,
      latitude: location.latitude,
      longitude: location.longitude,
      reason: isExternal ? punchReason.value : null,
    });

    // 顯示成功訊息
    successMessage.value = getTypeLabel(type) + ' 成功';
    successTime.value = formatDateTime(new Date());
    showSuccessModal.value = true;

    // 重新載入狀態
    await loadTodayStatus();
    await loadRecentLogs();

    // 清空原因
    punchReason.value = '';

  } catch (error) {
    alert(error.response?.data?.detail || '打卡失敗');
  }
};

// 獲取 GPS 位置
const getLocation = async () => {
  if (!navigator.geolocation) {
    return { latitude: null, longitude: null };
  }

  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      });
    });

    return {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
    };
  } catch (error) {
    console.warn('GPS 定位失敗:', error);
    return { latitude: null, longitude: null };
  }
};

// 檢查是否為外部打卡
const checkIsExternal = async () => {
  // 這裡可以根據 IP 或其他方式判斷
  // 簡化版：直接返回 false
  return false;
};

// 載入今日狀態
const loadTodayStatus = async () => {
  try {
    const data = await attendanceApi.getStatus();
    todayStatus.value = data;
  } catch (error) {
    console.error('載入狀態失敗:', error);
  }
};

// 載入最近記錄
const loadRecentLogs = async () => {
  try {
    const data = await attendanceApi.getLogs({ limit: 5 });
    recentLogs.value = data;
  } catch (error) {
    console.error('載入記錄失敗:', error);
  }
};

// 格式化時間
const formatDateTime = (date) => {
  if (!date) return '-';
  const d = new Date(date);
  return d.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

// 獲取類型標籤
const getTypeLabel = (type) => {
  const labels = {
    'IN': '上班',
    'OUT': '下班',
    'BREAK_OUT': '外出',
    'BREAK_IN': '返回',
  };
  return labels[type] || type;
};

// 獲取狀態標籤
const getStatusLabel = (log) => {
  if (log.is_late) return '⚠ 遲到';
  if (log.is_early) return '⚠ 早退';
  return '✓';
};

// 獲取狀態樣式
const getStatusClass = (log) => {
  if (log.is_late || log.is_early) return 'warning';
  return 'success';
};

// 初始化
onMounted(() => {
  loadTodayStatus();
  loadRecentLogs();
});
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #F4F7F9;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

/* 狀態區域 */
.status-section {
  margin-bottom: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

/* 打卡區域 */
.punch-section {
  margin-bottom: 24px;
}

.punch-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.punch-btn {
  padding: 32px 24px;
  background: #4A6FA5;
  color: #FFFFFF;
  border: none;
  border-radius: 16px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  box-shadow: 0 4px 12px rgba(74, 111, 165, 0.2);
}

.punch-btn:hover:not(:disabled) {
  background: #3D5A8A;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(74, 111, 165, 0.3);
}

.punch-btn:disabled {
  background: #DDEAF3;
  color: #A0B4C7;
  cursor: not-allowed;
  box-shadow: none;
}

.punch-btn.punch-break-out,
.punch-btn.punch-break-in {
  background: #F2E8DF;
  color: #2D3A52;
}

.punch-btn.punch-break-out:hover:not(:disabled),
.punch-btn.punch-break-in:hover:not(:disabled) {
  background: #E8D9CA;
}

.punch-icon {
  width: 48px;
  height: 48px;
  fill: currentColor;
}

.punch-reason {
  margin-top: 20px;
}

.punch-reason label {
  display: block;
  margin-bottom: 8px;
  color: #2D3A52;
  font-weight: 500;
}

.punch-reason textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #DDCBB5;
  border-radius: 12px;
  font-size: 15px;
  font-family: inherit;
  resize: vertical;
}

.punch-hint {
  text-align: center;
  margin-top: 16px;
  color: #5A6C7D;
  font-size: 14px;
}

/* 快速功能 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.action-btn {
  padding: 20px;
  background: #FFFFFF;
  border: 1px solid #E8D9CA;
  border-radius: 12px;
  text-decoration: none;
  color: #2D3A52;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #F2E8DF;
  border-color: #DDCBB5;
}

.action-icon {
  width: 32px;
  height: 32px;
  fill: #4A6FA5;
}

/* 最近記錄 */
.recent-logs {
  margin-bottom: 24px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #F4F7F9;
  border-radius: 12px;
}

.log-time {
  color: #2D3A52;
  font-weight: 500;
}

.log-type {
  color: #5A6C7D;
}

.log-status {
  font-weight: 600;
}

.log-status.success {
  color: #2E7D32;
}

.log-status.warning {
  color: #F57C00;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #A0B4C7;
}

/* 成功彈窗 */
.success-content {
  text-align: center;
  padding: 20px;
}

.success-icon {
  width: 64px;
  height: 64px;
  fill: #2E7D32;
  margin-bottom: 16px;
}

.success-content h3 {
  color: #2D3A52;
  font-size: 20px;
  margin-bottom: 8px;
}

.success-time {
  color: #5A6C7D;
  font-size: 14px;
}

/* 響應式 */
@media (max-width: 768px) {
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .punch-grid {
    grid-template-columns: 1fr;
  }

  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>
```

---

## 📊 其他頁面設計

### 2. 個人資料頁面
### 3. 請假申請頁面
### 4. 補打卡申請頁面
### 5. 報表查詢頁面
### 6. 使用者管理頁面（管理員）

（詳細設計請參考完整文檔）

---

**報告生成時間**: 2026-03-05  
**設計者**: Claude (Opus 4)
