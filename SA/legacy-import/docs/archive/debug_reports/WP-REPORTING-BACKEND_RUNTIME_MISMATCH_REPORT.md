# WP-REPORTING-BACKEND — Runtime Mismatch 調查報告

**調查日期：** 2026-03-14  
**調查人：** AI Pair Programmer  
**狀態：** 調查完成，根本原因確認

---

## 1. 問題描述

`api.py` 在 2026-03-13 19:13 加入三支 reporting endpoint：

- `GET /api/v1/attendance/sessions`
- `GET /api/v1/attendance/reports/user-summary`
- `GET /api/v1/attendance/reports/company-summary`

但重啟 uvicorn 後，`/docs` 與 `/openapi.json` 仍然沒有這三支 API。

---

## 2. 調查結果總覽

| 檢查項目 | 結果 |
|---------|------|
| `api.py` 是否含三支 endpoint decorator | **YES**（第 620、744、840 行）|
| `main.py` 是否 include `attendance_router_v1` | **YES**（第 39 行）|
| `api.py` 的 `.pyc` 是否最新 | **YES**（mtime 與 source 一致，2026-03-13 19:13）|
| 新建 Python 進程 import `router_v1` 是否包含三支路由 | **YES**（完全正確）|
| 目前服務的 `/openapi.json` 是否包含三支路由 | **NO**（完全缺失）|
| uvicorn reloader 進程是否存在 | **NO**（已死亡）|
| HTTP worker 何時啟動 | **2026-03-11 16:58**（3 天前）|
| `api.py` 修改後是否有任何 reload | **NO**（從未觸發）|

---

## 3. 根本原因：完整時間線

```
2026-03-10 18:00  uvicorn 首次啟動
                  reloader PID: 1687903（WatchFiles 模式）
                  worker  PID: 1687905

2026-03-11 16:55  WatchFiles 偵測到 app/modules/attendance/repo.py 變更
                  → Reloading...
                  → Finished server process [1725487]
                  → Started server process [1856041]    ← 最後一次 reload

2026-03-11 16:58  PID 1856041 啟動完成
                  此時 api.py 尚未加入 reporting endpoints

[某時間點]        uvicorn reloader process (PID 1687903) 死亡
                  PID 1856041 被 init (PID 1) 收養（孤兒進程）
                  PPid 從 1687903 變為 1

2026-03-13 19:13  api.py 加入三支 reporting endpoint
                  .pyc 同步更新（mtime: 19:13:27）
                  但 reloader 已死 → WatchFiles 無人監看 → 無 reload

2026-03-14 今日   PID 1856041 仍在服務，記憶體中是 2026-03-11 的舊版 code
                  port 8000 socket（inode 784177950）由 PID 1856041 持有
                  沒有 uvicorn 主進程，沒有 reloader，無法自動 reload
```

---

## 4. 技術細節確認

### 4.1 PID 1856041 是什麼

```
cmdline: /opt/attendance-system/venv/bin/python -c
         from multiprocessing.spawn import spawn_main;
         spawn_main(tracker_fd=7, pipe_handle=12) --multiprocessing-fork
cwd:     /opt/attendance-system/backend
exe:     /usr/bin/python3.11
PPid:    1（init，代表父進程已死）
啟動時間: 2026-03-11 16:58:30
fd=1:    /opt/attendance-system/backend.log
fd=2:    /opt/attendance-system/backend.log
fd=5:    socket:[784177950]（port 8000 LISTEN）
```

PID 1856041 是 uvicorn 的 **multiprocessing worker**（spawn_main fork），是真正在處理 HTTP 請求的進程。它在 2026-03-11 16:58 啟動後，父進程（uvicorn reloader）在某時間點死亡，worker 成為孤兒進程繼續持有 port 8000。

### 4.2 為什麼 api.py 的修改沒有觸發 reload

uvicorn `--reload` 的架構：

```
[reloader process]  監看檔案系統變更
       ↓ 偵測到 app/ 目錄有 .py 變更
[kill worker] → [spawn new worker]  ← 這步無法執行（reloader 已死）
```

reloader 進程死亡後：
- `backend.log` 中最後一筆 `WatchFiles detected changes in 'app/...` 是第 28374 行（`repo.py`，2026-03-11）
- 此後 `api.py` 修改（2026-03-13 19:13）完全沒有觸發任何 reload 記錄
- `backend.log` 末尾也沒有任何 `Started server process` 記錄

