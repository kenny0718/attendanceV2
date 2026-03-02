# Audit Log API 文件

## 概述

Audit Log API 提供稽核紀錄的查詢與匯出功能，支援多種篩選條件、分頁、排序，以及 JSON/CSV 兩種匯出格式。

**Phase 8 新增：** Retention Policy（保留政策）與 Purge（清理）功能。

## 權限規則

- **必須提供 `X-Company-ID` header**：所有 API 都需要此 header
- **Tenant Isolation**：只能查詢/匯出該公司的稽核紀錄
- **沒有 header 回傳 422 錯誤**

---

## Phase 7: Query & Export API

### 1. 查詢稽核紀錄

**端點：** `GET /api/audit/logs`

**功能：** 查詢稽核紀錄，支援篩選、分頁、排序

**Headers：**
```
X-Company-ID: company-A
```

**Query 參數：**

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `event_type` | string | 否 | - | 事件類型（例如：`backup.export`, `backup.restore`） |
| `actor` | string | 否 | - | 執行者 |
| `date_from` | string | 否 | - | 開始日期（ISO 8601 格式，例如：`2026-01-28T00:00:00Z`） |
| `date_to` | string | 否 | - | 結束日期（ISO 8601 格式） |
| `q` | string | 否 | - | 關鍵字搜尋（搜尋 action, actor, error, metadata） |
| `page` | integer | 否 | 1 | 頁碼（從 1 開始） |
| `page_size` | integer | 否 | 50 | 每頁筆數（最大 200） |
| `sort` | string | 否 | `-created_at` | 排序欄位（支援：`created_at`, `-created_at`, `action`, `-action`） |

**回應格式：**

```json
{
  "page": 1,
  "page_size": 50,
  "total": 123,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "company_id": "company-A",
      "event_type": "backup.export",
      "action": "backup.export",
      "actor": "boss",
      "target": "company-A",
      "status": "success",
      "message": "操作成功",
      "metadata": {
        "tables": 2,
        "version": "1.0"
      },
      "created_at": "2026-01-28T10:00:00Z"
    }
  ]
}
```

**範例 curl：**

```bash
# 基本查詢
curl -X GET "http://localhost:8000/api/audit/logs" \
  -H "X-Company-ID: company-A"

# 篩選 event_type
curl -X GET "http://localhost:8000/api/audit/logs?event_type=backup.export" \
  -H "X-Company-ID: company-A"

# 篩選日期範圍
curl -X GET "http://localhost:8000/api/audit/logs?date_from=2026-01-01T00:00:00Z&date_to=2026-01-31T23:59:59Z" \
  -H "X-Company-ID: company-A"

# 關鍵字搜尋
curl -X GET "http://localhost:8000/api/audit/logs?q=export" \
  -H "X-Company-ID: company-A"

# 分頁
curl -X GET "http://localhost:8000/api/audit/logs?page=2&page_size=20" \
  -H "X-Company-ID: company-A"

# 排序（升序）
curl -X GET "http://localhost:8000/api/audit/logs?sort=created_at" \
  -H "X-Company-ID: company-A"
```

---

### 2. 匯出稽核紀錄

**端點：** `GET /api/audit/export`

**功能：** 匯出稽核紀錄，支援 JSON 和 CSV 兩種格式

**Headers：**
```
X-Company-ID: company-A
```

**Query 參數：**

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `format` | string | 否 | `json` | 匯出格式（`json` 或 `csv`） |
| `event_type` | string | 否 | - | 事件類型 |
| `actor` | string | 否 | - | 執行者 |
| `date_from` | string | 否 | - | 開始日期（ISO 8601） |
| `date_to` | string | 否 | - | 結束日期（ISO 8601） |
| `q` | string | 否 | - | 關鍵字搜尋 |
| `sort` | string | 否 | `-created_at` | 排序欄位 |

**限制：**
- **最多匯出 5000 筆**
- 若超過 5000 筆，回傳 `400` 錯誤並提示縮小查詢條件

**範例 curl：**

```bash
# 匯出 JSON
curl -X GET "http://localhost:8000/api/audit/export?format=json" \
  -H "X-Company-ID: company-A"

# 匯出 CSV
curl -X GET "http://localhost:8000/api/audit/export?format=csv" \
  -H "X-Company-ID: company-A" \
  -o audit_logs.csv
```

---

## Phase 8: Retention Policy & Purge API

### 3. 取得保留政策

**端點：** `GET /api/audit/retention`

**功能：** 取得目前公司的 audit log 保留天數設定

**Headers：**
```
X-Company-ID: company-A
```

**回應格式：**

```json
{
  "company_id": "company-A",
  "retention_days": 365,
  "is_default": true,
  "created_at": null,
  "updated_at": null
}
```

**欄位說明：**
- `retention_days`: 保留天數（7 ~ 3650）
- `is_default`: 是否使用預設值（`true` = 使用預設 365 天，`false` = 已自訂）
- `created_at`: 建立時間（若未設定則為 `null`）
- `updated_at`: 更新時間（若未設定則為 `null`）

**範例 curl：**

