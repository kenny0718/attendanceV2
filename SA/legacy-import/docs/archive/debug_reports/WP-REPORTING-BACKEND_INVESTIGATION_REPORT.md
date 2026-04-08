# WP-REPORTING-BACKEND — 調查報告

**建立日期：** 2026-03-14
**類型：** INVESTIGATION REPORT（調查報告，本輪不修改任何程式碼）
**調查人：** Cursor AI Agent
**調查範圍：** Reporting API 為何未出現在 OpenAPI / 回傳 404

---

## 1. 已讀取的檔案／資料夾

| 路徑 | 說明 |
|------|------|
| `docs/AI_CONTEXT.md` | AI 文件導覽 |
| `docs/NEXT_WP_TICKET.md` | 目前 WP 狀態與下一步 |
| `docs/WP-REPORTING-UI_IMPLEMENTATION_PLAN.md` | Reporting UI 實作計畫（確認 CODE_COMPLETE 狀態）|
| `docs/WP-REPORTING-UI_API_FIELD_MAPPING.md` | API 欄位對照表 |
| `backend/app/modules/attendance/api.py` | 完整 attendance API（31,487 bytes，修改於 2026-03-13 19:13）|
| `backend/app/modules/attendance/schemas.py` | 完整 schemas 定義 |
| `backend/app/modules/attendance/repo.py` | 完整 repo 定義 |
| `backend/app/main.py` | FastAPI 應用入口與 router 掛載 |
| `/etc/systemd/system/attendance-system.service` | systemd 服務設定 |
| `/opt/attendance-system/backend.log` | 後端服務 log（5.2MB）|
| `curl http://127.0.0.1:8000/openapi.json` | 實際 OpenAPI 路由清單（runtime 驗證）|
| `ps`, `ss`, `/proc/1856041/cwd`, `/proc/1856041/cmdline` | 執行中進程資訊 |

---

## 2. Reporting API Existence Matrix

| API 路徑 | code 存在 | router 掛載正確 | 出現在 OpenAPI | 實際可呼叫 | 狀態判定 |
|---------|----------|---------------|--------------|----------|---------|
| `GET /api/v1/attendance/sessions` | YES | YES | NO | NO（404）| code 完整；服務未重啟 |
| `GET /api/v1/attendance/reports/user-summary` | YES | YES | NO | NO（404）| code 完整；服務未重啟 |
| `GET /api/v1/attendance/reports/company-summary` | YES | YES | NO | NO（404）| code 完整；服務未重啟 |

**三支 API 的程式碼、schema、repo、router include 全部齊備。問題不在 code，在 runtime。**

---

## 3. schemas.py / repo.py / service 現況盤點

### 3.1 schemas.py

| Schema | 存在 | 說明 |
|--------|------|------|
| `SessionResponse` | YES | session_id, user_id, company_id, punch_in/out_time, duration_minutes, status, punches |
| `SessionsListResponse` | YES | sessions list + total/limit/offset（WP-11-06 Step 1）|
| `UserSummaryResponse` | YES | 8 欄位，含 nullable average/first/last（WP-11-06 Step 2）|
| `CompanySummaryResponse` | YES | 10 欄位，含 nullable average/first/last（WP-11-06 Step 3）|

schemas.py **完整，零缺口**。

### 3.2 repo.py

| 方法 | 所屬 Class | 存在 | 說明 |
|------|-----------|------|------|
| `get_sessions_for_reporting()` | `ReportingRepository` | YES | 支援 company_id, user_id, start/end_utc, status, limit/offset |
| `count_sessions_for_reporting()` | `ReportingRepository` | YES | 供分頁 total 使用 |
| `get_user_summary_sessions()` | `ReportingRepository` | YES | 全量拉取，應用層聚合 |
| `get_company_summary_sessions()` | `ReportingRepository` | YES | 全量拉取，不過濾 user_id |
| `get_reporting_repository()` | Factory function | YES | DI factory，被 api.py 正確 import |

- 所有方法均強制 WHERE company_id（tenant isolation OK）
- 日期過濾僅使用 punch_in_time（符合設計規格）
- 分頁 / 日期區間 / status 過濾邏輯完整

repo.py **完整，零缺口**。

### 3.3 service.py

`service.py` 僅含舊版 Phase 4 邏輯（mock_create_attendance、approve_attendance）。
Reporting 功能完全不依賴 service.py，直接在 api.py 呼叫 ReportingRepository，設計正確。

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

三支 reporting endpoint 的裝飾器（均掛載於 router_v1）：

```python
@router_v1.get("/sessions", response_model=SessionsListResponse)
@router_v1.get("/reports/user-summary", response_model=UserSummaryResponse)
@router_v1.get("/reports/company-summary", response_model=CompanySummaryResponse)
```

**Router registration 完全正確，無任何條件式掛載、feature flag 或 import guard。**

---

## 5. OpenAPI 缺失原因分析（Root Cause）

### 5.1 關鍵時間線

| 時間點 | 事件 |
|--------|------|
| 2026-03-06 22:51 | systemd attendance-system.service crash，此後永遠 FAILED，未重啟成功 |
| 2026-03-11 16:58:30 | 手動啟動 uvicorn（帶 --reload），fork worker PID 1856041 |
| 2026-03-13 19:13:27 | api.py 更新，加入三支 reporting endpoint（WP-11-06 Step 1/2/3）|
| 2026-03-14（現在）| port 8000 仍由 PID 1856041（2026-03-11 啟動的 worker）提供服務 |

### 5.2 OpenAPI 不含 reporting endpoint 的直接原因