### 4.3 新的 Python 進程可以正確載入三支路由

```
$ cd /opt/attendance-system/backend
$ python3 -c "from app.modules.attendance.api import router_v1; \\
              print([r.path for r in router_v1.routes])"

['/api/v1/attendance/reports/company-summary',
 '/api/v1/attendance/reports/user-summary',
 '/api/v1/attendance/sessions',
 ...]
```

**code 本身完全正確**。問題只在於 runtime 進程從未重新載入。

### 4.4 pyc 已是最新版本

```
api.py  mtime: 2026-03-13 19:13:27（Fri Mar 13）
api.pyc mtime: 2026-03-13 19:13:34（Fri Mar 13）
pyc embedded source mtime: 2026-03-13 19:13:27  ← 與 api.py 完全一致
```

**沒有 pyc 舊版本問題**。

---

## 5. 排除的錯誤假設

| 假設 | 結論 |
|------|------|
| 多份 code（錯誤目錄）| 排除：cwd 確認是 `/opt/attendance-system/backend`，唯一的 code base |
| import cache 問題（pyc 過期）| 排除：pyc mtime 與 source 完全一致 |
| router_v1 被覆寫或條件式排除 | 排除：main.py 第 39 行正確 `include_router(attendance_router_v1)` |
| module import 失敗但未報錯 | 排除：新 Python 進程 import 成功，三支路由正確出現 |
| 啟動錯 app | 排除：cwd 正確，fd=1/2 指向 backend.log，確認是同一個 app |

---

## 6. 最小修復路徑

### 修復方式：重新啟動 uvicorn（不需改 code）

**不需要任何 code 修改。** 只需重新啟動 uvicorn 進程即可立即載入三支 reporting endpoint。

#### 方法 A：直接 kill + 重啟（最快）

```bash
# 1. kill 現有孤兒 worker
kill 1856041
kill 1687904  # resource_tracker 也一併清理

# 2. 重新啟動（帶 --reload-dir 限縮監看範圍）
cd /opt/attendance-system/backend
/opt/attendance-system/venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir app \
  --log-level info \
  >> /opt/attendance-system/backend.log 2>&1 &

# 3. 驗證
curl -s http://127.0.0.1:8000/openapi.json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  [print(p) for p in d['paths'] if 'sessions' in p or 'reports' in p]"
```

#### 方法 B：修正 systemd service 再重啟（根本解）

```bash
# 查看 service 狀態與失敗原因
systemctl status attendance-system.service
journalctl -u attendance-system.service -n 50

# 修復後重啟
systemctl restart attendance-system.service
systemctl status attendance-system.service
```

> **注意：** `attendance-system.service` 自 2026-03-06 起 FAILED，
> 需先確認 service 失敗原因，否則 systemctl restart 可能立即再次失敗。
> 若 service 無法修復，用方法 A 手動啟動是最穩健的當下修復方案。

---

## 7. 修復後驗證步驟

```bash
# 確認三支 endpoint 出現
curl -s http://127.0.0.1:8000/openapi.json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  paths=[p for p in d['paths'] if 'sessions' in p or 'reports' in p]; \
  print('Found:', paths)"

# 預期輸出：
# Found: ['/api/v1/attendance/sessions',
#         '/api/v1/attendance/reports/user-summary',
#         '/api/v1/attendance/reports/company-summary']
```

---

## 8. 後續建議

### 8.1 修復 systemd service（防止再次發生）

uvicorn reloader 作為孤兒進程持續運行是不健康的狀態。當 reloader 死亡時，應由 systemd 自動重啟整個服務。需要調查 `attendance-system.service` 自 2026-03-06 起 FAILED 的根本原因並修復。

### 8.2 啟動命令加 `--reload-dir app`

加入 `--reload-dir app` 限縮監看範圍，避免 WatchFiles 監看整個 venv 目錄（過去曾多次因 venv 套件更新觸發無意義的大批量 reload）：

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir app \
  --log-level info
```

### 8.3 生產環境移除 `--reload`

若此機器是生產環境，應移除 `--reload`，改用多 worker 模式並依賴 systemd 管理重啟：

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2
```

---

## 9. 最終結論

| 問題 | 答案 |
|------|------|
| runtime 實際載入的是哪份 code | `/opt/attendance-system/backend/app/` — **但是 2026-03-11 16:58 的記憶體快照**，磁碟上的新版 api.py 從未被 reload 進記憶體 