```bash
curl -X GET "http://localhost:8000/api/audit/retention" \
  -H "X-Company-ID: company-A"
```

---

### 4. 更新保留政策

**端點：** `PUT /api/audit/retention`

**功能：** 更新 audit log 保留天數

**Headers：**
```
X-Company-ID: company-A
Content-Type: application/json
```

**Body 參數：**

```json
{
  "retention_days": 180,
  "actor": "admin"
}
```

| 參數 | 類型 | 必填 | 範圍 | 說明 |
|------|------|------|------|------|
| `retention_days` | integer | 是 | 7 ~ 3650 | 保留天數 |
| `actor` | string | 是 | 1 ~ 255 字元 | 執行者 |

**回應格式：**

```json
{
  "company_id": "company-A",
  "retention_days": 180,
  "is_default": false,
  "created_at": "2026-01-28T10:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z"
}
```

**注意事項：**
- ✅ 更新行為會寫入 audit log（`event_type: audit.retention.update`）
- ✅ `retention_days` 必須在 7 ~ 3650 之間
- ✅ 超出範圍會回傳 `400` 錯誤

**範例 curl：**

```bash
curl -X PUT "http://localhost:8000/api/audit/retention" \
  -H "X-Company-ID: company-A" \
  -H "Content-Type: application/json" \
  -d '{
    "retention_days": 180,
    "actor": "admin"
  }'
```

---

### 5. 清理過期紀錄（Purge）

**端點：** `POST /api/audit/purge`

**功能：** 安全地清理過期的 audit logs

**Headers：**
```
X-Company-ID: company-A
Content-Type: application/json
```

**Body 參數：**

```json
{
  "actor": "admin",
  "dry_run": true,
  "batch_size": 1000,
  "max_delete": 10000
}
```

| 參數 | 類型 | 必填 | 預設值 | 範圍 | 說明 |
|------|------|------|--------|------|------|
| `actor` | string | 是 | - | 1 ~ 255 字元 | 執行者 |
| `dry_run` | boolean | 否 | `true` | - | 是否為 dry run（僅回報，不實際刪除） |
| `batch_size` | integer | 否 | 1000 | 1 ~ 2000 | 批次大小（分批刪除，避免 DB lock） |
| `max_delete` | integer | 否 | 10000 | 1 ~ 20000 | 單次最大刪除筆數上限 |

**回應格式：**

```json
{
  "company_id": "company-A",
  "cutoff_date": "2025-01-28T10:00:00Z",
  "retention_days": 365,
  "deleted_count": 1234,
  "total_purgeable": 1234,
  "dry_run": true,
  "batch_size": 1000,
  "max_delete": 10000,
  "batches_executed": 0,
  "duration_ms": 123
}
```

**欄位說明：**
- `cutoff_date`: 截止日期（`created_at < cutoff_date` 的紀錄會被刪除）
- `retention_days`: 使用的保留天數
- `deleted_count`: 刪除筆數（`dry_run=true` 時為預估值）
- `total_purgeable`: 總共可刪除筆數
- `dry_run`: 是否為 dry run
- `batches_executed`: 執行的批次數（`dry_run=true` 時為 0）
- `duration_ms`: 執行時間（毫秒）

**範例 curl：**

```bash
# Dry run（建議先執行）
curl -X POST "http://localhost:8000/api/audit/purge" \
  -H "X-Company-ID: company-A" \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "admin",
    "dry_run": true,
    "batch_size": 1000,
    "max_delete": 10000
  }'

# 實際刪除
curl -X POST "http://localhost:8000/api/audit/purge" \
  -H "X-Company-ID: company-A" \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "admin",
    "dry_run": false,
    "batch_size": 1000,
    "max_delete": 10000
  }'
```

---

## Retention Policy 說明

### 保留天數規則

- **預設值：** 365 天
- **合法範圍：** 7 ~ 3650 天（約 1 週 ~ 10 年）
- **套用方式：** 每個 `company_id` 可獨立設定

### 計算方式

```
cutoff_date = now - retention_days
可刪除的紀錄 = created_at < cutoff_date
```

### 設定流程

1. **查詢目前設定：** `GET /api/audit/retention`
2. **更新設定：** `PUT /api/audit/retention`
3. **驗證設定：** 再次查詢確認

---

## Purge 使用指南

### 建議流程

1. **先執行 dry run：** 確認會刪除多少筆資料
   ```bash
   curl -X POST ".../purge" -d '{"actor":"admin","dry_run":true,...}'
   ```

2. **檢查回報：** 確認 `deleted_count` 和 `cutoff_date` 符合預期

3. **實際執行：** 設定 `dry_run=false`
   ```bash
   curl -X POST ".../purge" -d '{"actor":"admin","dry_run":false,...}'
   ```

4. **查詢 audit log：** 確認 purge 行為已被記錄
   ```bash
   curl -X GET ".../logs?event_type=audit.purge"
   ```

### 安全限制

| 參數 | 上限 | 理由 |
|------|------|------|
| `batch_size` | 2000 | 避免單次刪除過多造成 DB lock |
| `max_delete` | 20000 | 避免一次刪除過多資料 |

