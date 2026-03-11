# SA MODULE SPECIFICATION

# Attendance System

Version: 2.0 Status: Platform‑First Architecture + Location Policy

------------------------------------------------------------------------

# 1. Architecture Purpose

本版本定義 **Platform‑first Identity 架構** 的正式規範，並新增 **Location Policy / Geofence** 功能。

設計目標：

-   採用 Platform‑first Identity
-   保證 Tenant Isolation 100%
-   支援單一公司 Backup / Restore
-   支援 SaaS 功能分級 (Feature Flags)
-   支援客服跨公司 Scope
-   防止工程層面誤用
-   **新增：支援 GPS 定位與地理圍欄打卡限制**

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
notifications\
**allowed_locations (WP-11-13)**

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
3️⃣ Feature Gate\
**4️⃣ Location Policy (WP-11-13)**

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

# 11. Location Policy Rules (WP-11-13)

## 11.1 Location Policy 設計原則

**後端 Authoritative Enforcement**：

-   前端 precheck 僅為 UX-friendly
-   後端必須強制執行 location policy
-   不可信任前端傳來的 location_id

**Policy 邏輯**：

-   無 allowed locations → 允許任何地點打卡
-   有 allowed locations → 必須在任一地點範圍內

------------------------------------------------------------------------

## 11.2 Location Policy 驗證流程

打卡時必須執行：

1.  **GPS 獲取**（Mobile 裝置必須）
2.  **Policy Check**：
    -   取得公司啟用中的 allowed_locations
    -   計算與每個地點的距離（Haversine 公式）
    -   檢查是否在任一地點半徑內
3.  **結果處理**：
    -   ✅ 在範圍內 → 允許打卡，記錄 location_id
    -   ❌ 不在範圍內 → 拒絕打卡，返回 403 + 最近地點資訊

------------------------------------------------------------------------

## 11.3 Location Policy 資料模型

**allowed_locations 表**：

-   company_id (Tenant Isolation)
-   name (地點名稱)
-   latitude / longitude (GPS 座標)
-   radius_meters (允許半徑)
-   location_type (地點類型)
-   is_active (啟用狀態)

**attendance_punches 擴充**：

-   location_id (匹配的允許地點 ID)

------------------------------------------------------------------------

## 11.4 Location Policy API

**管理端 API** (`/api/v1/admin/allowed-locations`):

-   POST / - 建立允許地點
-   GET / - 查詢地點列表
-   GET /{id} - 查詢單筆地點
-   PUT /{id} - 更新地點
-   DELETE /{id} - 刪除地點

**打卡端整合**：

-   BREAK_OUT API 自動執行 location policy check
-   返回錯誤碼：`LOCATION_POLICY_VIOLATION`

------------------------------------------------------------------------

# 12. Backup / Restore

## Export

僅匯出 Tenant Data

WHERE company_id = ?

**包含**：

-   attendance_punches (含 location_id)
-   allowed_locations

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

# 13. Primary Key Design

Tenant Data 必須使用：

UUID

禁止依賴 auto-increment INT。

------------------------------------------------------------------------

# 14. Index Rules

所有 Tenant Data：

必須

index(company_id)

**Location Policy 索引**：

-   idx_allowed_locations_company (company_id)
-   idx_allowed_locations_active (company_id, is_active)
-   idx_punches_location (location_id)

------------------------------------------------------------------------

# 15. Tenant Isolation Tests

必須測試：

-   A company 無法讀取 B company
-   錯誤 company_id 寫入被拒
-   無 membership → 403
-   restore 不污染其他 company
-   **Location policy 跨租戶隔離**

------------------------------------------------------------------------

# 16. API Error Codes

401 → 未登入\
403 → 權限或 Feature Gate\
400 → Business Rule\
422 → Schema Error\
**403 + LOCATION_POLICY_VIOLATION → 不在允許打卡範圍內**

------------------------------------------------------------------------

# 17. Feature Flags (Company Entitlements)

每個 company 具有 feature flags。

feature_key 格式：

`<domain>`{=html}.`<feature>`{=html}

範例：

attendance.shift_templates\
attendance.split_shift\
attendance.shift_overrides\
**attendance.location_policy (WP-11-13)**

------------------------------------------------------------------------

## Feature Enforcement

若 feature 未啟用：

HTTP 403

response:

code = FEATURE_DISABLED

feature = "`<feature_key>`{=html}"

------------------------------------------------------------------------

## Validation Order

