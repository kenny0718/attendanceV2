# 外出功能恢復完成報告

## 執行時間
2025-03-09 10:50

## 目標
補回被誤刪的外出打卡相關功能，但不恢復錯誤的 OUT Checkpoint 功能

---

## 1. What features were wrongly removed

在之前移除 OUT Checkpoint 時，以下屬於正常 break-out / break-in 流程的功能被誤刪：

### 誤刪的功能
- ❌ 外出原因快速選擇（常用原因 chips）
- ❌ 自訂原因新增與管理
- ❌ 外出 / 返回紀錄查看
- ❌ 外出紀錄編輯功能
- ❌ GPS 座標顯示與地圖連結

### 應該刪除且已正確刪除
- ✅ OUT Checkpoint 獨立打點功能
- ✅ `createOutCheckpoint` API
- ✅ `listOutCheckpoints` API
- ✅ 「紀錄當前位置」按鈕

---

## 2. What reason quick-add / quick-select features were restored

### A. 常用原因快速選擇
**位置：** 外出 / 返回區塊上方

**功能：**
- 預設常用原因：拜訪客戶、外出洽公、外出開會、銀行辦事
- 點擊即可快速帶入外出原因欄位
- 選中狀態會高亮顯示（藍色背景）

**實作：**
```javascript
// Store state
reasonPresets: ['拜訪客戶', '外出洽公', '外出開會', '銀行辦事']

// Template
<button
  v-for="reason in reasonPresets"
  @click="selectReason(reason)"
  :class="breakOutReason === reason ? 'bg-primary text-white' : 'bg-gray-100'"
>
  {{ reason }}
</button>
```

### B. 自訂原因管理
**位置：** 常用原因下方

**功能：**
- 使用者可新增自己的常用原因
- 自訂原因會顯示在獨立區域（淺藍色背景）
- 每個自訂原因旁有「✕」按鈕可移除
- 自訂原因保存在 localStorage，重新整理後仍保留

**實作：**
```javascript
// Store methods
addCustomReason(reason) {
  this.reasonCustoms.push(reason)
  this.saveReasonsToLocalStorage()
}

removeCustomReason(reason) {
  const index = this.reasonCustoms.indexOf(reason)
  if (index > -1) {
    this.reasonCustoms.splice(index, 1)
    this.saveReasonsToLocalStorage()
  }
}

saveReasonsToLocalStorage() {
  localStorage.setItem('customBreakReasons', JSON.stringify(this.reasonCustoms))
}

hydrateReasonsFromLocalStorage() {
  const saved = localStorage.getItem('customBreakReasons')
  if (saved) {
    this.reasonCustoms = JSON.parse(saved)
  }
}
```

### C. 新增自訂原因輸入框
**位置：** 外出原因輸入欄下方

**功能：**
- 輸入框 + 「＋新增」按鈕
- 按 Enter 或點擊按鈕即可新增
- 新增後自動帶入外出原因欄位
- 空白時按鈕禁用

---

## 3. How break-out reason is now stored and sent

### 儲存方式
```javascript
// 前端狀態
const breakOutReason = ref('')  // 當前輸入的原因

// Store 狀態
reasonPresets: ['拜訪客戶', '外出洽公', '外出開會', '銀行辦事']  // 固定
reasonCustoms: []  // 從 localStorage 載入
```

### 驗證與發送
```javascript
const handleBreakOutPunch = async () => {
  // 1. 驗證原因不可為空
  if (!breakOutReason.value.trim()) {
    errorMessage.value = '請先輸入外出原因'
    showErrorMessage.value = true
    return
  }

  // 2. 取得 GPS
  const gpsData = await getLocationIfRequired()
  
  // 3. 發送到後端
  await attendanceStore.punchWithLocation('BREAK_OUT', {
    notes: breakOutReason.value.trim(),  // 原因帶入 notes 欄位
    gps: gpsData
  })
  
  // 4. 成功後清空
  breakOutReason.value = ''
}
```

### 流程
1. 使用者選擇常用原因或輸入自訂原因
2. 點擊「外出打卡」
3. 前端驗證原因非空
4. 取得 GPS 定位
5. 呼叫既有 `punchWithLocation('BREAK_OUT', { notes, gps })`
6. 原因保存在 `punch.notes` 欄位
7. 成功後清空原因欄位

---

## 4. What break record view was restored

### 外出 / 返回紀錄列表
**位置：** 外出 / 返回區塊下方

