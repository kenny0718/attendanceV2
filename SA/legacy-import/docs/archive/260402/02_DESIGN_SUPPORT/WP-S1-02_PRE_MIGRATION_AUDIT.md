# WP-S1-02 Pre-Migration Audit Report

**審計票號:** WP-S1-02 Pre-Migration Audit  
**審計日期:** 2026-03-18  
**審計人:** AI session (Cursor)  
**審計性質:** 唯讀靜態審計，不修改任何檔案  
**依據:** WP-S1-01 COMPLETE；進入 WP-S1-02 前的 gate check

---

## 1. Objective

確認 Schedule 模組在進入 migration（WP-S1-02）前，Alembic chain、ORM 模型、env.py metadata 是否安全就緒，避免以下風險：

- Alembic chain 斷裂或多 head
- env.py / metadata import 不完整導致 autogenerate 遺漏
- ORM 欄位型別與現有系統不相容
- FK 指向型別不一致（company_id / user_id）
- schedule router 意外掛入主 app

---

## 2. Files Read

| 檔案 | 說明 |
|------|------|
| `backend/alembic/env.py` | Alembic 環境設定 |
| `backend/alembic/versions/001b_*` | Migration chain 審查 |
| `backend/alembic/versions/002_*` | Migration chain 審查 |
| `backend/alembic/versions/003_*` | Migration chain 審查 |
| `backend/alembic/versions/004_create_tenants.py` | tenants.id 型別確認（String(50) PK）|
| `backend/alembic/versions/005_*` | Migration chain 審查 |
| `backend/alembic/versions/006_*` | Migration chain 審查 |
| `backend/alembic/versions/007_wp_11_10_*` | user_id/company_id 型別確認 |
| `backend/alembic/versions/008_wp_11_13_*` | Migration chain 審查 |
| `backend/alembic/versions/009_wp_11_08_*` | Current head 確認；company_id 型別確認 |
| `backend/alembic/versions/3532deda024c_*` | Migration chain 審查（auth tables）|
| `backend/alembic/versions/wp_11_04a_entitlements.py` | Migration chain 審查 |
| `backend/app/main.py` | Router 掛載狀況確認 |
| `backend/app/modules/schedule/models.py` | ORM 模型審查 |
| `backend/app/modules/schedule/__init__.py` | 副作用 import 審查 |
| `backend/app/core/database.py` | Base 來源確認 |
| `docs/03_WP_CONTROL/NEXT_WP_TICKET.md` | 治理文件一致性 |
| `docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md` | 治理文件一致性 |
| `docs/02_DEVELOPMENT_STATUS/WORKSTREAM_STATUS_LEDGER.md` | 治理文件一致性 |
| `docs/02_DEVELOPMENT_STATUS/MODULE_STATUS_MATRIX.md` | 治理文件一致性 |
| `docs/02_DEVELOPMENT_STATUS/CURRENT_SYSTEM_STATE.md` | 治理文件一致性 |

---

## 3. Alembic Chain Audit

### 3.1 Migration Chain 重建

```
004 (tenants)
  └── 3532deda024c (auth tables)
        └── 005 (notifications)
              └── 002 (audit_logs)
                    └── 003 (audit_retention_policies)
                          └── 001b (attendance domain v2)
                                └── wp_11_04a_entitlements
                                      └── 006 (expand session status)
                                            └── 007_wp_11_10 (out_checkpoints)
                                                  └── 008_wp_11_13 (allowed_locations)
                                                        └── 009_wp_11_08 (leave tables) ← CURRENT HEAD
```

### 3.2 Chain 健康狀況

| 項目 | 結果 |
|------|------|
| Head 數量 | **1 個**（唯一 head = `009_wp_11_08`）|
| 多 head / 分叉 | **無** |
| Branch / merge 風險 | **無** |
| `.deprecated` 檔案 | 有 `001_create_attendance_domain_v2.py.deprecated`，Alembic 不讀取（副檔名過濾），不影響 chain |
| schedule 相關既有 migration | **無**（009 內容確認不含 shift/schedule 字樣）|
| `shift_templates` / `shift_assignments` 殘留 | **無** |

### 3.3 命名規則觀察

現有命名混用多種風格：

