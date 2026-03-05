# WP-11-07 UI MVP Phase 2 - API Integration Test Log

**測試日期**: 2026-03-05  
**測試人員**: AI Assistant  
**測試環境**: Development  

---

## 📋 測試環境設定

### Backend 配置
- **API Base URL**: `http://localhost:8000/api`
- **Backend Status**: Running on port 8000 (uvicorn)
- **Database**: PostgreSQL (attendance_test)

### Frontend 配置
- **Dev Server**: `http://localhost:5173` (需要 npm run dev)
- **API Proxy**: Vite proxy `/api` → `http://localhost:8000`
- **Environment**: Development (`.env.development`)

### 認證設定
- **認證方式**: Header-based (X-Company-ID, X-User-ID)
- **Token 來源**: localStorage (MVP 階段使用 mock token)
- **Tenant Headers**:
  - `X-Company-ID`: 從 `authStore.companyId` 取得 (預設: "company-a")
  - `X-User-ID`: 從 `authStore.userId` 取得 (預設: mock user id)

### Mock User 資料
```javascript
{
  id: '1',
  name: '張三',
  company_id: 'company-a',
  role: 'employee'
}
```

---

## 🎯 API Endpoints 對應

| 功能 | Frontend Method | Backend Endpoint | HTTP Method |
|------|----------------|------------------|-------------|
| 上班打卡 | `attendanceApi.punchIn()` | `/api/v1/attendance/punch-in` | POST |
| 下班打卡 | `attendanceApi.punchOut()` | `/api/v1/attendance/punch-out` | POST |
| 獲取狀態 | `attendanceApi.getCurrentStatus()` | `/api/v1/attendance/current-status` | GET |
| 獲取記錄 | `attendanceApi.getHistory()` | `/api/v1/attendance/history` | GET |

**注意**: 外出/返回功能暫時不支援（後端無對應 endpoints）

---

## ✅ 測試流程 1: 正常打卡流程

### 1.1 頁面初始載入

**操作**: 訪問 `http://localhost:5173`

**預期行為**:
- 自動呼叫 `getCurrentStatus()` 獲取今日狀態
- 自動呼叫 `getHistory()` 獲取最近記錄
- 顯示 4 張狀態卡（全部顯示 "-"）
- 上班打卡按鈕啟用，其他按鈕禁用

**實際結果** (需實際測試):
```
[ ] 頁面正常載入
[ ] API 請求成功
[ ] 狀態卡顯示正確
[ ] 按鈕狀態正確
```

**API Request**:
```http
GET /api/v1/attendance/current-status
Headers:
  X-Company-ID: company-a
  X-User-ID: 1
```

**API Response** (預期):
```json
{
  "has_open_session": false,
  "session": null,
  "elapsed_minutes": null
}
```

---

### 1.2 上班打卡

**操作**: 點擊「上班打卡」按鈕

**預期行為**:
- 顯示 Loading 動畫
- 呼叫 `punchIn()` API
- 成功後顯示綠色 Toast "✓ 打卡成功"
- 自動刷新狀態和記錄
- 上班時間卡顯示時間（例如 "09:00"）
- 上班打卡按鈕禁用，下班打卡按鈕啟用

**實際結果** (需實際測試):
```
[ ] Loading 動畫顯示
[ ] API 請求成功
[ ] Toast 提示顯示
[ ] 狀態卡更新正確
[ ] 按鈕狀態切換正確
[ ] 記錄列表新增一筆
```

**API Request**:
```http
POST /api/v1/attendance/punch-in
Headers:
  X-Company-ID: company-a
  X-User-ID: 1
  Content-Type: application/json
Body:
{
  "notes": ""
}
```

**API Response** (預期):
```json
{
  "session_id": "uuid-xxx",
  "user_id": "1",
  "company_id": "company-a",
  "punch_in_time": "2026-03-05T09:00:00+08:00",
  "punch_out_time": null,
  "duration_minutes": null,
  "status": "open"
}
```

---

### 1.3 下班打卡

**操作**: 點擊「下班打卡」按鈕

**預期行為**:
- 顯示 Loading 動畫
- 呼叫 `punchOut()` API
- 成功後顯示綠色 Toast "✓ 打卡成功"
- 自動刷新狀態和記錄
- 下班時間卡顯示時間（例如 "18:00"）
- 所有打卡按鈕禁用（今日打卡已完成）

