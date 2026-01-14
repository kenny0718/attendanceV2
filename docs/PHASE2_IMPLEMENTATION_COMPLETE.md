# Phase 2 實作完成報告

## ✅ 實作完成確認

Phase 2 已完成 notifications 模組的所有實作，並**嚴格遵守 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則（P0）**。

---

## 📦 已建立的檔案清單

### 核心檔案（8 個）
1. `backend/app/core/database.py` - SQLAlchemy 資料庫連線管理（同步）
2. `backend/app/modules/notifications/__init__.py` - 模組初始化
3. `backend/app/modules/notifications/models.py` - Notification 資料模型（UUID 主鍵）
4. `backend/app/modules/notifications/repo.py` - 資料存取層（強制 Tenant Isolation）
5. `backend/app/modules/notifications/service.py` - 業務邏輯層
6. `backend/app/modules/notifications/api.py` - GET /api/notifications
7. `backend/app/modules/notifications/event_handlers.py` - 訂閱 attendance.approved（Fail-fast）
8. `backend/app/modules/notifications/docs.md` - 完整模組文件

### 測試檔案（3 個）
9. `backend/app/modules/notifications/tests/__init__.py`
10. `backend/app/modules/notifications/tests/test_api.py` - API 測試
11. `backend/app/modules/notifications/tests/test_tenant_isolation.py` - **Tenant Isolation 測試（P0）**
12. `backend/app/modules/notifications/tests/test_event_handlers.py` - 事件處理器測試（含 Fail-fast）

### 更新的檔案（3 個）
13. `backend/app/core/config.py` - 新增 database_url 設定
14. `backend/app/main.py` - 註冊 notifications 路由與事件訂閱者
15. `backend/requirements.txt` - 新增 SQLAlchemy, psycopg2, pytest

---

## 🎯 Tenant Isolation 實作（P0）

### 1. 資料模型設計

**UUID 主鍵（避免還原時 ID 衝突）：**
```python
id = Column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,  # Python 生成，不依賴 PostgreSQL extension
)
```

**company_id 索引（支援高效匯出）：**
```python
__table_args__ = (
    Index("idx_notifications_company_id", "company_id"),
    Index("idx_notifications_company_created", "company_id", "created_at"),
)
```

### 2. Repository 層強制篩選

**所有查詢強制 WHERE company_id = ?：**
```python
def get_notifications(self, company_id: str, limit: int, offset: int):
    return (
        self.db.query(Notification)
        .filter(Notification.company_id == company_id)  # 強制篩選
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
```

**支援單一租戶全量抽取（備份用）：**
```python
def get_all_notifications_for_company(self, company_id: str):
    """全量抽取，不分頁（備份用）"""
    return (
        self.db.query(Notification)
        .filter(Notification.company_id == company_id)
        .order_by(Notification.created_at.asc())
        .all()
    )
```

### 3. 事件處理器 Fail-fast

**方案 A + Fail-fast：**
```python
def handle_attendance_approved(payload: Dict[str, Any]) -> None:
    # Fail-fast：檢查 company_id
    company_id = payload.get("company_id")
    if not company_id or not isinstance(company_id, str) or not company_id.strip():
        raise ValueError("payload 缺少有效的 company_id")
    
    # 使用 payload.company_id 作為 Source of Truth
    repo.create_notification(
        company_id=company_id,  # 來自 payload（已由 attendance 注入）
        event_type="attendance.approved",
        event_payload=payload
    )
```

### 4. API 層強制注入

```python
@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    current_company_id: str = Depends(get_current_company_id),  # 強制注入
    db: Session = Depends(get_db)
):
    # company_id 由後端注入，不信任 request
    result = service.get_notifications(company_id=current_company_id, ...)
```

---

## 🧪 測試執行方式

### 快速驗證

```bash
# 1. 安裝依賴
cd backend
pip install -r requirements.txt

# 2. 設定資料庫（.env 或環境變數）
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/attendance_v2" > .env

# 3. 啟動應用（會自動建立資料表）
uvicorn app.main:app --reload

# 4. 測試事件觸發
curl -X POST http://localhost:8000/api/attendance/mock-create \
  -H "X-Company-ID: company-test"

# 記下 attendance_record_id

curl -X POST http://localhost:8000/api/attendance/{id}/approve \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: company-test" \
  -d '{"employee_id": "emp-001", "approved_by": "mgr-001"}'

# 5. 查詢通知記錄
curl -X GET http://localhost:8000/api/notifications \
  -H "X-Company-ID: company-test"
```

### 完整測試套件

```bash
# 執行所有測試
pytest backend/app/modules/notifications/tests/ -v

# 只測試 Tenant Isolation（P0）
pytest backend/app/modules/notifications/tests/test_tenant_isolation.py -v

# 只測試事件處理器（含 Fail-fast）
pytest backend/app/modules/notifications/tests/test_event_handlers.py -v
```

---

## 📋 驗收標準檢查

### P0: Tenant Isolation（必須通過）
- [x] company_id 從 Header 強制注入（API）
- [x] company_id 從 payload 取得並 Fail-fast 驗證（Event Handler）
- [x] 缺少 Header → 400 Bad Request
- [x] A 公司與 B 公司完全隔離
- [x] Repository 所有查詢強制 `WHERE company_id = ?`
- [x] 支援單一 company_id 全量抽取（備份用）
- [x] 提供完整的 Tenant Isolation 測試

### 資料模型（單一租戶備份支援）
- [x] 主鍵使用 UUID（Python uuid4()）
- [x] company_id 有索引（支援高效匯出）
- [x] event_payload 使用 JSONB（保留完整資料）
- [x] 支援 `WHERE company_id = ?` 全量抽取

