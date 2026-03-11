# WORKSTREAM_STATUS_LEDGER.md

## Purpose

本文件為「工作流狀態帳本」，每完成一個 WP 或模組後必須更新。
不是一次性報告，而是持續維護的執行記錄。

## Scope

記錄每個 WP 的完成狀態、已驗證內容、未驗證內容、測試結果、文件一致性、下一步建議。

## Source of Truth

- 本文件（持續更新）
- `MODULE_STATUS_MATRIX.md`（模組層面狀態）
- `GATE_PROGRESS_TRACKER.md`（Gate 層面進度）

## Last Updated

2026-03-11（首次建立，基線版本）

## 更新規則

每完成一個 WP 後，必須在本文件新增一個章節，格式如下：

```markdown
### WP-[ID]：[名稱]

**完成日期：** YYYY-MM-DD  
**Git Commit：** [commit hash]  
**負責人：** [AI session / 開發者]

**已完成：**
- [具體交付物列表]

**已驗證（VERIFIED）：**
- [通過的測試、手動驗證的功能]

**未驗證（NOT_VERIFIED）：**
- [尚未驗證的項目及原因]

**測試結果：**
- pytest 結果：[X/Y PASS]
- Manual QA：[PASS/FAIL/BLOCKED]

**文件一致性：**
- [更新了哪些文件]
- [發現的文件不一致問題]

**下一步：**
- [後續 WP 或行動項目]
```

---

## 歷史記錄

### WP-11-01：Attendance Domain Model

**完成日期：** 2026-03-03  
**Git Commit：** 未記錄  

**已完成：**
- `001b_create_attendance_domain_v2_fixed.py`（migration）
- `attendance/models.py`（attendance_policies, attendance_sessions, attendance_punches）
- `attendance/repo.py`
- `attendance/tests/test_model_constraints.py`
- `attendance/tests/test_migration.py`
- `attendance/tests/test_business_invariant.py`

**已驗證（VERIFIED）：**
- 文件記載：41/41 測試通過（來源：ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md）

**未驗證（NOT_VERIFIED）：**
- 測試是否在真實 PostgreSQL DB 通過（文件未明確說明執行環境）
- migration 001b 在 fresh DB 可否獨立執行

**狀態：** `DOC_COMPLETE`（41 tests）、`CODE_COMPLETE`（code scan 確認）、runtime `NOT_VERIFIED`

---

### WP-11-02：Punch In/Out API

**完成日期：** 2026-03-03  
**Git Commit：** 未記錄  

**已完成：**
- `attendance/api.py`（punch-in, punch-out, current-status, history endpoints）
- `attendance/service.py`
- `attendance/schemas.py`
- `attendance/tests/test_punch_api.py`

**已驗證（VERIFIED）：**
- 文件記載：17/17 測試通過

**未驗證（NOT_VERIFIED）：**
- 測試使用 Header auth（非 JWT），需在 JWT 轉換後重新驗證
- 真實 DB 執行未確認

**狀態：** `CODE_COMPLETE`；auth 方式需 WP-C1-02 修正

---

### WP-11-03：Policy Engine v1

**完成日期：** 2026-03-04  
**Git Commit：** 未記錄  

**已完成：**
- `attendance/policy_engine.py`（24KB）
- `attendance/tests/test_policy_engine.py`

**已驗證（VERIFIED）：**
- 文件記載：24/24 測試通過

**未驗證（NOT_VERIFIED）：**
- PENDING_APPROVAL exclusion 邏輯是否正確（需回歸測試 Test 4 驗證）
- 真實 DB 執行未確認

**狀態：** `CODE_COMPLETE`；runtime `NOT_VERIFIED`

---

### WP-11-04A：Company Entitlements + Feature Flags

**完成日期：** 2026-03-04  
**Git Commit：** 未記錄  

**已完成：**
- `wp_11_04a_entitlements.py`（migration）
- `tenants/api.py`（entitlements CRUD）
- `customer_service/api.py`（assignments）
- `core/feature_service.py`
- `core/features.py`

**已驗證（VERIFIED）：**
- 文件記載：測試通過

**未驗證（NOT_VERIFIED）：**
- Feature Gate 套用至 API endpoint（尚未完成）
- 真實 DB 執行未確認

**狀態：** `CODE_COMPLETE`；Feature Gate 套用 `MISSING`

---

### WP-11-04B：Gate Ready Audit

**完成日期：** 2026-03-04  
**Git Commit：** 未記錄  

**已完成：**
- SA_REALITY_GAP_REPORT.md
- REALITY_AUDIT_STATUS_INVENTORY.md
- MIGRATION_CHAIN_AUDIT_REPORT.md（referenced）

**未驗證（NOT_VERIFIED）：**
- 部分結論已過期（如 backup auth 方式誤記）

**狀態：** `DOC_COMPLETE`；被本次 SYSTEM_VERIFICATION_BASELINE.md 更新取代

---

### WP-11-05A：Attendance Models Sync

**完成日期：** 未記錄  
**Git Commit：** 未記錄  

**狀態：** 文件列為 COMPLETED，具體內容未詳細記錄

---