**顯示內容：**
- 今日最近 10 筆外出 / 返回紀錄
- 每筆記錄顯示：
  - 類型圖示（外出：⊖ 橙色 / 返回：✓ 綠色）
  - 類型文字（外出 / 返回）
  - 打卡時間（HH:mm 格式）
  - 原因 / 備註（若有）
  - Google Maps 連結（若有 GPS）
  - 編輯按鈕（僅外出記錄）

**資料來源：**
```javascript
// Store
async loadBreakPunches() {
  const data = await attendanceApi.getBreakPunches({ limit: 50 })
  this.breakPunches = data.punches || []
}

// API
getBreakPunches: (params = {}) => 
  apiClient.get('/v1/attendance/break-punches', { params })
```

**Template 結構：**
```vue
<div v-if="breakPunches.length > 0" class="break-records">
  <h4>今日外出 / 返回紀錄</h4>
  <div v-for="punch in breakPunches.slice(0, 10)">
    <!-- 類型圖示 -->
    <!-- 時間與原因 -->
    <!-- Google Maps 連結 -->
    <!-- 編輯按鈕 -->
  </div>
</div>
```

---

## 5. Whether break record edit was restored or blocked by missing backend support

### ✅ 編輯功能已成功恢復

**後端支援：**
- API 已存在：`PATCH /v1/attendance/punch/{punchId}/note`
- 方法：`attendanceApi.updatePunchNote(punchId, { notes })`

**前端實作：**

#### 編輯對話框
```vue
<div v-if="showEditDialog" class="fixed inset-0 bg-black bg-opacity-50">
  <div class="bg-white rounded-lg p-6">
    <h3>編輯外出原因</h3>
    <input v-model="editingNote" />
    <button @click="saveEditedNote">保存</button>
    <button @click="cancelEdit">取消</button>
  </div>
</div>
```

#### 編輯流程
```javascript
// 1. 點擊編輯按鈕
const editPunchNote = (punch) => {
  if (punch.punch_type !== 'break_start') return  // 僅外出記錄可編輯
  
  editingPunch.value = punch
  editingNote.value = punch.notes || ''
  showEditDialog.value = true
}

// 2. 保存編輯
const saveEditedNote = async () => {
  await attendanceApi.updatePunchNote(editingPunch.value.punch_id, {
    notes: editingNote.value
  })
  
  // 更新本地數據
  const index = breakPunches.value.findIndex(p => p.punch_id === editingPunch.value.punch_id)
  if (index !== -1) {
    breakPunches.value[index].notes = editingNote.value
  }
  
  // 關閉對話框
  showEditDialog.value = false
}
```

**限制：**
- 僅外出記錄（`break_start`）可編輯
- 返回記錄（`break_end`）不顯示編輯按鈕

---

## 6. Which GPS fields were used

### GPS 欄位名稱
```javascript
punch.location_lat  // 緯度
punch.location_lng  // 經度
```

### 檢查邏輯
```vue
<a
  v-if="punch.location_lat && punch.location_lng"
  :href="`https://www.google.com/maps?q=${punch.location_lat},${punch.location_lng}`"
  target="_blank"
>
  地圖
</a>
```

### 資料來源
- 外出打卡時，`punchWithLocation` 會將 GPS 座標保存到資料庫
- `getBreakPunches` API 返回的每筆記錄包含 `location_lat` 和 `location_lng`

---

## 7. How Google Maps link is rendered in the break record list

### UI 設計
**位置：** 每筆外出 / 返回記錄右側

**顯示條件：**
- 僅當 `punch.location_lat && punch.location_lng` 存在時顯示
- 無 GPS 的記錄不顯示地圖按鈕

**樣式：**
```vue
<a
  v-if="punch.location_lat && punch.location_lng"
  :href="`https://www.google.com/maps?q=${punch.location_lat},${punch.location_lng}`"
  target="_blank"
  rel="noopener noreferrer"
  class="text-xs text-primary hover:text-primary-dark flex items-center gap-1 px-2 py-1 rounded hover:bg-primary-lighter transition-colors"
  title="在 Google Maps 開啟"
>
  <svg class="w-4 h-4"><!-- 地圖圖示 --></svg>
  <span>地圖</span>
</a>
```

**行為：**
- 點擊後在新分頁開啟 Google Maps
- URL 格式：`https://www.google.com/maps?q={lat},{lng}`
- 地圖會自動定位到該座標並顯示標記

**手機優化：**
- 按鈕大小適中（px-2 py-1）
- 觸控區域足夠大
- hover 效果在手機上也能正常顯示

