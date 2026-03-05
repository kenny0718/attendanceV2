# 考勤系統（Attendance System V2）開發進度與順序追蹤

**建立日期：** 2026-03-02  
**最後更新：** 2026-03-02  
**系統架構：** Multi-tenant SaaS Backend（同庫同表 + company_id 隔離）  
**技術堆疊：** Python 3.11 + FastAPI + SQLAlchemy（同步）+ PostgreSQL 15 + Alembic  
**環境：** Debian 12 (LXC) + venv

---

## 📊 開發階段總覽

| 階段 | 名稱 | 狀態 | 完成日期 | Git Commit |
|------|------|------|----------|------------|
| Phase 0 | 後端骨架初始化 | ✅ 已完成 | 2026-01-13 | `8797f60` |
| Phase 1 | Attendance 最小模組 + EventBus + Tenant Context | ✅ 已完成 | 2026-01-14 | `81eeadf` |
| Phase 2 | Notifications 模組 + DB 層（SQLAlchemy + PostgreSQL） | ✅ 已完成 | 2026-01-14 | `65a7b37` |
| Phase 3 | Backup 模組（單一租戶匯出/還原） | ✅ 已完成 | 2026-01-14 | `8bdfd73` |
| Phase 4 | Attendance DB 層實作（models + repo + Alembic） | ✅ 已完成 | 2026-01-25 | `6fc7ffe` |
| Phase 5 | Backup Restore UPSERT + Tenant Isolation 強化 | ✅ 已完成 | 2026-01-27 | `fd7c6a5` |
| Phase 6C | Backup Audit Log（稽核紀錄） | ✅ 已完成 | 2026-01-27 | `cf52aef` |
| Phase 7 | Audit Log 查詢 + 匯出 API（JSON/CSV） | ✅ 已完成 | 2026-01-28 | `a568029` |
| Phase 8 | Audit Retention Policy + Purge 機制 | ✅ 已完成 | 2026-01-28 | `a568029`（同 commit） |

---

## ✅ 各階段詳細內容

### Phase 0 — 後端骨架初始化（2026-01-13）

**目標：** 建立專案骨架，包含核心架構

**已完成項目：**
- [x] FastAPI 應用框架 (`backend/app/main.py`)
- [x] 核心設定 (`backend/app/core/config.py`)
- [x] EventBus 事件匯流排 (`backend/app/core/event_bus.py`)
- [x] 健康檢查端點 `GET /health`
- [x] 測試事件端點 `GET/POST /api/test/event`
- [x] 規範文件 SA_MODULE_SPEC v1.6 → v1.7
- [x] 環境鎖定文件 `ENVIRONMENT_LOCK.md`
- [x] Cursor 任務模板

**產出檔案：**
```
backend/app/core/__init__.py
backend/app/core/config.py
backend/app/core/event_bus.py
backend/app/main.py
docs/SA_MODULE_SPECV1.7.md
docs/ENVIRONMENT_LOCK.md
docs/Cursor任務模板.txt
requirements.txt
```

---

### Phase 1 — Attendance 最小模組 + Tenant Context（2026-01-14）

**目標：** 建立 attendance 模組骨架，實作 EventBus 事件觸發，建立 Tenant Isolation 基礎

**已完成項目：**
- [x] Tenant Context 注入機制 (`X-Company-ID` Header)
- [x] `POST /api/attendance/mock-create` — 建立假考勤記錄
- [x] `POST /api/attendance/{id}/approve` — 核准考勤 + 發出 `attendance.approved` 事件
- [x] EventBus 事件發出 + demo 訂閱者
- [x] Tenant Isolation P0：company_id 從 Header 注入，不信任 request body
- [x] 完整模組結構（api/service/repo/models/docs/tests）
- [x] Tenant Isolation 測試套件

**產出檔案：**
```
backend/app/core/tenant_context.py
backend/app/modules/attendance/__init__.py
backend/app/modules/attendance/api.py
backend/app/modules/attendance/service.py
backend/app/modules/attendance/repo.py          ← Phase 1 空實作
backend/app/modules/attendance/models.py        ← Phase 1 空實作
backend/app/modules/attendance/docs.md
backend/app/modules/attendance/tests/__init__.py
backend/app/modules/attendance/tests/test_api.py
backend/app/modules/attendance/tests/test_tenant_isolation.py
backend/test_phase1.py
```

