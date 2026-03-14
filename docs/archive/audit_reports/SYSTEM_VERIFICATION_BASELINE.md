# SYSTEM_VERIFICATION_BASELINE.md

## Purpose

本文件為 Attendance SaaS 系統的「全系統驗證基線」，記錄透過直接 code scan 所建立的真實系統狀態。  
本文件是後續所有開發決策、驗收判斷、測試計畫的起點權威。

## Scope

- Backend：`backend/app/modules/`（7 模組）、`backend/app/core/`、`backend/alembic/versions/`
- Frontend：`frontend/src/`（所有 .vue / .js / .ts）
- Documentation：`docs/`（所有 .md）
- Migration Chain：alembic versions 完整鏈條
- Test Files：所有 pytest 測試檔案

## Source of Truth

- **CODE SCAN**：直接讀取程式碼檔案、API 路由定義、migration revision
- **DOCS**：docs/ 目錄下的規格文件（僅作為對照參考，非驗證依據）
- **RUNTIME VERIFICATION**：本次未執行（原因見下方「驗證限制」）

## Last Updated

2026-03-11（首次建立）

---

## 1. 驗證方法

| 驗證層 | 方法 | 結果可信度 |
|--------|------|------------|
| 檔案存在性 | 直接 find + cat | HIGH |
| API 路由定義 | 讀取 api.py / main.py | HIGH |
| Auth 機制 | 讀取 Depends() 宣告 | HIGH |
| Tenant Isolation | 讀取 repo/service 查詢 | HIGH |
| Migration Chain | 讀取 down_revision 鏈 | HIGH |
| 測試存在性 | 讀取測試檔案結構 | HIGH |
| 測試實際通過 | 未在真實 DB 執行 | NOT_VERIFIED |
| Runtime behavior | 未啟動服務 | NOT_VERIFIED |
| Browser GPS 流程 | 未在真實瀏覽器測試 | NOT_VERIFIED |

## 2. 驗證限制

以下項目因環境限制，本次**未能完成** runtime 驗證：

1. `alembic upgrade head` 是否可在 fresh PostgreSQL DB 執行成功
2. pytest 回歸測試是否在真實 DB 環境下全部通過
3. GPS / Location Policy 端到端流程是否正確（需真實瀏覽器）
4. JWT token 從 login 到打卡的完整流程
5. 跨租戶隔離是否在真實查詢下有效（DB 層級）

如需完成上述驗證，需要：
- PostgreSQL 15+ 資料庫（可用）
- `alembic upgrade head` 執行
- `pytest backend/` 執行並取得報告
- 瀏覽器環境 + GPS 支援

---

## 3. Migration Chain 驗證結果

**來源：CODE SCAN（讀取每個 migration 的 down_revision）**

```
真實 Migration Chain（從 CODE 讀取）：

004_create_tenants
  ↓ (down_revision: None — 為 chain root)
3532deda024c_create_auth_tables_v2_platform_first
  ↓ (down_revision: '004')
005_create_notifications
  ↓ (down_revision: '3532deda024c')
002_create_audit_logs
  ↓ (down_revision: '005')
003_create_audit_retention_policies
  ↓ (down_revision: '002')
001b_create_attendance_domain_v2_fixed
  ↓ (down_revision: '003')
wp_11_04a_entitlements
  ↓ (down_revision: '001b')
006_expand_session_status
  ↓ (down_revision: 'wp_11_04a_entitlements')
007_wp_11_10_create_out_checkpoints
  ↓ (down_revision: '006')
008_wp_11_13_create_allowed_locations
  ↓ (down_revision: '007_wp_11_10')
[HEAD]
```

**結論：**
- ✅ Migration chain 為線性（single head），無分叉
- ✅ `001_create_attendance_domain_v2.py.deprecated` 已標記為 deprecated，chain 使用 001b
- ✅ Head revision：`008_wp_11_13`
- ⚠️ `007_wp_11_10_create_out_checkpoints` 建立了 `attendance_out_checkpoints` 表，但 WP-11-10 已被 COMPLETED+REMOVED
- ⚠️ Runtime 執行（alembic upgrade head on fresh DB）未驗證
- **MIGRATION 狀態：CODE_COMPLETE，NOT_VERIFIED（runtime）**

**已確認的 Tables（基於 migration code scan）：**

| Table | Migration | company_id? | 備註 |
|-------|-----------|-------------|------|
| tenants | 004 | N/A (PK) | Root |
| users | 3532deda024c | ❌ Global | Platform Data |
| roles | 3532deda024c | ❌ Global | |
| permissions | 3532deda024c | ❌ Global | |
| user_roles | 3532deda024c | ❌ Global | |
| user_company_memberships | 3532deda024c | ✅ | Membership Data |
| notifications | 005 | ✅ | Tenant Data |
| audit_logs | 002 | ✅ | Tenant Data |
| audit_retention_policies | 003 | ✅ | Tenant Data |
| attendance_policies | 001b | ✅ | Tenant Data |
| attendance_sessions | 001b | ✅ | Tenant Data |
| attendance_punches | 001b | ✅ | Tenant Data |
| company_entitlements | wp_11_04a | ✅ | Tenant Data |
| support_company_assignments | wp_11_04a | ✅ | Membership Data |
| attendance_sessions (status expand) | 006 | - | ALTER |
| attendance_out_checkpoints | 007 | ✅ | Tenant Data（功能已移除） |
| 