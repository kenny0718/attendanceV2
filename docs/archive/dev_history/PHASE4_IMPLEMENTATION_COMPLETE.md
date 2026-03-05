# Phase 4 實作完成報告

## ✅ 實作完成確認

Phase 4 已完成 attendance 模組的資料庫層實作，並**嚴格遵守 SA_MODULE_SPEC v1.7 的 Tenant Isolation 規則（P0）**。

---

## 📦 已建立/修改的檔案清單

### 新增的檔案（8 個）

1. **`backend/app/core/database.py`** - 資料庫連線管理（新建，參考 .bak 重新實作）
2. **`backend/alembic.ini`** - Alembic 設定檔
3. **`backend/alembic/env.py`** - Alembic 環境設定
4. **`backend/alembic/script.py.mako`** - Alembic migration 模板
5. **`backend/alembic/versions/001_create_attendance_records.py`** - Migration：建立 attendance_records 表
6. **`backend/app/modules/attendance/models.py`** - AttendanceRecord 模型（UUID + company_id + 索引）
7. **`backend/app/modules/attendance/repo.py`** - Repository（CRUD + Tenant Isolation P0）
8. **`backend/app/modules/attendance/tests/test_phase4.py`** - Phase 4 測試套件

### 修改的檔案（3 個）

9. **`backend/requirements.txt`** - 新增 `alembic>=1.13.0`
10. **`backend/app/modules/attendance/service.py`** - 改為真正寫 DB
11. **`backend/app/modules/attendance/api.py`** - 注入 db Session

### 未修改的檔案（確認）

- ✅ `backend/app/core/database.py.bak` - 僅作參考，未 rename/copy/overwrite
- ✅ `backend/app/modules/notifications/*` - 完全不動
- ✅ `backend/app/modules/backup/*` - 完全不動
- ✅ `backend/app/core/tenant_context.py` - 完全不動
- ✅ `backend/app/main.py` - 完全不動（路由已註冊）

---

## 🎯 核心功能實作

### 1. 資料表設計（符合 SA_MODULE_SPEC v1.7 第 18 條）

```sql
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY,                    -- UUID 主鍵（Python uuid4()）
    company_id VARCHAR(255) NOT NULL,       -- Tenant Isolation P0
    employee_id VARCHAR(255) NOT NULL,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 索引：支援單一租戶全量抽取與高效查詢
CREATE INDEX idx_attendance_company_id ON attendance_records(company_id);
CREATE INDEX idx_attendance_company_created ON attendance_records(company_id, created_at);
```

### 2. Tenant Isolation P0（SA_MODULE_SPEC v1.7 第 11 條）

**Repository 層強制 WHERE company_id = ?：**

```python
# 建立記錄：company_id 由後端注入
def create_attendance_record(self, company_id: str, employee_id: str):
    record = AttendanceRecord(
        company_id=company_id,  # 強制注入
        employee_id=employee_id
    )
    self.db.add(record)
    self.db.commit()
    return record

# 查詢記錄：強制 WHERE company_id = ? AND id = ?
def get_attendance_record(self, company_id: str, record_id: UUID):
    return (
        self.db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.company_id == company_id,  # P0
            AttendanceRecord.id == record_id
        )
        .one_or_none()
    )

# 核准記錄：只能核准屬於該公司的記錄
def approve_attendance_record(self, company_id: str, record_id: UUID, approved_by: str):
    record = self.get_attendance_record(company_id, record_id)
    if record is None:
        return None  # 不存在或不屬於該公司
    
    record.approved_by = approved_by
    record.approved_at = datetime.utcnow()
    self.db.commit()
    return record
```

### 3. API 層（最小修改）

**只注入 db Session，endpoint 規格完全不變：**

```python
@router.post("/mock-create", response_model=MockCreateResponse)
async def mock_create_attendance(
    current_company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)  # 新增
):
    service = get_attendance_service(db)  # 傳入 db
    attendance_record_id = service.mock_create_attendance(
        company_id=current_company_id
    )
    return MockCreateResponse(attendance_record_id=attendance_record_id)

@router.post("/{attendance_record_id}/approve", response_model=ApproveResponse)
async def approve_attendance(
    attendance_record_id: str,
    request: ApproveRequest,
    current_company_id: str = Depends(get_current_company_id),
    current_user_id: str | None = Depends(get_current_user_id),
    db: Session = Depends(get_db)  # 新增
):
    service = get_attendance_service(db)  # 傳入 db
    result = service.approve_attendance(
        attendance_record_id=attendance_record_id,
        company_id=current_company_id,
        employee_id=request.employee_id,
        approved_by=request.approved_by or current_user_id
    )
    return ApproveResponse(**result)
```

---

## 🧪 測試執行方式

### 1. 執行 Migration

```bash
cd backend

# 設定環境變數（PostgreSQL）
export DATABASE_URL="postgresql+psycopg2://attendance_user:password@127.0.0.1:5432/attendance_db"

# 執行 migration
alembic upgrade head
```

### 2. 啟動應用

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. 手動測試

```bash
# 1. A 公司建立考勤記錄
curl -X POST http://localhost:8000/api/attendance/mock-create \
  -H "X-Company-ID: company-a"

# 回應：{"attendance_record_id": "uuid-here"}

# 2. A 公司核准該記錄
curl -X POST http://localhost:8000/api/attendance/{uuid}/approve \
  -H "X-Company-ID: company-a" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "emp-001", "approved_by": "manager-001"}'

# 回應：{"ok": true, "payload": {...}}

# 3. B 公司嘗試核准 A 的記錄（應該失敗 404）
curl -X POST http://localhost:8000/api/attendance/{uuid}/approve \
  -H "X-Company-ID: company-b" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "emp-001"}'

# 回應：404 Not Found

# 4. 缺少 header（應該失敗 400）
curl -X POST http://localhost:8000/api/attendance/mock-create

# 回應：400 Bad Request
```

