# Notifications 模組文件

## 概述

Notifications 模組負責接收系統事件並將通知記錄寫入資料庫，供後續查詢與稽核使用。

## ⚠️ Tenant Isolation（P0，必須遵守）

本模組嚴格遵守 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則：

### 核心原則
1. **company_id 強制注入**：所有 API 的 company_id 必須由後端從 tenant context 注入
2. **不信任 request body**：禁止從 request body 或 querystring 接收 company_id
3. **跨公司隔離**：A 公司 context 無法存取 B 公司資料
4. **事件處理 Fail-fast**：事件 payload 必須包含有效的 company_id，否則拒絕處理

### 實作方式
- **API Context 來源**：HTTP Header `X-Company-ID`
- **事件 Context 來源**：Event payload（已由發出者從 tenant_context 注入）
- **注入機制**：使用 FastAPI Depends + `get_current_company_id()`
- **Phase 3 升級**：將改為從 JWT token 解析 company_id

### 驗證方式
- 執行 `tests/test_tenant_isolation.py` 確保跨公司隔離
- 缺少 `X-Company-ID` header → 400 Bad Request
- A 公司無法看到 B 公司的通知記錄

---

## Phase 2 實作範圍

Phase 2 實作資料庫層與事件訂閱，支援單一租戶備份需求。

### 功能

1. **訂閱事件**：監聽 `attendance.approved` 事件
2. **寫入資料庫**：將事件記錄寫入 `notifications` 資料表
3. **查詢通知**：提供 API 查詢通知記錄（分頁）
4. **支援備份**：資料模型與查詢設計支援單一租戶全量抽取

---

## 資料模型

### notifications 資料表（Tenant Data）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | UUID | 主鍵（Python uuid4() 生成，避免還原時 ID 衝突） |
| `company_id` | VARCHAR(255) | 公司 ID（Tenant Isolation，有索引） |
| `event_type` | VARCHAR(255) | 事件類型（例如：attendance.approved） |
| `event_payload` | JSONB | 完整事件 payload（供稽核） |
| `created_at` | TIMESTAMP | 建立時間（UTC） |

**索引：**
- `idx_notifications_company_id` - 支援 Tenant Isolation 查詢
- `idx_notifications_company_created` - 支援單一租戶全量抽取（備份用）

**設計原則：**
1. 主鍵使用 UUID（Python 生成），避免單一租戶還原時 ID 衝突
2. 必須包含 `company_id`（Tenant Isolation P0）
3. 為 `company_id` 建立索引，支援高效匯出
4. `event_payload` 使用 JSONB，保留完整事件資料供稽核

---

## API 端點

### GET /api/notifications

查詢通知記錄（分頁）。

**Headers（必填）：**
- `X-Company-ID`: 公司 ID（Tenant Context）

**Query Parameters：**
- `limit`: 每頁筆數（1-100，預設 50）
- `offset`: 偏移量（預設 0）

**回應範例：**
```json
{
  "notifications": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "company_id": "company-123",
      "event_type": "attendance.approved",
      "event_payload": {
        "company_id": "company-123",
        "employee_id": "emp-456",
        "attendance_record_id": "record-789",
        "approved_at": "2026-01-14T10:30:00.000000Z",
        "approved_by": "manager-001"
      },
      "created_at": "2026-01-14T10:30:01.000000Z"
    }
  ],
  "pagination": {
    "total": 100,
    "limit": 50,
    "offset": 0
  }
}
```

**Tenant Isolation：**
- ✅ company_id 從 Header 注入，不信任 request body
- ✅ 缺少 Header → 400 Bad Request
- ✅ 只回傳該公司的通知記錄

---

## 事件訂閱

### attendance.approved

當考勤記錄被核准時，自動建立通知記錄。

**處理邏輯：**
1. 從 payload 取得 `company_id`（已由 attendance 模組從 tenant_context 注入）
2. **Fail-fast**：若 payload 缺少 `company_id` 或為空，拋出 ValueError
3. 使用 `payload.company_id` 作為 Source of Truth 寫入資料庫
4. 完整 payload 保存在 `event_payload` 欄位（供稽核）