目前 port 8000 服務載入的是 **2026-03-11 16:58 時的 api.py**，而非 2026-03-13 19:13 更新後的版本。

uvicorn 以 --reload 模式啟動，理論上應自動 reload。但 backend.log 顯示：

- 所有 WatchFiles reload 事件均由 venv 套件檔案異動觸發（pygments、sqlalchemy、uvicorn 等）
- 沒有任何 app/modules/attendance/api.py 變更觸發 reload 的記錄
- uvicorn --reload 監視整個 CWD（含 venv/），venv 套件的更新不斷觸發 reload，但 app/ 目錄的變更反而可能在 noise 中被漏掉

最終結果：api.py 在 2026-03-13 19:13 的修改未被 reload 機制套用，服務仍運行舊版 code。

### 5.3 實際 OpenAPI 路由清單對比

目前運行中（舊版，8 個 v1 attendance endpoints）：

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

repo 現在程式碼應有（三支缺失）：

```
/api/v1/attendance/sessions               <- 缺失（WP-11-06 Step 1）
/api/v1/attendance/reports/user-summary   <- 缺失（WP-11-06 Step 2）
/api/v1/attendance/reports/company-summary <- 缺失（WP-11-06 Step 3）
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
服務啟動方式：    手動 uvicorn --reload（非 systemd）
systemd 狀態：    attendance-system.service = FAILED（2026-03-06 起）
Port 8000 PID：   1856041
PID 類型：        uvicorn multiprocessing fork worker（非主進程）
啟動時間：        2026-03-11 16:58:30
Working Dir：     /opt/attendance-system/backend（正確）
Python binary：   /opt/attendance-system/venv/bin/python（正確）

api.py 修改時間：  2026-03-13 19:13:27（服務啟動後 44 小時才更新）
OpenAPI 驗證：    缺少三支 reporting endpoint（curl /openapi.json 確認）
Log 驗證：        404 回應記錄：
                  GET /api/v1/attendance/reports/user-summary -> 404 Not Found
                  GET /api/v1/attendance/reports/company-summary -> 404 Not Found
```

結論：只有一份 backend code（/opt/attendance-system/backend），沒有多份程式碼或舊版目錄問題。
問題單純是「改了 code 但服務沒重啟」。

---

## 7. 若要補齊 Reporting Backend，最小缺口清單

根據調查結果，**程式碼層面零缺口**，唯一缺口是 runtime 未重啟。

| 項目 | 狀態 | 說明 |
|------|------|------|
| endpoint 程式碼 | COMPLETE | api.py 已有三支完整 endpoint |
| schema | COMPLETE | schemas.py 已有 SessionsListResponse / UserSummaryResponse / CompanySummaryResponse |
| repo query | COMPLETE | ReportingRepository 已有四個方法（get/count sessions, user/company summary）|
| service layer | N/A | Reporting 不需要 service layer，直接呼叫 repo |
| router include | COMPLETE | main.py 已正確 include_router(attendance_router_v1)|
| migration / index | COMPLETE | 使用現有 attendance_sessions 表，無需新 migration |
| auth / tenant isolation | COMPLETE | 強制 WHERE company_id，Header auth（JWT 遷移後續 WP-C1-03）|
| **服務重啟** | **MISSING** | **這是唯一缺口，重啟即可解決** |

---

## 8. 建議下一步

### 選項 A：只重啟服務（最小修復，立即生效）

```bash
# 殺掉舊的 uvicorn 進程，重新啟動
kill $(pgrep -f 'uvicorn') 2>/dev/null
cd /opt/attendance-system/backend
/opt/attendance-system/venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  >> /opt/attendance-system/backend.log 2>&1 &
```

重啟後三支 reporting API 立即出現在 OpenAPI，前端 404 問題解除。
預計工時：5 分鐘。

### 選項 B：修復 systemd service 並重啟（建議長期方案）

systemd service 自 2026-03-06 起 FAILED，建議一併修復：

1. 確認 crash 原因：`journalctl -u attendance-system.service --since "2026-03-06" | tail -50`
2. 修正後：`systemctl daemon-reload && systemctl start attendance-system.service`
3. 確認：`systemctl status attendance-system.service`

服務由 systemd 管理後，自動重啟更可靠，不再依賴手動啟動。
預計工時：15-30 分鐘。

### 選項 C：後端補充實作（不需要）

無需補充任何後端程式碼。三支 API 的實作在 WP-11-06 Step 1/2/3 中已全部完成。

---

## 9. 最終回報摘要

### Q1：Reporting API 是否存在？

YES。三支 API 的程式碼完全存在於 repo 中，包含 endpoint、schema、repo query，router 也正確掛載。

### Q2：缺的是 code、router、還是 deployment？

缺的是 deployment（重啟）。Code 完整，router 正確，唯一問題是服務自 2026-03-11 啟動後，2026-03-13 的 code 更新未被載入。

### Q3：最可能 Root Cause？

api.py 在 2026-03-13 19:13 加入三支 reporting endpoint，但 uvicorn --reload 未成功 reload 該次變更，加上 systemd service 長期 FAILED 無法依賴自動重啟，導致運行中服務仍載入 2026-03-11 的舊版本。

### Q4：最小修復路徑？

重啟 uvicorn 服務（5 分鐘內完成）。無需修改任何程式碼。

### Q5：是否建議直接進入 backend implementation？

否。Backend 已 COMPLETE。直接重啟服務即可解除 404 問題。
重啟後前端三個 Reporting 頁面應可正常呼叫 API。
注意：前端仍有 BUG-01（stores/reporting.js response 解構錯誤），詳見 WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md。

---

*Investigation completed — 2026-03-14*
