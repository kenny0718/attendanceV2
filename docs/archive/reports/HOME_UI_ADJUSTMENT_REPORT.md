# Home.vue UI 調整完成報告

## 執行時間
2025-03-09 10:45

## 目標
調整首頁打卡操作版面：
- 上班/下班打卡分離為獨立區塊
- 外出/返回打卡獨立成新區塊
- 外出打卡必填原因

---

## UI Layout Changes Made

### 1. 打卡操作區塊（主區塊）
**修改前：** 4個按鈕（上班、下班、外出、返回）混在一起
**修改後：** 只保留2個按鈕
- ✅ 上班打卡
- ✅ 下班打卡

### 2. 新增「外出 / 返回」獨立區塊
**位置：** 在「打卡操作」區塊下方
**結構：**
```
外出 / 返回 Card
├── 外出原因輸入區
│   ├── Label: "外出原因"
│   └── Input: placeholder="請輸入外出原因", maxlength=50
├── 按鈕區（2個按鈕）
│   ├── 外出打卡（左）
│   └── 返回打卡（右）
└── 提示訊息
    ├── 目前外出中
    ├── 可進行外出打卡
    └── 請先完成上班打卡
```

### 3. 移除的 UI 元素
- ❌ OUT Checkpoint 區塊（外出位置記錄）
- ❌ 原因選擇器（preset chips）
- ❌ 自訂原因管理
- ❌ 編輯備註對話框

---

## How breakOutReason is Stored and Validated

### 狀態變數
```javascript
const breakOutReason = ref('')
```

### 驗證邏輯（在 handleBreakOutPunch 中）
```javascript
// 驗證外出原因
if (!breakOutReason.value.trim()) {
  errorMessage.value = '請先輸入外出原因'
  showErrorMessage.value = true
  setTimeout(() => {
    showErrorMessage.value = false
  }, 3000)
  return
}
```

### 清空規則
- ✅ 外出打卡成功後：清空 `breakOutReason.value = ''`
- ✅ 返回打卡成功後：清空 `breakOutReason.value = ''`

---

## How Break-Out Request Now Sends the Reason

### 修改前
```javascript
await attendanceStore.punchWithLocation('BREAK_OUT', {
  notes: '',  // 固定空字串
  gps: gpsData
})
```

### 修改後
```javascript
await attendanceStore.punchWithLocation('BREAK_OUT', {
  notes: breakOutReason.value.trim(),  // 帶入使用者輸入的原因
  gps: gpsData
})
```

### 流程
1. 使用者在「外出原因」欄位輸入文字
2. 點擊「外出打卡」按鈕
3. 前端驗證：原因不可為空
4. 取得 GPS 定位（如需要）
5. 呼叫 `punchWithLocation('BREAK_OUT', { notes: 原因, gps: 定位 })`
6. 成功後清空原因欄位

---

## How Break-In Behaves Now

### 新增專用處理函數
```javascript
const handleBreakInPunch = async () => {
  attendanceStore.clearError()
  
  try {
    // 返回打卡不需要原因，直接處理
    await attendanceStore.punch('BREAK_IN', '')
    
    // 成功後清空原因欄位
    breakOutReason.value = ''
    
    // 顯示成功訊息
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('返回打卡失敗:', error)
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
    showErrorMessage.value = true
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}
```

### 行為特點
- ✅ 不需要驗證原因
- ✅ 直接呼叫 `attendanceStore.punch('BREAK_IN', '')`
- ✅ 成功後清空原因欄位（避免殘留）
- ✅ 不需要 GPS 定位

---

## Build Result

```
✓ built in 2.14s

dist/index.html                   0.45 kB │ gzip:  0.33 kB
dist/assets/Login-hZZlHQDw.css    0.11 kB │ gzip:  0.12 kB
dist/assets/Home-D-Rgyw19.css     2.99 kB │ gzip:  0.91 kB
dist/assets/index-BRZIRz48.css   12.33 kB │ gzip:  3.30 kB
dist/assets/Login-BrDZTSfO.js     3.10 kB │ gzip:  1.38 kB
dist/assets/Home-p73r1fk5.js     26.84 kB │ gzip: 10.12 kB
dist/assets/index-CxbRHBo3.js   137.16 kB │ gzip: 53.49 kB
```

**狀態：** ✅ 0 errors, 0 warnings

---

## Screens/Sections Affected

### 修改的檔案
- `frontend/src/views/Home.vue` (517 lines)

### 受影響的區塊

#### Template 部分
1. **打卡操作 Card** - 移除外出/返回按鈕
2. **新增外出/返回 Card** - 包含原因輸入和按鈕
3. **移除編輯對話框** - 不再需要

#### Script 部分
1. **新增狀態變數**
   - `breakOutReason` - 外出原因

2. **修改的函數**
   - `handlePunch()` - 移除 BREAK_OUT 特殊處理
   - `handleBreakOutPunch()` - 添加原因驗證，使用 breakOutReason

3. **新增的函數**
   - `handleBreakInPunch()` - 返回打卡專用處理

4. **移除的函數**
   - `selectReason()`
   - `addCustomReason()`
   - `removeCustomReason()`
   - `handleOutCheckpoint()`
   - `editPunchNote()`
   - `saveEditedNote()`
   - `cancelEdit()`

5. **移除的變數**
   - `selectedReason`
   - `newCustomReason`
   - `editingPunch`
   - `editingNote`
   - `showEditDialog`
   - `outCheckpointList`
   - `outCheckpointLoading`
   - `reasonPresets`
   - `reasonCustoms`
   - `lastSelectedReason`

---

## 驗證清單

- ✅ npm run build 成功
- ✅ 首頁正常渲染
- ✅ 「打卡操作」主區塊只剩上班/下班
- ✅ 新的「外出 / 返回」區塊存在
- ✅ 外出原因欄位在按鈕上方
- ✅ 未輸入原因時，外出打卡會顯示錯誤訊息
- ✅ 已輸入原因時，外出打卡會帶入 notes 參數
- ✅ 返回打卡不需原因即可送出
- ✅ 不再出現 out-checkpoint 相關 UI
- ✅ 成功後清空原因欄位

---

## 未修改的部分

- ✅ 沿用既有 break-out / break-in API
- ✅ 沿用既有 GPS 定位邏輯
- ✅ 沿用既有 store 方法
- ✅ 未新增後端 API
- ✅ 未修改後端 schema

---

## 備份檔案

- `Home.vue.before_out_checkpoint_removal` - 移除 OUT Checkpoint 前
- `Home.vue.after_ui_adjustment` - UI 調整完成後

