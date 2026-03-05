# 考勤打卡系統 - 技術規範與開發指南

---

## 🛠️ 技術棧

### 前端技術

```json
{
  "framework": "Vue 3.5+",
  "buildTool": "Vite 7.0+",
  "styling": "Tailwind CSS 4.0",
  "stateManagement": "Pinia 3.0+",
  "router": "Vue Router 4.6+",
  "httpClient": "Axios 1.13+",
  "validation": "VeeValidate + Yup",
  "dateTime": "Day.js",
  "charts": "ECharts (可選)",
  "maps": "Leaflet / Google Maps API"
}
```

### 後端技術（參考舊系統）

```json
{
  "framework": "FastAPI (Python)",
  "orm": "SQLAlchemy",
  "migration": "Alembic",
  "authentication": "JWT",
  "database": "PostgreSQL / MySQL"
}
```

---

## 📁 專案結構

```
/opt/attendance-system/
├─ frontend/
│  ├─ public/
│  │  ├─ favicon.ico
│  │  └─ index.html
│  ├─ src/
│  │  ├─ assets/
│  │  │  ├─ images/
│  │  │  └─ styles/
│  │  │     ├─ variables.css      # CSS 變數
│  │  │     ├─ base.css           # 基礎樣式
│  │  │     └─ components.css     # 組件樣式
│  │  ├─ components/              # 可重用組件
│  │  │  ├─ Button.vue
│  │  │  ├─ Card.vue
│  │  │  ├─ Modal.vue
│  │  │  ├─ Navbar.vue
│  │  │  ├─ StatusCard.vue
│  │  │  └─ Table.vue
│  │  ├─ views/                   # 頁面組件
│  │  │  ├─ Home.vue              # 首頁（打卡）
│  │  │  ├─ Login.vue             # 登入
│  │  │  ├─ Profile.vue           # 個人資料
│  │  │  ├─ LeaveRequest.vue      # 請假申請
│  │  │  ├─ MissedPunch.vue       # 補打卡
│  │  │  ├─ Reports.vue           # 報表
│  │  │  ├─ Users.vue             # 使用者管理
│  │  │  ├─ Companies.vue         # 公司管理
│  │  │  └─ Departments.vue       # 部門管理
│  │  ├─ api/                     # API 層
│  │  │  ├─ client.js             # Axios 客戶端
│  │  │  ├─ auth.js               # 認證 API
│  │  │  ├─ attendance.js         # 打卡 API
│  │  │  ├─ users.js              # 使用者 API
│  │  │  ├─ leave.js              # 請假 API
│  │  │  └─ reports.js            # 報表 API
│  │  ├─ stores/                  # Pinia 狀態管理
│  │  │  ├─ auth.js               # 認證狀態
│  │  │  ├─ attendance.js         # 打卡狀態
│  │  │  └─ app.js                # 應用狀態
│  │  ├─ router/                  # 路由
│  │  │  └─ index.js
│  │  ├─ utils/                   # 工具函數
│  │  │  ├─ validators.js         # 驗證器
│  │  │  ├─ formatters.js         # 格式化
│  │  │  ├─ constants.js          # 常數
│  │  │  └─ helpers.js            # 輔助函數
│  │  ├─ composables/             # 組合式函數
│  │  │  ├─ useGeolocation.js    # GPS 定位
│  │  │  ├─ useNotification.js   # 通知
│  │  │  └─ usePermission.js     # 權限檢查
│  │  ├─ App.vue                  # 根組件
│  │  └─ main.js                  # 入口文件
│  ├─ .env.development            # 開發環境變數
│  ├─ .env.production             # 生產環境變數
│  ├─ package.json
│  ├─ vite.config.js
│  ├─ tailwind.config.js
│  └─ .eslintrc.js
└─ backend/
   └─ ... (FastAPI 專案)
```

---

## 🎨 CSS 變數定義

### variables.css

