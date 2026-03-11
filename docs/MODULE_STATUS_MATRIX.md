# MODULE_STATUS_MATRIX.md

## Purpose

各模組的權威狀態表。每個狀態欄位明確區分 DOC_COMPLETE / CODE_COMPLETE / VERIFIED 三種層次，不得混用。

## Scope

覆蓋所有已實作模組（7 個）與缺少模組（7 個）。

## Source of Truth

- CODE SCAN（主要）：直接讀取程式碼、migration、測試檔案
- DOCS（對照）：docs/ 目錄
- RUNTIME VERIFICATION：WP-C1-01（2026-03-11）部分執行

## Last Updated

2026-03-11（WP-C1-01 完成後更新）

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
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py / policy_engine.py / 