# WP-09-05 Phase 1 完成報告

## 執行時間
- 開始：2026-03-02 22:40
- 完成：2026-03-02 23:05
- 耗時：約 25 分鐘

## 完成項目

### ✅ Notifications 模組（100% 完成）

#### 修復內容

1. **JSONB/SQLite 相容性問題**
   - **Root Cause**: PostgreSQL JSONB type 無法在 SQLite 測試中使用
   - **Solution**: 
     - 在 `app/core/database.py` 創建 `JSONB` TypeDecorator
     - 自動處理 PostgreSQL (native JSONB) 和 SQLite (TEXT + JSON serialization)
     - 修改 `app/modules/notifications/models.py` 使用新的 JSONB type
   - **Files Changed**:
     - `backend/app/core/database.py` (新增 JSONB class)
     - `backend/app/modules/notifications/models.py` (import from database)

2. **Tenant Seeds 缺失**
   - **Root Cause**: 測試使用假 company_id 但未在 DB 中建立對應 tenant
   - **Solution**:
     - 在 `conftest.py` 補充所有測試需要的 tenants
     - PostgreSQL 中手動創建大寫 tenants (company-A, company-B, company-from-payload)
   - **Files Changed**:
     - `backend/app/modules/notifications/tests/conftest.py`

3. **Event Handlers DB Session 問題**
   - **Root Cause**: event_handlers 使用 production SessionLocal，測試無法注入 test_db
   - **Solution**:
     - 修改 `handle_attendance_approved()` 支援可選的 `db` 參數
     - 測試時注入 test_db，production 時使用 SessionLocal
   - **Files Changed**:
     - `backend/app/modules/notifications/event_handlers.py`
     - `backend/app/modules/notifications/tests/test_event_handlers.py`

4. **API 測試資料庫不一致**
   - **Root Cause**: API 測試使用 TestClient (PostgreSQL)，但資料寫入 SQLite
   - **Solution**:
     - 修改 API 測試使用 `get_db()` 直接寫入 PostgreSQL
     - 在 `setup_test_tenant_for_api` fixture 中清理資料確保隔離
   - **Files Changed**:
     - `backend/app/modules/notifications/tests/conftest.py`
     - `backend/app/modules/notifications/tests/test_tenant_isolation.py`

5. **FastAPI 驗證錯誤碼**
   - **Root Cause**: 測試預期 400，但 FastAPI Header(...) 缺失時返回 422
   - **Solution**: 修改測試預期為 422（符合 FastAPI 標準）
   - **Files Changed**:
     - `backend/app/modules/notifications/tests/test_tenant_isolation.py`

#### 測試結果

```bash
pytest backend/app/modules/notifications/tests/ -v
```

**結果**: `19 passed, 1 skipped, 3 warnings in 1.23s` ✅

**詳細**:
- test_api.py: 6 passed, 1 skipped
- test_event_handlers.py: 6 passed
- test_tenant_isolation.py: 7 passed

#### Commits

1. `8150e30` - fix(notifications): tenant seed + db injection + PostgreSQL for API tests (WP-09-05)
2. `82a7ed1` - feat(backup): add conftest with tenant seeds (WP-09-05 partial)

---

### ⏳ Backup 模組（50% 完成）

#### 已完成

1. **創建 conftest.py**
   - 添加 tenant seeds
   - 創建 SQLite-compatible models (NotificationSQLite, AttendanceRecordSQLite)
   - 添加 PostgreSQL cleanup fixture

#### 測試結果

```bash
pytest backend/app/modules/backup/tests/ -v
```

**結果**: `11 passed, 11 failed, 3 warnings in 0.40s` ⚠️

**進度**: 從 4 errors + 7 failed 改善為 11 failed（無 error）

#### 待修復

- 11 個 API 測試失敗（類似 notifications 的問題）
- 需要修改測試使用 PostgreSQL 而非 SQLite

---

### ❓ Audit 模組（未開始）

預計需要類似 notifications 的修復。

---

## 技術債務清單

1. **SQLite/PostgreSQL 雙模式測試**
   - Unit tests 使用 SQLite (快速)
   - API tests 使用 PostgreSQL (真實環境)
   - 需要維護兩套 model 定義

2. **Tenant Seeds 管理**
   - 目前手動在 PostgreSQL 創建
   - 建議：創建統一的 test fixtures 管理腳本

3. **JSONB TypeDecorator**
   - 目前只處理基本 JSON serialization
   - 未來可能需要處理更複雜的 JSONB 操作（如 JSONB 查詢）

---

## 下一步行動

### Phase 2: 完成 Backup + Audit

**預估時間**: 20-30 分鐘

**任務清單**:

1. **Backup 模組**
   - [ ] 修改 API 測試使用 PostgreSQL
   - [ ] 修正 tenant validation 錯誤（404 → 預期狀態）
   - [ ] 確保所有 22 個測試通過

2. **Audit 模組**
   - [ ] 創建 conftest.py
   - [ ] 補充 tenant seeds
   - [ ] 修復 JSONB/SQLite 相容性（如需要）
   - [ ] 確保所有測試通過

3. **最終驗證**
   - [ ] 執行所有 regression tests
   - [ ] 更新 GATE_PROGRESS_TRACKER.md
   - [ ] 標記 WP-09-05 為 ✅ Complete

---

## 學到的經驗

1. **測試資料庫策略很重要**
   - Unit tests: SQLite (快速、隔離)
   - Integration/API tests: PostgreSQL (真實環境)
   - 需要明確區分並正確設置

2. **Tenant Isolation 測試需要完整 setup**
   - 不只是測試資料，tenant 本身也要存在
   - PostgreSQL 和 SQLite 都需要 seeds

3. **FastAPI 的驗證行為**
   - Header(...) 缺失 → 422 (Unprocessable Entity)
   - 自定義驗證 → 可返回 400
   - 測試需要符合框架標準

4. **TypeDecorator 是處理 DB 差異的好工具**
   - 一次定義，兩邊適用
   - 不影響 production 行為

---

## 附錄：關鍵程式碼片段

### JSONB TypeDecorator

```python
class JSONB(TypeDecorator):
    """SQLite-compatible JSONB type"""
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_JSONB())
        else:
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        return json.loads(value)
```

### Event Handler DB Injection

```python
def handle_attendance_approved(payload: Dict[str, Any], db: Optional[Session] = None) -> None:
    db_provided = db is not None
    if not db_provided:
        db = SessionLocal()
    
    try:
        # ... business logic ...
    finally:
        if not db_provided:
            db.close()
```

---

**報告產生時間**: 2026-03-02 23:05  
**狀態**: Phase 1 Complete, Ready for Phase 2