Scope → Tenant Isolation → Feature Gate → **Location Policy**

不得混合判斷。

------------------------------------------------------------------------

# 18. Future Scalability

架構支援：

-   一人多公司
-   SaaS billing
-   客服跨公司 scope
-   Feature tier control
-   排班 / Flex time / Split shift
-   **地理圍欄 / 位置追蹤 / 地圖 UI**

------------------------------------------------------------------------

# 19. Version Summary

  Data Type           company_id   GPS Support
  ------------------- ------------ -------------
  users               ❌           ❌
  memberships         ✅           ❌
  tenant data         ✅           ❌
  platform data       ❌           ❌
  allowed_locations   ✅           ✅
  attendance_punches  ✅           ✅ (optional)

------------------------------------------------------------------------

# 20. Version History

v1.7 --- Tenant baseline\
v1.8 --- Platform‑first identity\
v1.9 --- Scope / Feature / Backup architecture finalized\
**v2.0 --- Location Policy / Geofence (WP-11-13)**

------------------------------------------------------------------------

# 21. Location Policy 技術規格

## 21.1 GPS 距離計算

**演算法**: Haversine Formula

**精度**: 地球半徑 6371000 公尺

**實作**: `gps_utils.calculate_distance()`

**輸入**: (latitude, longitude) 兩組座標

**輸出**: 距離（公尺）

------------------------------------------------------------------------

## 21.2 前端 GPS 獲取

**裝置判斷**:

-   Mobile → 必須 GPS
-   PC → 不需要 GPS

**API**: `navigator.geolocation.getCurrentPosition()`

**選項**:

-   enableHighAccuracy: true
-   timeout: 10000ms
-   maximumAge: 0

**錯誤處理**:

-   NOT_SUPPORTED → 裝置不支援定位
-   PERMISSION_DENIED → 使用者拒絕權限
-   POSITION_UNAVAILABLE → 定位資訊無法取得
-   TIMEOUT → 定位請求逾時

------------------------------------------------------------------------

## 21.3 Location Policy Service

**責任**:

1.  讀取公司啟用中的 allowed locations
2.  檢查 GPS 是否命中任一允許地點
3.  回傳 allow/deny + matched location + violation reason

**方法**:

-   `get_active_allowed_locations(company_id)` → List[AllowedLocation]
-   `check_location_policy(company_id, lat, lng)` → PolicyCheckResult

**回傳結構**:

```python
@dataclass
class PolicyCheckResult:
    allowed: bool
    reason: str
    matched_location: Optional[Dict] = None
    nearest_location: Optional[Dict] = None
```

------------------------------------------------------------------------

# 22. 開發規範

## 22.1 新增 Location Policy 時

必須：

1.  ✅ 在 allowed_locations 表新增記錄
2.  ✅ 設定 company_id (Tenant Isolation)
3.  ✅ 設定 latitude / longitude / radius_meters
4.  ✅ 設定 is_active = true

------------------------------------------------------------------------

## 22.2 打卡時

必須：

1.  ✅ Mobile 裝置獲取 GPS
2.  ✅ 呼叫 location_policy_service.check_location_policy()
3.  ✅ 若 allowed=False → 返回 403 + LOCATION_POLICY_VIOLATION
4.  ✅ 若 allowed=True → 記錄 location_id 到 attendance_punches

------------------------------------------------------------------------

## 22.3 測試要求

必須測試：

-   ✅ 無 allowed locations → 允許任何地點
-   ✅ 在範圍內 → 允許打卡
-   ✅ 不在範圍內 → 拒絕打卡
-   ✅ 多地點 → 命中任一即可
-   ✅ Tenant isolation → A 公司無法讀取 B 公司地點

------------------------------------------------------------------------

# 23. Migration 記錄

**Migration 008** (WP-11-13):

-   建立 allowed_locations 表
-   擴充 attendance_punches.location_id
-   建立索引與外鍵約束
-   建立 CHECK 約束（半徑 > 0、經緯度範圍）

------------------------------------------------------------------------

# 24. 相關文件

-   WP-11-13_LOCATION_POLICY_DESIGN.md
-   ATTENDANCE_LOCATION_MODULE_SPEC.md
-   ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md (本次新增)
-   API_DOCUMENTATION_v2.0.md (本次新增)

------------------------------------------------------------------------

**文件版本**: v2.0\
**最後更新**: 2026-03-09\
**更新原因**: 新增 WP-11-13 Location Policy / Geofence 功能