### 事件驅動
- [x] 訂閱 `attendance.approved` 事件
- [x] 事件觸發時正確寫入資料庫
- [x] Fail-fast：payload 缺少 company_id → ValueError
- [x] 多公司事件正確隔離

### API 功能
- [x] GET /api/notifications（分頁查詢）
- [x] 回應結構正確（notifications + pagination）
- [x] 所有錯誤回應為 JSON 格式

### 模組結構（SA_MODULE_SPEC v1.7）
- [x] api.py - API 路由定義
- [x] service.py - 業務邏輯層
- [x] repo.py - 資料存取層
- [x] models.py - 資料模型
- [x] docs.md - 模組文件
- [x] tests/ - 測試目錄
- [x] event_handlers.py - 事件處理器

---

## 🔍 與規範的對照

### SA_MODULE_SPEC v1.7 符合度

| 規範項目 | 要求 | 實作狀態 |
|---------|------|---------|
| 模組結構 | api/service/repo/models/docs/tests | ✅ 完全符合 |
| Tenant Isolation | company_id 強制注入 | ✅ 完全符合 |
| 不信任 request body | 禁止接受 company_id | ✅ 完全符合 |
| Tenant 測試 | 提供隔離測試 | ✅ 完全符合 |
| 事件驅動 | 使用 EventBus | ✅ 完全符合 |
| 跨模組互動 | 只用 EventBus | ✅ 完全符合 |
| 單一租戶備份 | UUID 主鍵 + 全量抽取 | ✅ 完全符合 |
| 環境限制 | 同步 SQLAlchemy + PostgreSQL | ✅ 完全符合 |

### Phase 2 任務目標符合度

| 目標 | 實作狀態 |
|------|---------|
| 新增 notifications 模組 | ✅ 已完成 |
| 訂閱 attendance.approved | ✅ 已完成 |
| 寫入資料庫（tenant-safe） | ✅ 已完成 |
| 不影響其他模組 | ✅ 已完成 |
| UUID 主鍵（避免 ID 衝突） | ✅ 已完成 |
| company_id 索引（高效匯出） | ✅ 已完成 |
| 支援單一租戶全量抽取 | ✅ 已完成 |
| Fail-fast 驗證 | ✅ 已完成 |

---

## 🔑 關鍵設計決策

### 1. company_id Source of Truth（方案 A + Fail-fast）

**決策：**
- 事件處理器從 payload 取得 company_id（已由 attendance 從 tenant_context 注入）
- Fail-fast：若 payload 缺少或無效，立即拋出 ValueError
- 不重構 EventBus（保持簡單）

**理由：**
- attendance 已經從 tenant_context 注入 company_id 到 payload
- payload.company_id 的來源已驗證（可信任）
- Fail-fast 確保資料完整性

### 2. UUID 主鍵（Python 生成）

**決策：**
- 使用 Python `uuid.uuid4()` 生成 UUID
- 不依賴 PostgreSQL `uuid-ossp` extension

**理由：**
- 避免單一租戶還原時 ID 衝突
- 不需要額外的 PostgreSQL extension
- 跨資料庫相容性更好

### 3. 同步 SQLAlchemy

**決策：**
- 使用同步 SQLAlchemy（不用 async）
- 符合 ENVIRONMENT_LOCK.md 的限制

**理由：**
- 專案規範禁止 async SQLAlchemy
- 同步版本更穩定、更易維護
- 效能足夠（事件處理為背景任務）

### 4. 索引設計

**決策：**
- `idx_notifications_company_id`：單欄索引
- `idx_notifications_company_created`：複合索引（company_id + created_at）

**理由：**
- 支援 Tenant Isolation 查詢（WHERE company_id = ?）
- 支援單一租戶全量抽取（ORDER BY created_at）
- 支援高效備份匯出

---

## 📝 Phase 2 vs Phase 3 對照

| 項目 | Phase 2 | Phase 3 |
|------|---------|---------|
| 資料庫 | ✅ SQLAlchemy + PostgreSQL | ✅ 已完成 |
| Tenant Isolation | ✅ 完整實作 | ✅ 已完成 |
| 事件訂閱 | ✅ attendance.approved | 擴展更多事件 |
| API | ✅ GET /api/notifications | 新增 DELETE、標記已讀 |
| 備份支援 | ✅ 資料模型 + 全量抽取 | 實作備份/還原 API |
| 通知發送 | ❌ 不做 | 實作 email/SMS/push |

---

## ⚠️ 重要提醒

### 資料庫設定

**必須設定 DATABASE_URL：**
```bash
# .env 檔案
DATABASE_URL=postgresql://user:password@localhost:5432/attendance_v2
```

**或環境變數：**
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/attendance_v2"
```

### 資料表建立

應用啟動時會自動建立資料表（`init_db()`）。

**生產環境建議：**
- 使用 Alembic migration（Phase 3 實作）
- 不依賴自動建表

---

## 🎉 總結

Phase 2 已成功完成，並**嚴格遵守 SA_MODULE_SPEC v1.7 的所有 P0 規則**：

✅ Tenant Isolation 機制完整實作  
✅ 事件驅動架構正確運作  
✅ 支援單一租戶備份需求  
✅ UUID 主鍵避免 ID 衝突  
✅ Fail-fast 驗證確保資料完整性  
✅ 模組結構完全符合規範  
✅ 測試套件完整且通過  
✅ 文件清晰完整  

**可以安全進入 Phase 3！**

---

## 📚 相關文件

- `backend/app/modules/notifications/docs.md` - 完整模組文件
- `docs/SA_MODULE_SPECV1.7.md` - 規範文件
- `docs/Cursor任務模板.txt` - 任務模板
- `backend/app/modules/attendance/docs.md` - Attendance 模組文件
