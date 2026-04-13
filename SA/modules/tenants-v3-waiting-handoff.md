# Tenants / Companies v3 待開發交接文件

**建立日期**：2026-04-12  
**狀態**：等待開發  
**主題**：公司主資料補欄位、company detail endpoint、tax_id lookup、member_summary  
**對應 SDD**：`/opt/attendance-system/SA/modules/tenants.md`

---

## 1. 本文件用途

本文件用來給後續開發接手人快速理解：

- 這次需求已經定稿到哪裡
- 哪些要做、哪些先不要做
- 目前盤點後有沒有衝突
- 開發前要注意哪些相依關係

---

## 2. 目前結論

### 2.1 是否有阻塞衝突
**目前沒有看到硬阻塞衝突。**

也就是說：
- 這次規格本身可以獨立開發
- 不需要先推翻現有 `tenants` / `members` / `companies` 架構
- 不會直接和目前 `GET /api/admin/companies/{company_id}` 衝突，因為已決定改走新增 detail endpoint

### 2.2 有哪些非阻塞注意事項
以下不是阻塞，但開發時要注意：

1. **不要破壞既有 `CompanyResponse`**
   - 已定稿：新增 `GET /api/admin/companies/{company_id}/detail`
   - 不直接改壞原本 `GET /api/admin/companies/{company_id}` 的 response shape

2. **`company_admin` / `hr_manager` 更新公司資料的權限要與既有 scope 一致**
   - 現有 `api.py` 的 `_assert_admin_company_access()` 已符合方向
   - 後續新增 detail endpoint / update 權限時，要沿用同一套 scope 規則

3. **`lookup-by-tax-id` 只給 `super_admin`**
   - 外部工商查詢權限不能跟公司自己維護資料權限混在一起

4. **Phase 1 不做多打卡地點模型**
   - 已定稿：`Tenant` 主表先不放 `attendance_address` / lat / lng
   - 未來多據點另做 `company_locations`（或等價模型）

5. **Phase 1 不做管理者名單卡片 UI**
   - 已改成 `member_summary`
   - 避免 detail 頁隨客戶管理者數量成長而變長、變難用

---

## 3. 本次正式要做的範圍

### 3.1 Backend
- `Tenant` 新增公司主資料欄位
- `CreateCompanyRequest` / `UpdateCompanyRequest` / `CompanyResponse` 補欄位
- 新增 `GET /api/admin/companies/{company_id}/detail`
- 新增 `POST /api/admin/companies/lookup-by-tax-id`
- 新增 `member_summary` 回傳

### 3.2 Frontend
- `AdminOnboardingView.vue` 補公司主資料欄位
- onboarding 新增 `tax_id` 查詢按鈕與候選資料帶入
- `CompanyDetailPanel.vue` 顯示新公司欄位
- `CompanyDetailPanel.vue` 只顯示 `member_summary`，不顯示管理者名單卡片

### 3.3 DB
- `tenants` table 補公司主資料欄位
- 本階段不建立多據點 location table

---

## 4. 本次明確不做的範圍

以下明確留到下一階段：

- `company_locations`
- 多據點打卡地點管理
- geofence / GPS 半徑
- 地圖選點
- `attendance_address` / `attendance_latitude` / `attendance_longitude` 寫入 `Tenant`
- detail 頁管理者名單卡片 UI
- members 整體重構

---

## 5. 最終規格摘要

### 5.1 Company detail API
新增：
- `GET /api/admin/companies/{company_id}/detail`

用途：
- 後台公司 detail / 客服快速查詢

權限：
- `super_admin`
- `company_admin`
- `hr_manager`

限制：
- `company_admin` / `hr_manager` 只能看自己公司

### 5.2 detail response
Phase 1 改成回傳：
- `company`
- `member_summary`

`member_summary` 定義：
- `admin_count`
- `active_admin_count`
- `has_company_admin`
- `has_hr_manager`

### 5.3 tax_id lookup
新增：
- `POST /api/admin/companies/lookup-by-tax-id`

