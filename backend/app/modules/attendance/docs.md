# Attendance 模組文件

## 概述

Attendance 模組負責處理考勤相關的業務邏輯，包括考勤記錄的建立、核准等功能。

## ⚠️ Tenant Isolation（P0，必須遵守）

本模組嚴格遵守 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則：

### 核心原則
1. **company_id 強制注入**：所有 API 的 company_id 必須由後端從 tenant context 注入
2. **不信任 request body**：禁止從 request body 或 querystring 接收 company_id
3. **跨公司隔離**：A 公司 context 無法存取 B 公司資料

### Phase 1 實作方式
- **Context 來源**：HTTP Header `X-Company-ID`
- **注入機制**：使用 FastAPI Depends + `get_current_company_id()`
- **Phase 2 升級**：將改為從 JWT token 解析 company_id

### 驗證方式
- 執行 `tests/test_tenant_isolation.py` 確保跨公司隔離
- 缺少 `X-Company-ID` header → 400 Bad Request
- 嘗試在 request body 傳入 company_id → 被忽略或拒絕（422）

---

## Phase 1 實作範圍

Phase 1 為最小可行實作，目標是建立事件驅動架構的基礎與 Tenant Isolation 機制。

### 功能

1. **Mock 建立考勤記錄**：產生假的考勤記錄 ID（用於測試）
2. **核准考勤記錄**：觸發考勤核准流程，發出 `attendance.approved` 事件

### API 端點

#### 1. POST /api/attendance/mock-create

建立假的考勤記錄（用於測試）。

**Headers（必填）：**
- `X-Company-ID`: 公司 ID（Tenant Context）

**回應範例：**
```json
{
  "attendance_record_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Tenant Isolation：**
- ✅ company_id 從 Header 注入
- ✅ 缺少 Header → 400 Bad Request

#### 2. POST /api/attendance/{attendance_record_id}/approve

核准指定的考勤記錄。

**路徑參數：**
- `attendance_record_id`: 考勤記錄 ID

**Headers（必填）：**
- `X-Company-ID`: 公司 ID（Tenant Context）
- `X-User-ID`: 使用者 ID（選填，若未提供 approved_by 則自動使用此值）

**請求 Body：**
```json
{
  "employee_id": "emp-456",
  "approved_by": "manager-789"
}
```

**欄位說明：**
- `employee_id` (必填): 員工 ID
- `approved_by` (選填): 核准人 ID，若未提供則使用 `X-User-ID`

**⚠️ 重要：company_id 不在 request body 中**
- company_id 由後端從 Header (`X-Company-ID`) 強制注入
- 即使 request body 嘗試傳入 company_id，也會被忽略或拒絕（422）
- 這是 Tenant Isolation (P0) 的核心要求

**回應範例：**
```json
{
  "ok": true,
  "payload": {
    "company_id": "company-123",
    "employee_id": "emp-456",
    "attendance_record_id": "550e8400-e29b-41d4-a716-446655440000",
    "approved_at": "2026-01-14T10:30:00.000000Z",
    "approved_by": "manager-789"
  }
}
```

**Tenant Isolation：**
- ✅ company_id 從 Header 注入，不信任 request body
- ✅ 缺少 Header → 400 Bad Request
- ✅ payload 中的 company_id 保證是後端注入的值

## 事件定義

### attendance.approved

當考勤記錄被核准時發出此事件。

**Payload 規格：**

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `company_id` | string | 是 | 公司 ID（多租戶隔離用） |
| `employee_id` | string | 是 | 員工 ID |
| `attendance_record_id` | string | 是 | 考勤記錄 ID |
| `approved_at` | string | 是 | 核准時間（ISO8601 格式，UTC） |
| `approved_by` | string | 否 | 核准人 ID（建議提供） |

**Payload 範例：**
```json
{
  "company_id": "company-123",
  "employee_id": "emp-456",
  "attendance_record_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_at": "2026-01-14T10:30:00.000000Z",
  "approved_by": "manager-789"
}
```

## 架構說明

### 檔案結構

```
backend/app/modules/attendance/
├── __init__.py       # 模組初始化
├── api.py            # API 路由定義
├── service.py        # 業務邏輯層
├── repo.py           # 資料存取層（Phase 1 空實作）
├── models.py         # 資料模型（Phase 1 空實作）
├── docs.md           # 模組文件（本檔案）
└── tests/            # 測試目錄
    ├── __init__.py
    ├── test_api.py              # API 功能測試
    └── test_tenant_isolation.py # Tenant Isolation 測試（P0）
```

### 設計原則

1. **Tenant Isolation (P0)**：所有 API 強制 company_id 注入，不信任 request body
2. **最小實作**：Phase 1 不包含資料庫操作，專注於事件驅動架構與 Tenant Isolation
3. **事件驅動**：使用 EventBus 發出事件，解耦模組間的依賴
4. **多租戶支援**：所有 payload 都包含 `company_id`，為未來的多租戶隔離做準備
5. **可測試性**：提供 mock 端點方便測試，並包含完整的 Tenant Isolation 測試

## 測試流程

### 前置準備

1. 啟動應用：`uvicorn app.main:app --reload`

### 使用 curl 測試

2. 建立假考勤記錄：
   ```bash
   curl -X POST http://localhost:8000/api/attendance/mock-create \
     -H "X-Company-ID: company-123"
   ```

3. 核准考勤記錄（使用上一步回傳的 ID）：
   ```bash
   curl -X POST http://localhost:8000/api/attendance/{attendance_record_id}/approve \
     -H "Content-Type: application/json" \
     -H "X-Company-ID: company-123" \
     -H "X-User-ID: user-001" \
     -d '{
       "employee_id": "emp-456",
       "approved_by": "manager-789"
     }'
   ```

4. 檢查 log 確認事件已發出

### 執行測試套件

```bash
# 執行所有測試
pytest backend/app/modules/attendance/tests/

