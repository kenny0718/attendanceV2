# WP-11-13 Step 2 實作報告

**票號**: WP-11-13  
**階段**: Step 2 - Backend Foundation  
**日期**: 2026-03-08  
**狀態**: 🔄 進行中（核心完成，待手動整合）

---

## 執行摘要

WP-11-13 Step 2 的核心後端基礎已完成，包括資料模型、Policy Service、管理端 API 和測試。由於檔案操作工具的限制，部分修改需要手動套用。

**關鍵成就**:
- ✅ 建立完整的 Implementation Plan
- ✅ 建立 AllowedLocation 資料模型與 migration
- ✅ 實作 Policy Service（後端 authoritative enforcement）
- ✅ 建立管理端 CRUD API
- ✅ 建立測試框架
- ⏳ BREAK_OUT enforcement 待手動套用

---

## 已完成項目

### 1. 文件

✅ **Implementation Plan**
- 檔案: `docs/WP-11-13_IMPLEMENTATION_PLAN.md`
- 內容: 完整的實作計劃，包含步驟拆分、技術設計、風險評估

✅ **BREAK_OUT Enforcement Patch**
- 檔案: `docs/WP-11-13_BREAK_OUT_ENFORCEMENT_PATCH.md`
- 內容: 詳細的修改指引，說明如何在 api.py 和 repo.py 中加入 location policy enforcement

---

### 2. 資料模型

✅ **Migration**
- 檔案: `backend/alembic/versions/008_wp_11_13_create_allowed_locations.py`
- 內容:
  - 建立 `allowed_locations` 表
  - 擴充 `attendance_punches` 表（新增 `location_id` 欄位）
  - 建立索引與約束
  - 支援 upgrade/downgrade

✅ **AllowedLocation Model**
- 檔案: `backend/app/modules/attendance/models.py`
- 內容:
  - 完整的 SQLAlchemy model
  - Tenant isolation (company_id)
  - 支援多筆地點
  - 使用 Numeric(10, 7) 儲存經緯度
  - 完整的約束與索引

✅ **Schemas**
- 檔案: `backend/app/modules/attendance/schemas.py`
- 內容:
  - `AllowedLocationCreate` - 建立請求
  - `AllowedLocationUpdate` - 更新請求
  - `AllowedLocationResponse` - 回應
  - `AllowedLocationListResponse` - 列表回應
  - `LocationPolicyCheckResult` - Policy 檢查結果
  - `LocationPolicyViolationError` - 錯誤回應

---

### 3. Policy Service

✅ **AttendanceLocationPolicyService**
- 檔案: `backend/app/modules/attendance/location_policy_service.py`
- 功能:
  - `get_active_allowed_locations()` - 取得啟用中的地點
  - `check_location_policy()` - 檢查 location policy
- 邏輯:
  - 無 allowed locations → 允許任何地點
  - 有 allowed locations → 必須在任一地點範圍內
  - 回傳 matched location 或 nearest location
- 重用: 使用既有的 `gps_utils.calculate_distance()` 計算距離

---

### 4. 管理端 API

✅ **Admin Location API**
- 檔案: `backend/app/modules/attendance/admin_location_api.py`
- Endpoints:
  - `POST /api/v1/admin/allowed-locations` - 建立地點
  - `GET /api/v1/admin/allowed-locations` - 查詢列表（支援過濾、分頁）
  - `GET /api/v1/admin/allowed-locations/{id}` - 查詢單筆
  - `PUT /api/v1/admin/allowed-locations/{id}` - 更新地點
  - `DELETE /api/v1/admin/allowed-locations/{id}` - 刪除地點
- 特性:
  - Tenant isolation
  - 基本參數驗證
  - 審計欄位（created_by, updated_by）

---

### 5. 測試

✅ **Location Policy Tests**
- 檔案: `backend/app/modules/attendance/tests/test_location_policy.py`
- 測試案例:
  - 無 allowed locations 時允許任何地點
  - 在範圍內允許打卡
  - 超出範圍拒絕打卡
  - 多個地點，命中其中一個即可
  - 停用的地點不被考慮
  - Tenant isolation
  - Haversine 距離計算正確性

---

## 待完成項目

### 1. BREAK_OUT Enforcement（待手動套用）

⏳ **修改 api.py**
- 檔案: `backend/app/modules/attendance/api.py`
- 修改位置: `@router_v1.post("/break-out")` endpoint
- 修改內容: 參考 `docs/WP-11-13_BREAK_OUT_ENFORCEMENT_PATCH.md`
- 步驟:
  1. 更新 docstring
  2. 在 "Get open session" 之後加入 policy check
  3. 修改 `repo.create_punch()` 呼叫，加入 `location_id` 參數

⏳ **修改 repo.py**
- 檔案: `backend/app/modules/attendance/repo.py`
- 修改位置: `create_punch()` method
- 修改內容:
  1. 在參數中加入 `location_id: Optional[UUID] = None`
  2. 在建立 AttendancePunch 時加入 `location_id=location_id`

---

### 2. Migration 執行

⏳ **執行 migration**
```bash
cd /opt/attendance-system/backend
alembic upgrade head
```

---

### 3. 測試執行

⏳ **執行測試**
```bash
cd /opt/attendance-system/backend
pytest app/modules/attendance/tests/test_location_policy.py -v
```

---

### 4. 整合測試

⏳ **Manual QA**
- 測試 Admin CRUD API
- 測試 BREAK_OUT enforcement
- 測試 tenant isolation
- 測試 regression（不破壞既有流程）

---

## 設計決策

### 1. 後端 Authoritative Enforcement

