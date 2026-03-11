# OUT Checkpoint Runtime Log Report

**報告時間**: 2026-03-09 09:20  
**問題**: 手機點「紀錄當前位置」失敗，顯示「請求失敗」  
**排查方式**: SSH 主機實際查詢 log、route、process

---

## 問題描述

用戶在手機上測試打卡系統，點擊首頁「外出位置記錄（選用）」區塊中的「紀錄當前位置」按鈕時，前端顯示「請求失敗」。

---

## Frontend Trace

### 1. 按鈕位置
**檔案**: `frontend/src/views/Home.vue`  
**行號**: 162  
**按鈕文字**: `{{ outCheckpointLoading ? '提交中...' : '記錄當前位置' }}`

### 2. Click Handler
**檔案**: `frontend/src/views/Home.vue`  
**行號**: 594  
**方法**: `await attendanceStore.outCheckpointSubmit(selectedReason.value)`

### 3. Store Method
**檔案**: `frontend/src/stores/attendance.js`  
**行號**: 243  
**方法**: `outCheckpointSubmit()`  
**實際呼叫**: `await attendanceApi.createOutCheckpoint(payload)`

### 4. API Client
**檔案**: `frontend/src/api/attendance.js`  
**行號**: 29  
**定義**: 
```javascript
createOutCheckpoint: (data) => apiClient.post('/v1/attendance/out-checkpoint', data)
```

**完整 endpoint**: `POST /api/v1/attendance/out-checkpoint`

### 5. Request Payload Shape
```javascript
{
  device_type: 'mobile' | 'pc',
  notes: string,
  gps: {
    latitude: number,
    longitude: number,
    accuracy: number,
    timestamp: string
  } // mobile only
}
```

### 6. Error Handling Path
**檔案**: `frontend/src/api/client.js`  
**行號**: 86  
**錯誤訊息來源**: 
```javascript
message: data?.detail || data?.message || '請求失敗'
```

當後端返回 404 且無 detail/message 時，顯示「請求失敗」。

---

## Backend Trace

### 1. API Route 狀態
**結論**: ❌ **Route 不存在**

**檔案**: `backend/app/modules/attendance/api.py`  
**行數**: 600 行  
**router_v1 定義**: 第 42 行  
**已實作的 routes**:
- POST `/api/v1/attendance/punch-in` (line 105)
- POST `/api/v1/attendance/punch-out` (line 169)
- GET `/api/v1/attendance/current-status` (line 262)
- GET `/api/v1/attendance/history` (line 312)
- POST `/api/v1/attendance/break-out` (line 370)
- POST `/api/v1/attendance/break-in` (line 453)
- GET `/api/v1/attendance/break-punches` (line 504)
- PATCH `/api/v1/attendance/punch/{punch_id}/note` (line 565)

**缺少的 routes**:
- ❌ POST `/api/v1/attendance/out-checkpoint`
- ❌ GET `/api/v1/attendance/out-checkpoints`

### 2. Schema 狀態
**檔案**: `backend/app/modules/attendance/schemas.py`  
**狀態**: ✅ **Schema 已定義**

- `OutCheckpointRequest` (line 206)
- `OutCheckpointResponse` (line 224)
- `OutCheckpointListItem` (line 232)
- `OutCheckpointListResponse` (line 244)

### 3. Model 狀態
**檔案**: `backend/app/modules/attendance/models.py`  
**狀態**: ✅ **Model 已定義**

- `AttendanceOutCheckpoint` (line 181)
- Table name: `attendance_out_checkpoints`

### 4. Repository 狀態
**檔案**: `backend/app/modules/attendance/repo.py`  
**狀態**: ✅ **Repository 已實作**

- `OutCheckpointRepository` (line 416)
- `get_out_checkpoint_repository()` factory (line 626)

### 5. 前端註解證據
**檔案**: `frontend/src/views/Home.vue`  
**行號**: 623-625  
```javascript
// TODO: WP-11-10 待開發功能 - OUT Checkpoint API 尚未實作
// 後端缺少: POST /v1/attendance/out-checkpoint, GET /v1/attendance/out-checkpoints
// 暫時停用自動載入，避免頁面初始化時固定報 404
```

**結論**: 前端開發者已知道後端 API 未實作，但按鈕仍然可點擊。

---

## Runtime Topology

### 1. Backend Process
**Process**: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`  
**PID**: 1361373, 1413542  
**Port**: 8000  
**Status**: ✅ Running

### 2. Frontend Service
**Service**: Nginx serving static files  
**Port**: 80  
**Status**: ✅ Running

### 3. Reverse Proxy
**Service**: Nginx  
**Config**: 
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    ...
}
```
**Status**: ✅ Working