```css
:root {
  /* ========== 主色調 ========== */
  --primary: #4A6FA5;
  --primary-hover: #3D5A8A;
  --primary-light: #7BA3D1;
  --primary-lighter: #DDEAF3;
  --primary-lightest: #EBF4F9;
  
  /* ========== 輔助色 ========== */
  --secondary: #F2E8DF;
  --secondary-hover: #E8D9CA;
  --secondary-border: #DDCBB5;
  --accent-beige: #BFBF99;
  
  /* ========== 標題色 ========== */
  --heading: #1C3B6B;
  
  /* ========== 文字色 ========== */
  --text-primary: #2D3A52;
  --text-secondary: #5A6C7D;
  --text-hint: #A0B4C7;
  --text-disabled: #C5D0DC;
  
  /* ========== 背景色 ========== */
  --bg-main: #F4F7F9;
  --bg-card: #FFFFFF;
  --bg-hover: #F8FBFE;
  --bg-disabled: #F0F4F8;
  
  /* ========== 狀態色 ========== */
  --success: #2E7D32;
  --success-bg: #E8F5E9;
  --error: #C62828;
  --error-bg: #FFEBEE;
  --warning: #F57C00;
  --warning-bg: #FFF3E0;
  --info: #1976D2;
  --info-bg: #E3F2FD;
  
  /* ========== 邊框 ========== */
  --border-light: #E8EDF2;
  --border-medium: #D1DAE3;
  --border-dark: #B8C5D3;
  
  /* ========== 陰影 ========== */
  --shadow-sm: 0 1px 3px rgba(28, 59, 107, 0.08);
  --shadow-md: 0 2px 8px rgba(28, 59, 107, 0.08);
  --shadow-lg: 0 4px 16px rgba(28, 59, 107, 0.12);
  --shadow-xl: 0 8px 24px rgba(28, 59, 107, 0.15);
  
  /* ========== 圓角 ========== */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-full: 9999px;
  
  /* ========== 間距 ========== */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  
  /* ========== 字體大小 ========== */
  --text-xs: 12px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 30px;
  
  /* ========== 字重 ========== */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  /* ========== 過渡 ========== */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;
  --transition-slow: 0.3s ease;
  
  /* ========== Z-index ========== */
  --z-dropdown: 1000;
  --z-sticky: 1020;
  --z-fixed: 1030;
  --z-modal-backdrop: 1040;
  --z-modal: 1050;
  --z-popover: 1060;
  --z-tooltip: 1070;
}
```

---

## 🎯 Tailwind 配置

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色調
        primary: {
          DEFAULT: '#4A6FA5',
          hover: '#3D5A8A',
          light: '#7BA3D1',
          lighter: '#DDEAF3',
          lightest: '#EBF4F9',
        },
        // 輔助色
        secondary: {
          DEFAULT: '#F2E8DF',
          hover: '#E8D9CA',
          border: '#DDCBB5',
        },
        // 標題色
        heading: '#1C3B6B',
        // 文字色
        text: {
          primary: '#2D3A52',
          secondary: '#5A6C7D',
          hint: '#A0B4C7',
          disabled: '#C5D0DC',
        },
        // 背景色
        bg: {
          main: '#F4F7F9',
          card: '#FFFFFF',
          hover: '#F8FBFE',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"SF Pro Display"',
          '"Helvetica Neue"',
          'sans-serif',
        ],
      },
      boxShadow: {
        'sm': '0 1px 3px rgba(28, 59, 107, 0.08)',
        'md': '0 2px 8px rgba(28, 59, 107, 0.08)',
        'lg': '0 4px 16px rgba(28, 59, 107, 0.12)',
        'xl': '0 8px 24px rgba(28, 59, 107, 0.15)',
      },
      borderRadius: {
        'sm': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '20px',
      },
    },
  },
  plugins: [],
}
```

---

## 🔌 API 客戶端配置

### api/client.js

```javascript
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';

// 創建 Axios 實例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器
apiClient.interceptors.request.use(
  (config) => {
    // 自動添加 token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 響應攔截器
apiClient.interceptors.response.use(
  (response) => {
    // 直接返回 data
    return response.data;
  },
  (error) => {
    // 統一錯誤處理
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          // 未授權，清除 token 並跳轉登入
          localStorage.removeItem('token');
          const authStore = useAuthStore();
          authStore.logout();
          router.push('/login');
          break;
          
        case 403:
          // 無權限
          console.error('無權限訪問');
          break;
          
        case 404:
          // 資源不存在
          console.error('資源不存在');
          break;
          
        case 500:
          // 伺服器錯誤
          console.error('伺服器錯誤');
          break;
      }
      
      // 返回錯誤訊息
      return Promise.reject({
        status,
        message: data?.detail || data?.message || '請求失敗',
        data,
      });
    } else if (error.request) {
      // 請求已發送但沒有收到響應
      return Promise.reject({
        message: '網絡連接失敗，請檢查網絡設定',
      });
    } else {
      // 其他錯誤
      return Promise.reject({
        message: error.message || '未知錯誤',
      });
    }
  }
);

export default apiClient;
```

### api/attendance.js

```javascript
import apiClient from './client';