| 風格 | 範例 |
|------|------|
| 短數字 ID | `001b`、`002`、`003`、`004`、`005`、`006` |
| 數字 + WP 後綴 | `007_wp_11_10`、`008_wp_11_13`、`009_wp_11_08` |
| Hash ID | `3532deda024c`（自動生成）|
| 無數字前綴 | `wp_11_04a_entitlements` |

**建議下一個 migration：**
- revision ID：`010_wp_s1_02`
- 檔名：`010_wp_s1_02_create_schedule_tables.py`
- down_revision：`009_wp_11_08`

### 3.4 Chain Verdict

**SAFE** — Chain 唯一、無分叉、無殘留 schedule migration。  
可安全新增 `010_wp_s1_02_create_schedule_tables.py`，`down_revision = '009_wp_11_08'`。

---

## 4. env.py / Metadata Registration Audit

### 4.1 env.py 目前 import 清單

```python
# env.py 目前只 import 以下 models：
from app.modules.notifications.models import Notification
from app.modules.attendance.models import AttendanceRecord
from app.modules.leave.models import (
    LeaveType, LeaveApprovalPolicy, LeaveRequest, LeaveApprovalLog,
)
```

### 4.2 Schedule Models 是否在 env.py 中

**否。** `env.py` **未 import** `ShiftTemplate` 或 `ShiftAssignment`。

### 4.3 影響評估

| 場景 | 影響 |
|------|------|
| 手動撰寫 migration（`op.create_table()`）| **無影響**：不依賴 metadata |
| `alembic revision --autogenerate` | **會遺漏** shift_templates / shift_assignments |
| `alembic upgrade head`（執行已寫好的 migration）| **無影響** |

### 4.4 專案慣例觀察

env.py 也未 import auth、tenants、audit、backup、customer_service 等模組 models，顯示本專案慣例為**手動撰寫 migration**，不依賴 autogenerate。

### 4.5 env.py Verdict

**MINOR RISK（非 blocking，若採用手動撰寫 migration）**

若 WP-S1-02 採用手動撰寫 migration（與現有 007/008/009 一致），env.py 不補 import 不阻塞。  
但建議在 WP-S1-02 內一併補上以確保未來 autogenerate 可用：
```python
from app.modules.schedule.models import ShiftTemplate, ShiftAssignment
```

---

## 5. Schedule ORM Model Audit

### 5.1 BLOCKING RISK 1：company_id 型別不相容

**嚴重程度：BLOCKING**

| 項目 | Schedule Models（現況）| 全系統慣例 |
|------|----------------------|----------|
| `company_id` 型別 | `Column(Integer, ...)` | `Column(String(255), ...)` |
| FK 指向 | 無 FK constraint | `ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE')` |
| `tenants.id` 型別 | — | `String(50)` Primary Key |

**驗證來源：**
- `004_create_tenants.py`：`sa.Column('id', sa.String(50), primary_key=True)`
- `001b_create_attendance_domain_v2_fixed.py`：`company_id = sa.Column('company_id', sa.String(255), ...)`
- `007_wp_11_10_create_out_checkpoints.py`：`sa.Column('company_id', sa.String(255), ...)`
- `009_wp_11_08_create_leave_tables.py`：`sa.Column('company_id', sa.String(255), ...)`

**影響：**
1. 若依目前 models.py 建立 migration，`company_id INTEGER` 會與 `tenants.id VARCHAR(50)` 型別不符，FK constraint 建立失敗
2. 即使跳過 FK，Integer 型別無法存放現有系統的 String company_id（如 `"company-abc-123"`）
3. Tenant isolation 語意破壞

**必須修正：** `company_id = Column(String(255), nullable=False, index=True)` + 加入 FK constraint

---

### 5.2 BLOCKING RISK 2：user_id 型別不相容

**嚴重程度：BLOCKING**

| 項目 | Schedule Models（現況）| 全系統慣例 |
|------|----------------------|----------|
| `user_id` 型別 | `Column(Integer, ...)` | `Column(UUID(as_uuid=True), ...)` |
| FK 指向 | 無 FK constraint | `ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')` |
| `users.id` 型別 | — | `UUID` Primary Key（見 3532deda024c auth migration）|

**驗證來源：**
- `007_wp_11_10_create_out_checkpoints.py`：`sa.Column('user_id', postgresql.UUID(as_uuid=True), ...)` + FK to `users.id`
- `009_wp_11_08_create_leave_tables.py`：`sa.Column('user_id', UUID(as_uuid=True), ...)` + FK to `users.id`
- `001b_*`：`user_id = Column(PGUUID(as_uuid=True), ...)`