**Fail-fast 驗證：**
```python
# 必須通過的檢查
if not company_id or not isinstance(company_id, str) or not company_id.strip():
    raise ValueError("payload 缺少有效的 company_id")
```

---

## 架構說明

### 檔案結構

```
backend/app/modules/notifications/
├── __init__.py              # 模組初始化
├── api.py                   # API 路由定義
├── service.py               # 業務邏輯層
├── repo.py                  # 資料存取層（含 Tenant Isolation）
├── models.py                # SQLAlchemy models
├── event_handlers.py        # 事件處理器（訂閱 attendance.approved）
├── docs.md                  # 模組文件（本檔案）
└── tests/                   # 測試目錄
    ├── __init__.py
    ├── test_api.py                  # API 測試
    ├── test_tenant_isolation.py     # Tenant Isolation 測試（P0）
    └── test_event_handlers.py       # 事件處理器測試
```

### 設計原則

1. **Tenant Isolation (P0)**：所有查詢強制 `WHERE company_id = ?`
2. **事件驅動**：使用 EventBus 訂閱事件，不直接呼叫其他模組
3. **Fail-fast**：事件處理器嚴格驗證 payload.company_id
4. **支援備份**：提供 `get_all_notifications_for_company()` 全量抽取
5. **UUID 主鍵**：避免單一租戶還原時 ID 衝突

---

## 測試流程

### 前置準備

1. 設定資料庫連線（`.env` 或環境變數）：
   ```
   DATABASE_URL=postgresql://user:pass@localhost:5432/attendance_v2
   ```

2. 啟動應用：
   ```bash
   uvicorn app.main:app --reload
   ```

### 執行測試套件

```bash
# 執行所有測試
pytest backend/app/modules/notifications/tests/ -v

# 只執行 Tenant Isolation 測試（P0）
pytest backend/app/modules/notifications/tests/test_tenant_isolation.py -v

# 只執行事件處理器測試
pytest backend/app/modules/notifications/tests/test_event_handlers.py -v
```

### 手動測試

#### 測試 1: 觸發事件並查詢通知

```bash
# 1. 核准考勤（會觸發 attendance.approved 事件）
curl -X POST http://localhost:8000/api/attendance/mock-create \
  -H "X-Company-ID: company-123"

# 記下回傳的 attendance_record_id

curl -X POST http://localhost:8000/api/attendance/{id}/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-123" \
  -d '{"employee_id": "emp-456", "approved_by": "manager-789"}'

# 2. 查詢通知記錄
curl -X GET http://localhost:8000/api/notifications \
  -H "X-Company-ID: company-123"
```

#### 測試 2: Tenant Isolation

```bash
# A 公司核准考勤
curl -X POST http://localhost:8000/api/attendance/{id}/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-A" \
  -d '{"employee_id": "emp-A-001"}'

# B 公司核准考勤
curl -X POST http://localhost:8000/api/attendance/{id}/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-B" \
  -d '{"employee_id": "emp-B-001"}'

# A 公司查詢（只看到 A 的通知）
curl -X GET http://localhost:8000/api/notifications \
  -H "X-Company-ID: company-A"

# B 公司查詢（只看到 B 的通知）
curl -X GET http://localhost:8000/api/notifications \
  -H "X-Company-ID: company-B"
```

#### 測試 3: 缺少 Header（應回 400）

```bash
curl -X GET http://localhost:8000/api/notifications
# 預期：400 Bad Request
```

---

## 單一租戶備份支援

### 全量抽取 API（Repository 層）

```python
# 取得指定公司的所有通知記錄（不分頁）
notifications = repo.get_all_notifications_for_company("company-123")

# 用途：
# 1. 單一租戶備份
# 2. 資料匯出
# 3. 租戶遷移
```

### 備份設計原則

1. **WHERE company_id = ?**：匯出時強制篩選
2. **UUID 主鍵**：避免還原時 ID 衝突
3. **索引支援**：`idx_notifications_company_created` 支援高效匯出
4. **完整 payload**：保留完整事件資料供稽核

### Phase 3 備份功能（未來）

Phase 2 只提供資料模型與查詢支援，Phase 3 將實作：
- `POST /api/backup/export` - 匯出單一租戶資料
- `POST /api/backup/restore` - 還原單一租戶資料
- Company Consistency Check
- FK Closure Check