**限制：** repo.py / models.py 為空實作（無 DB），Phase 4 實作

---

### Phase 2 — Notifications 模組 + DB 層（2026-01-14）

**目標：** 建立 notifications 模組，訂閱 `attendance.approved` 事件，寫入 DB

**已完成項目：**
- [x] SQLAlchemy 資料庫連線管理（同步）(`backend/app/core/database.py`)
- [x] Notification ORM Model（UUID 主鍵 + company_id 索引）
- [x] Repository 層（強制 `WHERE company_id = ?`）
- [x] 事件處理器：訂閱 `attendance.approved`，Fail-fast 驗證
- [x] `GET /api/notifications` — 查詢通知（分頁）
- [x] 支援單一租戶全量抽取（備份用）
- [x] 完整模組結構 + Tenant Isolation 測試

**產出檔案：**
```
backend/app/core/database.py
backend/app/modules/notifications/__init__.py
backend/app/modules/notifications/models.py
backend/app/modules/notifications/repo.py
backend/app/modules/notifications/service.py
backend/app/modules/notifications/api.py
backend/app/modules/notifications/event_handlers.py
backend/app/modules/notifications/docs.md
backend/app/modules/notifications/tests/__init__.py
backend/app/modules/notifications/tests/test_api.py
backend/app/modules/notifications/tests/test_tenant_isolation.py
backend/app/modules/notifications/tests/test_event_handlers.py
```

---

### Phase 3 — Backup 模組（單一租戶匯出/還原）（2026-01-14）

**目標：** 實作單一公司備份匯出與還原，符合 SA_MODULE_SPEC v1.7 第 12-16 條

**已完成項目：**
- [x] `POST /api/backup/export` — 匯出指定公司所有 Tenant Data（JSON）
- [x] `POST /api/backup/restore?clear_existing={true|false}` — 還原資料
- [x] Company Consistency Check（P0）：拒絕混入多個 company_id 的備份檔
- [x] FK Closure Check（P0）：stub 實作（Phase 3 無外鍵）
- [x] 還原時強制覆寫 company_id = target_company_id
- [x] Transaction 管理：失敗完整 rollback
- [x] Merge 模式 / Replace 模式
- [x] 完整驗證器 + Tenant Isolation 測試

**產出檔案：**
```
backend/app/modules/backup/__init__.py
backend/app/modules/backup/api.py
backend/app/modules/backup/service.py
backend/app/modules/backup/exporter.py
backend/app/modules/backup/importer.py
backend/app/modules/backup/validator.py
backend/app/modules/backup/docs.md
backend/app/modules/backup/tests/__init__.py
backend/app/modules/backup/tests/test_api.py
backend/app/modules/backup/tests/test_tenant_isolation.py
backend/app/modules/backup/tests/test_validator.py
```

**限制：** 只支援 notifications 表，不支援 ZIP 壓縮，FK Closure Check 為 stub

---

### Phase 4 — Attendance DB 層實作（2026-01-25）

**目標：** 為 attendance 模組接上真正的資料庫層

**已完成項目：**
- [x] `attendance_records` 資料表（UUID PK + company_id 索引）
- [x] Alembic Migration `001_create_attendance_records.py`
- [x] AttendanceRecord ORM Model
- [x] Repository（CRUD + 強制 Tenant Isolation）
- [x] Service 改為真正寫 DB
- [x] API 注入 db Session
- [x] B 公司不能 approve A 的記錄 → 404（不洩漏存在性）

**產出/修改檔案：**
```
backend/alembic.ini
backend/alembic/env.py
backend/alembic/script.py.mako
backend/alembic/versions/001_create_attendance_records.py
backend/app/modules/attendance/models.py       ← 從空實作改為真正 model
backend/app/modules/attendance/repo.py         ← 從空實作改為真正 CRUD
backend/app/modules/attendance/service.py      ← 改為寫 DB
backend/app/modules/attendance/api.py          ← 注入 db Session
backend/app/modules/attendance/tests/test_phase4.py
```

---

### Phase 5 — Backup Restore UPSERT + 強化（2026-01-27）

**目標：** 強化備份還原功能，支援 UPSERT，擴展支援 attendance_records 表

