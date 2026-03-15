# WP-REPORTING-BACKEND — 調查報告

**建立日期：** 2026-03-14  
**類型：** INVESTIGATION REPORT（調查報告，本輪不修改任何程式碼）  
**調查人：** Cursor AI Agent  
**調查範圍：** Reporting API 為何未出現在 OpenAPI / 回傳 404

---

## 1. 已讀取的檔案／資料夾

| 路徑 | 說明 |
|------|------|
| `/opt/attendance-system/docs/AI_CONTEXT.md` | AI 文件導覽 |
| `/opt/attendance-system/docs/NEXT_WP_TICKET.md` | 目前 WP 狀態與下一步 |
| `/opt/attendance-system/docs/WP-REPORTING-UI_IMPLEMENTATION_PLAN.md` | Reporting UI 實作計畫 |
| `/opt/attendance-system/docs/WP-REPORTING-UI_API_FIELD_MAPPING.md` | API 欄位對照表 |
| `/opt/attendance-system/backend/app/modules/attendance/api.py` | 完整 attendance API 實作（31,487 bytes，最後修改 2026-03-13 19:13） |
| `/opt/attendance-system/backend/app/modules/attendance/schemas.py` | 完整 schemas 定義 |
| `/opt/attendance-system/backend/app/modules/attendance/repo.py` | 完整 repo 定義 |
| `/opt/attendance-system/backend/app/main.py` | FastAPI 應用入口與 router 掛載 |
| `/etc/systemd/system/attendance-system.service` | systemd 服務設定 |
| `/opt/attendance-system/backend.log` | 後端服務 log（5.2MB） |
| `curl http://127.0.0.1:8000/openapi.json` | 實際 OpenAPI 路由清單 |
| `ps`, `ss`, `/proc/1856041/cwd`, `/proc/1856041/cmdline` | 執行中進程資訊 |

---

## 2. Reporting API Existence Matrix

| API 路徑 | code 存在 | router 掛載正確 | 出現在 OpenAPI | 實際可呼叫 | 狀態判定 |
|---------|----------|---------------|--------------|----------|---------|
| `GET /api/v1/attendance/sessions` | YES | YES | **NO** | **NO（404）** | code 完整；服務未重啟 |
| `GET /api/v1/attendance/reports/user-summary` | YES | YES | **NO** | **NO（404）** | code 完整；服務未重啟 |
| `GET /api/v1/attendance/reports/company-summary` | YES | YES | **NO** | **NO（404）** | code 完整；服務未重啟 |

**三支 API 的程式碼、schema、repo、router include 全部齊備。問題不在 code，在 runtime。**

---

## 3. schemas.py / repo.py / service 現況盤點

### 3.1 schemas.py

| Schema | 存在 | 說明 |
|--------|------|------|
| `SessionResponse` | YES | session_id, user_id, company_id, punch_in/out_time, duration_minutes, status, punches |
| `SessionsListResponse` | YES | sessions list + total/limit/offset（WP-11-06 Step 1） |
| `UserSummaryResponse` | YES | 8 欄位，含 nullable average/first/last（WP-11-06 Step 2） |
| `CompanySummaryResponse` | YES | 10 欄位，含 nullable average/first/last（WP-11-06 Step 3） |

schemas.py **完整，零缺口**。

### 3.2 repo.py

| 方法 | 所屬 Class | 存在 | 說明 |
|------|-----------|------|------|
| `get_sessions_for_reporting()` | `ReportingRepository` | YES | 支援 company_id, user_id, start/end_utc, status, limit/offset |
| `count_sessions_for_reporting()` | `ReportingRepository` | YES | 供分頁 total 使用 |
| `get_user_summary_sessions()` | `ReportingRepository` | YES | 全量拉取，應用層聚合 |
| `get_company_summary_sessions()` | `ReportingRepository` | YES | 全量拉取，不過濾 user_id |
| `get_reporting_repository()` | Factory function | YES | DI factory，被 api.py 正確 import |

- 所有方法均強制 `WHERE company_id = ?`（tenant isolation OK）
- 日期過濾僅使用 `punch_in_time`（符合設計規格）
- 分頁 / 日期區間 / status 過濾邏輯完整

repo.py **完整，零缺口**。

### 3.3 service.py

`service.py` 僅含舊版 Phase 4 邏輯（`mock_create_attendance`、`approve_attendance`），**Reporting 功能完全不依賴 service.py**，直接在 api.py 呼叫 `ReportingRepository`，設計正確。

---

## 4. App Router Registration 現況

`main.py` 第 11 行：
```python
from app.modules.attendance.api import router as attendance_router, router_v1 as attendance_router_v1
```

`main.py` 第 38-39 行：
```python
app.include_router(attendance_router)
app.include_router(attendance_router_v1)
```

`api.py` 中 router 定義：
```python
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])
```