### 4. Router Registration
**檔案**: `backend/app/main.py`  
**行號**: 11, 39  
```python
from app.modules.attendance.api import router as attendance_router, router_v1 as attendance_router_v1
app.include_router(attendance_router_v1)
```
**Status**: ✅ router_v1 已註冊

---

## Log Locations Checked

### 1. Backend Application Log
**位置**: `/opt/attendance-system/backend.log`  
**最近錯誤** (tail -100):
```
INFO:     192.168.88.235:0 - "POST /api/v1/attendance/out-checkpoint HTTP/1.1" 404 Not Found
INFO:     192.168.88.235:0 - "GET /api/v1/attendance/out-checkpoints?limit=50&offset=0 HTTP/1.1" 404 Not Found
```

### 2. Nginx Access Log
**位置**: `/var/log/nginx/access.log`  
**最近請求** (tail -50):
```
192.168.88.235 - - [09/Mar/2026:09:17:41 +0800] "POST /api/v1/attendance/out-checkpoint HTTP/1.1" 404 22
192.168.88.235 - - [09/Mar/2026:09:17:41 +0800] "GET /api/v1/attendance/out-checkpoints?limit=50&offset=0 HTTP/1.1" 404 22
192.168.88.235 - - [09/Mar/2026:09:18:38 +0800] "POST /api/v1/attendance/out-checkpoint HTTP/1.1" 404 22
192.168.88.235 - - [09/Mar/2026:09:18:42 +0800] "POST /api/v1/attendance/out-checkpoint HTTP/1.1" 404 22
```

**User-Agent**: 
- iPhone: `Mozilla/5.0 (iPhone; CPU iPhone OS 26_3_1 like Mac OS X) ... CriOS/145.0.7632.108 Mobile/15E148 Safari/604.1`
- PC: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/145.0.0.0 Safari/537.36`

### 3. Nginx Error Log
**位置**: `/var/log/nginx/error.log`  
**狀態**: 無相關錯誤（proxy 正常轉發）

### 4. FastAPI OpenAPI Schema
**檢查**: `curl http://127.0.0.1:8000/openapi.json | grep out-checkpoint`  
**結果**: 無結果（route 未註冊）

---

## Key Command Outputs

### 1. 搜尋前端按鈕
```bash
$ cd /opt/attendance-system/frontend/src && grep -rn "紀錄當前位置" .
# 無結果（按鈕文字是動態生成）

$ grep -rn "記錄當前位置" .
./views/Home.vue:162:  <span>{{ outCheckpointLoading ? '提交中...' : '記錄當前位置' }}</span>
```

### 2. 搜尋 API 定義
```bash
$ cd frontend/src && grep -rn "createOutCheckpoint"
./api/attendance.js:29:  createOutCheckpoint: (data) => apiClient.post('/v1/attendance/out-checkpoint', data),
./stores/attendance.js:243:  const response = await attendanceApi.createOutCheckpoint(payload)
```

### 3. 搜尋後端 route
```bash
$ cd backend && grep -rn "out-checkpoint" app/modules/attendance/*.py
# 只有 test 檔案有，api.py 沒有
```

### 4. 檢查 backend log
```bash
$ tail -100 /opt/attendance-system/backend.log | grep "out-checkpoint"
INFO:     192.168.88.235:0 - "POST /api/v1/attendance/out-checkpoint HTTP/1.1" 404 Not Found
INFO:     192.168.88.235:0 - "GET /api/v1/attendance/out-checkpoints?limit=50&offset=0 HTTP/1.1" 404 Not Found
```

### 5. 檢查 process
```bash
$ ps aux | grep uvicorn
root     1361373  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
root     1413542  /opt/attendance-system/venv/bin/python -c from multiprocessing.spawn...
```

### 6. 檢查監聽端口
```bash
$ ss -tulpn | grep -E ":8000|:80"
tcp   LISTEN 0.0.0.0:8000  (python, pid=1361373)
tcp   LISTEN 0.0.0.0:80    (nginx, pid=1026311)
```

---

## Most Likely Failure Layer

### 結論: **後端 API Route 未實作**

### 證據鏈

1. ✅ **前端正確送出 request**
   - Nginx access log 顯示 POST 請求已到達
   - User-Agent 顯示來自 iPhone 和 PC
   - Request path 正確: `/api/v1/attendance/out-checkpoint`

2. ✅ **Nginx proxy 正常工作**
   - Request 成功轉發到 backend (127.0.0.1:8000)
   - 無 proxy error