權限：
- 只開放 `super_admin`

查詢帶入欄位：
- `name`
- `owner_name`
- `registered_address`

### 5.4 公司資料更新權限
可更新自己公司資料者：
- `super_admin`
- `company_admin`
- `hr_manager`

---

## 6. Tenant 主表 Phase 1 欄位定稿

### 6.1 要新增
- `display_name`
- `owner_name`
- `registered_address`
- `contact_address`
- `contact_phone`
- `contact_email`
- `logo_url`

### 6.2 不新增
- `attendance_address`
- `attendance_latitude`
- `attendance_longitude`
- `attendance_geo_source`
- `attendance_geo_updated_at`

原因：
- 未來已確認需要多據點
- 不應再把單一打卡地址硬塞進 company 主表

---

## 7. 盤點後的衝突與相依說明

### 7.1 與既有 `GET /api/admin/companies/{company_id}`
**無直接衝突。**

原因：
- 已定稿新增 `/detail`，不直接改舊 response
- 舊前端 / 舊測試可以維持原狀

### 7.2 與 members API
**無直接衝突。**

原因：
- `member_summary` 只是從既有 membership / user 資料彙整出摘要
- 不另建第二份成員主資料
- `CompanyMembersPanel.vue` 仍維持完整 members 管理用途

### 7.3 與 auth model
**無直接衝突。**

原因：
- `Membership.role_id` 已存在
- `company_admin` / `hr_manager` 可直接用來做 `member_summary` 統計

### 7.4 與多據點 GPS 規劃
**有未來相依，但非本階段阻塞。**

結論：
- 本階段先不要碰 location model
- 下一階段再獨立實作

### 7.5 與外部資料來源查詢
**有相依，但可用 provider 保留抽換。**

結論：
- 本階段只定義 lookup endpoint 與 schema
- 實際 provider 可晚點接
- 若另一個功能尚未好，可先做假的 provider interface 或 stub response

---

## 8. 後續開發順序建議

### Step 1
DB migration + `Tenant` model

### Step 2
schemas / repo / service

### Step 3
`GET /api/admin/companies/{company_id}/detail`

### Step 4
`POST /api/admin/companies/lookup-by-tax-id`

### Step 5
frontend onboarding 補欄位 + lookup

### Step 6
frontend company detail 顯示新欄位 + `member_summary`

---

## 9. 若目前需要等待其他功能，建議暫停點

若現在因另一個功能尚未完成而要等待，建議停在以下狀態：

- **規格已定稿**
- **SDD 已更新**
- **不要先動 code**
- 待另一功能完成後，再依本文件順序開始實作

這樣可以避免：
- 半套 migration
- 半套 API
- frontend 先改但 backend 還沒好
- 權限與 response 形狀來回變更

---

## 10. 對應檔案清單

### 已完成文件
- `/opt/attendance-system/SA/modules/tenants.md`
- `/opt/attendance-system/SA/modules/tenants-v3-waiting-handoff.md`（本文件）

### 未來會改到的主要程式檔案
- `/opt/attendance-system/backend/app/modules/tenants/models.py`
- `/opt/attendance-system/backend/app/modules/tenants/repo.py`
- `/opt/attendance-system/backend/app/modules/tenants/service.py`
- `/opt/attendance-system/backend/app/modules/tenants/api.py`
- `/opt/attendance-system/backend/app/modules/tenants/schemas_companies.py`
- `/opt/attendance-system/backend/app/modules/tenants/schemas_onboarding.py`
- `/opt/attendance-system/frontend/src/views/admin/AdminOnboardingView.vue`
- `/opt/attendance-system/frontend/src/components/admin/CompanyDetailPanel.vue`

---
## 11. 一句話交接結論
本次 company / tenants 規格已定稿，**目前沒有阻塞性衝突**；可以等待另一功能完成後，再依本文件順序開發。Phase 1 以公司主資料治理、detail endpoint、tax_id lookup、member_summary 為主；多據點打卡位置留待下一階段獨立模型處理。