**已完成項目：**
- [x] Backup Export 擴展支援 attendance_records 表
- [x] Backup Restore 擴展支援 attendance_records 表
- [x] Restore UPSERT 邏輯（處理重複 UUID）
- [x] Tenant Isolation 驗證強化

---

### Phase 6C — Backup Audit Log（2026-01-27）

**目標：** 為備份匯出/還原建立稽核紀錄

**已完成項目：**
- [x] `audit_logs` 資料表（UUID PK + company_id 索引 + JSONB meta）
- [x] Alembic Migration `002_create_audit_logs.py`
- [x] AuditLog ORM Model
- [x] Audit Repository（`create_log()`）
- [x] Backup API 整合 audit log（Export/Restore 成功/失敗都記錄）
- [x] Actor 抓取規則（X-Actor > X-User > "system"）
- [x] 獨立 Session 設計（不影響主流程 transaction）
- [x] 錯誤隔離機制（audit 寫入失敗不中斷主流程）
- [x] 6 個測試全部通過

**產出檔案：**
```
backend/alembic/versions/002_create_audit_logs.py
backend/app/modules/audit/__init__.py
backend/app/modules/audit/models.py
backend/app/modules/audit/repo.py
backend/app/modules/audit/tests/__init__.py
backend/app/modules/audit/tests/test_audit_backup.py
backend/app/modules/backup/api.py              ← 修改加入 audit log
backend/verify_audit_log.py
```

---

### Phase 7 — Audit Log 查詢 + 匯出 API（2026-01-28）

**目標：** 把 audit log 做成可查詢、可篩選、可匯出（JSON/CSV）的 API

**已完成項目：**
- [x] `GET /api/audit/logs` — 查詢稽核紀錄（分頁 + 篩選 + 排序）
  - 支援 event_type, actor, date_from, date_to, q（關鍵字）篩選
  - 支援 page / page_size 分頁
  - 支援 sort 排序（allowlist 防 SQL injection）
- [x] `GET /api/audit/export?format=json|csv` — 匯出稽核紀錄
  - JSON：回傳 items 陣列（最多 5000 筆）
  - CSV：UTF-8 + BOM（讓 Excel 正確開啟）
- [x] Audit Service 層（query + export 邏輯）
- [x] Tenant Isolation 100%（只能查自己公司）
- [x] 完整測試套件

**產出檔案：**
```
backend/app/modules/audit/api.py
backend/app/modules/audit/service.py
backend/app/modules/audit/docs.md
backend/app/modules/audit/tests/test_audit_api.py
backend/app/main.py                            ← 註冊 audit router
```

---

### Phase 8 — Audit Retention Policy + Purge（2026-01-28）

**目標：** 為 audit log 加入保留政策與清理機制

**已完成項目：**
- [x] `audit_retention_policies` 資料表（company_id 為 PK）
- [x] Alembic Migration `003_create_audit_retention_policies.py`
- [x] AuditRetentionPolicy ORM Model
- [x] `GET /api/audit/retention` — 取得保留政策（預設 365 天）
- [x] `PUT /api/audit/retention` — 更新保留政策（7 ~ 3650 天）
- [x] `POST /api/audit/purge` — 清理過期 audit log
  - 支援 dry_run（只回報不刪除）
  - 分批刪除（避免 DB lock）
  - Purge 操作自身也會寫 audit log
- [x] 測試套件

**產出檔案：**
```
backend/alembic/versions/003_create_audit_retention_policies.py
backend/app/modules/audit/models.py            ← 新增 AuditRetentionPolicy
backend/app/modules/audit/api.py               ← 新增 retention + purge API
backend/app/modules/audit/repo.py              ← 擴展
backend/app/modules/audit/service.py           ← 擴展
backend/app/modules/audit/tests/test_audit_retention.py
```

---

## 📂 已實作模組總覽

| 模組 | 路徑 | 狀態 | 說明 |
|------|------|------|------|
| **attendance** | `modules/attendance/` | ✅ 已實作 | 打卡核心（mock-create + approve + DB） |
| **notifications** | `modules/notifications/` | ✅ 已實作 | 事件訂閱 + DB 寫入 + 查詢 API |
| **backup** | `modules/backup/` | ✅ 已實作 | 單一租戶匯出/還原 + 驗證器 |
| **audit** | `modules/audit/` | ✅ 已實作 | 稽核紀錄 + 查詢/匯出 + 保留策略 + 清理 |