---

## 8. Confirmed removed checkpoint items still not restored

### ✅ 以下項目確認未恢復

#### API 層面
- ❌ `POST /v1/attendance/out-checkpoint`
- ❌ `GET /v1/attendance/out-checkpoints`
- ❌ `createOutCheckpoint`
- ❌ `listOutCheckpoints`

#### Store 層面
- ❌ `outCheckpointList`
- ❌ `outCheckpointLoading`
- ❌ `canCreateOutCheckpoint`
- ❌ `outCheckpointSubmit`

#### UI 層面
- ❌ 「外出位置記錄（選用）」區塊
- ❌ 「紀錄當前位置」按鈕
- ❌ OUT Checkpoint 專用列表

#### 函數層面
- ❌ `handleOutCheckpoint()`

### 驗證方式
```bash
grep -i "out-checkpoint\|outCheckpoint\|handleOutCheckpoint" Home.vue
# 結果：無匹配
```

---

## 9. Build result

```
✓ built in 2.33s

dist/index.html                   0.45 kB │ gzip:  0.33 kB
dist/assets/Login-hZZlHQDw.css    0.11 kB │ gzip:  0.12 kB
dist/assets/Home-CgUzVMfx.css     3.48 kB │ gzip:  0.99 kB
dist/assets/index-CFZIy2e7.css   14.54 kB │ gzip:  3.70 kB
dist/assets/Login-BPbxBGqq.js     3.10 kB │ gzip:  1.38 kB
dist/assets/Home-DHFABzv_.js     33.68 kB │ gzip: 12.09 kB
dist/assets/index-CyGwGa9z.js   137.46 kB │ gzip: 53.64 kB
```

**狀態：** ✅ 0 errors, 0 warnings

---

## 修改的檔案

### 1. frontend/src/stores/attendance.js
**新增：**
- `reasonPresets` - 常用原因陣列
- `reasonCustoms` - 自訂原因陣列
- `addCustomReason()` - 新增自訂原因
- `removeCustomReason()` - 移除自訂原因
- `saveReasonsToLocalStorage()` - 保存到 localStorage
- `hydrateReasonsFromLocalStorage()` - 從 localStorage 載入

### 2. frontend/src/views/Home.vue (816 lines)
**新增 Template：**
- 常用原因快速選擇器（chips）
- 自訂原因顯示與移除
- 新增自訂原因輸入框
- 外出 / 返回紀錄列表
- Google Maps 連結
- 編輯按鈕
- 編輯外出原因對話框

**新增 Script：**
- `newCustomReason` - 新增原因輸入
- `showEditDialog` - 對話框顯示狀態
- `editingPunch` - 正在編輯的記錄
- `editingNote` - 編輯中的備註
- `selectReason()` - 選擇原因
- `addCustomReason()` - 新增自訂原因
- `removeCustomReason()` - 移除自訂原因
- `editPunchNote()` - 開啟編輯對話框
- `saveEditedNote()` - 保存編輯
- `cancelEdit()` - 取消編輯

**新增 Style：**
- `.reason-chip` - 原因按鈕樣式
- `.remove-btn` - 移除按鈕樣式
- `.record-item` - 記錄項目樣式
- `.break-records` - 記錄列表動畫

---

## 驗證清單

- ✅ `npm run build` 成功
- ✅ 首頁正常渲染
- ✅ 外出原因可輸入
- ✅ 常用原因可快速點選
- ✅ 可新增自訂原因
- ✅ 自訂原因保存在 localStorage
- ✅ 外出打卡未輸入原因時顯示錯誤
- ✅ 外出打卡有原因時，原因會帶入 request
- ✅ 首頁可看到外出 / 返回紀錄
- ✅ 可編輯外出記錄原因
- ✅ 有 GPS 的記錄顯示 Google Maps 連結
- ✅ 點擊 Google Maps 連結正確開啟
- ✅ 無 GPS 的記錄不顯示地圖按鈕
- ✅ 不出現 OUT Checkpoint 相關 API 呼叫

---

## 總結

成功恢復了所有屬於正常 break-out / break-in 流程的功能，包括：
1. 外出原因快速選擇與管理
2. 外出 / 返回紀錄查看
3. 外出紀錄編輯
4. GPS 座標的 Google Maps 連結

同時確保沒有恢復任何 OUT Checkpoint 相關的錯誤功能。所有修改僅涉及前端，未新增任何後端 API 或修改 schema。
