# 備份/還原與稽核系統設計文件

**版本：** 1.0  
**最後更新：** 2026-01-27  
**適用系統：** Attendance System V2 (Multi-tenant Backend)

---

## 1. 設計目標

### 1.1 為什麼需要備份與還原

在多租戶 SaaS 系統中，備份與還原功能是資料保護與業務連續性的核心需求：

- **資料保護**：防止人為誤操作、系統故障導致的資料遺失
- **租戶遷移**：支援單一租戶的資料匯出與跨環境遷移
- **災難復原**：快速恢復特定租戶的資料至特定時間點
- **合規要求**：滿足資料可攜性（Data Portability）的法規要求

### 1.2 為什麼需要稽核紀錄

稽核紀錄（Audit Log）是企業級系統的必要功能：

- **內控合規**：滿足 SOC 2、ISO 27001 等資安標準要求
- **責任追溯**：記錄「誰、何時、對哪家公司、做了什麼」
- **異常偵測**：追蹤失敗操作，及早發現系統問題
- **營運分析**：統計備份/還原頻率，優化系統資源配置

### 1.3 核心設計原則

1. **Tenant Isolation（P0）**：絕對不可跨租戶存取資料
2. **Non-blocking Audit**：稽核紀錄失敗不影響主流程
3. **Immutable Log**：稽核紀錄一旦寫入不可修改
4. **Complete Traceability**：所有操作必須可追溯

---

## 2. 系統整體流程說明

### 2.1 備份流程（Export）

```
[Client Request]
    ↓
[API: POST /api/backup/export]
    ↓
[驗證 X-Company-ID Header] ← Tenant Isolation
    ↓
[BackupService.export_company()]
    ↓
[BackupExporter.export_company_data()]
    ├─ 查詢 notifications (WHERE company_id = ?)
    ├─ 查詢 attendance_records (WHERE company_id = ?)
    └─ 轉換為 JSON（UUID → str, datetime → ISO8601）
    ↓
[組裝 metadata + data]
    ↓
[寫入 Audit Log] ← 獨立 Session，不影響主流程
    ↓
[回傳 JSON Response]
```

**關鍵特性：**
- 強制 Tenant Isolation：所有查詢必須 `WHERE company_id = ?`
- 資料序列化：UUID 轉字串、datetime 轉 ISO8601
- 不壓縮：直接回傳 JSON（未來可擴充壓縮）

### 2.2 還原流程（Restore）

```
[Client Request with Backup JSON]
    ↓
[API: POST /api/backup/restore?clear_existing=false]
    ↓
[驗證 X-Company-ID Header] ← Tenant Isolation
    ↓
[BackupService.restore_company()]
    ↓
[BackupValidator.validate_for_restore()]
    ├─ 格式驗證（metadata + data 結構）
    ├─ Company Consistency Check（所有資料 company_id 一致）
    └─ FK Closure Check（外鍵完整性）
    ↓
[BackupImporter.restore_company_data()]
    ├─ [可選] 清空現有資料（clear_existing=true）
    ├─ 強制覆寫所有 company_id 為 target_company_id
    ├─ 轉換資料類型（str → UUID, str → datetime）
    └─ 批次插入資料
    ↓
[寫入 Audit Log] ← 獨立 Session，不影響主流程
    ↓
[回傳統計結果]
```

**關鍵特性：**
- **Company Consistency Check（P0）**：拒絕混入多個 company_id 的備份檔
- **強制覆寫 company_id**：不信任備份檔內的 company_id，全部覆寫為 target_company_id
- **Transaction 保證**：使用 SQLAlchemy transaction，失敗時完整 rollback
- **兩種模式**：
  - Merge 模式（clear_existing=false）：保留現有資料，新增備份資料
  - Replace 模式（clear_existing=true）：清空後還原

---

## 3. 稽核紀錄設計（Audit Log）

### 3.1 什麼時候會記錄

**所有備份/還原操作都會記錄，無論成功或失敗：**

| 操作 | 成功 | 失敗 |
|------|------|------|
| Export | ✅ 記錄 | ✅ 記錄 |
| Restore | ✅ 記錄 | ✅ 記錄 |

### 3.2 成功與失敗如何處理

#### 成功時（status="success"）

**Export 成功：**
```json
{
  "action": "backup.export",
  "status": "success",
  "meta": {
    "tables": ["notifications", "attendance_records"],
    "total_records": 150,
    "version": "1.0"
  },
  "error": null
}
```

**Restore 成功：**
```json
{
  "action": "backup.restore",
  "status": "success",
  "meta": {
    "clear_existing": true,
    "restored_tables": ["notifications", "attendance_records"],
    "restored_records": 150,
    "version": "1.0"
  },
  "error": null
}
```