三支 reporting endpoint 的裝飾器：
```python
@router_v1.get("/sessions", response_model=SessionsListResponse)
@router_v1.get("/reports/user-summary", response_model=UserSummaryResponse)
@router_v1.get("/reports/company-summary", response_model=CompanySummaryResponse)
```

**Router registration 在 repo 中的程式碼完全正確，無任何條件式掛載、feature flag 或 import guard。**

---

## 5. OpenAPI 缺失原因分析（Root Cause）

### 5.1 關鍵時間線

| 時間點 | 事件 |
|--------|------|
| 2026-03-06 22:51 | systemd `attendance-system.service` crash，此後 **永遠 FAILED**，未重啟成功 |
| 2026-03-11 16:58:30 | 有人**手動啟動** uvicorn（推測帶 `--reload`），PID 主進程 → fork worker PID 1856041 |
| 2026-03-13 19:13:27 | `api.py` 被更新，加入三支 reporting endpoint（WP-11-06 Step 1/2/3） |
| 2026-03-14（現在） | port 8000 仍由 PID 1856041（2026-03-11 啟動的 worker）提供服務 |

### 5.2 OpenAPI 不含 reporting endpoint 的直接原因

**目前 port 8000 服務載入的是 2026-03-11 16:58 時的 `api.py`，而非 2026-03-13 19:13 更新後的版本。**

uvicorn 以 `--reload` 模式啟動，理論上應自動 reload。但 `backend.log` 顯示：
- 所有 WatchFiles reload 事件均由 **venv 套件檔案異動** 觸發（pygments、sqlalchemy、uvicorn 自身等）
- 沒有任何 `app/modules/attendance/api.py` 變更觸發 reload 的記錄
- 這是因為 uvicorn `--reload` 預設監視的是 **CWD 下的 .py 檔案**，但 `venv/` 目錄下的套件更新也在監視範圍內，干擾了正常 reload 流程

最終結果：**`api.py` 在 2026-03-13 19:13 的修改未被 reload 機制偵測並套用，服務仍運行舊版 code。**

### 5.3 實際 OpenAPI 路由清單對比

**目前運行中（舊版）：**
```
/api/v1/attendance/punch-in
/api/v1/attendance/punch-out
/api/v1/attendance/current-status
/api/v1/attendance/history
/api/v1/attendance/break-out
/api/v1/attendance/break-in
/api/v1/attendance/break-punches
/api/v1/attendance/punch/{punch_id}/note
```
（共 8 個 v1 attendance endpoints，不含任何 sessions / reports）

**repo 現在程式碼應有（含新版）：**
```
/api/v1/attendance/sessions               ← 缺失（WP-11-06 Step 1）
/api/v1/attendance/reports/user-summary   ← 缺失（WP-11-06 Step 2）
/api/v1/attendance/reports/company-summary ← 缺失（WP-11-06 Step 3）
```

### 5.4 Root Cause 確定判定

```
ROOT CAUSE：服務部署後未重啟（Not Restarted After Deployment）

- api.py 在 2026-03-13 19:13 加入三支 reporting endpoint
- uvicorn --reload 未成功 reload 該次變更
- systemd service 長期 FAILED，無法依賴 systemctl restart
- 結果：運行中的服務仍是 2026-03-11 的舊版本
- 三支 API 從未被載入，OpenAPI 中不存在，前端收到 404
```

---

## 6. Runtime Service / Code Source 檢查結果

```
服務啟動方式：    手動 uvicorn --reload（非 systemd，而是手動執行）
systemd 狀態：    attendance-system.service = FAILED（2026-03-06 起）
Port 8000 PID：   1856041
PID 1856041 類型：uvicorn multiprocessing fork worker（非主進程）
啟動時間：        2026-03-11 16:58:30
Working Dir：     /opt/attendance-system/backend（正確路徑）
Python binary：   /opt/attendance-system/venv/bin/python（同 systemd 設定）

api.py 修改時間：  2026-03-13 19:13:27（服務啟動後 44 小時才更新）
OpenAPI 驗證：    缺少三支 reporting endpoint（已由 curl /openapi.json 確認）
Log 驗證：        log 中可見 404 回應：
                  GET /api/v1/attendance/reports/user-summary → 404 Not Found
                  GET /api/v1/attendance/reports/company-summary → 404 Not Found
```

**結論：只有一份 backend code（`/opt/attendance-system/backend`），沒有多份程式碼或舊版目錄問題。問題單純是「改了 code 但服務沒重啟」。**

---

## 7. 若要補齊 Reporting Backend，最小缺口清單

根據調查結果，**程式碼層面零缺口**，唯一缺口是 runtime 未重啟。

| 項目 | 狀態 | 說明 |
|------|------|------|
| endpoint 程式碼 | COMPLETE | api.py 已有三支 endpoint |
| schema | COMPLETE | schemas.py 已有 SessionsListResponse / UserSummaryResponse / CompanySummaryResponse |
| repo query | COMPLETE | ReportingRepository 已有四個方法 |
| service layer | N/A | reporting 