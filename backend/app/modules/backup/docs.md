# Backup 模組文件

## 概述

Backup 模組提供單一租戶的資料匯出與還原功能，支援以 company_id 為單位進行備份與還原，確保租戶間完全隔離。

## ⚠️ Tenant Isolation（P0，必須遵守）

本模組嚴格遵守 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則：

### 核心原則
1. **匯出隔離**：只匯出指定 company_id 的資料，不可匯出其他公司
2. **還原覆寫**：還原時強制覆寫所有 company_id = target_company_id
3. **不信任備份檔**：不信任備份檔內的 company_id，以 tenant_context 為準
4. **Fail-fast 驗證**：備份檔混入其他公司資料時，立即拒絕還原

### Company Consistency Check（P0）
- 檢查備份檔內所有 company_id 是否一致
- 檢查是否與 metadata.company_id 一致
- 若不一致 → fail fast（400 Bad Request）

### FK Closure Check（P0）
- 檢查所有外鍵引用是否在備份集內
- Phase 3: notifications 表無外鍵，為 stub 實作
- Phase 4+: 當有外鍵時必須完整檢查

---

## Phase 5 實作範圍

Phase 5 實作單一租戶備份/還原的核心功能。

### 功能

1. **匯出（Export）**：將指定公司的所有資料匯出為 JSON
2. **還原（Restore）**：將備份資料還原到指定公司
3. **驗證（Validation）**：Company Consistency Check + FK Closure Check
4. **Transaction 管理**：還原失敗時完整 rollback

### 支援的資料表

Phase 5 支援：
- `notifications`（Tenant Data）
- `attendance_records`（Tenant Data）

Phase 6+ 將支援：
- `employees`
- `locations`
- 其他 Tenant Data 表

---

## API 端點

### POST /api/backup/export

匯出公司資料（單一租戶備份）。

**Headers（必填）：**
- `X-Company-ID`: 要匯出的公司 ID

**回應範例：**
```json
{
  "metadata": {
    "company_id": "company-123",
    "exported_at": "2026-01-14T12:00:00.000000Z",
    "version": "1.0",
    "tables": ["notifications", "attendance_records"]
  },
  "data": {
    "notifications": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "company_id": "company-123",
        "event_type": "attendance.approved",
        "event_payload": {...},
        "created_at": "2026-01-14T10:00:00.000000Z"
      }
    ],
    "attendance_records": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "company_id": "company-123",
        "employee_id": "emp-001",
        "approved_by": "manager-001",
        "approved_at": "2026-01-14T11:00:00.000000Z",
        "created_at": "2026-01-14T10:00:00.000000Z"
      }
    ]
  }
}
```

**Tenant Isolation：**
- ✅ company_id 從 Header 注入
- ✅ 只匯出該公司的資料
- ✅ 所有查詢強制 `WHERE company_id = ?`

**資料格式：**
- JSON 格式（不壓縮）
- UUID 轉為字串
- datetime 轉為 ISO8601 字串（UTC）

---

### POST /api/backup/restore

還原公司資料（單一租戶還原）。

**Headers（必填）：**
- `X-Company-ID`: 要還原到的公司 ID（target_company_id）

**Query Parameters：**
- `clear_existing`: boolean（是否清空現有資料，預設 false）
  - `false`（預設）：Merge 模式，保留現有資料
  - `true`：Replace 模式，清空後還原

**Request Body：**
```json
{
  "metadata": {
    "company_id": "company-source",
    "exported_at": "2026-01-14T12:00:00Z",
    "version": "1.0"
  },
  "data": {
    "notifications": [...],
    "attendance_records": [...]
  }
}
```

**回應範例：**
```json
{
  "ok": true,
  "target_company_id": "company-123",
  "summary": {
    "notifications": 100,
    "attendance_records": 50
  }
}
```

**Tenant Isolation（P0）：**
- ✅ target_company_id 從 Header 注入
- ✅ 所有資料的 company_id 強制覆寫為 target_company_id
- ✅ 不信任備份檔內的 company_id

