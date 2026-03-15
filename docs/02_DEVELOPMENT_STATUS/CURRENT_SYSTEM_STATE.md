# Current System State

**建立日期：** 2026-03-15（WP-11-07 COMPLETE 後更新）  
**基於：** 已確認的 repo scan（2026-03-14）+ docs 交叉驗證  
**Repository：** `/opt/attendance-system`

---

## 1. Current WP（當前工作包）

**WP-11-08 — Leave Request System**

- **Status：** PLANNED（WP-11-07 已 COMPLETE，可開始規劃）
- **內容：** 員工請假申請、主管審核流程、請假記錄查詢
- **範圍：** Backend API + Frontend UI + Tenant Isolation
- **前置條件：** WP-11-07 COMPLETE ✅

---

## 2. Next WP（下一個工作包）

**WP-11-09 — Shift / Schedule Management**

- **Status：** PLANNED（必須等 WP-11-08 COMPLETE 後才可開始）
- **內容：** 班表管理、員工班次指派
- **範圍：** Backend API + Frontend UI

---

## 3. Completed Core Modules（已完成核心模組）

| 模組 | 狀態 | 說明 |
|------|------|------|
| **Punch Engine** | ✅ STABLE | punch-in/out、session 建立、跨午夜規則、tenant isolation |
| **Break Engine** | ✅ STABLE | break-out/break-in、GPS 地點條件式驗證 |
| **Session Model** | ✅ STABLE | AttendanceSession 完整資料模型（status、duration、breaks、location）|
| **Policy Engine** | ✅ STABLE | 遲到/早退/加班計算、Split Shift 支援 |
| **Timezone / Cross-midnight Rules** | ✅ STABLE | Session ownership = punch_in_time 的 Asia/Taipei 日期（SA v2.1 §29.2）|
| **Reporting Backend API** | ✅ COMPLETE | 三支 endpoint 全部實作並驗證（WP-11-06，2026-03-14）|
| **Home UI** | ✅ STABLE | 主打卡頁、3-Card 佈局、近期打卡記錄、mobile-first |
| **Authentication（JWT）** | ✅ STABLE | JWT-based auth，Attendance 模組遷移完成（WP-C1-07，2026-03-12）|
| **OUT Checkpoint API** | ✅ DONE | break-out/break-in API（WP-C1-09，2026-03-12）|
| **PostgreSQL Migration Chain** | ✅ VERIFIED | 17 tables，head = 008_wp_11_13（WP-C1-01，2026-03-11）|
| **Reporting UI** | ✅ COMPLETE | 三頁 UI（Sessions / CompanySummary / UserSummary）驗收通過（WP-11-07，2026-03-15）|

### 已完成 Reporting Backend Endpoints

| Endpoint | 狀態 |
|----------|------|
| `GET /api/v1/attendance/sessions` | ✅ COMPLETE |
| `GET /api/v1/attendance/reports/user-summary` | ✅ COMPLETE |
| `GET /api/v1/attendance/reports/company-summary` | ✅ COMPLETE |

---

## 4. Partially Implemented Modules（部分完成模組）

| 模組 | 狀態 | 已完成部分 | 缺口 |
|------|------|-----------|------|
| **Reporting UI** | ✅ COMPLETE（WP-11-07，2026-03-15）| 三頁 UI 驗收通過；BUG-01 FIXED；WARN-01 cleaned；timezone 確認；四態完整 | — |
| **GPS / Location** | ⚠️ FOUNDATION ONLY | `useLocation.js`、`location_policy_service.py`、`gps_utils.py`、break-out 條件式驗證 | punch-in/out/break-in 無 location policy check；外勤打卡流程未實作 |
| **Auth JWT 遷移** | ⚠️ PARTIAL | Attendance 模組已遷移（WP-C1-07）| audit、notifications、backup 模組尚未遷移（WP-C1-03）|
| **Regression Tests** | ⚠️ PARTIAL | 1/8 測試已實作；test infrastructure 存在 | 0/8 在真實 DB 通過（WP-C1-04）|

---

## 5. Known Limitations（已知限制）

### 功能限制

1. **GPS 模組不完整**
   - 現有 GPS 僅為 Foundation（break-out 條件式驗證）
   - punch-in、punch-out、break-in 均無 location policy check
   - 完整 GPS / Field Work（WP-11-10）屬 Phase 3，NOT STARTED
   - ⚠️ 不得將現有 GPS Foundation 誤判為完整 GPS 模組

2. **Leave Request System 尚未實作**
   - 計畫於 WP-11-08 實作
   - 必須等 WP-11-07 完成後才可開始

3. **Shift / Schedule 尚未實作**
   - 計畫於 WP-11-09 實作（Phase 2）

4. **Feature Gate 未套用**
   - 所有核心 API 目前 Feature Gate 覆蓋率 0%
   - 計畫於 WP-C1-06 補足

