# 修復外出打卡記錄顯示問題

**修復日期**: 2026-03-06 18:30  
**問題**: 前端顯示的是"外出打點"記錄，而不是"外出打卡"記錄

---

## 問題分析

### 原始問題
用戶反映：可以連續外出打卡，但記錄顯示有問題

### 根本原因
前端有兩個不同的功能混淆：

1. **外出打卡（break-out/break-in）** - WP-11-07 Phase 3B
   - 傳統的外出/返回打卡功能
   - 記錄在 `attendance_punches` 表中
   - `punch_type` 為 `break_start` 或 `break_end`

2. **外出打點（out-checkpoint）** - WP-11-10
   - 外出期間的位置記錄功能
   - 記錄在 `out_checkpoints` 表中
   - 用於記錄外出期間的多個位置點

前端原本顯示的是 `outCheckpointList`（外出打點），而用戶實際使用的是外出打卡功能。

---

## 修復方案

### 1. 後端新增 API 端點

**文件**: `backend/app/modules/attendance/api.py`

新增 `/break-punches` 端點：

```python
@router_v1.get("/break-punches", response_model=dict)
async def get_break_punches(
    limit: int = 50,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get today's break punches (外出打卡記錄)"""
    # 獲取今日 session 的所有 break_start 和 break_end 記錄
    ...
```

**功能**:
- 獲取當前 session 的所有外出打卡記錄
- 包含 `break_start`（外出）和 `break_end`（返回）
- 按時間倒序排列

---

### 2. 前端 API 調用

**文件**: `frontend/src/api/attendance.js`

新增方法：
```javascript
// 獲取今日外出打卡記錄
getBreakPunches: (params = {}) => apiClient.get('/v1/attendance/break-punches', { params })
```

---

### 3. 前端 Store 修改

**文件**: `frontend/src/stores/attendance.js`

**新增狀態**:
```javascript
breakPunches: [],  // 今日外出打卡記錄
```

**新增方法**:
```javascript
async loadBreakPunches() {
  try {
    const data = await attendanceApi.getBreakPunches({ limit: 50 })
    this.breakPunches = data.punches || []
  } catch (error) {
    console.error('載入外出打卡記錄失敗:', error)
    this.breakPunches = []
  }
}
```

**修改 punch 方法**:
- 外出或返回打卡成功後，自動刷新 `breakPunches`

---

### 4. 前端 UI 修改

**文件**: `frontend/src/views/Home.vue`

**修改前**:
```vue
<h4>今日位置記錄</h4>
<div v-for="checkpoint in outCheckpointList">
  {{ checkpoint.notes }}
</div>
```

**修改後**:
```vue
<h4>今日外出打卡記錄</h4>
<div v-for="punch in breakPunches">
  <span>{{ punch.punch_type === 'break_start' ? '外出' : '返回' }}</span>
  <span>{{ punch.notes }}</span>
  <span>{{ formatTime(punch.punch_time) }}</span>
</div>
```

**顯示內容**:
- 🟡 外出圖標（break_start）
- ✅ 返回圖標（break_end）
- 時間
- 備註（如果有）
- 位置圖標（如果有經緯度）

---

## 功能對比

| 功能 | 外出打卡 (break-out) | 外出打點 (out-checkpoint) |
|------|---------------------|-------------------------|
| 用途 | 記錄外出/返回時間 | 記錄外出期間位置 |
| 表 | attendance_punches | out_checkpoints |
| 類型 | break_start / break_end | - |
| 必須配對 | 否（可連續外出） | 不適用 |
| 位置 | 可選 | 必須（mobile） |
| 顯示 | 今日外出打卡記錄 | 外出位置記錄（選用） |

---

## 測試驗證

### 測試場景

1. **連續外出打卡**
   - 打外出卡 3 次
   - 應該在"今日外出打卡記錄"看到 3 筆 🟡 外出記錄

2. **外出後返回**
   - 打外出卡
   - 打返回卡
   - 應該看到 🟡 外出 + ✅ 返回

3. **自動補返回**
   - 打外出卡
   - 直接打下班卡
   - 應該看到 🟡 外出 + ✅ 返回（備註：自動返回（下班時補））

---

## 部署狀態

- ✅ 後端 API 已添加
- ✅ 前端代碼已修改
- ✅ 前端已重新編譯
- ✅ 後端服務運行中

---

## 備份文件

- `api.py.backup.20260306_182812`
- `attendance.js.backup.20260306_183022`
- `Home.vue.backup.20260306_183047`

---

## 使用說明

### 用戶操作

1. 清除瀏覽器緩存（Ctrl+F5）
2. 打外出卡
3. 查看"今日外出打卡記錄"區塊
4. 應該看到外出記錄，包含時間和圖標

### 記錄說明

- 🟡 **外出**: 表示外出打卡（break_start）
- ✅ **返回**: 表示返回打卡（break_end）
- 📍 **位置圖標**: 表示有記錄 GPS 位置
- **時間**: 打卡時間（HH:mm 格式）
- **備註**: 如果有備註會顯示

---

## 注意事項

1. **兩個功能並存**:
   - "外出打卡"（break-out/break-in）- 主要功能
   - "外出位置記錄"（out-checkpoint）- 選用功能

2. **數據來源不同**:
   - 外出打卡記錄來自 `/break-punches` API
   - 外出位置記錄來自 `/out-checkpoints` API

3. **顯示邏輯**:
   - 外出打卡記錄：顯示所有 break_start 和 break_end
   - 外出位置記錄：顯示 out-checkpoint（如果有使用）

---

**修復完成時間**: 2026-03-06 18:30  
**狀態**: ✅ 已完成，待測試
