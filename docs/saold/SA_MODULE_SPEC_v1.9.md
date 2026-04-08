# SA MODULE SPECIFICATION

# Attendance System

Version: 1.9 Status: Platform‑First Architecture Baseline

------------------------------------------------------------------------

# 1. Architecture Purpose

本版本定義 **Platform‑first Identity 架構** 的正式規範。

設計目標：

-   採用 Platform‑first Identity
-   保證 Tenant Isolation 100%
-   支援單一公司 Backup / Restore
-   支援 SaaS 功能分級 (Feature Flags)
-   支援客服跨公司 Scope
-   防止工程層面誤用

------------------------------------------------------------------------

# 2. Architecture Principles

系統採用：

Platform‑first Identity\
Same Database\
Same Tables\
Tenant Isolation via company_id

核心原則：

-   使用者為 **Platform User（全域身份）**
-   業務資料為 **Tenant Data（租戶資料）**
-   company_id 僅存在於 Tenant Data

users 不屬於任何 company。

------------------------------------------------------------------------

# 3. Mandatory Project Structure

每個模組必須存在：

api.py\
service.py\
repo.py\
models.py\
docs.md\
tests/

路徑：

backend/app/modules/`<module_name>`{=html}/

模組清單：

tenants\
auth\
locations\
attendance\
approvals\
notifications\
vehicles\
dispatch\
leave\
accrual\
reporting

------------------------------------------------------------------------

# 4. Cross‑Module Restrictions

禁止事項：

-   禁止跨模組 import 對方 service
-   禁止跨模組 import 對方 repo
-   禁止跨模組寫入其他模組資料表
-   禁止繞過 tenant filter
-   reporting 模組 **只讀**

------------------------------------------------------------------------

# 5. Data Classification

## 5.1 Platform Data

不屬於任何 company。

不得包含 company_id。

範例：

users\
global_permissions\
system_configs\
platform_audit_logs

規則：

-   不可依 company_id 過濾
-   不參與 company restore

------------------------------------------------------------------------

## 5.2 Membership Data

連結 user 與 company。

資料表：

user_company_memberships\
support_company_assignments

規則：

必須包含：

user_id\
company_id

Unique rule

UNIQUE (user_id, company_id)

------------------------------------------------------------------------

### Membership Login Uniqueness

若存在公司登入名稱：

login_username

必須：

UNIQUE (company_id, login_username)

目的：

-   支援 per-company login
-   避免跨公司衝突

------------------------------------------------------------------------

## 5.3 Tenant Data

Tenant Data **必須 100% 綁定 company_id**

範例：

attendance\
leave\
approvals\
dispatch\
vehicles\
accrual\
locations\
notifications

硬規則：

-   每張表必須有 company_id
-   必須 index(company_id)
-   所有查詢必須帶 company_id

------------------------------------------------------------------------

# 6. Request Context

每個 request 必須存在：

current_user_id\
current_company_id

Context 建立流程：

1.  驗證 users（platform identity）
2.  驗證 membership 或 assignment
3.  設定 current_company_id

company_id 不得來自 request body。

------------------------------------------------------------------------

# 7. Platform Roles

## 7.1 super_admin

-   全域角色
-   可操作所有 company
-   可管理 entitlements

------------------------------------------------------------------------

## 7.2 customer_service

全域身份

scope 來源：

support_company_assignments

------------------------------------------------------------------------

## 7.3 company_user

只能操作其 membership company。

------------------------------------------------------------------------

# 8. Company Scope Validation

API 必須依序驗證：

1️⃣ Scope Validation\
2️⃣ Tenant Isolation\
3️⃣ Feature Gate

順序不可顛倒。

------------------------------------------------------------------------

# 9. Tenant Isolation

## Write Rules

Create / Update：

不得信任 request.company_id

必須覆寫：

company_id = current_company_id

------------------------------------------------------------------------

## Query Rules

所有 Tenant Data 查詢：

WHERE company_id = current_company_id

禁止：

-   全表掃描
-   Application layer filter

------------------------------------------------------------------------

# 10. Attendance Core Rules

attendance 核心語意不可破壞：

PENDING_APPROVAL 不參與推導

必須：

APPROVED IN → 才成立出勤

其他模組不得改變此語意。

------------------------------------------------------------------------

# 11. Backup / Restore

## Export

僅匯出 Tenant Data

WHERE company_id = ?

------------------------------------------------------------------------

## Restore

僅還原 Tenant Data

company_id 必須覆寫：

target_company_id

------------------------------------------------------------------------

Restore 禁止：

修改 users\
修改 memberships

------------------------------------------------------------------------

# 12. Primary Key Design

Tenant Data 必須使用：

UUID

禁止依賴 auto-increment INT。

------------------------------------------------------------------------

# 13. Index Rules

所有 Tenant Data：

必須

index(company_id)

------------------------------------------------------------------------

# 14. Tenant Isolation Tests

必須測試：

-   A company 無法讀取 B company
-   錯誤 company_id 寫入被拒
-   無 membership → 403
-   restore 不污染其他 company

------------------------------------------------------------------------

# 15. API Error Codes

401 → 未登入\
403 → 權限或 Feature Gate\
400 → Business Rule\
422 → Schema Error

------------------------------------------------------------------------

# 16. Feature Flags (Company Entitlements)

每個 company 具有 feature flags。

feature_key 格式：

`<domain>`{=html}.`<feature>`{=html}

範例：

attendance.shift_templates\
attendance.split_shift\
attendance.shift_overrides

------------------------------------------------------------------------

## Feature Enforcement

若 feature 未啟用：

HTTP 403

response:

code = FEATURE_DISABLED

feature = "`<feature_key>`{=html}"

------------------------------------------------------------------------

## Validation Order

Scope → Tenant Isolation → Feature Gate

不得混合判斷。

------------------------------------------------------------------------

# 17. Future Scalability

架構支援：

-   一人多公司
-   SaaS billing
-   客服跨公司 scope
-   Feature tier control
-   排班 / Flex time / Split shift

------------------------------------------------------------------------

# 18. Version Summary

  Data Type       company_id
  --------------- ------------
  users           ❌
  memberships     ✅
  tenant data     ✅
  platform data   ❌

------------------------------------------------------------------------

# 19. Version History

v1.7 --- Tenant baseline\
v1.8 --- Platform‑first identity\
v1.9 --- Scope / Feature / Backup architecture finalized
