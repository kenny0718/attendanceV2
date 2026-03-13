#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

DOCS = "/opt/attendance-system/docs"

# ============================================================
# FILE 1: WP-11-06_SAFE_START_PRE_EXECUTION_REPORT.md
# ============================================================

report1 = """# WP-11-06 Safe Start Pre-Execution Report

**建立日期：** 2026-03-13
**任務：** WP-11-06 Reporting v1 — Safe Start
**類型：** PRE-EXECUTION REPORT (Documentation Only — No Code Changes)
**狀態：** ACTIVE

---

## 1. 目的

本報告為 WP-11-06 Reporting v1 正式實作前的環境與代碼庫準備狀態評估。
本報告不包含任何程式碼實作。目的僅為：

1. 判斷現有代碼庫是否處於可安全進行 WP-11-06 的狀態
2. 識別可複用的現有基礎
3. 識別已知風險
4. 提供清晰的 GO / NO-GO 決策依據

---

## 2. 現有系統狀態

### 2.1 已完成的基礎工作（Phase 1-3 Closeout）

| 項目 | 狀態 | 來源文件 |
|------|------|----------|
| policy_engine.py P1 時區 bug 修正（3個） | 已完成 | ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md |
| 業務日歸屬規則文件化 | 已完成 | WP-11-06_REPORTING_BOUNDARY_DECISIONS.md |
| 月份歸屬規則文件化 | 已完成 | WP-11-06_REPORTING_BOUNDARY_DECISIONS.md |
| Canonical duration 規則文件化 | 已完成 | WP-11-06_REPORTING_BOUNDARY_DECISIONS.md |
| Query guardrails 文件化 | 已完成 | WP-11-06_REPORTING_QUERY_GUARDRAILS.md |
| JWT naive datetime bug 修正 | 已完成 | ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md |
| test_business_invariant.py timezone 修正（12處） | 已完成 | ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md |
| test_model_constraints.py timezone 修正（15處） | 已完成 | ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md |
| Frontend timezone display 修正（Home.vue） | 已完成 | ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md |
| models.py comment vs CHECK constraint 修正 | 已完成 | ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md |

### 2.2 test_policy_engine.py 測試狀態

- **執行結果：28/28 passed, 7 warnings**（2026-03-13 現場驗證）
- 包含 4 個 timezone 回歸測試（TestTimezoneFixRegression）
- 所有 P1 時區 bug 的修正均有對應測試覆蓋

### 2.3 現有 attendance 模組檔案清單

| 檔案 | 用途 | WP-11-06 關係 |
|------|------|---------------|
| backend/app/modules/attendance/api.py | FastAPI 路由 | 需新增報表 endpoints |
| backend/app/modules/attendance/repo.py | 資料存取層 | 需新增報表查詢方法 |
| backend/app/modules/attendance/schemas.py | Pydantic DTO | 需新增報表 response schemas |
| backend/app/modules/attendance/models.py | SQLAlchemy models | **不修改**（無需新增欄位） |
| backend/app/modules/attendance/policy_engine.py | 政策計算 | **不修改** |
| backend/app/modules/attendance/service.py | 業務邏輯 | **不修改**（Reporting 不需要） |
| backend/app/modules/attendance/location_policy_service.py | 地點政策 | **不修改** |

### 2.4 現有 AttendanceSession 欄位確認

`attendance_sessions` 表中與 reporting 直接相關的欄位：

| 欄位 | 類型 | Nullable | WP-11-06 使用方式 |
|------|------|----------|------------------|
| id | UUID | NOT NULL | session 識別 |
| company_id | String(255) | NOT NULL | tenant isolation |
| user_id | UUID | NOT NULL | 個人報表過濾 |
| punch\_in\_time | DateTime(TZ) | NOT NULL | **月份/日期歸屬基準（唯一）** |
| punch\_out\_time | DateTime(TZ) | NULL | 顯示用；**禁止用於歸屬過濾** |
| status | String(20) | NOT NULL | open/closed 過濾 |
| duration\_minutes | Integer | NULL | **canonical 工時來源（唯一）** |

`session_date` 欄位不存在。依 WP-11-06\_SESSION\_DATE\_FEASIBILITY.md 決策，
WP-11-06 階段不引入此欄位，使用 `punch_in_time` UTC 邊界比較方案。

### 2.5 現有索引確認

| 索引 | 欄位 | WP-11-06 可用性 |
|------|------|----------------|
| idx\_sessions\_company\_punch\_in | (company\_id, punch\_in\_time) | **報表主要索引** — 月報/sessions 查詢 |
| idx\_sessions\_company\_user | (company\_id, user\_id) | 個人報表輔助索引 |
| uq\_sessions\_company\_user\_open | (company\_id, user\_id WHERE open) | 不適用（reporting 查 closed sessions） |

月報查詢模式 `WHERE company_id = ? AND punch_in_time >= ? AND punch_in_time < ?`
可直接命中 `idx_sessions_company_punch_in` 執行 Index Range Scan，無需建立新索引。

### 2.6 現有 start_date / end_date Schema 狀態

`AttendanceHistoryRequest`（schemas.py）已定義 `start_date` / `end_date`，型別為 `Optional[datetime]`，但：

- API endpoint `GET /api/v1/attendance/history` 接收後直接丟棄，未傳入 repo
- `repo.get_sessions()` 不接受日期範圍參數
- 此為已知 placeholder；WP-11-06 Sessions endpoint 實作時須補齊，並遵守 guardrails

---

## 3. Readiness Verdict：GO

### 3.1 GO 依據

| 檢查項目 | 狀態 | 說明 |
|---------|------|------|
| policy_engine.py 時區計算正確 | PASS | 28/28 tests passed |
| 業務日歸屬規則明確 | PASS | BOUNDARY_DECISIONS.md 已文件化 |
| Canonical duration 規則明確 | PASS | 同上 |
| Query guardrails 明確 | PASS | REPORTING_QUERY_GUARDRAILS.md 已文件化 |
| 現有索引足以支援 Sessions endpoint | PASS | idx_sessions_company_punch_in |
| schema/models 無需修改 | PASS | 無 migration 需求 |
| Test fixtures 可複用 | PASS | conftest.py 提供 test_user, test_session |
| 禁止模式清單明確 | PASS | REPORTING_QUERY_GUARDRAILS.md |

### 3.2 前提條件確認（實作前必須遵守）

1. 所有 reporting query 遵守 `WP-11-06_REPORTING_QUERY_GUARDRAILS.md` 所有規則
2. `start_date` / `end_date` 過濾器實作時，同步加入 naive datetime 拒絕 validator
3. 跨日 session 測試案例必須涵蓋 `punch_in 23:50 / punch_out 00:30+1d` 邊界情境

---

## 4. WP-11-06 涉及的修改範圍

### 4.1 Step 1（本任務）：GET /api/v1/attendance/sessions

**需修改的檔案：**

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| backend/app/modules/attendance/repo.py | 新增方法 | `get_sessions_for_reporting()` — 接受 company\_id, user\_id(optional), start\_utc, end\_utc, status, limit, offset |
| backend/app/modules/attendance/schemas.py | 新增 Schema | `SessionsQueryParams`, `SessionsListResponse` |
| backend/app/modules/attendance/api.py | 新增 endpoint | `GET /api/v1/attendance/sessions` |
| backend/app/modules/attendance/tests/test\_reporting\_sessions.py | 新建檔案 | Sessions endpoint 專用測試 |

**不得修改的檔案：**

| 檔案 | 原因 |
|------|------|
| models.py | WP-11-06 階段不修改 schema，無需新增欄位 |
| policy\_engine.py | Phase 1-3 已修正，不觸碰 |
| service.py | Reporting 不經過 service layer |
| location\_policy\_service.py | 與 reporting 無關 |
| admin\_location\_api.py | 與 reporting 無關 |
| gps\_utils.py | 與 reporting 無關 |
| 任何 migration 檔案 | WP-11-06 不引入 migration |

### 4.2 後續 Steps（本任務不實作）

| Step | Endpoint | 依賴 |
|------|----------|------|
| Step 2 | GET /api/v1/attendance/reports/user-summary | Step 1 完成 |
| Step 3 | GET /api/v1/attendance/reports/company-summary | Step 2 完成 |

---

## 5. 可複用的現有程式碼

### 5.1 repo.py 現有方法

| 方法 | 複用方式 |
|------|----------|
| `get_sessions(company_id, user_id, limit, offset, status)` | 個人歷史記錄用途；Sessions reporting 需新方法，**不修改舊方法** |
| `count_sessions(company_id, user_id, status)` | 分頁計數邏輯可參考，需擴充 date range |

重要注意事項：現有 `get_sessions()` 使用 `user_id` 作為必填參數。新的 Sessions reporting
endpoint 需要支援 company 管理者查詢全員記錄（`user_id` 為可選）。須建立新方法，不修改舊方法。

### 5.2 schemas.py 現有 Schema

| Schema | 複用方式 |
|--------|----------|
| `SessionResponse` | Sessions endpoint response 的單筆 session 結構可直接複用 |
| `AttendanceHistoryResponse` | 結構接近，可參考，但 Sessions reporting 需獨立的 response schema |

### 5.3 tests/conftest.py 現有 Fixtures

| Fixture | 複用說明 |
|---------|----------|
| `client` | 直接複用 — TestClient |
| `test_session` (db) | 直接複用 — SQLAlchemy session |
| `test_user` | 直接複用 — 建立測試用 Tenant + User，含 `user.company_id = "company-test"` |

### 5.4 已定義的查詢輔助函數規格（待實作）

下列函數規格已在 `WP-11-06_REPORTING_QUERY_GUARDRAILS.md` 和
`WP-11-06_REPORTING_QUERY_PLAN.md` 中明確定義，實作時直接套用：

```python
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from typing import Optional

TZ_TAIPEI = ZoneInfo("Asia/Taipei")

def get_month_utc_boundaries(year: int, month: int) -> tuple[datetime, datetime]:
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    end   = datetime(next_year, next_month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

def normalize_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        raise ValueError("naive datetime rejected — must be timezone-aware")
    return dt.astimezone(timezone.utc)
```

---

## 6. Step 1 測試策略

### 6.1 測試檔案

新建 `backend/app/modules/attendance/tests/test_reporting_sessions.py`  
不修改任何現有測試檔案。

### 6.2 必要測試案例（最小集合）

| Test ID | 案例 | 驗證重點 |
|---------|------|----------|
| SES-01 | 基本分頁查詢（無日期過濾） | limit/offset 正確，回傳 SessionResponse 列表 |
| SES-02 | start_date / end_date 日期過濾 | 僅回傳 punch_in_time 在範圍內的 sessions |
| 