**驗證流程：**
1. 格式驗證（metadata, data 必要欄位）
2. Company Consistency Check（P0）
3. FK Closure Check（P0）
4. 還原資料（使用 transaction）

**Transaction 管理：**
- 使用 transaction 確保原子性
- 失敗時完整 rollback
- 不會污染資料庫

---

## 還原策略

### Merge 模式（預設，clear_existing=false）

**行為：**
- 保留現有資料
- 新增備份檔的資料
- UUID 相同時可能衝突（但 UUID 應該不會衝突）

**適用場景：**
- 增量還原
- 安全還原（不會遺失資料）

**範例：**
```bash
curl -X POST http://localhost:8000/api/backup/restore \
  -H "X-Company-ID: company-123" \
  -H "Content-Type: application/json" \
  -d @backup.json
```

### Replace 模式（clear_existing=true）

**行為：**
- 清空現有資料（只清空該公司）
- 還原備份檔的資料
- 完全取代

**適用場景：**
- 完整還原
- 災難恢復

**範例：**
```bash
curl -X POST "http://localhost:8000/api/backup/restore?clear_existing=true" \
  -H "X-Company-ID: company-123" \
  -H "Content-Type: application/json" \
  -d @backup.json
```

---

## 驗證機制

### Company Consistency Check（P0）

**檢查項目：**
1. 備份檔內所有 Tenant Data 的 company_id 必須相同
2. 必須與 metadata.company_id 一致
3. 不可混入其他公司資料

**失敗情況：**
```json
{
  "detail": "驗證失敗: 備份檔包含多個 company_id（違反 Tenant Isolation）: {'company-A', 'company-B'}"
}
```

**狀態碼：** 400 Bad Request

### FK Closure Check（P0）

**檢查項目：**
- 所有被引用的資料必須存在於備份集內

**Phase 5 實作：**
- notifications 與 attendance_records 表無外鍵，直接通過（stub）

**Phase 6+ 範例：**
```python
# 若 employees.manager_id 引用 employees.id
# 必須檢查所有 manager_id 都在 employees 表內
if employee.get("manager_id") and employee["manager_id"] not in employee_ids_in_backup:
    raise ValueError("FK Closure 失敗: 缺少 manager 資料")
```

---

## 架構說明

### 檔案結構

```
backend/app/modules/backup/
├── __init__.py          # 模組初始化
├── api.py               # API 路由（export, restore）
├── service.py           # 業務邏輯層
├── exporter.py          # 匯出器
├── importer.py          # 匯入器（還原器）
├── validator.py         # 驗證器（Consistency Check, FK Closure Check）
├── docs.md              # 模組文件（本檔案）
└── tests/               # 測試目錄
    ├── __init__.py
    ├── test_api.py                  # API 測試
    ├── test_tenant_isolation.py     # Tenant Isolation 測試（P0）
    └── test_validator.py            # 驗證器測試
```

### 設計原則

1. **Tenant Isolation (P0)**：所有操作強制 company_id 隔離
2. **UUID 主鍵**：保留原始 UUID，避免還原時 ID 衝突
3. **Transaction 管理**：還原失敗時完整 rollback
4. **Fail-fast 驗證**：備份檔有問題時立即拒絕
5. **JSON 格式**：不壓縮，方便檢視與編輯

---

## 測試流程

### 前置準備

1. 啟動應用：`uvicorn app.main:app --reload`
2. 準備測試資料

### 手動測試

#### 測試 1: 匯出資料

```bash
# 建立測試資料
curl -X POST http://localhost:8000/api/attendance/mock-create \
  -H "X-Company-ID: company-test"

curl -X POST http://localhost:8000/api/attendance/{id}/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-test" \
  -d '{"employee_id": "emp-001"}'

# 匯出
curl -X POST http://localhost:8000/api/backup/export \
  -H "X-Company-ID: company-test" \
  > backup.json
```

#### 測試 2: 還原資料（Merge 模式）