# 只執行 Tenant Isolation 測試（P0）
pytest backend/app/modules/attendance/tests/test_tenant_isolation.py -v

# 執行 API 功能測試
pytest backend/app/modules/attendance/tests/test_api.py -v
```

### Tenant Isolation 驗證（P0）

**測試 1：缺少 X-Company-ID header**
```bash
curl -X POST http://localhost:8000/api/attendance/test-001/approve \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "emp-001"}'
```
預期：400 Bad Request

**測試 2：A 公司 context**
```bash
curl -X POST http://localhost:8000/api/attendance/test-002/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-A" \
  -d '{"employee_id": "emp-A-001"}'
```
預期：200 OK，payload.company_id = "company-A"

**測試 3：B 公司 context**
```bash
curl -X POST http://localhost:8000/api/attendance/test-003/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-B" \
  -d '{"employee_id": "emp-B-001"}'
```
預期：200 OK，payload.company_id = "company-B"

**測試 4：嘗試在 body 偽造 company_id（應被拒絕）**
```bash
curl -X POST http://localhost:8000/api/attendance/test-004/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-A" \
  -d '{"company_id": "company-B", "employee_id": "emp-001"}'
```
預期：422 Unprocessable Entity（schema 不接受 company_id）

## 未來擴展

Phase 1 之後的擴展方向：

### Phase 2: 資料庫層
- 實作 `models.py`（SQLAlchemy models）
- 實作 `repo.py`（資料庫 CRUD，強制 company_id 篩選）
- 所有查詢必須加上 `WHERE company_id = ?`
- 新增跨公司隔離測試（A 公司無法讀取/更新/刪除 B 公司資料）

### Phase 3: Auth 系統升級
- 將 `get_current_company_id()` 改為從 JWT token 解析
- 實作完整的 token 驗證
- 實作使用者權限檢查

### Phase 4: 功能擴展
- 實作真實的工時計算邏輯
- 加入更多考勤相關的事件（如：`attendance.created`, `attendance.rejected`）
- 實作事件訂閱者（如：工時計算模組、通知模組）

### Phase 5: 進階安全
- 考慮實作 PostgreSQL RLS（Row Level Security）作為最後防線
- 實作 audit log（記錄所有 CRUD 操作）

---

## 回歸測試清單（必須通過）

根據 SA_MODULE_SPEC v1.7 與 Cursor任務模板，本模組必須通過以下測試：

### P0: Tenant Isolation（必做）
- [x] 缺少 `X-Company-ID` header → 400 Bad Request
- [x] A 公司 context 核准考勤 → payload.company_id = A
- [x] B 公司 context 核准考勤 → payload.company_id = B
- [x] 嘗試在 request body 傳入 company_id → 被拒絕（422）或被忽略
- [ ] Phase 2: A 公司 context 無法讀取 B 公司資料（需資料庫）
- [ ] Phase 2: A 公司 context 無法更新 B 公司資料（需資料庫）
- [ ] Phase 2: A 公司 context 無法刪除 B 公司資料（需資料庫）

### P0: API 基本功能
- [x] mock-create 成功建立假考勤記錄
- [x] approve 成功核准考勤記錄
- [x] approve 回應包含正確的 payload 結構
- [x] payload 包含所有必填欄位（company_id, employee_id, attendance_record_id, approved_at）
- [x] approved_at 是 ISO8601 格式（UTC）

### P0: 事件驅動
- [x] approve 時發出 `attendance.approved` 事件
- [x] log 顯示「準備發出事件 attendance.approved」
- [x] log 顯示「發出事件: attendance.approved，訂閱者數量: N」
- [x] 訂閱者收到事件並正確處理

### P0: 錯誤處理
- [x] 缺少必填欄位 → 422 Unprocessable Entity
- [x] 缺少 X-Company-ID header → 400 Bad Request
- [x] 所有錯誤回應必須是 JSON 格式（不得回 HTML error page）

---

## 設定項

Phase 1 無額外設定項。

Phase 2 將加入：
- `ATTENDANCE_AUTO_APPROVE_THRESHOLD`: 自動核准門檻（秒）
- `ATTENDANCE_PENDING_EXPIRY_DAYS`: PENDING 狀態過期天數

---

## 本次修改記錄

### v1.1 - Tenant Isolation 實作（符合 SA_MODULE_SPEC v1.7）

**修改內容：**
1. 新增 `core/tenant_context.py`：提供 company_id 注入機制（Header 方式）
2. 新增 `repo.py` 和 `models.py`：符合模組結構規範（Phase 1 空實作）
3. 新增 `tests/` 目錄：包含 API 測試與 Tenant Isolation 測試
4. 修改 `api.py`：移除 request body 的 company_id，改用 Depends 注入
5. 修改 `service.py`：確保 company_id 由上層注入
6. 更新 `docs.md`：說明 Tenant Isolation 機制與測試方式

**影響的事件：**
- `attendance.approved`：payload 中的 company_id 現在保證由後端注入

**新增的規則：**
- 所有 API 必須提供 `X-Company-ID` header
- company_id 不得從 request body 接收
- Phase 2 將改為從 JWT token 解析 company_id

**驗收條件：**
- ✅ 通過 `test_tenant_isolation.py` 所有測試
- ✅ 通過 `test_api.py` 所有測試
- ✅ 符合 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則