5. **Auth 遷移未完成**
   - audit、notifications、backup 模組仍使用舊 auth 方式
   - 計畫於 WP-C1-03 遷移

### 技術債

1. **多個 backup 檔案存在於 repo**
   - `Home.vue.backup*`（4 個版本）
   - `attendance.js.backup*`（3 個版本）
   - `api.py.backup*`（2 個版本）

2. **Dead code：** `sessionsFilters` state 在 `reporting.js`（WARN-01）

3. **缺少共用 `formatDuration()` helper**（WARN-03）

### 已知 WP-11-13 阻塞

- WP-11-13 Manual QA（GPS + UI 人工測試）BLOCKED
- 阻塞原因：需真實瀏覽器 + PostgreSQL 環境

---

## 6. Testing Gaps（測試缺口）

### Backend Tests

| 測試類型 | 狀態 | 說明 |
|---------|------|------|
| Migration Smoke Tests | ⚠️ PARTIAL | `test_migration_smoke.py` 存在；部分通過 |
| Model Constraints Tests | ✅ PASS | `test_model_constraints.py` 20/20 通過 |
| Business Invariant Tests | ⚠️ PARTIAL | 6/12 通過（API 簽名問題）|
| Migration Tests | ❌ FAIL | 0/9 通過（env.py URL 覆蓋問題）|
| Regression Tests（真實 DB）| ❌ NOT STARTED | 0/8 通過（WP-C1-04 計畫中）|
| Tenant Isolation Tests（真實 DB）| ❌ NOT STARTED | 0/5 通過（WP-C1-05 計畫中）|

### Frontend Tests

| 測試類型 | 狀態 | 說明 |
|---------|------|------|
| Component Tests | ❌ NOT FOUND | `frontend/src/` 無測試檔案 |
| Integration Tests | ❌ NOT FOUND | 無 |
| E2E Tests | ❌ NOT FOUND | 無 |

### QA 狀態

- **WP-11-07 QA：** IN PROGRESS（Reporting UI 三頁手動 QA 進行中）
- **WP-11-13 Manual QA：** BLOCKED（需真實環境）
- **整體測試覆蓋率：** 低（後端部分覆蓋，前端無覆蓋）

---

## 7. Gate 5 Progress（開發進度）

**Gate 5 估計完成度：50%**

| 條件 | 狀態 |
|------|------|
| WP-C1-01 PostgreSQL 環境建立 | ✅ VERIFIED |
| WP-11-06 Reporting Backend API | ✅ COMPLETE |
| WP-11-07 Reporting UI Polish / QA | ✅ COMPLETE（2026-03-15）|
| Phase 1 基線修正（WP-C1-02 ~ WP-C1-07）| 🔄 部分完成 |
| WP-11-13 Manual QA | ⛔ BLOCKED |
| SA 符合度 > 95% | ❌ 目前約 65-70% |
| 8 個回歸測試真實 DB 通過 | ❌ 0/8 |
| 5 個 Tenant Isolation 測試真實 DB 通過 | ❌ 0/5 |
| 所有模組使用 JWT auth | ❌ 2/7 |
| Feature Gate 套用至所有核心 API | ❌ 0% |

---

## 8. Architecture Summary（架構摘要）

### 技術棧

- **Frontend：** Vue 3 + Pinia + Axios（mobile-first）
- **Backend：** FastAPI + SQLAlchemy + PostgreSQL
- **Auth：** JWT（Bearer token）
- **Timezone：** Asia/Taipei（cross-midnight 規則）
- **Migration HEAD：** `008_wp_11_13`（17 tables）

### 模組位置

```
bachend/app/modules/
├── attendance/     ← 核心打卡模組（STABLE）
├── auth/           ← JWT 認證（STABLE）
├── audit/          ← 審計（auth 未遷移）
├── backup/         ← 備份（auth 未遷移）
├── customer_service/
├── notifications/  ← 通知（auth 未遷移）
└── tenants/        ← 租戶管理

frontend/src/
├── views/
│   ├── Home.vue           ← 主打卡頁（STABLE）
│   ├── Login.vue          ← 登入頁（STABLE）
│   └── reports/           ← 三頁報表 UI（MVP COMPLETE）
├── stores/
│   ├── attendance.js      ← 打卡狀態機（核心保護）
│   ├── auth.js            ← JWT token 管理（核心保護）
│   └── reporting.js       ← 報表資料（BUG-01 已修復）
└── composables/
    └── useLocation.js     ← GPS Foundation
```

---

**此文件為當前系統狀態的單一真相來源（Single Source of Truth）。**  
**更新原則：每完成一個 WP 後，同步更新本文件第 1、2、3、4 節。**

---

*本文件由 AI 依據 2026-03-14 實際 repo scan 結果建立於 2026-03-15。*  
*權威基礎：SYSTEM_DEVELOPMENT_STATUS_SNAPSHOT.md v3.0 + GATE_PROGRESS_TRACKER.md + ATTENDANCE_DEVELOPMENT_ROADMAP.md*