```bash
curl -X POST http://localhost:8000/api/backup/restore \
  -H "X-Company-ID: company-target" \
  -H "Content-Type: application/json" \
  -d @backup.json
```

#### 測試 3: 還原資料（Replace 模式）

```bash
curl -X POST "http://localhost:8000/api/backup/restore?clear_existing=true" \
  -H "X-Company-ID: company-target" \
  -H "Content-Type: application/json" \
  -d @backup.json
```

#### 測試 4: Tenant Isolation

```bash
# A 公司匯出
curl -X POST http://localhost:8000/api/backup/export \
  -H "X-Company-ID: company-A" \
  > backup-a.json

# B 公司還原（company_id 會被覆寫為 B）
curl -X POST http://localhost:8000/api/backup/restore \
  -H "X-Company-ID: company-B" \
  -H "Content-Type: application/json" \
  -d @backup-a.json

# 驗證：B 公司有資料，A 公司不受影響
curl -X GET http://localhost:8000/api/notifications \
  -H "X-Company-ID: company-B"
```

### 執行測試套件

```bash
# 執行所有測試
pytest backend/app/modules/backup/tests/ -v

# 只執行 Tenant Isolation 測試（P0）
pytest backend/app/modules/backup/tests/test_tenant_isolation.py -v

# 只執行驗證器測試
pytest backend/app/modules/backup/tests/test_validator.py -v
```

---

## 回歸測試清單（必須通過）

根據 SA_MODULE_SPEC v1.7，本模組必須通過以下測試：

### P0: Tenant Isolation（必做）
- [x] 缺少 `X-Company-ID` header → 400 Bad Request
- [x] 匯出時只匯出指定公司資料
- [x] 還原時覆寫 company_id = target_company_id
- [x] 還原時保留 UUID（避免衝突）
- [x] 備份檔混入其他 company_id → fail fast（400）
- [x] A 公司匯出 → B 公司還原 → 資料屬於 B

### P0: Company Consistency Check（必做）
- [x] 備份檔 company_id 一致 → 通過
- [x] 備份檔混入多個 company_id → 失敗
- [x] 備份檔與 metadata 不一致 → 失敗

### P0: FK Closure Check（必做）
- [x] Phase 5: notifications 與 attendance_records 無外鍵，直接通過（stub）
- [ ] Phase 6+: 有外鍵時必須檢查

### 還原策略
- [x] clear_existing=false（預設）：Merge 模式
- [x] clear_existing=true：Replace 模式
- [x] Transaction 失敗時完整 rollback

### API 基本功能
- [x] POST /api/backup/export 成功匯出
- [x] POST /api/backup/restore 成功還原
- [x] 匯出 → 還原 → 資料正確（roundtrip）
- [x] 所有錯誤回應必須是 JSON 格式

---

## 限制與假設

### Phase 5 限制

1. **只支援 notifications 與 attendance_records 表**：目前只有這兩張 Tenant Data 表
2. **不支援 ZIP 壓縮**：直接回傳 JSON
3. **不支援增量備份**：只支援全量備份
4. **不支援排程備份**：只提供 API，不做自動排程
5. **不支援備份版本管理**：不記錄備份歷史

### 未來擴展（Phase 6+）

- 支援更多 Tenant Data 表（employees, locations 等）
- 支援 ZIP 壓縮（大檔案）
- 支援增量備份
- 支援排程備份
- 支援備份版本管理
- 實作 `POST /api/backup/validate`（還原前預覽）

---

## 錯誤處理

| 錯誤情況 | 狀態碼 | 說明 |
|---------|--------|------|
| 缺少 X-Company-ID | 400 | Bad Request |
| 備份檔格式錯誤 | 400 | Bad Request |
| Company Consistency 失敗 | 400 | Bad Request（混入其他公司） |
| FK Closure 失敗 | 400 | Bad Request（缺少引用資料） |
| 資料庫錯誤 | 500 | Internal Server Error |

**所有錯誤回應必須是 JSON 格式。**

---

## 設計決策

### 1. 還原策略（選項 C）

