# TEST_STRATEGY_MASTER.md

## Purpose

系統總測試計畫，按模組分類，明確標記現有測試、缺少測試、需要補的測試，以及執行環境要求。

## Scope

覆蓋所有 backend 模組的單元測試、整合測試、回歸測試、Tenant Isolation 測試、Auth/RBAC 測試、Migration 測試、Frontend 互動測試、Manual QA。

## Source of Truth

- CODE SCAN（讀取所有 tests/ 目錄）
- `MODULE_STATUS_MATRIX.md`

## Last Updated

2026-03-11

---

## 測試環境要求

| 環境 | 用途 | 目前狀態 |
|------|------|----------|
| In-memory / Mock DB | 純邏輯單元測試 | ✅ 可用（現有 DummySession） |
| 真實 PostgreSQL DB | 整合測試、回歸測試、Tenant Isolation | ⚠️ 需建立（WP-C1-01）|
| 真實 Browser + GPS | Location Policy Manual QA | ⚠️ 需手動環境 |
| Backend 服務啟動 | API-level 整合測試 | ⚠️ 需啟動服務 |

---

## 最低測試門檻（每個模組上線前必須達到）

| 模組 | 最低門檻 |
|------|----------|
| auth | 登入/失敗/JWT 解析/membership 查詢 各 1 個 API test，在真實 DB 通過 |
| tenants | Entitlements CRUD + Scope 驗證 各 1 個 API test，在真實 DB 通過 |
| attendance | 8 個回歸測試 + 5 個 Tenant Isolation 測試，在真實 DB 全部通過 |
| audit | query + export + retention + purge 各 1 個 API test，在真實 DB 通過 |
| backup | export + restore + Tenant Isolation 各 1 個測試，在真實 DB 通過 |
| notifications | query + EventBus 觸發 各 1 個測試 |
| customer_service | Scope 驗證（已指派/未指派） 各 1 個測試 |

---

## 各模組測試盤點

### T1. auth 模組

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| test_login_api.py | API | ✅ 存在 | 未確認 JWT auth 轉換後是否更新 | ✅ |
| test_repo.py | Unit | ✅ 存在 | - | ✅ |
| **Auth/RBAC 測試** | API | ❌ 缺失 | 過期 token → 401；非 active user → 403 | ✅ |
| **JWT token 解析測試** | Unit | ❌ 缺失 | decode_access_token edge cases | ❌ |

**缺口優先級：** P1

---

### T2. tenants 模組

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| test_entitlements_api.py | API | ✅ 存在 | 是否含 Scope 驗證測試？需確認 | ✅ |
| test_repo.py | Unit | ✅ 存在 | - | ✅ |
| test_service.py | Unit | ✅ 存在 | - | ✅ |
| **Scope 驗證測試** | API | ❌ 可能缺失 | 無 membership → 403；跨公司 → 403 | ✅ |

**缺口優先級：** P1

---

### T3. attendance 模組

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| test_regression.py | 回歸 | ⚠️ 只有 Test 8 | **Test 1-7 未實作** | ✅ |
| test_tenant_isolation.py | Tenant | ⚠️ Mock DB | **需改用真實 DB** | ✅ |
| test_tenant_validation.py | Tenant | ✅ 存在 | 未確認是否使用真實 DB | ✅ |
| test_api.py | API | ✅ 存在 | 未確認 JWT 轉換後是否更新 | ✅ |
| test_punch_api.py | API | ✅ 存在 | 同上 | ✅ |
| test_business_invariant.py | Unit | ✅ 存在 | - | ⚠️ |
| test_migration.py | Migration | ✅ 存在 | 未在真實 DB 執行 | ✅ |
| test_model_constraints.py | Unit | ✅ 存在 | - | ⚠️ |
| test_policy_engine.py | Unit | ✅ 存在 | - | ❌ |
| test_location_policy.py | Unit | ✅ 存在 | 需 db_session fixture | ✅ |
| test_break_out_enforcement.py | API | ✅ 存在 | 是否含 JWT auth？ | ✅ |
| test_out_checkpoint.py | Unit | ✅ 存在（功能已移除） | 可能需要清理 | - |
| test_phase4.py | 整合 | ✅ 存在 | 舊版測試，可能過期 | ✅ |
| **Feature Gate 測試** | API | ❌ 缺失 | attendance.punch_in_out disabled → 403 | ✅ |
| **RBAC 測試（Admin Location）** | API | ❌ 缺失 | 普通員工建立 location → 403 | ✅ |
| **Location Policy 整合（punch-in/out）** | API | ❌ 缺失 | WP-C2-01 完成後補 | ✅ |

