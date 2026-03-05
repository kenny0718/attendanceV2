# 考勤打卡系統 - 前端

基於 Vue 3 + Vite + Tailwind CSS + Pinia 的現代化考勤打卡系統前端。

## 技術棧

- **框架**: Vue 3.5+ (Composition API)
- **構建工具**: Vite 7.0+
- **樣式**: Tailwind CSS 4.0
- **狀態管理**: Pinia 3.0+
- **路由**: Vue Router 4.6+
- **HTTP 客戶端**: Axios 1.13+
- **日期處理**: Day.js

## 專案結構

```
frontend/
├── public/              # 靜態資源
├── src/
│   ├── assets/         # 資源文件
│   │   └── styles/     # 樣式文件
│   ├── components/     # 可重用組件
│   │   ├── Card.vue
│   │   ├── Navbar.vue
│   │   ├── StatusCard.vue
│   │   └── PunchButton.vue
│   ├── views/          # 頁面組件
│   │   ├── Home.vue    # 首頁（打卡頁面）
│   │   └── Login.vue   # 登入頁面
│   ├── api/            # API 層
│   │   ├── client.js   # Axios 客戶端
│   │   ├── auth.js     # 認證 API
│   │   └── attendance.js # 打卡 API
│   ├── stores/         # Pinia 狀態管理
│   │   ├── auth.js     # 認證狀態
│   │   └── attendance.js # 打卡狀態
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── utils/          # 工具函數
│   ├── App.vue         # 根組件
│   └── main.js         # 入口文件
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 開發指南

### 安裝依賴

```bash
npm install
```

### 啟動開發服務器

```bash
npm run dev
```

開發服務器將在 http://localhost:5173 啟動

### 構建生產版本

```bash
npm run build
```

### 預覽生產構建

```bash
npm run preview
```

## 配色系統

本系統採用專業的商務藍 + 沙色雙色調設計：

- **主色調**: 商務藍 #4A6FA5
- **輔助色**: 沙色 #F2E8DF
- **標題色**: 深海藍 #1C3B6B
- **背景色**: 藍灰 #F4F7F9

詳細配色規範請參考 `/docs/UIdoc/` 目錄。

## MVP 功能

當前 MVP 版本包含：

### ✅ 已完成
- [x] 前端專案骨架
- [x] 基礎組件（Card, Navbar, StatusCard, PunchButton）
- [x] 首頁（Punch Console）
- [x] 今日狀態顯示（4 張狀態卡）
- [x] 打卡按鈕（上班/下班/外出/返回）
- [x] 最近打卡記錄列表
- [x] Mock 數據與狀態管理
- [x] API 客戶端結構

### 🚧 待開發
- [ ] 串接後端 API
- [ ] JWT 認證整合
- [ ] GPS 定位功能
- [ ] 個人資料頁面
- [ ] 請假申請頁面
- [ ] 補打卡申請頁面
- [ ] 報表查詢頁面

## API 串接準備

API 客戶端已準備好，包含：

- **自動添加 JWT token** (Authorization header)
- **自動添加 tenant headers** (X-Company-ID, X-User-ID)
- **統一錯誤處理**
- **請求/響應攔截器**

### 切換到真實 API

在 `stores/attendance.js` 中，將 mock 邏輯替換為真實 API 呼叫：

```javascript
// 從
await new Promise(resolve => setTimeout(resolve, 500))

// 改為
const data = await attendanceApi.punchIn({ ... })
```

## 環境變數

- **開發環境** (`.env.development`):
  ```
  VITE_API_BASE=http://localhost:8000/api
  ```

- **生產環境** (`.env.production`):
  ```
  VITE_API_BASE=/api
  ```

## 開發規範

### 命名規範
- 組件名稱：PascalCase (e.g., `StatusCard.vue`)
- 文件名稱：kebab-case (e.g., `use-geolocation.js`)
- 變數名稱：camelCase (e.g., `userName`)
- 常數名稱：UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)

### 代碼風格
- 使用 Composition API
- 使用 `<script setup>` 語法
- 遵循 Vue 3 官方風格指南

## 相關文檔

- [UI/UX 設計總覽](/opt/attendance-system/docs/UIdoc/README_UI_UX設計總覽.md)
- [技術規範](/opt/attendance-system/docs/UIdoc/UI_UX設計報告_技術規範.md)
- [頁面設計](/opt/attendance-system/docs/UIdoc/UI_UX設計報告_頁面設計.md)
- [UI Readiness Report](/opt/attendance-system/docs/WP-11-05D_UI_READINESS.md)

## 授權

內部專案
