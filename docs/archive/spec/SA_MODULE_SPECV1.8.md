SA_MODULE_SPEC v1.8（Platform-first 正式版）

目的：

採用 Platform-first Identity 架構

保證 Tenant Isolation 100% 不破壞

支援單一公司 Backup / Restore

支援 SaaS 功能分級與公司層級功能開關

工程層面不可誤用

0?? 架構總則

本系統採用：

Platform-first Identity
Same DB
Same Tables
Tenant Isolation via company_id

核心原則：

使用者為「全域身份（Platform User）」

業務資料為「租戶資料（Tenant Data）」

company_id 僅存在於 Tenant Data

users 不屬於任何公司

1?? 強制專案結構

每個模組必須存在：

api.py

service.py

repo.py

models.py

docs.md

tests/

路徑：

backend/app/modules/<module_name>/

模組清單：

tenants

auth

locations

attendance

approvals

notifications

vehicles

dispatch

leave

accrual

reporting

2?? 禁止事項

禁止跨模組直接 import 對方 service/repo/models

禁止跨模組直接寫入對方資料表

禁止繞過 tenant filter

reporting 只讀，不可改變狀態

3?? 資料分類
A) Platform Data（全域資料）

不屬於任何公司，不含 company_id。

包含：

users

global permissions

system configs

platform audit logs

規則：

不可依 company_id 過濾

不參與單公司 restore

B) Membership Data（關聯資料）

連結 user 與 company。

包含：

user_company_memberships

support_company_assignments

規則：

必須包含 company_id

必須包含 user_id

必須 UNIQUE (user_id, company_id)

3.x Membership Login Uniqueness（建議）

若存在 company 專屬登入識別（如 login_username）：

必須：

UNIQUE (company_id, login_username)

目的：

支援 per-company 登入名稱

避免跨公司衝突

C) Tenant Data（租戶業務資料）

屬於某公司之資料，必須 100% 綁定 company_id。

包含：

attendance

leave

approvals

dispatch

vehicles

accrual

locations

company-level notifications

硬規則：

每張表必須有 company_id

必須建立 index(company_id)

所有查詢必須強制帶 company_id

4?? 身份與 Context 定義

每個 request 必須存在：

current_user_id

current_company_id

流程：

驗證 users（全域身份）

驗證 membership 或 assignment

設定 current_company_id

company_id 不得來自 request body。

4A?? Platform Roles & Company Scope（P0）
4A.1 Platform Roles
super_admin

全域角色

可操作所有 company

可管理 entitlements、assignments、公司設定

customer_service

全域身份

僅可操作被指派的 company

scope 來源：support_company_assignments

company user

僅能操作其 membership 所屬之 company

4A.2 Company Scope 驗證順序（強制）

對任何 company-scope API：

1?? Scope 驗證
2?? Tenant Isolation
3?? Feature Gate（若適用）

此順序不可顛倒。

5?? Tenant Isolation（P0）
寫入規則

Create / Update：

禁止信任 request company_id

必須覆寫為 current_company_id

查詢規則

所有 Tenant Data：

WHERE company_id = current_company_id

禁止全表掃描後過濾。

6?? attendance 核心不可破壞（P0）

PENDING_APPROVAL 不參與推導

必須 APPROVED IN 才成立出勤

其他模組不得改變推導語意

7?? Backup / Restore（P0）
Export

僅匯出 Tenant Data

必須依 company_id 過濾

Restore

僅還原 Tenant Data

覆寫 company_id = target_company_id

混入其他 company_id 必須 fail fast

Restore 不得修改 users 或 memberships。

8?? 主鍵設計原則

Tenant Data 必須使用 UUID。
不得依賴 auto-increment INT。

9?? 索引規則

所有 Tenant Data：

必須 index(company_id)

禁止全表掃描

?? Tenant 測試（P0）

A 公司不可查 B 公司資料

帶錯 company_id 不得寫入

無 membership → 403

restore 不得污染其他公司

11?? API Error 規則

422 → Schema 錯誤

400 → Business Rule

403 → 權限或 Feature Gate

401 → 未登入

12A?? Company Entitlements / Feature Flags（P0）

為支援 SaaS 分級與收費模型。

12A.1 原則

每個 company 有自己的 feature flags

feature 以固定字串 feature_key 表達

Plan（Basic / Pro）僅為建立 company 時的預設組合

super_admin 可後台調整

12A.2 Feature 命名規則

格式：

<domain>.<feature_name>

範例：

attendance.shift_templates

attendance.split_shift

attendance.shift_overrides

12A.3 API 強制規則（P0）

任何受控功能必須：

1?? UI 隱藏或提示
2?? API 強制驗證

若未啟用：

HTTP 403

code = "FEATURE_DISABLED"

feature = "<feature_key>"

12A.4 Scope 與 Feature 分離

驗證順序：

Scope → Tenant Isolation → Feature Gate

不得混合判斷。

13?? 未來擴充保證

本架構支援：

一人多公司

SaaS billing

Super Admin

客服跨公司 scope

功能分級控制

後續排班 / 分段 / Flex Time

? v1.8 總結
類型	是否有 company_id
users	?
memberships	?
tenant data	?
platform data	?
?? 本版本確保

? Platform-first
? Multi-tenant isolation
? 支援客服多公司 scope
? 支援功能分級（Basic/Pro 可調）
? 不破壞既有 attendance 設計