**缺口優先級：**
- P0：回歸測試 Test 1-7、Tenant Isolation 真實 DB
- P1：Feature Gate 測試、RBAC 測試、JWT 轉換後更新舊測試
- P2：Location Policy 整合測試（WP-C2-01 後）

---

### T4. audit 模組

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| test_audit_api.py | API | ✅ 存在 | 未確認是否含 JWT auth | ✅ |
| test_audit_backup.py | 整合 | ✅ 存在 | - | ✅ |
| test_audit_retention.py | API | ✅ 存在 | - | ✅ |
| **JWT 轉換後更新** | API | ❌ 缺失 | Auth 轉換後所有測試需改用 JWT | ✅ |
| **Feature Gate 測試** | API | ❌ 缺失 | audit.query disabled → 403 | ✅ |
| **Tenant Isolation 測試** | API | ❌ 缺失 | 跨公司 audit log 查詢 | ✅ |

**缺口優先級：** P1

---

### T5. backup 模組

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| test_api.py | API | ✅ 存在 | Auth 轉換後需更新 | ✅ |
| test_tenant_isolation.py | Tenant | ✅ 存在 | 是否使用真實 DB？ | ✅ |
| test_validator.py | Unit | ✅ 存在 | - | ❌ |
| **Feature Gate 測試** | API | ❌ 缺失 | backup.export disabled → 403 | ✅ |

**缺口優先級：** P1

---

### T6. notifications 模組

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| test_api.py | API | ✅ 存在 | Auth 轉換後需更新 | ✅ |
| test_event_handlers.py | Unit | ✅ 存在 | - | ❌ |
| test_tenant_isolation.py | Tenant | ✅ 存在 | 真實 DB 驗證 | ✅ |

**缺口優先級：** P1

---

### T7. customer_service 模組

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| (只有 __init__.py) | - | ⚠️ 幾乎無測試 | **需補齊基本 API 測試** | ✅ |
| **Scope 驗證測試** | API | ❌ 缺失 | 已指派/未指派各 1 個 | ✅ |
| **API CRUD 測試** | API | ❌ 缺失 | assignments CRUD | ✅ |

**缺口優先級：** P1

---

### T8. core 模組

| 測試檔 | 類型 | 現有 | 需 DB |
|--------|------|------|-------|
| test_feature_service.py | Unit | ✅ 存在 | ⚠️ |
| test_scope.py | Unit | ✅ 存在 | ❌ |
| test_tenant_context.py | Unit | ✅ 存在 | ❌ |

---

### T9. Migration / Smoke Tests

| 測試檔 | 類型 | 現有 | 缺口 | 需 DB |
|--------|------|------|------|-------|
| tests/test_migration_smoke.py | Smoke | ✅ 存在 | 未在真實 DB 執行 | ✅ |
| test_db_connection.py | Connection | ✅ 存在 | - | ✅ |

**缺口優先級：** P0（需在真實 DB 執行確認）

---

### T10. Frontend 測試

| 測試類型 | 現有 | 缺口 |
|----------|------|------|
| Unit tests（Vue components） | ❌ 完全缺失 | 需建立（Vitest 或 Jest） |
| Integration tests（store + API mock） | ❌ 完全缺失 | 需建立 |
| Manual QA（WP-11-13 Runsheet） | ⚠️ Runsheet 存在但未執行 | 需環境後執行 |

**缺口優先級：** P1（Manual QA）/ P2（Unit + Integration）

---

## 測試執行順序建議

```
1. WP-C1-01 環境建立後：
   - pytest backend/tests/test_migration_smoke.py
   - pytest backend/test_db_connection.py

2. WP-C1-02 完成後：
   - pytest backend/app/modules/attendance/tests/ -v

3. WP-C1-04 完成後：
   - pytest backend/app/modules/attendance/tests/test_regression.py -v
   - 確認 8/8 PASS

4. WP-C1-05 完成後：
   - pytest backend/app/modules/attendance/tests/test_tenant_isolation_real_db.py -v
   - 確認 5/5 PASS

5. WP-C1-03 完成後：
   - pytest backend/app/modules/audit/tests/ -v
   - pytest backend/app/modules/backup/tests/ -v
   - pytest backend/app/modules/notifications/tests/ -v

6. 全套回歸：
   - pytest backend/ -v --ignore=backend/venv
```