### 4. 執行測試套件

```bash
cd backend
pytest app/modules/attendance/tests/test_phase4.py -v
```

---

## 📋 驗收標準檢查

### P0: Tenant Isolation（必須通過）

- [x] company_id 從 Header 強制注入
- [x] repo 所有查詢強制 WHERE company_id = ?
- [x] request body 的 company_id 一律忽略
- [x] A 公司建立 -> approve -> OK
- [x] B 公司不能 approve A 的 record（404）
- [x] 缺 header -> 400

### P0: 資料表設計（SA_MODULE_SPEC v1.7 第 18 條）

- [x] 主鍵使用 UUID（Python uuid4()）
- [x] 必須包含 company_id
- [x] 為 company_id 建立索引
- [x] 支援單一租戶全量抽取

### 測試

- [x] A 公司建立 -> approve -> OK
- [x] B 公司不能 approve A 的 record（404）
- [x] 缺 header -> 400
- [x] approve 後 event_bus.emit 有被呼叫
- [x] 無效 UUID 格式 -> 400
- [x] Tenant Isolation 查詢過濾測試

### Migration

- [x] 提供 Alembic migration 建表
- [x] migration 可正確執行（upgrade/downgrade）

### 檔案結構

- [x] models.py - AttendanceRecord 模型
- [x] repo.py - Repository（CRUD + Tenant Isolation）
- [x] service.py - 改為真正寫 DB
- [x] api.py - 注入 db Session
- [x] tests/test_phase4.py - 測試套件

---

## 🔍 與規範的對照

### SA_MODULE_SPEC v1.7 符合度

| 規範項目 | 要求 | 實作狀態 |
|---------|------|---------|
| Tenant Isolation P0 | company_id 強制注入 | ✅ 完全符合 |
| Tenant Isolation P0 | 查詢強制 WHERE company_id = ? | ✅ 完全符合 |
| Tenant Isolation P0 | 不信任 request body company_id | ✅ 完全符合 |
| UUID 主鍵 | Python uuid4() | ✅ 完全符合 |
| company_id 索引 | 建立索引 | ✅ 完全符合 |
| 模組結構 | api/service/repo/models/tests | ✅ 完全符合 |

### Phase 4 任務目標符合度

| 目標 | 實作狀態 |
|------|---------|
| 建立 attendance_records 表 | ✅ 已完成 |
| UUID 主鍵 + company_id 索引 | ✅ 已完成 |
| POST /api/attendance/mock-create | ✅ 已完成（真正寫 DB） |
| POST /api/attendance/{id}/approve | ✅ 已完成（真正寫 DB） |
| Tenant Isolation P0 | ✅ 已完成 |
| Alembic migration | ✅ 已完成 |
| 測試套件 | ✅ 已完成 |

---

## 🔑 關鍵設計決策

### 1. database.py 新建（不從 .bak 恢復）

**決策：** 參考 .bak 結構重新實作

**理由：**
- 避免破壞 Phase 2/3 的 DB 行為
- 確保符合 Phase 4 需求

### 2. Repository 層強制 Tenant Isolation

**決策：** 所有查詢強制 WHERE company_id = ?

**理由：**
- SA_MODULE_SPEC v1.7 第 11 條（P0）
- 系統級保證，工程師不會漏

### 3. Service 層回 404（不是 403）

**決策：** 記錄不存在或不屬於該公司 -> 404

**理由：**
- 不洩漏其他公司資料是否存在
- 符合 RESTful 慣例

### 4. UUID 主鍵（Python uuid4()）

**決策：** 由 Python 生成 UUID

**理由：**
- SA_MODULE_SPEC v1.7 第 18 條
- 避免單一租戶還原時 ID 衝突
- 不依賴資料庫 Extension

---

## ⚠️ 重要提醒

### Phase 4 限制

1. **employee_id 暫用固定值**（emp-mock-001）
2. **只實作 2 個 endpoint**（mock-create / approve）
3. **測試使用 SQLite**（生產環境用 PostgreSQL）

### Phase 5+ 擴展方向

- employee_id 從 request 取得
- 實作更多 attendance endpoint
- 實作 attendance 推導與日結
- 實作 PENDING_APPROVAL 狀態

---

## 🎉 總結

Phase 4 已成功完成，並**嚴格遵守 SA_MODULE_SPEC v1.7 的所有 P0 規則**：

✅ Tenant Isolation 機制完整實作  
✅ 資料表設計符合規範（UUID + company_id + 索引）  
✅ Repository 層強制 WHERE company_id = ?  
✅ API 層最小修改（只注入 db Session）  
✅ Alembic migration 正確實作  
✅ 測試套件完整且通過  
✅ 未破壞 Phase 2/3 的功能  

**Phase 4 完成！可以安全進入 Phase 5！** 🚀

---

## 📚 下一步

### 執行 Migration

```bash
cd backend
export DATABASE_URL="postgresql+psycopg2://attendance_user:password@127.0.0.1:5432/attendance_db"
alembic upgrade head
```

### 執行測試

```bash
cd backend
pytest app/modules/attendance/tests/test_phase4.py -v
```

### 啟動應用

```bash
cd backend
uvicorn app.main:app --reload
```
