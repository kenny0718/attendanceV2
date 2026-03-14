# WP-C1-09 Completion Note

**WP ID：** WP-C1-09  
**名稱：** OUT Checkpoint API 實作  
**完成日期：** 2026-03-12  
**狀態：** DONE  
**負責人：** AI session (Cursor)

---

## 驗證結果

### Router Import 驗證
```
from app.modules.attendance.api import router_v1
routes: [..., '/api/v1/attendance/out-checkpoint', '/api/v1/attendance/out-checkpoints']
```
✅ 兩個端點均已正確註冊

### 測試結果
```
app/modules/attendance/tests/test_out_checkpoint.py
  TestOutCheckpointMultiSubmit::test_multi_checkpoint_allowed         PASSED
  TestOutCheckpointGPSValidation::test_mobile_requires_gps           PASSED
  TestOutCheckpointGPSValidation::test_pc_no_gps_allowed             PASSED
  TestOutCheckpointDedup::test_anti_spam_duplicate_checkpoint        PASSED
  TestOutCheckpointGPSCoordinates::test_invalid_latitude             PASSED
  TestOutCheckpointList::test_list_checkpoints_pagination            PASSED
  TestOutCheckpointWithoutSession::test_checkpoint_without_session   PASSED

7 passed in 12.71s
```

### 核心測試套件
```
63 passed（test_api, test_policy_engine, test_regression,
            test_break_out_enforcement, test_model_constraints,
            test_out_checkpoint）
```

---

## 修改檔案清單

### 核心實作
| 檔案 | 修改內容 |
|------|----------|
| `backend/app/modules/attendance/repo.py` | 新增 `OutCheckpointRepository`（5 個方法）、`get_out_checkpoint_repository()` factory、`get_current_time()` utility |
| `backend/app/modules/attendance/api.py` | 新增 `POST /out-checkpoint`、`GET /out-checkpoints`；完整 JWT Actor 遷移 |

### 必要測試基礎修復
| 檔案 | 修改內容 | 必要原因 |
|------|----------|----------|
| `backend/app/conftest.py` | 新增 `AttendanceOutCheckpoint` 等 model imports | `create_all()` 需要 model 先被 import 才能建立對應 table |
| `backend/app/conftest.py` | `drop_all`/`create_all` 加入 `checkfirst=True` | 修正跨測試 DB state 競爭，防止 `UndefinedTable` 錯誤 |

### 未動到
- `schemas.py`：未修改
- `models.py`：未修改
- `alembic/`：未修改
- frontend：未修改
- 其他 module：未修改

---

## 為什麼 conftest.py 必須修改

**修改 A（model imports）：**  
`conftest.py` 用 `Base.metadata.create_all()` 建立測試 DB schema。  
`create_all()` 只建立已被 import 的 model 對應 table。  
`AttendanceOutCheckpoint` 未在任何 import chain 上時，`attendance_out_checkpoints` table 不被建立。  
**若不改，失敗點：** `test_list_checkpoints_pagination` → `sqlalchemy.exc.ProgrammingError: relation "attendance_out_checkpoints" does not exist`

**修改 B（checkfirst=True）：**  
7 個 function-scope fixture 在每個測試前呼叫 `drop_all`。  
第 N 個測試的 `drop_all` 清除 table 後，第 N+1 個測試再次 `drop_all` 找不到 table。  
**若不改，失敗點：** `TestOutCheckpointWithoutSession` → `sqlalchemy.exc.ProgrammingError: table "attendance_out_checkpoints" does not exist` at DROP TABLE

---

## 已知非阻塞 Warnings

| Warning | 來源 | 類型 | 是否本票引入 |
|---------|------|------|-------------|
| `PydanticDeprecatedSince20`: `class Config` 用法 | `schemas.py` | 技術債 | ❌ 既有 |
| `PydanticDeprecatedSince20`: `@validator` 用法 | `schemas.py` | 技術債 | ❌ 既有 |
| `DeprecationWarning`: `app.on_event("startup")` | `main.py` | 技術債 | ❌ 既有 |

所有 warnings 均為既有技術債，不影響功能，不影響本票驗收。

---

## 端點規格

### POST /api/v1/attendance/out-checkpoint
- **Auth：** JWT Bearer（`get_actor_with_company`）
- **Request：** `OutCheckpointRequest`（device_type, gps?, client_timezone?, notes?）
- **Business Rules：**
  - `device_type == mobile` 且無 GPS → 422 `GPS_REQUIRED`
  - 30 秒內同一用戶同一位置（50m 內）重複打卡 → 409 `DUPLICATE_CHECKPOINT`
  - 不需要 open session（session_id 為 null 時仍允許）
  - punch_time 由 server 設定（UTC）
- **Response 201：** `{checkpoint_id, punch_time, gps, message}`

### GET /api/v1/attendance/out-checkpoints
- **Auth：** JWT Bearer
- **Query params：** `limit`（1-100，預設 50）、`offset`（預設 0）
- **Response 200：** `{checkpoints: [...], total, limit, offset}`
- **Tenant Isolation：** 強制 WHERE company_id = actor.active_company_id

---

## 下一步

**建議下一張票：WP-C1-03**  
auit / notifications / backup 三個模組的 Header auth → JWT Actor 遷移（P0 安全性）