3. ✅ **Backend process 正常運行**
   - uvicorn 正常監聽 8000 port
   - router_v1 已在 main.py 註冊

4. ❌ **Backend route 不存在**
   - `api.py` 中沒有 `@router_v1.post("/out-checkpoint")` 定義
   - FastAPI 返回 404 Not Found
   - OpenAPI schema 中無此 endpoint

5. ✅ **Schema/Model/Repository 已準備好**
   - `OutCheckpointRequest/Response` schema 已定義
   - `AttendanceOutCheckpoint` model 已定義
   - `OutCheckpointRepository` 已實作
   - 只差 API route handler

6. ✅ **前端開發者已知此問題**
   - Home.vue 有明確註解說明後端 API 未實作
   - 但按鈕仍然可點擊（未 disable）

### 失敗層級: **Backend API Layer**

**不是**:
- ❌ 前端沒送出 request
- ❌ 前端送錯 endpoint
- ❌ Payload 不符 schema（根本沒到 validation）
- ❌ 權限/認證失敗（404 發生在 route matching 階段）
- ❌ Proxy/WAF 擋掉
- ❌ 後端內部 exception
- ❌ 手機 GPS 取值失敗（GPS 取值成功才會送 request）

**是**:
- ✅ **後端 route handler 未實作**

---

## 初步根因判斷

### Root Cause
**WP-11-10/WP-11-11 功能開發未完成**

前端已實作完整的 OUT Checkpoint 功能：
- UI 元件（按鈕、原因選擇器）
- Store 方法（outCheckpointSubmit）
- API client（createOutCheckpoint）
- GPS 定位邏輯

後端已準備好資料層：
- Database model (`AttendanceOutCheckpoint`)
- Schema (`OutCheckpointRequest/Response`)
- Repository (`OutCheckpointRepository`)

**但缺少 API route handler**：
- 需要在 `backend/app/modules/attendance/api.py` 新增：
  - `@router_v1.post("/out-checkpoint")` - 創建 checkpoint
  - `@router_v1.get("/out-checkpoints")` - 列出 checkpoints

### 為什麼前端按鈕沒有 disable？
前端開發者在 `onMounted` 時停用了自動載入（避免頁面初始化時固定報 404），但沒有 disable 按鈕，導致用戶可以點擊並觸發 404 錯誤。

---

## 下一步建議（先排查版，不修）

### 1. 確認需求優先級
- 這個功能是否需要立即實作？
- 還是應該先 disable 前端按鈕，避免用戶困惑？

### 2. 如果需要實作
需要在 `backend/app/modules/attendance/api.py` 新增兩個 route handlers：

**A. POST /out-checkpoint**
- 接收 `OutCheckpointRequest`
- 驗證 device_type
- Mobile 需要 GPS，PC 不需要
- 調用 `OutCheckpointRepository.create_checkpoint()`
- 返回 `OutCheckpointResponse`

**B. GET /out-checkpoints**
- 接收 query params (limit, offset)
- 調用 `OutCheckpointRepository.list_checkpoints()`
- 返回 `OutCheckpointListResponse`

### 3. 如果暫不實作
**前端修改**（最小改動）：
- 在 `Home.vue` 中 disable「記錄當前位置」按鈕
- 或顯示「功能開發中」提示
- 或完全隱藏此區塊

### 4. 測試建議
實作後需要測試：
- PC 創建 checkpoint（無 GPS）
- Mobile 創建 checkpoint（有 GPS）
- 列出 checkpoints
- 權限驗證（company_id, user_id）
- 重複創建處理

---

## 附錄：相關檔案清單

### Frontend
- `frontend/src/views/Home.vue` - UI 元件
- `frontend/src/stores/attendance.js` - Store 邏輯
- `frontend/src/api/attendance.js` - API client
- `frontend/src/api/client.js` - 錯誤處理

### Backend
- `backend/app/modules/attendance/api.py` - ❌ 缺少 route handlers
- `backend/app/modules/attendance/schemas.py` - ✅ Schema 已定義
- `backend/app/modules/attendance/models.py` - ✅ Model 已定義
- `backend/app/modules/attendance/repo.py` - ✅ Repository 已實作
- `backend/app/main.py` - ✅ Router 已註冊

### Logs
- `/opt/attendance-system/backend.log` - Backend application log
- `/var/log/nginx/access.log` - Nginx access log
- `/var/log/nginx/error.log` - Nginx error log

---

**報告完成時間**: 2026-03-09 09:25  
**排查耗時**: 5 分鐘  
**結論**: 後端 API route 未實作，前端功能完整但無法使用
