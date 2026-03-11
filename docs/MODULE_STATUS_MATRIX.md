# MODULE_STATUS_MATRIX.md

## Purpose

各模組的權威狀態表。每個狀態欄位明確區分 DOC_COMPLETE / CODE_COMPLETE / VERIFIED 三種層次，不得混用。

## Scope

覆蓋所有已實作模組（7 個）與缺少模組（7 個）。

## Source of Truth

- CODE SCAN（主要）：直接讀取程式碼、migration、測試檔案
- DOCS（對照）：docs/ 目錄
- RUNTIME VERIFICATION：本次未執行

## Last Updated

2026-03-11

---

## 狀態定義

| 標籤 | 定義 |
|------|------|
| `DOC_COMPLETE` | 規格文件存在且完整，但程式碼未實作或未驗證 |
| `CODE_COMPLETE` | 程式碼已實作，但未在真實環境執行驗證 |
| `VERIFIED` | 已在真實環境（真實 PostgreSQL + 真實請求）執行並確認正確 |
| `MISSING` | 完全缺失，規格文件也無詳細定義 |
| `PARTIAL` | 部分實作，有明確缺口 |
| `DEPRECATED` | 已廢棄或已移除 |

---

## A. 已實作模組狀態矩陣

### A1. auth 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | Platform-First Identity，JWT 登入，User/Role/Permission 管理 | - |
| **spec 狀態** | `CODE_COMPLETE` | SA_MODULE_SPEC v2.0 有定義；無獨立 docs.md |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py 齊全 |
| **migration** | `CODE_COMPLETE` | 3532deda024c_create_auth_tables_v2_platform_first |
| **tests** | `CODE_COMPLETE` | test_login_api.py, test_repo.py（共 2 files）；未在真實 DB 驗證 |
| **auth 方式** | `CODE_COMPLETE` | JWT Bearer（login endpoint 本身無需 auth） |
| **tenant isolation** | `CODE_COMPLETE` | users 為 global（無 company_id）；memberships 有 company_id |
| **RBAC** | `CODE_COMPLETE` | roles/permissions/user_roles 已建立；但 RBAC 在 endpoint 層未強制套用 |
| **feature gate** | `MISSING` | 未套用 |
| **runtime verification** | `MISSING` | 未在真實 DB 執行登入流程驗證 |
| **完成度（保守）** | 80% | |
| **主要風險** | 無獨立 docs.md；RBAC 在 API 層未強制；runtime 未驗證 |
| **可進入下一階段** | ✅ 可，但需補 runtime verification |
| **建議優先級** | P1 |

---

### A2. tenants 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | Tenant 管理、Entitlements CRUD、Feature Flag 控制 | - |
| **spec 狀態** | `CODE_COMPLETE` | SA_MODULE_SPEC v2.0 有定義；無獨立 docs.md |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py 齊全 |
| **migration** | `CODE_COMPLETE` | 004_create_tenants + wp_11_04a_entitlements |
| **tests** | `CODE_COMPLETE` | test_entitlements_api.py, test_repo.py, test_service.py（3 files） |
| **auth 方式** | `CODE_COMPLETE` | JWT Bearer + `get_current_actor()` ✅ |
| **tenant isolation** | `CODE_COMPLETE` | 所有查詢帶 company_id |
| **RBAC** | `CODE_COMPLETE` | `assert_company_scope()` 已套用 |
| **feature gate** | `PARTIAL` | Feature Gate 基礎設施完整；entitlements API 本身不需 feature gate |
| **runtime verification** | `MISSING` | 未在真實 DB 驗證 |
| **完成度（保守）** | 85% | |
| **主要風險** | runtime 未驗證；docs.md 缺失 |
| **可進入下一階段** | ✅ 可 |
| **建議優先級** | P1 |

---

### A3. attendance 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | 打卡核心（punch-in/out）、break-out/in、Session 管理、Policy Engine、Location Policy | - |
| **spec 狀態** | `DOC_COMPLETE` | SA_MODULE_SPEC v2.0 + ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py / policy_engine.py / location_policy_service.py / gps_utils.py 齊全 |
| **migration** | `CODE_COMPLETE` | 001b + 006 + 007 + 008（共 4 個相關 migration） |
| **tests** | `PARTIAL` | 10 個測試檔存在；8 個回歸測試只有 Test 8（cross-midnight），其餘 7 個**未實作**；所有測試**未在真實 DB 執行** |
| **auth 方式** | `PARTIAL` | 使用 X-Company-ID Header（`get_current_company_id`）；**需轉換為 JWT**（WP-11-06） |
| **tenant isolation** | `CODE_COMPLETE` | repo 層所有查詢帶 company_id；代碼正確但 runtime 未驗證 |
| **RBAC** | `PARTIAL` | admin_location_api.py 的 CRUD 有 `# TODO: 驗證管理員權限`，**完全無 RBAC** |
| **feature gate** | `MISSING` | `assert_feature_enabled()` 未套用到任何 attendance endpoint |
| **runtime verification** | `MISSING` | WP-11-13 Manual QA BLOCKED；回歸測試從未在真實 DB 通過 |
| **完成度（保守）** | 65% | |
| **主要風險** | (1) Header auth 安全漏洞；(2) Admin Location API 無 RBAC；(3) 回歸測試 7/8 未實作；(4) Location Policy 只在 BREAK_OUT 生效；(5) Runtime 未驗證 |
| **可進入下一階段** | ❌ 不可，Auth 轉換和回歸測試是前提 |
| **建議優先級** | P0 |