**實際結果** (需實際測試):
```
[ ] Loading 動畫顯示
[ ] API 請求成功
[ ] Toast 提示顯示
[ ] 狀態卡更新正確
[ ] 按鈕全部禁用
[ ] 記錄列表新增一筆
[ ] 提示訊息顯示「今日打卡已完成」
```

**API Request**:
```http
POST /api/v1/attendance/punch-out
Headers:
  X-Company-ID: company-a
  X-User-ID: 1
  Content-Type: application/json
Body:
{
  "notes": ""
}
```

**API Response** (預期):
```json
{
  "session_id": "uuid-xxx",
  "user_id": "1",
  "company_id": "company-a",
  "punch_in_time": "2026-03-05T09:00:00+08:00",
  "punch_out_time": "2026-03-05T18:00:00+08:00",
  "duration_minutes": 540,
  "status": "closed",
  "policy_evaluation": {
    "is_late": false,
    "late_minutes": 0,
    ...
  }
}
```

---

## ❌ 測試流程 2: 錯誤情境

### 2.1 錯誤情境：重複打卡 (409 Conflict)

**操作**: 
1. 已經打過上班卡
2. 再次點擊「上班打卡」按鈕

**預期行為**:
- API 返回 409 錯誤
- 顯示紅色錯誤 Toast
- 錯誤訊息：「已有打開的打卡記錄，請勿重複打卡」
- 自動刷新狀態（確保 UI 與後端同步）
- 狀態卡不會變成錯誤狀態

**實際結果** (需實際測試):
```
[ ] API 返回 409
[ ] 錯誤 Toast 顯示
[ ] 錯誤訊息正確
[ ] 狀態自動刷新
[ ] UI 狀態正確
```

**API Response** (預期):
```json
{
  "detail": {
    "error": "Already have an open session",
    "error_code": "ALREADY_OPEN_SESSION",
    "open_session_id": "uuid-xxx",
    "punch_in_time": "2026-03-05T09:00:00+08:00"
  }
}
```

**Frontend 錯誤處理**:
```javascript
// stores/attendance.js
case 409:
  errorMessage = '已有打開的打卡記錄，請勿重複打卡'
  // 自動刷新狀態
  await this.fetchTodayStatus()
```

---

### 2.2 錯誤情境：未打卡就下班 (404 Not Found)

**操作**: 
1. 未打上班卡
2. 直接點擊「下班打卡」按鈕

**預期行為**:
- API 返回 404 錯誤
- 顯示紅色錯誤 Toast
- 錯誤訊息：「找不到打開的打卡記錄，請先打上班卡」
- 自動刷新狀態
- 按鈕狀態恢復正確（上班按鈕啟用）

**實際結果** (需實際測試):
```
[ ] API 返回 404
[ ] 錯誤 Toast 顯示
[ ] 錯誤訊息正確
[ ] 狀態自動刷新
[ ] 按鈕狀態正確
```

**API Response** (預期):
```json
{
  "detail": {
    "error": "No open session found",
    "error_code": "NO_OPEN_SESSION"
  }
}
```

**Frontend 錯誤處理**:
```javascript
// stores/attendance.js
case 404:
  errorMessage = '找不到打開的打卡記錄，請先打上班卡'
  // 自動刷新狀態
  await this.fetchTodayStatus()
```

---

### 2.3 錯誤情境：無權限 (403 Forbidden)

**操作**: 
1. 移除 token 或修改 company_id
2. 點擊任意打卡按鈕

**預期行為**:
- API 返回 403 錯誤
- 顯示紅色錯誤 Toast
- 錯誤訊息：「無權限執行此操作，請檢查登入狀態或公司設定」
- 可能需要跳轉到登入頁（未來實作）

**實際結果** (需實際測試):
```
[ ] API 返回 403
[ ] 錯誤 Toast 顯示
[ ] 錯誤訊息正確
```

**模擬方式**:
```javascript
// 在瀏覽器 Console 執行
localStorage.removeItem('token')
// 或
const authStore = useAuthStore()
authStore.mockUser.company_id = 'invalid-company'
```

**Frontend 錯誤處理**:
```javascript
// stores/attendance.js
case 403:
  errorMessage = '無權限執行此操作，請檢查登入狀態或公司設定'
```

