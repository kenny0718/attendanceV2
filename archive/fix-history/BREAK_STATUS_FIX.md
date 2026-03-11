# 外出打卡狀態修復報告

## 問題描述

用戶反映：**外出打卡後，無法再次進行聯繫（返回）打卡**

## 根本原因分析

### 前端邏輯
前端 (`frontend/src/stores/attendance.js`) 依賴後端 API `/v1/attendance/current-status` 返回的 `is_on_break` 字段來判斷：
- `canBreakOut`: 是否可以外出打卡
- `canBreakIn`: 是否可以返回打卡

```javascript
canBreakOut: (state) => state.todayStatus.is_punched_in && !state.todayStatus.is_on_break && !state.todayStatus.punch_out,
canBreakIn: (state) => state.todayStatus.is_on_break,
```

### 後端問題
後端 API (`backend/app/modules/attendance/api.py`) 的 `get_current_status` 端點：
1. ✅ `CurrentStatusResponse` schema 中定義了 `is_on_break` 字段
2. ❌ **但實際返回時沒有計算和設置這個字段的值**
3. 結果：前端始終收到 `is_on_break = False`（默認值）

## 修復方案

### 修改文件
`/opt/attendance-system/backend/app/modules/attendance/api.py`

### 修改內容

在 `get_current_status` 函數中添加邏輯來檢查用戶是否在外出狀態：

```python
# 檢查用戶是否在外出狀態 (WP-11-07 Phase 3B)
is_on_break = False
last_break_punch = repo.get_last_break_punch(session.id)
if last_break_punch and last_break_punch.punch_type == 'break_start':
    is_on_break = True
```

並在返回 `CurrentStatusResponse` 時包含此字段：

```python
return CurrentStatusResponse(
    has_open_session=True,
    session=session_response,
    elapsed_minutes=elapsed_minutes,
    is_on_break=is_on_break  # 新增
)
```

## 修復時間
2026-03-06 18:06

## 測試驗證

### 預期行為
1. 用戶上班打卡後 → `is_on_break = False`
2. 用戶外出打卡後 → `is_on_break = True`
3. 用戶返回打卡後 → `is_on_break = False`

### 前端按鈕狀態
- 上班打卡後：「外出打卡」按鈕啟用
- 外出打卡後：「返回打卡」按鈕啟用，「外出打卡」按鈕禁用
- 返回打卡後：「外出打卡」按鈕再次啟用

## 相關文件
- `backend/app/modules/attendance/api.py` - API 端點
- `backend/app/modules/attendance/schemas.py` - Response schema
- `backend/app/modules/attendance/repo.py` - 數據庫操作（`get_last_break_punch` 方法）
- `frontend/src/stores/attendance.js` - 前端狀態管理
- `frontend/src/views/Home.vue` - 前端 UI

## 備註
- 後端使用 `--reload` 模式運行，修改後自動重新加載
- 前端使用 Vite HMR，會自動更新
- 無需手動重啟服務