---

## 回歸測試清單（必須通過）

根據 SA_MODULE_SPEC v1.7，本模組必須通過以下測試：

### P0: Tenant Isolation（必做）
- [x] 缺少 `X-Company-ID` header → 400 Bad Request
- [x] A 公司 context 查詢 → 只看到 A 公司通知
- [x] B 公司 context 查詢 → 只看到 B 公司通知
- [x] A 公司無法看到 B 公司的通知
- [x] 事件處理器寫入時使用正確的 company_id
- [x] 事件處理器 Fail-fast（payload 缺少 company_id → ValueError）
- [x] Repository 所有查詢強制 `WHERE company_id = ?`
- [x] 支援單一 company_id 全量抽取（備份用）

### P0: API 基本功能
- [x] GET /api/notifications 成功查詢
- [x] 分頁功能正確（limit, offset）
- [x] 回應包含正確的結構（notifications, pagination）
- [x] 空結果正確處理

### P0: 事件驅動
- [x] 訂閱 `attendance.approved` 事件
- [x] 事件觸發時正確寫入資料庫
- [x] 多公司事件正確隔離
- [x] Fail-fast 驗證正確運作

### P0: 錯誤處理
- [x] 缺少必填 Header → 400 Bad Request
- [x] 參數驗證失敗 → 422 Unprocessable Entity
- [x] 所有錯誤回應必須是 JSON 格式（不得回 HTML error page）

---

## 設定項

### 資料庫連線

在 `.env` 或環境變數中設定：

```
DATABASE_URL=postgresql://user:password@localhost:5432/attendance_v2
```

**預設值：**
```
postgresql://postgres:postgres@localhost:5432/attendance_v2
```

---

## 本次修改記錄

### v2.0 - Notifications 模組實作（Phase 2）

**新增內容：**
1. 新增 `core/database.py`：SQLAlchemy 資料庫連線管理
2. 新增 `notifications/models.py`：Notification 資料模型（UUID 主鍵）
3. 新增 `notifications/repo.py`：資料存取層（強制 Tenant Isolation）
4. 新增 `notifications/service.py`：業務邏輯層
5. 新增 `notifications/api.py`：GET /api/notifications
6. 新增 `notifications/event_handlers.py`：訂閱 attendance.approved（Fail-fast）
7. 新增 `notifications/tests/`：完整測試套件（API + Tenant Isolation + Event Handler）
8. 更新 `main.py`：註冊 notifications 路由與事件訂閱者
9. 更新 `config.py`：新增 database_url 設定

**影響的事件：**
- 訂閱 `attendance.approved`：將事件記錄寫入資料庫

**新增的規則：**
- 所有通知記錄必須包含 `company_id`
- 事件處理器必須 Fail-fast 驗證 payload.company_id
- Repository 所有查詢必須強制 `WHERE company_id = ?`
- 支援單一租戶全量抽取（備份用）

**驗收條件：**
- ✅ 通過 `test_tenant_isolation.py` 所有測試
- ✅ 通過 `test_api.py` 所有測試
- ✅ 通過 `test_event_handlers.py` 所有測試
- ✅ 符合 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則
- ✅ 支援單一租戶備份需求

---

## 未來擴展

Phase 2 完成後，可以考慮：

### Phase 3: 備份/還原 API
- 實作 `POST /api/backup/export` - 匯出單一租戶資料
- 實作 `POST /api/backup/restore` - 還原單一租戶資料
- Company Consistency Check
- FK Closure Check

### Phase 4: 通知功能擴展
- 實作實際通知發送（email/SMS/push）
- 標記已讀/未讀
- 通知偏好設定
- 通知模板管理

### Phase 5: 更多事件訂閱
- `attendance.created`
- `attendance.rejected`
- `leave.approved`
- `dispatch.assigned`

---

## 相關文件

- [SA_MODULE_SPEC v1.7](../../docs/SA_MODULE_SPECV1.7.md)
- [Cursor任務模板](../../docs/Cursor任務模板.txt)
- [Attendance 模組文件](../attendance/docs.md)