---

## 🗄️ 資料表總覽

| 表名 | Migration | 類型 | 說明 |
|------|-----------|------|------|
| `attendance_records` | 001 | Tenant Data | 考勤記錄（UUID PK） |
| `audit_logs` | 002 | Tenant Data | 稽核紀錄（UUID PK + JSONB） |
| `audit_retention_policies` | 003 | Tenant Data | 保留政策（company_id PK） |
| `notifications` | auto-create | Tenant Data | 通知記錄（UUID PK） |

---

## 🌐 API 端點總覽

| 端點 | 方法 | Phase | 說明 |
|------|------|-------|------|
| `/health` | GET | 0 | 健康檢查 |
| `/api/test/event` | GET | 0 | 事件訂閱狀態 |
| `/api/test/event` | POST | 0 | 發出測試事件 |
| `/api/attendance/mock-create` | POST | 1→4 | 建立考勤記錄 |
| `/api/attendance/{id}/approve` | POST | 1→4 | 核准考勤記錄 |
| `/api/notifications` | GET | 2 | 查詢通知 |
| `/api/backup/export` | POST | 3→5 | 匯出公司資料 |
| `/api/backup/restore` | POST | 3→5 | 還原公司資料 |
| `/api/audit/logs` | GET | 7 | 查詢稽核紀錄 |
| `/api/audit/export` | GET | 7 | 匯出稽核紀錄 |
| `/api/audit/retention` | GET | 8 | 取得保留政策 |
| `/api/audit/retention` | PUT | 8 | 更新保留政策 |
| `/api/audit/purge` | POST | 8 | 清理過期紀錄 |

---

## ❌ 尚未實作的模組（依據 SA_MODULE_SPEC v1.7 模組清單）

以下模組在規格文件中有列出，但**尚未實作**：

| 模組 | 優先級 | 說明 | 建議開發順序 |
|------|--------|------|-------------|
| **tenants** | 🔴 高 | 公司/租戶管理（CRUD）、公司設定 | Phase 9 |
| **auth** | 🔴 高 | JWT 認證、角色權限（RBAC）、登入/登出 | Phase 10 |
| **locations** | 🟡 中 | 站點管理、Trusted Device / Site Pairing | Phase 11 |
| **approvals** | 🟡 中 | 核准流程管理（通用核准引擎） | Phase 12 |
| **leave** | 🟡 中 | 請假流程管理 | Phase 13 |
| **accrual** | 🟡 中 | 假期額度 ledger 管理 | Phase 14 |
| **vehicles** | 🟠 低 | 車輛管理 | Phase 15 |
| **dispatch** | 🟠 低 | 派車管理（Level 0/1） | Phase 16 |
| **reporting** | 🟠 低 | 只讀彙總報表 | Phase 17 |

---

## ❌ 尚未實作的核心功能

| 功能 | 所屬模組 | 優先級 | 說明 |
|------|---------|--------|------|
| JWT 認證 | auth | 🔴 高 | 目前只用 X-Company-ID Header，需改為 JWT token |
| RBAC 權限 | auth | 🔴 高 | 角色權限控制（admin/manager/employee） |
| customer_service 權限 | auth | 🔴 高 | 客服只能操作指派公司 |
| 出勤推導邏輯 | attendance | 🔴 高 | IN/OUT 配對、工時計算 |
| PENDING_APPROVAL 狀態 | attendance | 🔴 高 | 不參與推導與日結 |
| 日結機制 | attendance | 🔴 高 | 21:00 日結缺卡判定 |
| approve pending → 重算 | attendance | 🔴 高 | 核准後重新推導當日 |
| Trusted Device Pairing | locations | 🟡 中 | Pairing code 綁定裝置 |
| PostgreSQL RLS | core/database | 🟡 中 | DB 層 Row Level Security（最後防線） |
| FK Closure Check 完整實作 | backup | 🟡 中 | 目前為 stub |
| 備份 ZIP 壓縮 | backup | 🟠 低 | 大檔案壓縮 |
| 增量備份 | backup | 🟠 低 | 只備份差異 |
| 排程備份 | backup | 🟠 低 | 自動定期備份 |
| 備份加密 | backup | 🟠 低 | AES-256 加密 |

---

## ❌ 尚未通過的核心回歸測試（SA_MODULE_SPEC v1.7 第 10 條）