**影響：**
1. FK constraint 建立失敗（Integer vs UUID 型別不符）
2. 無法 JOIN 現有 users 表
3. 未來 attendance 整合時 session lookup 失敗

**必須修正：** `user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)` + 加入 FK constraint

---

### 5.3 MINOR RISK：shift_template_id FK 使用行內 ForeignKey

**嚴重程度：MINOR（不阻塞 migration，但與慣例不一致）**

| 項目 | Schedule Models（現況）| 全系統慣例 |
|------|----------------------|----------|
| FK 定義方式 | 行內 `ForeignKey("shift_templates.id", ondelete="RESTRICT")` | `__table_args__` 中使用 `ForeignKeyConstraint([...], [...])` |

行內 ForeignKey 功能上可運作，但與 001b/007/008/009 的 `ForeignKeyConstraint` 慣例不一致。建議統一，但不阻塞 migration。

---

### 5.4 MINOR RISK：ShiftTemplate.id / ShiftAssignment.id 使用 Integer 而非 UUID

**嚴重程度：MINOR（設計選擇，不阻塞）**

| 項目 | Schedule Models | 全系統慣例 |
|------|----------------|----------|
| PK 型別 | `Integer` autoincrement | `UUID(as_uuid=True)` + `gen_random_uuid()` |

全系統所有既有表均使用 UUID PK。Schedule 使用 Integer 功能上可運作，但：
1. 與全系統 PK 設計慣例不一致
2. 跨 tenant 備份還原時可能發生 ID 衝突。建議統一使用 UUID，但若團隊決定 Integer 也可接受，需在 WP-S1-02 明確記錄設計決策。

---

### 5.5 SAFE：work_date 欄位

**Date** 型別，符合排班日期語意，無風險。

---

### 5.6 SAFE：start_time / end_time 欄位

**Time** 型別，符合班別時間語意。is_overnight flag 為輔助資訊欄位，不涉及跨日計算，無風險。

---

### 5.7 SAFE：break_minutes 欄位

**SmallInteger**，儲存分鐘數，語意清晰，無風險。

---

### 5.8 MINOR RISK：缺少 UniqueConstraint（company_id + code）

**嚴重程度：MINOR（建議但不阻塞）**

ShiftTemplate 的 `code` 欄位語意上應為「同公司內唯一」（如 DAY / NIGHT 不可重複），但 models.py 目前沒有 `UniqueConstraint('company_id', 'code')`。參考 leave_types 的 `uq_leave_types_company_code` 慣例，建議在 WP-S1-02 migration 中加入。

---

### 5.9 MINOR RISK：缺少 UniqueConstraint（company_id + user_id + work_date）

**嚴重程度：MINOR（建議但不阻塞）**

ShiftAssignment 語意上「同一人同一天最多一個排班」，但 models.py 沒有對應 unique constraint。未來業務邏輯若依賴此約束，需在 migration 中加入。目前 WP-S1-02 foundation ticket 可選擇性加入。

---

### 5.10 SAFE：AssignmentStatus Enum 設計

`scheduled / confirmed / cancelled` 三個值，使用 Python `str + enum.Enum`，與 attendance session status 的 String CHECK constraint 慣例略有差異（attendance 使用 String + CheckConstraint，leave 使用 String + CheckConstraint；schedule 使用 SQLAlchemy Enum type）。功能上可運作，但需在 migration 中確認 PostgreSQL Enum type 的建立方式（`CREATE TYPE` 或 `VARCHAR + CHECK`）。不阻塞，但需在 WP-S1-02 記錄選擇。

---

### 5.11 ORM Audit 總結

| 項目 | 嚴重程度 | 說明 |
|------|----------|------|
| company_id 使用 Integer | **BLOCKING** | 全系統為 String(255)，FK 指向 tenants.id String(50) |
| user_id 使用 Integer | **BLOCKING** | 全系統為 UUID，FK 指向 users.id UUID |
| PK 使用 Integer 而非 UUID | MINOR | 設計決策，需明確記錄 |
| shift_template_id FK 用行內 ForeignKey | MINOR | 與慣例不一致，建議改為 ForeignKeyConstraint |
| 缺少 UniqueConstraint (company + code) | MINOR | 建議加入 migration |
| 缺少 UniqueConstraint (company + user + date) | MINOR | 建議評估是否加入 |
| Enum type 選擇 | MINOR | 需在 migration 記錄選擇（SQLAlchemy Enum vs VARCHAR+CHECK）|
| work_date / start_time / end_time | SAFE | 型別合理 |
| break_minutes / is_overnight / is_active | SAFE | 型別合理 |


