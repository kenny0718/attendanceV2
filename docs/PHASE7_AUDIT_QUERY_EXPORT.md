# Phase 7-2：Audit Log 查詢 + 匯出（可稽核交付版）

目標：把 Phase 6 已完成的「備份匯出/還原稽核紀錄」做成可查詢、可篩選、可匯出（JSON/CSV）的 API，並補齊測試與文件，確保 multi-tenant 隔離正確。

---

## 一、範圍與規則

### 1) 權限規則（先簡化，不要卡住）
- 先做「只要帶 X-Company-ID 就能查該公司」，不做帳號登入/RBAC（若系統已有 auth 再加）。
- 任何查詢都**必須** tenant isolation：只能看到 `company_id == X-Company-ID` 的資料。
- 沒有 X-Company-ID：
  - 查詢 API 回 `422`（沿用你目前 header 驗證機制的行為）
  - 若你已有自訂驗證可回 `400`，但測試要一致

### 2) AuditLog 的資料來源
- 以現有「備份匯出/還原」操作寫入的紀錄為準（你 Phase 6 已完成）
- 如果目前 audit 表/模型名稱不是 `audit_logs`，請以實際存在的為準（但 API 對外統一叫 audit logs）

---

## 二、要新增的 API

路由建議放：`backend/app/modules/audit/api.py`（若你已經有 audit module 就沿用）

### A) 查詢 Audit Logs
- `GET /api/audit/logs`
- Query params：
  - `event_type` (optional) 例：`backup.export`, `backup.restore`
  - `actor` (optional) 誰操作（若有存）
  - `date_from` / `date_to` (optional) ISO 8601（或 yyyy-mm-dd）
  - `q` (optional) 關鍵字搜尋（可搜 message/summary/metadata）
  - `page` (default 1), `page_size` (default 50, max 200)
  - `sort` (default `-created_at`) 支援 `created_at`、`event_type`
- Response（JSON）格式：
```json
{
  "page": 1,
  "page_size": 50,
  "total": 123,
  "items": [
    {
      "id": "uuid",
      "company_id": "company-A",
      "event_type": "backup.export",
      "action": "export",
      "actor": "boss",
      "target": "company-A",
      "status": "success",
      "message": "匯出成功",
      "metadata": {"tables": 2, "version": "1.0"},
      "created_at": "2026-01-28T10:00:00Z"
    }
  ]
}


注意：回傳內容可以依你現有欄位調整，但務必包含：id/company_id/event_type/created_at。

B) 匯出 Audit Logs（JSON/CSV）

GET /api/audit/export

Query params 與 /api/audit/logs 相同，額外多：

format = json or csv（預設 json）

Response：

json：回傳 items 陣列（不用分頁，最多 5000 筆，超過回 400 並提示縮小條件）

csv：Content-Type: text/csv; charset=utf-8，第一列 header，UTF-8（可含 BOM 讓 Excel 好開）

三、Repository / Service 設計（簡單但乾淨）
1) Repo

檔案：backend/app/modules/audit/repo.py

list_logs(company_id, filters, page, page_size, sort) -> (items, total)

export_logs(company_id, filters, sort, limit=5000) -> items

2) Service

檔案：backend/app/modules/audit/service.py

負責組 query、套 tenant filter、排序、分頁

export 的 limit/超量錯誤由 service 負責

四、測試（必做，避免回歸）

檔案：backend/app/modules/audit/tests/test_audit_api.py

至少覆蓋：

GET /api/audit/logs 沒有 header → 422（或你系統定義的錯誤碼）

tenant isolation：建立 A、B 兩家公司 log，各自查只能看到自己

filter：event_type=backup.export 能過濾

分頁：page/page_size 能正常回 total/items 數量

export json：回 items 陣列，筆數 <= 5000

export csv：回 200，Content-Type 正確，且內容包含 header 列與至少一筆資料

五、文件（交付用）

新增文件：backend/app/modules/audit/docs.md

內容包含：

端點列表

query 參數說明

範例 curl（含 X-Company-ID）

CSV 匯出說明（Excel 開啟注意 UTF-8/BOM）

六、驗收標準（Definition of Done）

 pytest 全綠

 /api/audit/logs 能查、能 filter、分頁正確

 /api/audit/export?format=csv 可直接下載 CSV

 tenant isolation 100% 正確（A 看不到 B）

 docs 完整可讀

七、實作提示（請照做）

不要直接在 api.py 寫 SQL，請走 repo/service

sort 請做 allowlist，避免 SQL injection

export 筆數限制要有（避免一次拉爆 DB）

全程都要套 company_id == X-Company-ID 條件

八、你要修改/新增的檔案清單（Cursor 請照清單做）

新增：

backend/app/modules/audit/__init__.py

backend/app/modules/audit/api.py

backend/app/modules/audit/repo.py

backend/app/modules/audit/service.py

backend/app/modules/audit/tests/__init__.py

backend/app/modules/audit/tests/test_audit_api.py

backend/app/modules/audit/docs.md

可能需要調整：

backend/app/main.py（把 audit router include 進去）

若已有 audit model：沿用；若沒有，請建立 AuditLog ORM model（並補 migration）

九、如果你發現沒有 AuditLog 表怎麼辦（Cursor 指令）

若系統沒有 audit_logs（或類似）表：

新增 ORM model（backend/app/modules/audit/models.py）

Alembic migration 建表

Phase 6 寫 audit 的地方改成寫入這張表

完成後請回報：

pytest 結果（pass/fail）