以下 8 條核心測試尚未有完整實作支撐：

| # | 測試項目 | 狀態 | 需要模組 |
|---|---------|------|---------|
| 1 | NO_MATCH 未填原因 → 拒絕 | ❌ 未實作 | attendance |
| 2 | NO_MATCH 有原因 → PENDING | ❌ 未實作 | attendance |
| 3 | APPROVED → 推導正確 | ❌ 未實作 | attendance |
| 4 | PENDING 不參與推導與日結 | ❌ 未實作 | attendance |
| 5 | 21:00 日結缺卡/可能缺卡正確 | ❌ 未實作 | attendance |
| 6 | approve pending → 該日重算 | ❌ 未實作 | attendance |
| 7 | customer_service 未指派公司 → 403 | ❌ 未實作 | auth |
| 8 | OTP / Reset token 一次性 + 強制改密碼 | ❌ 未實作 | auth |

---

## 🔮 建議後續開發順序

### 第一優先（基礎建設）

| 順序 | Phase | 目標 | 原因 |
|------|-------|------|------|
| 1 | Phase 9 | **tenants 模組** — 公司/租戶 CRUD + 設定 | 所有模組的基礎，需要正式的 company 資料 |
| 2 | Phase 10 | **auth 模組** — JWT 認證 + RBAC + 登入 | 取代 X-Company-ID Header，正式安全認證 |
| 3 | Phase 10b | **auth 整合** — 將所有 API 改為 JWT 驗證 | Tenant Context 升級為 JWT token 解析 |

### 第二優先（核心業務）

| 順序 | Phase | 目標 | 原因 |
|------|-------|------|------|
| 4 | Phase 11 | **locations 模組** — 站點管理 + Device Pairing | 打卡需要站點位置匹配 |
| 5 | Phase 12 | **attendance 核心邏輯** — 推導 + 日結 + 狀態機 | 完成出勤核心，通過 8 條回歸測試 |
| 6 | Phase 13 | **approvals 模組** — 通用核准引擎 | 請假/出勤異常的核准流程 |

### 第三優先（業務擴展）

| 順序 | Phase | 目標 | 原因 |
|------|-------|------|------|
| 7 | Phase 14 | **leave 模組** — 請假流程 | 員工請假管理 |
| 8 | Phase 15 | **accrual 模組** — 假期額度 ledger | 搭配請假使用 |
| 9 | Phase 16 | **vehicles + dispatch** — 車輛 + 派車 | Level 0/1 派車功能 |
| 10 | Phase 17 | **reporting 模組** — 只讀彙總報表 | 最後階段，只讀不寫 |

### 第四優先（強化安全 & 運維）

| 順序 | Phase | 目標 | 原因 |
|------|-------|------|------|
| 11 | Phase 18 | **PostgreSQL RLS** — Row Level Security | 資料庫層最後防線 |
| 12 | Phase 19 | **Backup 強化** — 完整 FK Check + ZIP + 增量 | 備份功能完善 |
| 13 | Phase 20 | **通知發送** — Email / SMS / Push | 真正的通知管道 |

---

## 📈 開發進度統計

- **已完成 Phase 數：** 9 個（Phase 0 ~ Phase 8）
- **已實作模組：** 4 / 11（attendance, notifications, backup, audit）
- **未實作模組：** 7 個（tenants, auth, locations, approvals, leave, accrual, vehicles, dispatch, reporting）
- **已建立資料表：** 4 張（attendance_records, notifications, audit_logs, audit_retention_policies）
- **已建立 API 端點：** 13 個
- **已完成 Alembic Migration：** 3 個
- **核心回歸測試（8 條）：** 0 / 8 通過（需要出勤推導 + auth 才能跑）

---

## ⚠️ 重要注意事項

1. **Tenant Isolation P0** — 所有已實作模組均通過 Tenant Isolation 驗證
2. **目前認證為簡化版** — 使用 `X-Company-ID` Header，Phase 10 需升級為 JWT
3. **notifications 表無 Alembic migration** — 使用 `init_db()` auto-create，建議補上
4. **FK Closure Check 為 stub** — 待更多表有外鍵關係後完整實作
5. **核心出勤邏輯尚未實作** — 推導、日結、狀態機是最關鍵的業務邏輯

---

**文件結束**
