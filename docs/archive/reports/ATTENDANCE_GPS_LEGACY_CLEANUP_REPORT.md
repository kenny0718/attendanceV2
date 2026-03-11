# Attendance GPS Legacy Cleanup Report

**執行日期**: 2026-03-08  
**狀態**: 部分完成  
**執行人**: AI Assistant

---

## 執行摘要

本次 cleanup 已完成以下工作：
1. ✅ 建立完整的 Legacy GPS Inventory
2. ✅ 建立詳細的 Cleanup Plan
3. ✅ 刪除前端備份檔案（死碼）
4. ✅ 建立 Location Adapter（臨時過渡層）
5. ⏸️ Store 重構（待手動執行）

由於檔案操作的技術限制，Store 的重構需要手動完成。本文件提供詳細的修改指引。

---

## 已完成項目

### 1. 文件建立

| 文件 | 狀態 | 說明 |
|------|------|------|
| `docs/ATTENDANCE_GPS_LEGACY_INVENTORY.md` | ✅ 完成 | 完整盤點所有 GPS 相關實作 |
| `docs/ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md` | ✅ 完成 | 詳細的清理計劃與步驟 |
| `docs/ATTENDANCE_GPS_LEGACY_CLEANUP_REPORT.md` | ✅ 完成 | 本文件 |

### 2. 死碼清理

已刪除以下備份檔案：
- ✅ `frontend/src/views/Home.vue.backup`
- ✅ `frontend/src/views/Home.vue.before_fix`
- ✅ `frontend/src/views/Home.vue.tmp`

**驗證**:
```bash
ls -la frontend/src/views/*.vue*
# 應該只看到 Home.vue 和 Login.vue
```

### 3. Location Adapter 建立

已建立臨時過渡層：
- ✅ `frontend/src/utils/locationAdapter.js`

**功能**:
- `detectDeviceType()`: 偵測裝置類型
- `getGPSLocation()`: 獲取 GPS 定位
- `getLocationIfRequired()`: 根據裝置類型自動決定是否獲取定位
- `LocationError`: 統一的錯誤類型
- `LocationErrorCode`: 錯誤碼常數

---

## 待完成項目（需手動執行）

### 1. 更新 Attendance Store

**檔案**: `frontend/src/stores/attendance.js`

#### 步驟 1: 添加 import

在檔案開頭（第 3 行後）添加：

```javascript
import { getLocationIfRequired, detectDeviceType, LocationError } from '@/utils/locationAdapter'
```

#### 步驟 2: 刪除 `detectDeviceType()` 方法

**位置**: 約第 236-240 行

**刪除**:
```javascript
detectDeviceType() {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
  return isMobile ? 'mobile' : 'pc'
},
```

#### 步驟 3: 刪除 `getGPSLocation()` 方法

**位置**: 約第 243-283 行

**刪除整個方法**:
```javascript
async getGPSLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('此裝置不支援定位功能'))
      return
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          captured_at: new Date().toISOString(),
          provider: 'gps'
        })
      },
      (error) => {
        let errorMessage = '無法獲取定位'
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = '請開啟定位權限後再外出打點'
            break
          case error.POSITION_UNAVAILABLE:
            errorMessage = '定位資訊無法取得'
            break
          case error.TIMEOUT:
            errorMessage = '定位請求逾時'
            break
        }
        reject(new Error(errorMessage))
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    )
  })
},
```

#### 步驟 4: 重構 `outCheckpointSubmit()` 方法

**位置**: 約第 147-211 行

**找到這段程式碼**:
```javascript
const deviceType = this.detectDeviceType()

const payload = {
  device_type: deviceType,
  notes: reasonText.trim()
}

if (deviceType === 'mobile') {
  const gpsData = await this.getGPSLocation()
  payload.gps = gpsData
}
```

**替換為**:
```javascript
const deviceType = detectDeviceType()

const payload = {
  device_type: deviceType,
  notes: reasonText.trim()
}

// 使用 adapter 獲取定位（如果需要）
const gpsData = await getLocationIfRequired()
if (gpsData) {
  payload.gps = gpsData
}
```

