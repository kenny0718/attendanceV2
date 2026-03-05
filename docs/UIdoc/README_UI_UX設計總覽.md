# 考勤打卡系統 UI/UX 設計總覽

> 基於舊系統經驗與配色整合的完整設計方案  
> 採用考勤系統的專業配色：商務藍 + 沙色雙色調

---

## 📚 文檔導航

本設計報告包含以下文檔：

1. **[UI_UX設計報告_完整版.md](./UI_UX設計報告_完整版.md)**
   - 設計理念與核心價值
   - 完整配色系統
   - 基礎組件設計
   - 與序號系統的差異對比

2. **[UI_UX設計報告_頁面設計.md](./UI_UX設計報告_頁面設計.md)**
   - 首頁（打卡頁面）完整實作
   - 頁面佈局結構
   - Vue 組件完整代碼
   - 響應式設計方案

3. **[UI_UX設計報告_技術規範.md](./UI_UX設計報告_技術規範.md)**
   - 技術棧選擇
   - 專案結構
   - API 客戶端配置
   - Pinia 狀態管理
   - 路由配置
   - 開發規範

4. **[參考舊系統_開發指南.md](./參考舊系統_開發指南.md)**
   - 舊系統功能清單
   - 值得保留的設計
   - 需要避免的問題
   - 開發優先級

5. **[雙系統配色整合報告.md](./雙系統配色整合報告.md)**
   - PSMS 序號系統配色分析
   - 考勤系統配色分析
   - 配色整合方案
   - 系統切換設計

6. **[barcode-前端設計風格分析報告.md](./barcode-前端設計風格分析報告.md)**
   - PSMS 系統設計風格
   - 極簡主義設計特點
   - 配色方案詳解

---

## 🎨 核心設計理念

### 設計定位

```
考勤打卡系統 = 專業 + 沉穩 + 溫暖
```

### 配色策略

**採用考勤系統的配色方案**（與序號系統區分）

```css
主色調：商務藍 #4A6FA5
輔助色：沙色 #F2E8DF
標題色：深海藍 #1C3B6B
背景色：藍灰 #F4F7F9
```

### 與序號系統的差異

| 特性 | 序號系統 | 考勤系統 |
|------|---------|---------|
| 主色 | 亮藍 #2563EB | 商務藍 #4A6FA5 |
| 風格 | 現代科技感 | 沉穩企業感 |
| 輔助色 | 灰色系 | 沙色系 |
| 適用 | 動態操作 | 正式操作 |

---

## 🎯 快速開始

### 1. 查看配色系統

```css
/* 主要配色 */
--primary: #4A6FA5;              /* 主要按鈕 */
--primary-hover: #3D5A8A;        /* Hover 狀態 */
--secondary: #F2E8DF;            /* 次要按鈕 */
--secondary-hover: #E8D9CA;      /* 次要 Hover */
--heading: #1C3B6B;              /* 標題文字 */
--text-primary: #2D3A52;         /* 主要文字 */
--bg-main: #F4F7F9;              /* 頁面背景 */
```

### 2. 使用 Tailwind 類名

```vue
<!-- 主要按鈕 -->
<button class="bg-[#4A6FA5] hover:bg-[#3D5A8A] text-white">
  上班打卡
</button>

<!-- 次要按鈕 -->
<button class="bg-[#F2E8DF] hover:bg-[#E8D9CA] text-[#2D3A52]">
  外出打卡
</button>

<!-- 卡片 -->
<div class="bg-white rounded-2xl shadow-md p-8">
  內容
</div>
```

### 3. 組件使用範例

```vue
<template>
  <div class="home-page">
    <!-- 導航欄 -->
    <Navbar />
    
    <!-- 狀態卡片 -->
    <Card title="今日狀態">
      <div class="grid grid-cols-4 gap-4">
        <StatusCard label="上班時間" value="09:00" />
        <StatusCard label="下班時間" value="-" />
        <StatusCard label="外出時間" value="-" />
        <StatusCard label="返回時間" value="-" />
      </div>
    </Card>
    
    <!-- 打卡按鈕 -->
    <Card title="打卡操作">
      <div class="grid grid-cols-2 gap-4">
        <button class="punch-btn-primary">上班打卡</button>
        <button class="punch-btn-primary">下班打卡</button>
        <button class="punch-btn-secondary">外出打卡</button>
        <button class="punch-btn-secondary">返回打卡</button>
      </div>
    </Card>
  </div>
</template>
```

---

## 📱 頁面結構

### 首頁（打卡頁面）

```
┌─────────────────────────────────┐
│ Navbar (商務藍 #4A6FA5)         │
├─────────────────────────────────┤
│ 今日狀態 (4個狀態卡片)          │
├─────────────────────────────────┤
│ 打卡操作 (4個大按鈕)            │
│ - 上班/下班：商務藍             │
│ - 外出/返回：沙色               │
├─────────────────────────────────┤
│ 快速功能 (3個功能按鈕)          │
├─────────────────────────────────┤
│ 最近打卡記錄 (列表)             │
└─────────────────────────────────┘
```

### 其他頁面

- **個人資料**：表單 + 密碼修改
- **請假申請**：表單 + 審核流程
- **補打卡申請**：表單 + 審核流程
- **報表查詢**：篩選 + 圖表 + 匯出
- **使用者管理**：表格 + CRUD 操作
- **公司管理**：表格 + CRUD 操作

---

## 🛠️ 技術實作

### 技術棧

```
前端：Vue 3 + Vite + Tailwind CSS 4 + Pinia
後端：FastAPI + SQLAlchemy + PostgreSQL
認證：JWT
部署：Docker + Nginx
```