---

## 6. Router Isolation Audit

### 6.1 main.py 掛載狀況

審查 `backend/app/main.py` 全文，確認 include_router 清單如下：

```
attendance_router
attendance_router_v1
attendance_gate_demo_router
admin_location_router
notifications_router
backup_router
audit_router
auth_router
tenants_router
customer_service_router
leave_router_v1
```

**schedule router：未出現在 main.py。**

### 6.2 schedule/__init__.py 副作用審查

`__init__.py` 內容為純 docstring，無任何 import 語句，無任何副作用。

### 6.3 Router Isolation Verdict

**SAFE** — schedule router 未掛入主 app，不影響任何現有路由。`__init__.py` 無副作用 import 風險。

---

## 7. Docs Consistency Audit

### 7.1 NEXT_WP_TICKET.md

| 項目 | 狀態 | 說明 |
|------|------|------|
| WP-S1-01 標示為 COMPLETE | OK | 文件末段已追加 WP-S1-01 COMPLETE 記錄 |
| WP-S1-02 標示為下一票 | OK | 文件末段已標示 WP-S1-02 PENDING |
| Gate 6 啟動記錄 | OK | 已記錄 Gate 6 IN_PROGRESS |

### 7.2 GATE_PROGRESS_TRACKER.md

| 項目 | 狀態 | 說明 |
|------|------|------|
| Gate 5 / C1 CLOSED 記錄 | OK | 已記錄 |
| Gate 6 啟動記錄 | OK | 已追加 Gate 6 WP 完成狀態表 |
| WP-S1-01 COMPLETE | OK | 已記錄 |

### 7.3 CURRENT_SYSTEM_STATE.md

| 項目 | 狀態 | 說明 |
|------|------|------|
| Current WP 更新 | OK | 已更新至 WP-S1-02 PENDING |
| Schedule 模組現況描述 | OK | 已標明無資料表、無 API endpoint |

### 7.4 MODULE_STATUS_MATRIX.md

| 項目 | 狀態 | 說明 |
|------|------|------|
| schedule 模組新增 | OK | 已標記 FOUNDATION，完成度 5% |
| migration: NOT_STARTED | OK | 正確 |
| tests: NOT_STARTED | OK | 正確 |

### 7.5 schedule/docs.md 內容一致性

| 項目 | 狀態 | 說明 |
|------|------|------|
| 明確說明 repo/service 為 stub | OK | Section 2 有明確列出 |
| 明確說明 router 無 endpoint | OK | Section 2 有列出 api.py 骨架 |
| 明確說明未掛主 app | OK | Section 4 明確標注 |
| 明確說明無 migration | OK | Section 4.1 明確標注 |
| 給未來 AI 的說明 | OK | Section 7 有完整說明 |

### 7.6 Docs Consistency Verdict

**CONSISTENT** — 治理文件與 docs.md 內容一致，無矛盾項目。

---

## 8. Risk Summary

### BLOCKING Issues（必須修復後才能進 WP-S1-02）

| # | 問題 | 位置 | 修復方式 |
|---|------|------|----------|
| B1 | `company_id` 型別為 `Integer`，應為 `String(255)` | `schedule/models.py` | 修改 ShiftTemplate 和 ShiftAssignment 的 company_id 欄位型別；加入 FK constraint to tenants.id |
| B2 | `user_id` 型別為 `Integer`，應為 `UUID` | `schedule/models.py` | 修改 ShiftAssignment 的 user_id 欄位型別；加入 FK constraint to users.id |

### MINOR Issues（建議在 WP-S1-02 中一併處理，不阻塞）