#### 失敗時（status="fail"）

**Export 失敗：**
```json
{
  "action": "backup.export",
  "status": "fail",
  "meta": {
    "step": "export"
  },
  "error": "psycopg2.OperationalError: connection timeout"
}
```

**Restore 失敗（驗證失敗）：**
```json
{
  "action": "backup.restore",
  "status": "fail",
  "meta": {
    "step": "restore",
    "clear_existing": false
  },
  "error": "驗證失敗: 備份檔包含多個 company_id（違反 Tenant Isolation）: {'company-A', 'company-B'}"
}
```

### 3.3 不影響主流程的設計原則

**核心原則：Audit Log 寫入失敗不能導致主流程失敗**

實作方式：

1. **獨立 Session**：使用獨立的 database session，與主流程完全隔離
   ```python
   # 使用獨立 session
   from app.conftest import test_engine
   SessionLocal = sessionmaker(bind=test_engine)
   audit_db = SessionLocal()
   try:
       audit_db.add(audit_log)
       audit_db.commit()
   finally:
       audit_db.close()
   ```

2. **錯誤隔離**：所有 audit log 寫入都包在 try/except 中
   ```python
   try:
       _write_audit_log_direct(...)
   except Exception as e:
       logger.warning(f"寫入 audit log 失敗（不影響主流程）: {e}")
       # 不 raise，不影響主流程
   ```

3. **非同步寫入（未來可擴充）**：目前同步寫入，未來可改用 message queue

---

## 4. 資料欄位說明

### 4.1 資料表結構

**表名：** `audit_logs`

| 欄位 | 類型 | 必填 | 索引 | 說明 |
|------|------|------|------|------|
| id | UUID | ✅ | PK | 稽核紀錄 ID |
| company_id | VARCHAR(255) | ✅ | ✅ | 目標公司 ID |
| action | VARCHAR(255) | ✅ | ✅ | 操作類型 |
| status | VARCHAR(50) | ✅ | - | 操作狀態 |
| actor | VARCHAR(255) | ✅ | - | 執行者 |
| request_id | VARCHAR(255) | - | - | 請求 ID |
| ip | VARCHAR(255) | - | - | 來源 IP |
| user_agent | VARCHAR(500) | - | - | User Agent |
| meta | JSONB | ✅ | - | 操作 meta 資料 |
| error | TEXT | - | - | 錯誤訊息 |
| created_at | TIMESTAMP | ✅ | ✅ | 建立時間（UTC） |

**索引：**
- `idx_audit_logs_company_created` (company_id, created_at DESC)
- `idx_audit_logs_action_created` (action, created_at DESC)

### 4.2 欄位詳細說明

#### company_id
- **用途**：記錄操作的目標公司
- **來源**：從 `X-Company-ID` header 解析
- **Tenant Isolation**：查詢時必須加上 `WHERE company_id = ?`

#### action
- **用途**：記錄操作類型
- **可能值**：
  - `backup.export`：備份匯出
  - `backup.restore`：備份還原
  - 未來可擴充：`backup.delete`、`backup.schedule` 等

#### status
- **用途**：記錄操作結果
- **可能值**：
  - `success`：操作成功
  - `fail`：操作失敗

#### actor
- **用途**：記錄執行者身份
- **來源優先序**：
  1. `X-Actor` header
  2. `X-User` header
  3. fallback: `"system"`
- **未來擴充**：整合 JWT token，自動解析 user_id

#### request_id
- **用途**：關聯分散式追蹤（Distributed Tracing）
- **來源**：`X-Request-ID` header
- **未來擴充**：整合 OpenTelemetry / Jaeger

#### ip
- **用途**：記錄來源 IP，用於安全稽核
- **來源**：`request.client.host`

#### user_agent
- **用途**：記錄客戶端資訊
- **來源**：`User-Agent` header

#### meta (JSONB)
- **用途**：記錄操作的詳細資訊（彈性擴充）
- **Export 成功時包含**：
  - `tables`: 匯出的資料表清單
  - `total_records`: 匯出總筆數
  - `version`: 備份版本
- **Restore 成功時包含**：
  - `clear_existing`: 是否清空現有資料
  - `restored_tables`: 還原的資料表清單
  - `restored_records`: 還原總筆數
  - `version`: 備份版本
- **失敗時包含**：
  - `step`: 失敗的步驟（export / restore）
  - 其他相關資訊

#### error
- **用途**：記錄失敗時的錯誤訊息
- **限制**：最多 2000 字（自動截斷）
- **內容**：exception 的字串表示

#### created_at
- **用途**：記錄操作時間
- **時區**：UTC
- **格式**：ISO8601