### 專案結構

```
frontend/
├─ src/
│  ├─ components/     # 可重用組件
│  ├─ views/          # 頁面組件
│  ├─ api/            # API 層
│  ├─ stores/         # Pinia 狀態
│  ├─ router/         # 路由配置
│  └─ utils/          # 工具函數
```

### API 呼叫範例

```javascript
import { attendanceApi } from '@/api/attendance';

// 打卡
await attendanceApi.punch({
  attendance_type: 'IN',
  latitude: 25.0330,
  longitude: 121.5654,
});

// 獲取狀態
const status = await attendanceApi.getStatus();

// 獲取記錄
const logs = await attendanceApi.getLogs({ limit: 10 });
```

---

## 📊 配色速查表

### 主要配色

| 用途 | 色碼 | Tailwind | 使用場景 |
|------|------|----------|----------|
| 主要按鈕 | #4A6FA5 | bg-[#4A6FA5] | 上班/下班打卡 |
| 主要 Hover | #3D5A8A | bg-[#3D5A8A] | 按鈕懸停 |
| 次要按鈕 | #F2E8DF | bg-[#F2E8DF] | 外出/返回打卡 |
| 次要 Hover | #E8D9CA | bg-[#E8D9CA] | 次要懸停 |
| 標題文字 | #1C3B6B | text-[#1C3B6B] | 頁面標題 |
| 主要文字 | #2D3A52 | text-[#2D3A52] | 正文內容 |
| 次要文字 | #5A6C7D | text-[#5A6C7D] | 說明文字 |
| 頁面背景 | #F4F7F9 | bg-[#F4F7F9] | 整體背景 |
| 卡片背景 | #FFFFFF | bg-white | 內容卡片 |

### 功能色彩

| 用途 | 色碼 | 使用場景 |
|------|------|----------|
| 成功 | #2E7D32 | 打卡成功、已完成 |
| 錯誤 | #C62828 | 打卡失敗、錯誤 |
| 警告 | #F57C00 | 遲到、早退 |
| 資訊 | #1976D2 | 提示訊息 |

---

## 🎯 開發檢查清單

### 開始前

- [ ] 閱讀所有設計文檔
- [ ] 理解配色系統
- [ ] 熟悉組件設計
- [ ] 了解技術棧

### 開發中

- [ ] 使用正確的配色（商務藍 + 沙色）
- [ ] 遵循組件設計規範
- [ ] 保持代碼風格一致
- [ ] 撰寫清晰的註釋
- [ ] 測試響應式佈局

### 完成後

- [ ] 檢查配色是否正確
- [ ] 測試所有交互功能
- [ ] 驗證響應式設計
- [ ] 檢查無障礙性
- [ ] 性能優化

---

## 📝 設計原則

### 1. 專業性優先

```
沉穩的商務藍 > 活潑的亮藍色
溫暖的沙色 > 冷淡的灰色
```

### 2. 功能性優先

```
清晰的操作流程 > 花俏的動畫效果
明確的狀態提示 > 複雜的視覺設計
```

### 3. 一致性優先

```
統一的圓角 (12-16px)
統一的陰影 (0 2px 8px)
統一的間距 (8px 倍數)
統一的過渡 (0.2s ease)
```

---

## 🔗 相關資源

### 設計參考

- [舊系統](http://localhost:8000) - 功能參考
- [PSMS 系統](http://localhost:8080) - 技術參考

### 技術文檔

- [Vue 3 官方文檔](https://vuejs.org/)
- [Tailwind CSS 文檔](https://tailwindcss.com/)
- [Pinia 文檔](https://pinia.vuejs.org/)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)

### 設計工具

- [Figma](https://www.figma.com/) - UI 設計
- [Coolors](https://coolors.co/) - 配色工具
- [Heroicons](https://heroicons.com/) - 圖示庫

---

## 💡 常見問題

### Q1: 為什麼不使用序號系統的亮藍色？

**A**: 考勤系統需要更沉穩、專業的視覺感受，商務藍 (#4A6FA5) 比亮藍色 (#2563EB) 更適合正式的人事管理場景。同時，通過顏色區分兩個系統，用戶可以快速識別當前所在系統。

### Q2: 沙色系的作用是什麼？

**A**: 沙色 (#F2E8DF) 作為輔助色，為系統增加溫暖感，避免純藍色系統過於冷淡。用於次要按鈕、下拉選單等輔助元素。

### Q3: 如何確保兩個系統的一致性？

**A**: 雖然配色不同，但兩個系統在以下方面保持一致：
- 組件結構（按鈕、卡片、表格）
- 交互方式（Hover、點擊、過渡）
- 響應式斷點
- 功能色彩（成功、錯誤、警告）

### Q4: 移動端如何適配？

**A**: 採用響應式設計：
- 手機版：單列佈局、全寬按鈕
- 平板版：雙列佈局、適中按鈕
- 桌面版：多列佈局、標準按鈕

---

## 📞 聯絡資訊

如有任何設計或技術問題，請參考：

- **設計文檔**: `/opt/attendance-system/docs/UIdoc/`
- **技術文檔**: `/opt/attendance-system/docs/`
- **舊系統參考**: `/opt/oldsystem/attendancev1/`

---

## 📅 更新記錄

- **2026-03-05**: 初版發布
  - 完成配色系統設計
  - 完成組件設計規範
  - 完成首頁完整實作
  - 完成技術規範文檔

---

**設計團隊**: Claude (Opus 4)  
**報告日期**: 2026-03-05  
**版本**: v1.0