| # | 問題 | 位置 | 建議 |
|---|------|------|------|
| M1 | env.py 未 import schedule models | `alembic/env.py` | 補上 import（若需支援 autogenerate）；手動寫 migration 可忽略 |
| M2 | PK 使用 Integer 而非 UUID | `schedule/models.py` | 建議改為 UUID 與系統慣例一致；若決定保留 Integer 需記錄設計決策 |
| M3 | FK 使用行內 ForeignKey 而非 ForeignKeyConstraint | `schedule/models.py` | 建議改為 ForeignKeyConstraint 與慣例一致 |
| M4 | 缺少 UniqueConstraint(company_id, code) 在 ShiftTemplate | `schedule/models.py` / migration | 建議在 migration 中加入 |
| M5 | 缺少 UniqueConstraint(company_id, user_id, work_date) 在 ShiftAssignment | migration | 評估是否需要加入 |
| M6 | AssignmentStatus 使用 SQLAlchemy Enum type（CREATE TYPE）| `schedule/models.py` | 確認是否使用 PostgreSQL native enum 或改為 VARCHAR + CHECK constraint（參考現有慣例）|

---

## 9. Final Verdict

```
╔══════════════════════════════════════════════════╗
║  NOT READY FOR WP-S1-02                         ║
║  2 BLOCKING ISSUES MUST BE RESOLVED FIRST       ║
╚══════════════════════════════════════════════════╝
```

**原因：**

1. **B1: company_id 型別錯誤**（Integer vs String(255)）— 若直接建立 migration，FK constraint 會失敗，migration 無法執行
2. **B2: user_id 型別錯誤**（Integer vs UUID）— 若直接建立 migration，FK constraint 會失敗，migration 無法執行

這兩個問題必須在 **models.py 修正後**，才能安全建立 migration 檔案。

**非 blocking 項目說明：**
- Alembic chain 健康（SAFE）
- Router 未掛入主 app（SAFE）
- 治理文件一致（CONSISTENT）
- env.py 不補 import 也可手動寫 migration（MINOR）

---

## 10. Recommended Next Action

### 步驟順序（在開始 WP-S1-02 之前）

**Step 1：修正 schedule/models.py（必做，blocking）**

建議修正項目（最小可行修正）：

```python
# ShiftTemplate 和 ShiftAssignment 的 company_id
# 修正前：company_id = Column(Integer, nullable=False, index=True)
# 修正後：
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# company_id
company_id = Column(String(255), nullable=False, index=True)

# user_id (ShiftAssignment only)
user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

# 加入 __table_args__ 含 ForeignKeyConstraint
__table_args__ = (
    ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
    # ShiftAssignment 另加：
    ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    # 建議加入：
    UniqueConstraint('company_id', 'code', name='uq_shift_templates_company_code'),  # ShiftTemplate only
)
```

**Step 2：決定 PK 型別（建議 UUID，非強制）**

建議將 ShiftTemplate.id 和 ShiftAssignment.id 改為 UUID，與全系統慣例一致。
若保留 Integer，需在 docs.md 記錄設計決策。

**Step 3：決定 AssignmentStatus enum 實作方式**

建議改為 `String(20) + CheckConstraint`（與 attendance session status 慣例一致），避免 PostgreSQL `CREATE TYPE` 複雜度。
若保留 SQLAlchemy Enum type，需確認 migration 中正確使用 `sa.Enum(..., name='assignmentstatus', create_type=True)`。

**Step 4：建立 WP-S1-02 migration 票**

修正 models.py 後，即可執行 WP-S1-02：
- 建立 `010_wp_s1_02_create_schedule_tables.py`
- `revision = '010_wp_s1_02'`
- `down_revision = '009_wp_11_08'`
- 手動撰寫 `op.create_table('shift_templates', ...)` 和 `op.create_table('shift_assignments', ...)`
- 在 env.py 補上 schedule models import
- 執行 `alembic upgrade head` 驗證

### 修正優先序

```
[MUST] B1: company_id Integer → String(255) + FK to tenants.id
[MUST] B2: user_id Integer → UUID + FK to users.id
[RECOMMEND] M2: PK Integer → UUID
[RECOMMEND] M3: 行內 FK → ForeignKeyConstraint
[RECOMMEND] M4: 加入 UniqueConstraint(company_id, code)
[OPTIONAL] M5: 加入 UniqueConstraint(company_id, user_id, work_date)
[DECIDE] M6: AssignmentStatus enum 實作方式
[WP-S1-02] M1: env.py 補 import（migration 票內處理）
```

---

**審計結論：NOT READY FOR WP-S1-02**  
**Blocking Issues：2（B1 company_id 型別、B2 user_id 型別）**  
**建議下一步：先修正 schedule/models.py，再開始 WP-S1-02**  
**報告版本：v1.0**  
**建立日期：2026-03-18**