---

### A4. audit 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | 稽核日誌、retention policy、purge | - |
| **spec 狀態** | `CODE_COMPLETE` | 有 docs.md（attendance/docs.md 混在一起）；SA_MODULE_SPEC 有定義 |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py 齊全 |
| **migration** | `CODE_COMPLETE` | 002_create_audit_logs + 003_create_audit_retention_policies |
| **tests** | `CODE_COMPLETE` | test_audit_api.py, test_audit_backup.py, test_audit_retention.py（3 files） |
| **auth 方式** | `PARTIAL` | 使用 X-Company-ID Header；**需轉換為 JWT**（WP-12） |
| **tenant isolation** | `CODE_COMPLETE` | 所有查詢帶 company_id |
| **RBAC** | `MISSING` | 無 RBAC；任何有效 Header 的請求均可存取 |
| **feature gate** | `MISSING` | 未套用 |
| **runtime verification** | `MISSING` | 未在真實 DB 執行 |
| **完成度（保守）** | 70% | |
| **主要風險** | Header auth；無 RBAC；runtime 未驗證 |
| **可進入下一階段** | ❌ 需完成 Auth 轉換（WP-12） |
| **建議優先級** | P0（Auth 轉換）/ P1（其他） |

---

### A5. backup 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | 單一公司備份匯出/還原、Tenant Isolation | - |
| **spec 狀態** | `CODE_COMPLETE` | backup_restore_audit_design.md 存在 |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / exporter.py / importer.py / validator.py（無 models/repo，設計決策） |
| **migration** | N/A | 無自有 migration（跨模組操作） |
| **tests** | `CODE_COMPLETE` | test_api.py, test_tenant_isolation.py, test_validator.py（3 files） |
| **auth 方式** | `PARTIAL` | 使用 X-Company-ID Header；**SYSTEM_DEVELOPMENT_STATUS_REPORT 誤寫為 JWT**（CODE SCAN 確認為 Header） |
| **tenant isolation** | `CODE_COMPLETE` | exporter/importer 均強制單一 company_id |
| **RBAC** | `MISSING` | 無 RBAC；任何人可備份或還原 |
| **feature gate** | `MISSING` | 未套用 |
| **runtime verification** | `MISSING` | 未在真實 DB 執行備份/還原流程 |
| **完成度（保守）** | 70% | |
| **主要風險** | Header auth（SYSTEM_DEVELOPMENT_STATUS_REPORT 記錄有誤）；無 RBAC；runtime 未驗證 |
| **可進入下一階段** | ❌ 需完成 Auth 轉換（WP-12） |
| **建議優先級** | P0（Auth 轉換）/ P1（其他） |

> ⚠️ **文件不一致警告**：`SYSTEM_DEVELOPMENT_STATUS_REPORT.md` 將 backup 模組列為「JWT」auth，但 CODE SCAN 確認 `backup/api.py` 使用 `get_current_company_id`（Header）。舊報告此處**有誤**，應以本文件為準。

---

### A6. notifications 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | 事件通知、EventBus 訂閱者 | - |
| **spec 狀態** | `CODE_COMPLETE` | 有 docs.md |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / event_handlers.py 齊全 |
| **migration** | `CODE_COMPLETE` | 005_create_notifications |
| **tests** | `CODE_COMPLETE` | test_api.py, test_event_handlers.py, test_tenant_isolation.py（3 files） |
| **auth 方式** | `PARTIAL` | 使用 X-Company-ID Header；**需轉換為 JWT**（WP-12） |
| **tenant isolation** | `CODE_COMPLETE` | 所有查詢帶 company_id |
| **RBAC** | `MISSING` | 無 RBAC |
| **feature gate** | `MISSING` | 未套用 |
| **runtime verification** | `MISSING` | 未在真實 DB 執行 |
| **完成度（保守）** | 70% | |
| **主要風險** | Header auth；無 RBAC；runtime 未驗證 |
| **可進入下一階段** | ❌ 需完成 Auth 轉換（WP-12） |
| **建議優先級** | P0（Auth 轉換）/ P1（其他） |

---

### A7. customer_service 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | 客服人員跨公司存取範圍管理、support_company_assignments | - |
| **spec 狀態** | `CODE_COMPLETE` | SA_MODULE_SPEC 有定義 |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py 齊全 |
| **migration** | `CODE_COMPLETE` | wp_11_04a_entitlements（含 support_company_assignments） |
| **tests** | `PARTIAL` | 只有 1 個測試檔（__init__.py 在 tests/ 目錄）；測試覆蓋不足 |
| **auth 方式** | `CODE_COMPLETE` | JWT Bearer + `get_current_actor()` ✅ |
| **tenant isolation** | `CODE_COMPLETE` | Scope 驗證已套用 |
| **RBAC** | `CODE_COMPLETE` | `assert_company_scope()` 已套用 |
| **feature gate** | `MISSING` | 未套用 |
| **runtime verification** | `MISSING` | 未在真實 DB 執行 |
| **完成度（保守）** | 75% | |
| **主要風險** 