**原則**: 前端 policy 檢查只能作為 UX-friendly precheck，真正決定是否允許打卡的權威判斷，必須永遠在後端執行。

**實作**:
- 後端獨立驗證，不依賴前端
- 即使前端沒檢查到，後端仍會拒絕不合法打卡
- Policy Service 是唯一的 policy 評估來源

---

### 2. 向後相容

**策略**:
- 無 allowed locations → 允許任何地點（不破壞既有行為）
- `location_id` 欄位為 nullable（不影響既有資料）
- 只在有 location 時才檢查 policy（不強制要求 GPS）

---

### 3. 資料模型設計

**AllowedLocation**:
- 使用 `Numeric(10, 7)` 儲存經緯度（精度約 1.1 公分）
- 支援多筆地點（不做死成只能一筆）
- `location_type` 預留未來擴充
- `is_active` 支援軟啟用/停用
- v1 使用 hard delete（簡化實作）

**attendance_punches.location_id**:
- 記錄命中的 allowed location（不是使用者實際 GPS 點）
- `ON DELETE SET NULL`（保守策略）
- 保留既有 `location_lat` / `location_lng` 欄位

---

### 4. Policy 邏輯

**規則**:
1. 取得公司的所有啟用中的 allowed locations
2. 如果沒有任何 allowed locations → 允許任何地點打卡
3. 如果有 allowed locations：
   - 計算與每個地點的距離
   - 檢查是否有任一地點在半徑內
   - 如果有 → 允許打卡，返回匹配的地點
   - 如果沒有 → 拒絕打卡，返回最近的地點

---

## 技術亮點

### 1. 重用既有基礎設施

- 重用 `gps_utils.calculate_distance()` 計算距離
- 重用 tenant context (`get_current_company_id`, `get_current_user_id`)
- 重用 database session management

---

### 2. 清晰的責任分離

- **Policy Service**: 負責 policy 評估邏輯
- **Admin API**: 負責 CRUD 操作
- **Punch API**: 負責打卡流程與 enforcement
- **Repository**: 負責資料存取

---

### 3. 完整的錯誤處理

- 明確的錯誤碼 (`LOCATION_POLICY_VIOLATION`)
- 友善的錯誤訊息（包含最近地點與距離）
- 結構化的錯誤回應

---

## 風險與緩解

### 1. Migration 風險

**風險**: 新增表與欄位可能失敗

**緩解**:
- Migration 使用標準 Alembic 格式
- `location_id` 欄位為 nullable
- FK constraint 使用 `ON DELETE SET NULL`
- 支援 downgrade

---

### 2. 檔案操作限制

**風險**: 工具無法可靠地修改現有檔案

**緩解**:
- 建立詳細的 patch 文件
- 提供清楚的修改指引
- 標記待手動套用的項目

---

### 3. Tenant Isolation

**風險**: Allowed locations 可能跨租戶洩漏

**緩解**:
- 所有查詢必須包含 `company_id` filter
- API 層驗證 tenant context
- 測試覆蓋 tenant isolation

---

## 下一步行動

### 立即行動

1. **手動套用 BREAK_OUT enforcement patch**
   - 參考: `docs/WP-11-13_BREAK_OUT_ENFORCEMENT_PATCH.md`
   - 修改: `api.py` 和 `repo.py`

2. **執行 migration**
   ```bash
   cd /opt/attendance-system/backend
   alembic upgrade head
   ```

3. **執行測試**
   ```bash
   pytest app/modules/attendance/tests/test_location_policy.py -v
   ```

4. **Manual QA**
   - 測試 Admin CRUD API
   - 測試 BREAK_OUT enforcement
   - 測試 regression

---

### 後續步驟（Step 3）

1. **前端整合**
   - 前端 policy precheck（UX-friendly）
   - 管理端 UI（地點列表、CRUD）
   - 錯誤訊息顯示

2. **擴充到其他流程**
   - BREAK_IN enforcement
   - punch-in enforcement
   - punch-out enforcement

---

## 相關文件

### 實作文件
- `docs/WP-11-13_IMPLEMENTATION_PLAN.md` - 實作計劃
- `docs/WP-11-13_BREAK_OUT_ENFORCEMENT_PATCH.md` - Patch 指引
- `docs/WP-11-13_LOCATION_POLICY_DESIGN.md` - 設計文件

### 程式碼
- `backend/alembic/versions/008_wp_11_13_create_allowed_locations.py`
- `backend/app/modules/attendance/models.py`
- `backend/app/modules/attendance/schemas.py`
- `backend/app/modules/attendance/location_policy_service.py`
- `backend/app/modules/attendance/admin_location_api.py`
- `backend/app/modules/attendance/tests/test_location_policy.py`

---

## 檔案清單

### 新增檔案

```
docs/
  WP-11-13_IMPLEMENTATION_PLAN.md
  WP-11-13_BREAK_OUT_ENFORCEMENT_PATCH.md
  WP-11-13_STEP2_IMPLEMENTATION_REPORT.md (本文件)

backend/
  alembic/versions/
    008_wp_11_13_create_allowed_locations.py
  app/modules/attendance/
    location_policy_service.py
    admin_location_api.py
    tests/
      test_location_policy.py
```

### 修改檔案

```
backend/app/modules/attendance/
  models.py (新增 AllowedLocation model)
  schemas.py (新增 location policy schemas)
  api.py (待手動修改 - BREAK_OUT enforcement)
  repo.py (待手動修改 - location_id 參數)
```

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: 核心完成，待手動整合  
**下一步**: 手動套用 patch → 執行 migration → 測試 → QA