### WP-11-07 ~ WP-11-13 Step3A：Frontend UI 系列

**完成日期範圍：** 2026-03-05 ~ 2026-03-10  
**最後 Git Commit：** d8eb797（WP-11-13 Critical Bug Fix，2026-03-08）

**已完成：**
- Login.vue、Home.vue（3-Card 佈局）
- auth store、attendance store
- useLocation composable（GPS）
- break-out/in GPS 整合
- Location Policy 錯誤處理
- punch note 編輯

**已驗證（VERIFIED）：**
- Code scan 確認元件存在

**未驗證（NOT_VERIFIED）：**
- WP-11-13 Manual QA：BLOCKED（需真實瀏覽器 + PostgreSQL）
- GPS 定位實際流程
- Location Policy 端到端驗證

**狀態：** `CODE_COMPLETE`；Manual QA `NOT_VERIFIED`

---

## 當前系統基線狀態（2026-03-11）

| 項目 | 數值 |
|------|------|
| 已實作後端模組 | 7 |
| AUTH JWT 完成模組 | 2（tenants, customer_service） |
| AUTH Header 待轉換模組 | 5（attendance, audit, backup, notifications, admin_location） |
| Migration 數量 | 10（含 deprecated 1 個） |
| Migration Head | 008_wp_11_13 |
| 有效前端路由 | 2（/, /login） |
| 回歸測試實作數 | 1/8（Test 8 骨架） |
| 回歸測試在真實 DB 通過 | 0/8 |
| P0 技術債 | 4 項 |

---

## 待更新提醒

每完成以下 WP，必須在本文件新增對應章節：

- [ ] WP-C1-01：PostgreSQL 環境建立 + Migration 驗證
- [ ] WP-C1-02：Attendance Auth JWT 轉換
- [ ] WP-C1-03：Auth 轉換 Batch 2
- [ ] WP-C1-04：8 個回歸測試
- [ ] WP-C1-05：Tenant Isolation 真實 DB 測試
- [ ] WP-C1-06：Feature Gate 套用
- [ ] WP-C1-07：API 文件補齊
- [ ] WP-C2-01：Location Policy 擴展
- [ ] WP-C2-02：Reporting Backend
- [ ] WP-11-13 Manual QA：執行後記錄

---

## System Reality Verification v2（2026-03-11）

**執行日期：** 2026-03-11  
**性質：** 純驗證（Read-Only），未修改任何程式碼

### 驗證範圍

- A. Auth / Identity / Scope：逐 api.py grep Depends() 宣告
- B. Attendance 核心：逐 endpoint 讀取實作細節
- C. audit / backup / notifications：grep auth 機制
- D. Migration Chain：grep down_revision 建立完整鏈
- E. Test Coverage：grep def test_、DB 類型、Mock 使用
- F. Frontend：router/index.js、stores/、殘留檔案
- G. Docs 一致性：7 份文件交叉比對

### CODE_CONFIRMED 關鍵發現

| 發現 | 影響 |
|------|------|
| backup/api.py 使用 Header auth（非 JWT） | SYSTEM_DEVELOPMENT_STATUS_REPORT 此欄位有誤 |
| admin_location 3 個寫入端點均為 # TODO RBAC | P0 安全漏洞，任何用戶可管理地點政策 |
| Location Policy 只在 break-out 有效 | punch-in/out/break-in 無 location check |
| Feature Gate 完全未套用任何生產 endpoint | SaaS 功能分級無效 |
| test_regression.py 只有 1 個 test function | Test 1-7 完全不存在 |
| test_tenant_isolation.py 用 DummySession | 非真實 DB 驗證 |
| audit/backup/notifications 測試用 SQLite :memory: | 無法驗證 PostgreSQL 特有行為 |
| customer_service 有 0 個 test functions | 完全無測試覆蓋 |
| Header auth 端點實際為 24 個（非 18 個） | admin_location 5 個端點未被舊報告計入 |
| migration chain 單一 head（008_wp_11_13） | CODE_CONFIRMED 正確 |

### 仍 NOT_VERIFIED 項目

- alembic upgrade head runtime 執行
- 所有 pytest 在真實 PostgreSQL 執行結果
- JWT login → attendance API 完整流程
- GPS → break-out → location policy 端到端
- Tenant Isolation 在真實 DB 查詢層

### 文件更新

- **新增**：`docs/SYSTEM_REALITY_REPORT_v2.md`（主報告）
- **更新**：`docs/GATE_PROGRESS_TRACKER.md`（修正 Header auth 模組數、回歸測試狀態）
- **更新**：`docs/NEXT_WP_TICKET.md`（複核確認 WP-C1-01 不變）
- **更新**：`docs/SYSTEM_DEVELOPMENT_STATUS_REPORT.md`（加 SUPERSEDED 聲明）

### 被標示為過期或需 refresh 的文件

| 文件 | 問題 |
|------|------|
| SYSTEM_DEVELOPMENT_STATUS_REPORT.md | backup auth 欄位錯誤；Header 端點數錯誤 |
| ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md | 聲稱 location policy 適用全部打卡流程，實際只有 break-out |
| ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md | WP-11-04B 仍標為 CURRENT（已完成） |