---

### 2.4 錯誤情境：網路錯誤

**操作**: 
1. 停止後端服務
2. 點擊任意打卡按鈕

**預期行為**:
- 顯示紅色錯誤 Toast
- 錯誤訊息：「網絡連接失敗，請檢查網絡設定」
- 不會造成 UI 崩潰

**實際結果** (需實際測試):
```
[ ] 錯誤 Toast 顯示
[ ] 錯誤訊息正確
[ ] UI 不崩潰
```

---

## 📊 測試結果摘要

### 功能測試

| 測試項目 | 狀態 | 備註 |
|---------|------|------|
| 頁面初始載入 | ⏳ 待測試 | 需要 npm install + npm run dev |
| 上班打卡 | ⏳ 待測試 | 需要後端運行 |
| 下班打卡 | ⏳ 待測試 | 需要後端運行 |
| 狀態卡更新 | ⏳ 待測試 | |
| 記錄列表更新 | ⏳ 待測試 | |
| Loading 動畫 | ⏳ 待測試 | |
| 成功 Toast | ⏳ 待測試 | |

### 錯誤處理測試

| 錯誤類型 | HTTP 狀態碼 | 狀態 | 備註 |
|---------|------------|------|------|
| 重複打卡 | 409 | ⏳ 待測試 | |
| 未打卡就下班 | 404 | ⏳ 待測試 | |
| 無權限 | 403 | ⏳ 待測試 | |
| 網路錯誤 | - | ⏳ 待測試 | |
| 伺服器錯誤 | 500 | ⏳ 待測試 | |

---

## 🔧 已知限制

### Phase 2 範圍限制
1. **外出/返回功能未實作**
   - 原因：後端無對應 endpoints
   - 狀態：按鈕已禁用，顯示「開發中」提示
   - 未來：需要後端新增 `/break-out` 和 `/break-in` endpoints

2. **JWT 認證未完整整合**
   - 當前：使用 header-based auth (X-Company-ID, X-User-ID)
   - Mock user 資料寫在 authStore
   - 未來：需要實作完整的登入流程

3. **GPS 定位功能未實作**
   - API 支援 location 參數，但前端未實作
   - 未來：可使用 Geolocation API

---

## 🚀 如何執行測試

### 1. 啟動後端服務

```bash
cd /opt/attendance-system/backend
source ../venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

確認後端運行：
```bash
curl http://localhost:8000/api/v1/attendance/current-status \
  -H "X-Company-ID: company-a" \
  -H "X-User-ID: 1"
```

### 2. 安裝前端依賴

```bash
cd /opt/attendance-system/frontend
npm install
```

### 3. 啟動前端開發服務器

```bash
npm run dev
```

訪問：http://localhost:5173

### 4. 執行測試流程

按照上述測試流程逐一測試，並記錄結果。

---

## 📝 測試檢查清單

### 基本功能
- [ ] 頁面可以正常載入
- [ ] 狀態卡顯示正確
- [ ] 上班打卡成功
- [ ] 下班打卡成功
- [ ] 記錄列表更新
- [ ] Loading 動畫顯示
- [ ] 成功 Toast 顯示

### 錯誤處理
- [ ] 409 錯誤正確處理
- [ ] 404 錯誤正確處理
- [ ] 403 錯誤正確處理
- [ ] 網路錯誤正確處理
- [ ] 錯誤後狀態自動刷新

### UI/UX
- [ ] 按鈕禁用邏輯正確
- [ ] 提示訊息正確顯示
- [ ] 錯誤訊息友善易懂
- [ ] 不會重複點擊
- [ ] 響應式佈局正常

---

## 🎯 下一步

### Phase 2 完成後
- [ ] 所有測試項目通過
- [ ] 更新測試結果到本文件
- [ ] 更新 GATE_PROGRESS_TRACKER.md
- [ ] 更新 NEXT_WP_TICKET.md

### Phase 3 規劃
- 外出/返回功能（需後端支援）
- GPS 定位功能
- 照片上傳功能
- 其他頁面（個人資料、請假、補打卡）
- JWT 認證整合

---

**測試報告生成時間**: 2026-03-05  
**報告作者**: AI Assistant  
**狀態**: 待實際測試  
**備註**: 需要 Node.js 環境才能執行前端測試