---

## 5. Tenant Isolation 保證機制

### 5.1 設計原則

**絕對不可跨租戶存取資料（P0 優先級）**

### 5.2 實作機制

#### 5.2.1 Export 的 Tenant Isolation

1. **強制 Header 驗證**：
   - 缺少 `X-Company-ID` → 400 Bad Request
   - 由 `get_current_company_id()` dependency 強制注入

2. **查詢強制篩選**：
   ```python
   records = db.query(Model).filter(
       Model.company_id == company_id  # 強制篩選
   ).all()
   ```

3. **不信任 client 輸入**：
   - company_id 完全由 header 決定，不接受 request body 傳入

#### 5.2.2 Restore 的 Tenant Isolation

1. **Company Consistency Check（P0）**：
   - 驗證備份檔內所有資料的 company_id 必須一致
   - 不可混入其他公司資料
   - 違反時拒絕還原並記錄 audit log

2. **強制覆寫 company_id**：
   ```python
   # 不信任備份檔內的 company_id
   record_data["company_id"] = target_company_id  # 強制覆寫
   ```

3. **Target Company 由 Header 決定**：
   - 還原目標完全由 `X-Company-ID` header 決定
   - 不信任備份檔內的 metadata.company_id

#### 5.2.3 Audit Log 的 Tenant Isolation

1. **記錄目標公司**：
   - `company_id` 欄位記錄操作的目標公司
   - 查詢時必須加上 `WHERE company_id = ?`

2. **未來擴充**：
   - Audit Log 查詢 API 也必須遵守 Tenant Isolation
   - 只能查詢自己公司的 audit logs

---

## 6. 測試策略與覆蓋範圍說明

### 6.1 測試策略

採用 **pytest** 進行單元測試與整合測試，確保：
- 功能正確性
- Tenant Isolation 保證
- 錯誤處理完整性

### 6.2 測試覆蓋範圍

#### 6.2.1 Backup API 測試（22 個測試）

**Export 測試：**
- ✅ 成功匯出（有資料）
- ✅ 匯出空公司（無資料）
- ✅ 錯誤回應必須是 JSON
- ✅ 包含 attendance_records

**Restore 測試：**
- ✅ 成功還原
- ✅ 格式錯誤 → 400
- ✅ 混入其他公司 → 400（Company Consistency Check）
- ✅ 錯誤回應必須是 JSON
- ✅ 還原 attendance_records

**整合測試：**
- ✅ Export → Restore → 資料正確
- ✅ company_id 強制覆寫
- ✅ Roundtrip 測試

#### 6.2.2 Audit Log 測試（6 個測試）

**Export Audit：**
- ✅ 匯出成功會新增 audit log
- ✅ 沒有 X-Actor header 時使用 fallback

**Restore Audit：**
- ✅ 還原成功會新增 audit log
- ✅ 還原失敗會新增 audit log（status=fail）
- ✅ 混入其他公司會新增 fail audit log

**Metadata 測試：**
- ✅ audit log 記錄 request metadata（IP, User-Agent, Request-ID）

### 6.3 測試資料庫

使用獨立的測試資料庫：
- **資料庫名稱**：`attendance_test_db`
- **隔離機制**：每個測試前 `drop_all()` + `create_all()`
- **安全檢查**：資料庫名稱必須包含 `test` 關鍵字

---

## 7. 設計決策說明

### 7.1 為什麼使用獨立 Session 寫入 Audit Log？

**問題：**
如果使用主流程的 session，當主流程失敗 rollback 時，audit log 也會被 rollback。

**解決方案：**
使用獨立的 database session，完全隔離於主流程。

**優點：**
- Audit log 不受主流程 transaction 影響
- 即使主流程失敗，audit log 仍會寫入
- 符合「不影響主流程」的設計原則

**缺點：**
- 需要額外的 database connection
- 無法保證 audit log 與主流程的原子性（可接受）

### 7.2 為什麼不壓縮備份檔？

**目前設計：**
直接回傳 JSON，不壓縮。

**原因：**
- **簡化實作**：避免壓縮/解壓縮的複雜度
- **可讀性**：JSON 可直接檢視，方便除錯
- **資料量小**：目前單一租戶資料量不大（< 10MB）

**未來擴充：**
當資料量增大時，可加入 gzip 壓縮：
```python
import gzip
compressed = gzip.compress(json.dumps(backup_data).encode())
```

### 7.3 為什麼強制覆寫 company_id？

**問題：**
如果信任備份檔內的 company_id，可能導致跨租戶資料洩漏。

**解決方案：**
還原時強制覆寫所有 company_id 為 target_company_id。

