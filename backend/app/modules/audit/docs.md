# Audit Log API 文件

## 概述

Audit Log API 提供稽核紀錄的查詢與匯出功能，支援多種篩選條件、分頁、排序，以及 JSON/CSV 兩種匯出格式。

## 權限規則

- **必須提供 `X-Company-ID` header**：所有 API 都需要此 header
- **Tenant Isolation**：只能查詢/匯出該公司的稽核紀錄
- **沒有 header 回傳 400 錯誤**

## API 端點

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

**JSON 格式回應：**

```json
[
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
      "tables": 2
    },
    "created_at": "2026-01-28T10:00:00Z"
  }
]
```

**CSV 格式回應：**

- Content-Type: `text/csv; charset=utf-8`
- 第一列為 header
- UTF-8 編碼（含 BOM，讓 Excel 正確識別）

**範例 curl：**

```bash
# 匯出 JSON
curl -X GET "http://localhost:8000/api/audit/export?format=json" \
  -H "X-Company-ID: company-A"

# 匯出 CSV
curl -X GET "http://localhost:8000/api/audit/export?format=csv" \
  -H "X-Company-ID: company-A" \
  -o audit_logs.csv

# 匯出特定日期範圍的 CSV
curl -X GET "http://localhost:8000/api/audit/export?format=csv&date_from=2026-01-01T00:00:00Z&date_to=2026-01-31T23:59:59Z" \
  -H "X-Company-ID: company-A" \
  -o audit_logs_january.csv

# 匯出特定事件類型
curl -X GET "http://localhost:8000/api/audit/export?format=json&event_type=backup.export" \
  -H "X-Company-ID: company-A"
```

---

## CSV 匯出說明

### Excel 開啟注意事項

1. **UTF-8 編碼**：CSV 檔案使用 UTF-8 編碼（含 BOM），Excel 應該能正確識別中文
2. **如果 Excel 顯示亂碼**：
   - 方法 1：使用「資料」→「從文字/CSV」匯入，選擇 UTF-8 編碼
   - 方法 2：使用 Google Sheets 或 LibreOffice Calc 開啟（支援較好）

### CSV 欄位說明

| 欄位 | 說明 |
|------|------|
| `id` | 稽核紀錄 ID（UUID） |
| `company_id` | 公司 ID |
| `event_type` | 事件類型 |
| `action` | 操作類型 |
| `actor` | 執行者 |
| `target` | 目標（通常是 company_id） |
| `status` | 操作狀態（`success` 或 `fail`） |
| `message` | 訊息（成功或錯誤訊息） |
| `metadata` | Meta 資料（JSON 字串） |
| `created_at` | 建立時間（ISO 8601） |

---

## 錯誤處理

### 400 Bad Request

**原因：**
- 缺少 `X-Company-ID` header
- 匯出結果超過 5000 筆

**範例回應：**
```json
{
  "detail": "Missing X-Company-ID header"
}
```

```json
{
  "detail": "匯出結果超過 5000 筆，請縮小查詢條件"
}
```

### 422 Unprocessable Entity

**原因：**
- Query 參數格式錯誤（例如：`page_size` 超過 200）

### 500 Internal Server Error

**原因：**
- 伺服器內部錯誤

---

## 使用範例

### 範例 1：查詢最近 7 天的備份匯出紀錄

```bash
DATE_FROM=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)
DATE_TO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

curl -X GET "http://localhost:8000/api/audit/logs?event_type=backup.export&date_from=${DATE_FROM}&date_to=${DATE_TO}" \
  -H "X-Company-ID: company-A"
```

### 範例 2：匯出本月所有稽核紀錄（CSV）

```bash
DATE_FROM="2026-01-01T00:00:00Z"
DATE_TO="2026-01-31T23:59:59Z"

curl -X GET "http://localhost:8000/api/audit/export?format=csv&date_from=${DATE_FROM}&date_to=${DATE_TO}" \
  -H "X-Company-ID: company-A" \
  -o audit_logs_january_2026.csv
```

### 範例 3：搜尋特定使用者的操作紀錄

```bash
curl -X GET "http://localhost:8000/api/audit/logs?actor=alice&page_size=100" \
  -H "X-Company-ID: company-A"
```

---

## 技術細節

### Tenant Isolation

所有查詢都會自動套用 `company_id == X-Company-ID` 條件，確保：
- A 公司看不到 B 公司的資料
- 100% 資料隔離

### 排序規則

- 預設：`-created_at`（最新的在前）
- 支援欄位：`created_at`, `action`
- 前綴 `-` 表示降序（例如：`-created_at`）
- 無前綴表示升序（例如：`created_at`）

### 關鍵字搜尋

`q` 參數會搜尋以下欄位：
- `action`（操作類型）
- `actor`（執行者）
- `error`（錯誤訊息）
- `meta`（Meta 資料，JSON 字串）

搜尋不區分大小寫（case-insensitive）。

---

## 常見問題

### Q1：為什麼匯出限制 5000 筆？

**A：** 避免一次查詢過多資料導致資料庫負載過高。如果需要匯出更多資料，請：
1. 縮小日期範圍
2. 使用 `event_type` 或 `actor` 篩選
3. 分批匯出

### Q2：CSV 在 Excel 中顯示亂碼怎麼辦？

**A：** CSV 已包含 UTF-8 BOM，Excel 應該能正確識別。如果仍有問題：
1. 使用「資料」→「從文字/CSV」匯入
2. 手動選擇 UTF-8 編碼
3. 或使用 Google Sheets / LibreOffice Calc

### Q3：如何查詢失敗的操作？

**A：** 目前 API 不支援直接篩選 `status`，但可以：
1. 匯出所有資料後在 Excel 中篩選
2. 或在程式碼中新增 `status` 參數（需要修改 API）

### Q4：日期格式有哪些支援？

**A：** 支援 ISO 8601 格式：
- `2026-01-28T10:00:00Z`（推薦）
- `2026-01-28T10:00:00+00:00`
- `2026-01-28T18:00:00+08:00`（會自動轉換為 UTC）

---

## 更新日誌

### Phase 7-2 (2026-01-28)
- ✅ 新增 `GET /api/audit/logs` 查詢 API
- ✅ 新增 `GET /api/audit/export` 匯出 API
- ✅ 支援 JSON 和 CSV 兩種匯出格式
- ✅ 實作 tenant isolation
- ✅ 完整測試覆蓋