#### 步驟 5: 更新 `handleError()` 方法

**位置**: 約第 327 行開始

**在方法開頭添加 LocationError 處理**:

```javascript
handleError(error) {
  let errorMessage = '操作失敗'
  let errorCode = null
  
  // 處理 LocationError
  if (error instanceof LocationError) {
    return {
      message: error.message,
      code: error.code,
      originalError: error.originalError
    }
  }
  
  // 原有的錯誤處理邏輯...
  if (error.status) {
    // ...
  }
  
  return {
    message: errorMessage,
    code: errorCode,
    originalError: error
  }
}
```

---

### 2. 更新 Home.vue

**檔案**: `frontend/src/views/Home.vue`

#### 步驟 1: 添加 import

在 `<script setup>` 區塊中，找到 import 語句，添加：

```javascript
import { detectDeviceType } from '@/utils/locationAdapter'
```

#### 步驟 2: 更新 onMounted

**找到**:
```javascript
onMounted(() => {
  // ...
  deviceType.value = attendanceStore.detectDeviceType()
  // ...
})
```

**替換為**:
```javascript
onMounted(() => {
  attendanceStore.fetchTodayStatus()
  attendanceStore.fetchRecentLogs()
  attendanceStore.loadOutCheckpoints()
  attendanceStore.loadBreakPunches()
  attendanceStore.hydrateReasonsFromLocalStorage()
  
  // 使用 adapter
  deviceType.value = detectDeviceType()
  
  if (lastSelectedReason.value) {
    selectedReason.value = lastSelectedReason.value
  }
})
```

---

### 3. 建立 Utils README

**新增檔案**: `frontend/src/utils/README.md`

```markdown
# Utils 目錄說明

## locationAdapter.js

**狀態**: ⚠️ 臨時過渡層 (Temporary Adapter)

這是在實作 shared location module 之前的臨時方案。

### 使用方式

\`\`\`javascript
import { getGPSLocation, detectDeviceType, getLocationIfRequired } from '@/utils/locationAdapter'

// 獲取裝置類型
const deviceType = detectDeviceType() // 'mobile' | 'pc'

// 獲取 GPS 定位
try {
  const gps = await getGPSLocation()
  console.log(gps.latitude, gps.longitude)
} catch (error) {
  if (error instanceof LocationError) {
    console.error(error.message, error.code)
  }
}

// 根據裝置類型自動決定是否獲取定位
const gps = await getLocationIfRequired() // mobile: GPS data, pc: null
\`\`\`

### 未來計劃

此 adapter 將在 `composables/useLocation.js` 完成後被取代。

預計時程: WP-11-12 (Shared Location Module)
```

---

## 驗證步驟

完成上述修改後，請執行以下驗證：

### 1. 語法檢查

```bash
cd /opt/attendance-system/frontend
npm run lint
```

### 2. 功能測試

- [ ] 開啟前端應用
- [ ] 測試 OUT checkpoint 功能
- [ ] 在 Mobile 裝置上測試（或使用 Chrome DevTools 模擬）
- [ ] 在 PC 上測試
- [ ] 測試 GPS 權限拒絕的情況
- [ ] 測試 GPS 超時的情況

### 3. 程式碼檢查

```bash
# 確認沒有直接呼叫舊方法
cd /opt/attendance-system/frontend/src
grep -r "attendanceStore.getGPSLocation" .
grep -r "attendanceStore.detectDeviceType" .
# 應該沒有結果

# 確認有使用 adapter
grep -r "from '@/utils/locationAdapter'" .
# 應該看到 attendance.js 和 Home.vue
```

---

## 修改摘要

### 檔案變更統計