export const attendanceApi = {
  // 打卡
  punch: (data) => apiClient.post('/attendance/punch', data),
  
  // 獲取今日狀態
  getStatus: () => apiClient.get('/attendance/status'),
  
  // 獲取打卡記錄
  getLogs: (params) => apiClient.get('/attendance/logs', { params }),
  
  // 獲取個人報表
  getReport: (params) => apiClient.get('/reports/user', { params }),
  
  // 補打卡申請
  requestMissedPunch: (data) => apiClient.post('/attendance/missed-punch', data),
  
  // 獲取補打卡申請列表
  getMissedPunchRequests: (params) => apiClient.get('/attendance/missed-punch', { params }),
  
  // 審核補打卡申請
  approveMissedPunch: (id, data) => apiClient.put(`/attendance/missed-punch/${id}`, data),
};
```

---

## 🗂️ Pinia 狀態管理

### stores/auth.js

```javascript
import { defineStore } from 'pinia';
import { authApi } from '@/api/auth';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token'),
    isLoading: false,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    isOwner: (state) => state.user?.role === 'owner',
    isManager: (state) => state.user?.role === 'manager',
    isEmployee: (state) => state.user?.role === 'employee',
    isSystemAdmin: (state) => state.user?.role === 'system_admin',
    
    hasPermission: (state) => (permission) => {
      if (!state.user) return false;
      return state.user.permissions?.includes(permission) || false;
    },
  },
  
  actions: {
    async login(credentials) {
      this.isLoading = true;
      try {
        const data = await authApi.login(credentials);
        this.token = data.access_token;
        this.user = data.user;
        localStorage.setItem('token', data.access_token);
        return data;
      } finally {
        this.isLoading = false;
      }
    },
    
    async fetchUser() {
      if (!this.token) return;
      
      try {
        const data = await authApi.getProfile();
        this.user = data;
      } catch (error) {
        console.error('獲取用戶資訊失敗:', error);
        this.logout();
      }
    },
    
    logout() {
      this.user = null;
      this.token = null;
      localStorage.removeItem('token');
    },
  },
});
```

---

## 🧭 路由配置

### router/index.js

```javascript
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/leave-request',
    name: 'LeaveRequest',
    component: () => import('@/views/LeaveRequest.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/missed-punch',
    name: 'MissedPunch',
    component: () => import('@/views/MissedPunch.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/Users.vue'),
    meta: { 
      requiresAuth: true,
      roles: ['owner', 'manager', 'system_admin'],
    },
  },
  {
    path: '/companies',
    name: 'Companies',
    component: () => import('@/views/Companies.vue'),
    meta: { 
      requiresAuth: true,
      roles: ['system_admin'],
    },
  },
  {
    path: '/departments',
    name: 'Departments',
    component: () => import('@/views/Departments.vue'),
    meta: { 
      requiresAuth: true,
      roles: ['owner', 'system_admin'],
    },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 路由守衛
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  // 檢查是否需要認證
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login');
    return;
  }
  
  // 檢查角色權限
  if (to.meta.roles && !to.meta.roles.includes(authStore.user?.role)) {
    next('/');
    return;
  }
  
  next();
});

export default router;
```

---

## 📝 開發規範

### 命名規範

```javascript
// 組件名稱：PascalCase
Button.vue
StatusCard.vue
UserTable.vue

// 文件名稱：kebab-case
use-geolocation.js
format-date.js

// 變數名稱：camelCase
const userName = 'John';
const isLoading = false;

// 常數名稱：UPPER_SNAKE_CASE
const API_BASE_URL = 'https://api.example.com';
const MAX_RETRY_COUNT = 3;

// CSS 類名：kebab-case
.btn-primary
.status-card
.user-table
```

### 代碼風格

```javascript
// 使用 ESLint + Prettier
// .eslintrc.js
module.exports = {
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended',
    '@vue/prettier',
  ],
  rules: {
    'vue/multi-word-component-names': 'off',
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
  },
};
```

### Git 提交規範

```bash
# 格式：<type>(<scope>): <subject>

# type 類型：
feat:     新功能
fix:      修復 bug
docs:     文檔更新
style:    代碼格式（不影響功能）
refactor: 重構
perf:     性能優化
test:     測試
chore:    構建/工具變動

# 範例：
git commit -m "feat(attendance): 新增打卡功能"
git commit -m "fix(auth): 修復登入 token 過期問題"
git commit -m "docs(readme): 更新安裝說明"
```

---

**報告生成時間**: 2026-03-05  
**技術負責人**: Claude (Opus 4)