**優點：**
- 絕對保證 Tenant Isolation
- 防止惡意備份檔混入其他公司資料
- 符合「不信任 client 輸入」的安全原則

### 7.4 為什麼使用 JSONB 儲存 meta？

**優點：**
- **彈性擴充**：不同操作可記錄不同的 meta 資料
- **查詢能力**：PostgreSQL JSONB 支援索引與查詢
- **避免 schema 變更**：新增 meta 欄位不需要 migration

**範例查詢：**
```sql
-- 查詢 clear_existing=true 的還原操作
SELECT * FROM audit_logs
WHERE action = 'backup.restore'
  AND meta->>'clear_existing' = 'true';
```

### 7.5 為什麼錯誤訊息限制 2000 字？

**原因：**
- 防止超長錯誤訊息（如 stack trace）佔用過多儲存空間
- 2000 字足以記錄關鍵錯誤資訊
- 超過部分自動截斷並加上 `... (truncated)`

---

## 8. 未來可擴充方向

### 8.1 Audit Log 查詢 API

**需求：**
提供 API 讓管理者查詢 audit logs。

**設計：**
```
GET /api/audit/logs?company_id=xxx&action=backup.export&status=fail&limit=50
```

**注意事項：**
- 必須遵守 Tenant Isolation
- 支援分頁（limit + offset）
- 支援時間範圍篩選

### 8.2 Audit Log 統計與告警

**統計 API：**
```
GET /api/audit/stats?company_id=xxx
```

回傳：
- 成功率
- 失敗次數
- 最近 7 天操作趨勢

**告警機制：**
- 失敗率超過閾值 → 發送告警
- 異常操作頻率 → 發送告警
- 整合 Slack / Email / PagerDuty

### 8.3 Audit Log 清理機制

**需求：**
定期清理舊的 audit logs，避免資料表過大。

**設計：**
- 保留最近 90 天的 audit logs
- 超過 90 天的自動歸檔或刪除
- 使用 Celery / Cron Job 定期執行

### 8.4 備份檔壓縮

**需求：**
當資料量增大時，壓縮備份檔以節省頻寬。

**設計：**
- Export 時自動 gzip 壓縮
- Restore 時自動解壓縮
- 在 metadata 中記錄 `compression: "gzip"`

### 8.5 增量備份

**需求：**
只備份自上次備份後的新增/修改資料。

**設計：**
- 在 metadata 中記錄 `backup_type: "incremental"`
- 記錄 `last_backup_at` 時間戳記
- 查詢時加上 `WHERE created_at > last_backup_at`

### 8.6 備份檔加密

**需求：**
加密備份檔，防止資料洩漏。

**設計：**
- 使用 AES-256 加密
- 金鑰管理：AWS KMS / HashiCorp Vault
- 在 metadata 中記錄 `encrypted: true`

### 8.7 排程備份

**需求：**
自動定期備份所有租戶資料。

**設計：**
- 使用 Celery Beat 排程
- 每日凌晨 2:00 自動備份
- 備份檔上傳至 S3 / GCS

### 8.8 Audit Log 匯出

**需求：**
匯出 audit logs 供外部稽核系統使用。

**設計：**
```
GET /api/audit/export?company_id=xxx&start_date=2026-01-01&end_date=2026-01-31
```

回傳 CSV 或 JSON 格式。

---

## 9. 附錄

### 9.1 相關檔案清單

```
backend/
├── alembic/versions/
│   └── 002_create_audit_logs.py          # Migration
├── app/modules/audit/
│   ├── __init__.py                        # Module init
│   ├── models.py                          # AuditLog model
│   ├── repo.py                            # Repository
│   └── tests/
│       └── test_audit_backup.py           # 測試（6 個）
├── app/modules/backup/
│   ├── api.py                             # API 路由（含 audit log）
│   ├── service.py                         # 服務層
│   ├── exporter.py                        # 匯出器
│   ├── importer.py                        # 匯入器
│   ├── validator.py                       # 驗證器
│   └── tests/
│       └── test_api.py                    # 測試（22 個）
└── docs/
    └── backup_restore_audit_design.md     # 本文件
```

### 9.2 API 端點總覽

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/backup/export` | POST | 匯出公司資料 |
| `/api/backup/restore` | POST | 還原公司資料 |

### 9.3 資料庫表總覽

| 表名 | 說明 | Tenant Data |
|------|------|-------------|
| `notifications` | 通知記錄 | ✅ |
| `attendance_records` | 考勤記錄 | ✅ |
| `audit_logs` | 稽核紀錄 | ✅ |

### 9.4 參考資料

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [SOC 2 Compliance](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/sorhome)

---

**文件結束**