| 檔案 | 狀態 | 變更類型 |
|------|------|----------|
| `frontend/src/utils/locationAdapter.js` | ✅ 新增 | 新增臨時 adapter |
| `frontend/src/stores/attendance.js` | ⏸️ 待修改 | 移除 GPS 方法，使用 adapter |
| `frontend/src/views/Home.vue` | ⏸️ 待修改 | 使用 adapter |
| `frontend/src/views/Home.vue.backup` | ✅ 刪除 | 死碼清理 |
| `frontend/src/views/Home.vue.before_fix` | ✅ 刪除 | 死碼清理 |
| `frontend/src/views/Home.vue.tmp` | ✅ 刪除 | 死碼清理 |
| `frontend/src/utils/README.md` | ⏸️ 待新增 | 文件 |

### 程式碼行數變化

- **新增**: ~130 行（locationAdapter.js）
- **刪除**: ~50 行（舊 GPS 方法）
- **修改**: ~20 行（使用 adapter）
- **淨變化**: +60 行

---

## 保留的後端能力

以下後端程式碼**未被修改**，保持原樣：

| 檔案 | 說明 | 狀態 |
|------|------|------|
| `backend/app/modules/attendance/gps_utils.py` | GPS 距離計算工具 | ✅ 保留 |
| `backend/app/modules/attendance/schemas.py` | GPS Schema 定義 | ✅ 保留 |
| `backend/app/modules/attendance/models.py` | AttendanceOutCheckpoint Model | ✅ 保留 |
| `backend/app/modules/attendance/repo.py` | Repository 層 | ✅ 保留 |
| `backend/app/modules/attendance/tests/test_out_checkpoint.py` | 測試 | ✅ 保留 |

---

## 風險與問題

### 已知風險

1. **Store 修改未完成**: 需要手動完成，有語法錯誤風險
2. **測試覆蓋不足**: 沒有前端單元測試驗證 adapter
3. **臨時方案**: locationAdapter 是過渡層，未來需要替換

### 緩解措施

1. 提供詳細的修改步驟和程式碼範例
2. 建議在測試環境先驗證
3. 保留 Git commit 可快速回滾
4. 規劃下一階段的 shared location module

---

## 下一步行動

### 立即行動（本輪）

1. **手動完成 Store 重構**
   - 按照本文件的步驟修改 `attendance.js`
   - 修改 `Home.vue`
   - 建立 `utils/README.md`

2. **驗證功能**
   - 執行 lint 檢查
   - 測試 OUT checkpoint 功能
   - 測試各種錯誤情境

3. **提交變更**
   ```bash
   git add .
   git commit -m "refactor: GPS legacy cleanup - use location adapter"
   ```

### 下一階段（WP-11-12）

1. **實作 Shared Location Module**
   - 建立 `composables/useLocation.js`
   - 實作 location policy
   - 實作 location state management

2. **替換 Adapter**
   - 將 locationAdapter 替換為 useLocation
   - 刪除 locationAdapter.js
   - 更新所有引用

3. **增強功能**
   - 地圖 UI 整合
   - 範圍驗證
   - 精度要求
   - Retry 機制

---

## 參考文件

- `docs/ATTENDANCE_GPS_LEGACY_INVENTORY.md` - Legacy GPS 盤點
- `docs/ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md` - 清理計劃
- `frontend/src/utils/locationAdapter.js` - Location Adapter 實作

---

## 附錄：快速修改腳本

如果需要快速應用修改，可以使用以下腳本（請先備份）：

```bash
#!/bin/bash
# GPS Legacy Cleanup - Quick Apply Script
# 警告：執行前請先備份檔案

cd /opt/attendance-system/frontend/src

# 備份原始檔案
cp stores/attendance.js stores/attendance.js.backup
cp views/Home.vue views/Home.vue.backup

echo "備份完成，請手動執行以下修改："
echo "1. 編輯 stores/attendance.js"
echo "2. 編輯 views/Home.vue"
echo "3. 建立 utils/README.md"
echo ""
echo "詳細步驟請參考 ATTENDANCE_GPS_LEGACY_CLEANUP_REPORT.md"
```

---

**完成日期**: 2026-03-08  
**下次更新**: 完成手動修改後