**決策：** 提供 `clear_existing` 參數選擇
- `false`（預設）：Merge 模式，保留現有資料
- `true`：Replace 模式，清空後還原

**理由：**
- 提供彈性，適應不同場景
- 預設 Merge 較安全，不會遺失資料
- Replace 適合災難恢復

### 2. UUID 主鍵保留

**決策：** 還原時保留原始 UUID

**理由：**
- 避免 ID 衝突（UUID 碰撞機率極低）
- 保持資料一致性
- 支援跨公司資料遷移

### 3. JSON 格式（不壓縮）

**決策：** Phase 3 不支援 ZIP 壓縮

**理由：**
- 簡化實作
- 方便檢視與編輯
- Phase 4+ 再加入壓縮支援

### 4. Transaction 管理

**決策：** 還原時使用 transaction

**理由：**
- 確保原子性（全部成功或全部失敗）
- 失敗時完整 rollback
- 不會污染資料庫

---

## 本次修改記錄

### v5.0 - 新增 attendance_records 支援（Phase 5）

**新增內容：**
1. 更新 `backup/exporter.py`：TENANT_DATA_TABLES 加入 attendance_records
2. 更新 `backup/importer.py`：TENANT_DATA_TABLES 加入 attendance_records
3. 更新 `backup/validator.py`：FK Closure Check log 訊息更新為 Phase 5
4. 更新 `backup/docs.md`：文件更新為 Phase 5，範例包含 attendance_records
5. 新增 `backup/tests/`：attendance_records 備份/還原測試

**影響的模組：**
- 無（backup 模組完全獨立，不影響 attendance 模組）

**新增的規則：**
- attendance_records 匯出時強制 WHERE company_id = ?
- attendance_records 還原時強制覆寫 company_id = target_company_id
- attendance_records 保留原始 UUID（避免衝突）
- FK Closure Check 仍為 stub（attendance_records 無外鍵）

**驗收條件：**
- ✅ 通過 `test_tenant_isolation.py` 所有測試（含 attendance_records）
- ✅ 通過 `test_api.py` 所有測試（含 attendance_records）
- ✅ 通過 `test_validator.py` 所有測試
- ✅ 符合 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則
- ✅ Company Consistency Check 正確運作
- ✅ FK Closure Check 正確運作（Phase 5 為 stub）
- ✅ 不影響既有 notifications 的備份/還原功能

### v3.0 - Backup 模組實作（Phase 3）

**新增內容：**
1. 新增 `backup/exporter.py`：匯出器（支援單一租戶全量抽取）
2. 新增 `backup/importer.py`：匯入器（還原器，支援 Merge/Replace 模式）
3. 新增 `backup/validator.py`：驗證器（Company Consistency Check + FK Closure Check）
4. 新增 `backup/service.py`：業務邏輯層
5. 新增 `backup/api.py`：POST /export, POST /restore
6. 新增 `backup/tests/`：完整測試套件（API + Tenant Isolation + Validator）
7. 更新 `main.py`：註冊 backup 路由

**影響的模組：**
- 無（backup 模組完全獨立）

**新增的規則：**
- 匯出時只匯出指定 company_id 的資料
- 還原時強制覆寫 company_id = target_company_id
- 備份檔混入其他 company_id → fail fast
- 還原時保留 UUID（避免衝突）
- 支援 Merge/Replace 兩種還原模式

**驗收條件：**
- ✅ 通過 `test_tenant_isolation.py` 所有測試
- ✅ 通過 `test_api.py` 所有測試
- ✅ 通過 `test_validator.py` 所有測試
- ✅ 符合 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則
- ✅ Company Consistency Check 正確運作
- ✅ FK Closure Check 正確運作（Phase 3 為 stub）

---

## 相關文件

- [SA_MODULE_SPEC v1.7](../../docs/SA_MODULE_SPECV1.7.md)
- [Cursor任務模板](../../docs/Cursor任務模板.txt)
- [Notifications 模組文件](../notifications/docs.md)