**超出範圍會回傳 `400` 錯誤。**

### 分批刪除機制

Purge 會自動分批刪除，避免長時間鎖定資料庫：

```
總共要刪除 5000 筆，batch_size=1000
→ 執行 5 個批次，每批次刪除 1000 筆
→ batches_executed = 5
```

### Tenant Isolation

- ✅ Purge 只會刪除指定 `company_id` 的資料
- ✅ 不會影響其他公司的 audit logs
- ✅ 100% 資料隔離

---

## 稽核追蹤（Audit Trail）

### Purge 行為會被記錄

每次執行 purge（包括 dry run），都會寫入 audit log：

**Event Type:** `audit.purge`

**Metadata 包含：**
- `cutoff_date`: 截止日期
- `retention_days`: 使用的保留天數
- `deleted_count`: 刪除筆數
- `total_purgeable`: 總共可刪除筆數
- `dry_run`: 是否為 dry run
- `batch_size`: 批次大小
- `max_delete`: 最大刪除筆數
- `batches_executed`: 執行批次數
- `duration_ms`: 執行時間

**查詢 purge 紀錄：**

```bash
curl -X GET "http://localhost:8000/api/audit/logs?event_type=audit.purge" \
  -H "X-Company-ID: company-A"
```

### Retention 更新會被記錄

每次更新 retention policy，都會寫入 audit log：

**Event Type:** `audit.retention.update`

**Metadata 包含：**
- `old_retention_days`: 舊的保留天數
- `new_retention_days`: 新的保留天數

**查詢 retention 更新紀錄：**

```bash
curl -X GET "http://localhost:8000/api/audit/logs?event_type=audit.retention.update" \
  -H "X-Company-ID: company-A"
```

---

## 錯誤處理

### 422 Unprocessable Entity

**原因：**
- 缺少 `X-Company-ID` header
- 參數格式錯誤

**範例回應：**
```json
{
  "detail": [
    {
      "loc": ["header", "x-company-id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 400 Bad Request

**原因：**
- `retention_days` 超出範圍（7 ~ 3650）
- `batch_size` 超出範圍（1 ~ 2000）
- `max_delete` 超出範圍（1 ~ 20000）
- 匯出結果超過 5000 筆

**範例回應：**
```json
{
  "detail": "retention_days 必須在 7 ~ 3650 之間"
}
```

### 500 Internal Server Error

**原因：**
- 伺服器內部錯誤

---

## 常見問題

### Q1：為什麼需要 Retention Policy？

**A：** 
1. **法規遵循：** 某些產業要求保留特定期間的稽核紀錄
2. **儲存成本：** 長期累積的 audit logs 會佔用大量空間
3. **查詢效能：** 資料量過大會影響查詢速度

### Q2：Purge 會刪除哪些資料？

**A：** 只會刪除 `created_at < (now - retention_days)` 的紀錄。例如：
- Retention = 365 天
- 今天是 2026-01-28
- 會刪除 2025-01-28 之前的紀錄

### Q3：Purge 是否可逆？

**A：** **不可逆！** 刪除後無法復原。建議：
1. 先執行 `dry_run=true` 確認
2. 定期備份資料庫
3. 謹慎設定 `retention_days`

### Q4：如何避免誤刪重要資料？

**A：**
1. ✅ 使用 `dry_run=true` 先測試
2. ✅ 設定合理的 `retention_days`（建議至少 90 天）
3. ✅ 使用 `max_delete` 限制單次刪除筆數
4. ✅ 查詢 audit log 確認 purge 行為

### Q5：Purge 會影響效能嗎？

**A：** 不會。Purge 使用分批刪除機制：
- 每批次最多刪除 `batch_size` 筆（預設 1000）
- 避免長時間鎖定資料庫
- 不影響其他查詢操作

### Q6：可以手動刪除 audit logs 嗎？

**A：** **不建議。** 應該使用 Purge API，因為：
1. ✅ Purge 行為會被記錄（可追蹤）
2. ✅ 自動遵守 retention policy
3. ✅ 分批刪除，避免 DB lock
4. ✅ Tenant isolation 保證

---

## 更新日誌

### Phase 8 (2026-01-28)
- ✅ 新增 `GET /api/audit/retention` 查詢保留政策
- ✅ 新增 `PUT /api/audit/retention` 更新保留政策
- ✅ 新增 `POST /api/audit/purge` 清理過期紀錄
- ✅ Retention policy 支援每公司獨立設定（7 ~ 3650 天）
- ✅ Purge 支援 dry run、分批刪除、tenant isolation
- ✅ 所有 retention/purge 操作都會寫入 audit log
- ✅ 完整測試覆蓋

### Phase 7 (2026-01-28)
- ✅ 新增 `GET /api/audit/logs` 查詢 API
- ✅ 新增 `GET /api/audit/export` 匯出 API
- ✅ 支援 JSON 和 CSV 兩種匯出格式
- ✅ 實作 tenant isolation
- ✅ 完整測試覆蓋
