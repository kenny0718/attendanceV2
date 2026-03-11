# WP-11-12 Phase 2A 完成報告

**票號**: WP-11-12  
**階段**: Phase 2A - BREAK_OUT Integration (Strategy Revised)  
**狀態**: ✅ 設計完成，待實作  
**完成日期**: 2026-03-08

---

## 執行摘要

WP-11-12 Phase 2A 已完成策略修正和設計文件，明確定義了 **UI 層主導 location 取得，Store 層處理業務邏輯** 的架構。

**關鍵成果**:
- ✅ 策略修正完成
- ✅ GPS 兩層用途明確分離
- ✅ 避免雙重 useLocation() state
- ✅ 未來 geofence / location policy 已預留設計
- ✅ 完整的程式碼修改指引
- ✅ 測試驗證計劃

---

## 策略修正說明

### 原策略問題

原本計劃讓 store 直接主導 `useLocation()` state，會導致：
- ❌ Store 和 View 各自維護兩套 location state
- ❌ Reactive state 管理混亂
- ❌ UI 層無法直接控制 loading / error 顯示
- ❌ 違反關注點分離原則

### 新策略

**UI 層主導 location 取得，Store 層處理業務邏輯**

```
┌─────────────────────────────────────────┐
│ Home.vue (UI Layer)                     │
│ - 使用 useLocation()                    │
│ - 管理 location loading / error UI     │
│ - 取得 location 後傳給 store           │
└─────────────────────────────────────────┘
                    ↓
         location data (or null)
                    ↓
┌─────────────────────────────────────────┐
│ attendance.js (Store/Business Layer)    │
│ - 接收 location 參數                    │
│ - 處理打卡業務邏輯                      │
│ - 呼叫 API                              │
│ - 不直接管理 composable UI state       │
└─────────────────────────────────────────┘
```

---

## GPS 兩層用途明確分離

### Layer 1: Runtime Location Collection（本票實作）

**用途**: 打卡當下取得目前 GPS

**適用流程**:
- 外出打卡 (BREAK_OUT)
- 返回打卡 (BREAK_IN)
- 未來其他需要記錄位置的流程

**實作方式**:
- 使用 `useLocation` composable
- UI 層主導取得
- 傳遞給 store 作為 API payload

**本票完成**: ✅ 設計完成，待實作

---

### Layer 2: Attendance Location Policy / Geofence（未來票）

**用途**: 公司可在後台設定允許打卡的位置

**使用情境**:
- 工地打卡：只能在工地範圍內打卡
- 客戶現場：只能在客戶地點打卡
- 辦公室：只能在辦公室範圍內打卡
- 彈性工作：任何地點都可打卡

**資料模型（預留）**:
```typescript
interface AllowedLocation {
  id: string
  name: string              // 例如：「台北工地」
  latitude: number
  longitude: number
  radius_meters: number     // 允許半徑（公尺）
  enabled: boolean
  description?: string
}

interface LocationPolicy {
  require_location: boolean
  allowed_locations: AllowedLocation[]
  allow_any_location: boolean
}
```

**本票完成**: ✅ 設計預留，不實作

---

## 修改檔案清單

### 已完成（設計文件）

1. **`docs/WP-11-12_PHASE2_REVISED_STRATEGY.md`**
   - ✅ 策略修正說明
   - ✅ GPS 兩層用途定義
   - ✅ 架構設計
   - ✅ 避免雙重 state 的方法

2. **`docs/WP-11-12_PHASE2A_CODE_CHANGES.md`**
   - ✅ 完整的程式碼修改指引
   - ✅ Home.vue 修改步驟
   - ✅ attendance.js 修改步驟
   - ✅ 測試驗證步驟
   - ✅ 回滾計劃

3. **`docs/WP-11-13_LOCATION_POLICY_PREP.md`**
   - ✅ Location Policy 設計預留
   - ✅ 使用情境說明
   - ✅ 資料模型建議
   - ✅ API 設計預留
   - ✅ 未來整合點說明

---

### 待實作（程式碼修改）

1. **`frontend/src/views/Home.vue`**
   - ⏳ 添加 `useLocation` import
   - ⏳ 使用 `useLocation()` 在 UI 層
   - ⏳ 修改 `handlePunch` 處理 BREAK_OUT
   - ⏳ 新增 `handleBreakOutPunch` 函數
   - ⏳ 顯示 location loading / error UI

2. **`frontend/src/stores/attendance.js`**
   - ⏳ 新增 `punchWithLocation()` 方法
   - ⏳ 標記舊方法為 deprecated
   - ⏳ 保留向後相容

3. **`frontend/src/utils/locationAdapter.js`**
   - ⏳ 更新註解，標記為 transitional bridge
   - ⏳ 記錄遷移狀態

---

## UI / Store 責任切分

### UI Layer (Home.vue)

**負責**:
- ✅ 使用 `useLocation()` 取得 location 服務
- ✅ 管理 location loading / error UI
- ✅ 顯示定位中、權限拒絕、超時等狀態
- ✅ 取得 location 後傳給 store

**不負責**:
- ❌ 打卡業務邏輯
- ❌ API 呼叫
- ❌ 狀態持久化

---

### Store Layer (attendance.js)

**負責**:
- ✅ 接收已取得的 location 資料
- ✅ 處理打卡業務邏輯
- ✅ 呼叫 API
- ✅ 更新 state
- ✅ 錯誤處理

**不負責**:
- ❌ 直接管理 composable reactive state
- ❌ UI loading / error 顯示
- ❌ 直接呼叫 navigator.geolocation

---

## 如何避免雙重 useLocation() State

### ❌ 錯誤做法

```javascript
// Home.vue
const location1 = useLocation()

// attendance.js
const location2 = useLocation()

// 問題：兩個獨立的 reactive state，無法同步
```

### ✅ 正確做法

```javascript
// Home.vue (唯一使用點)
const {
  location,
  error,
  isLoading,
  getLocationIfRequired
} = useLocation()

// 取得 location 後傳給 store
const gps = await getLocationIfRequired()
await store.punchWithLocation('BREAK_OUT', { gps })

// attendance.js (只接收資料)
async punchWithLocation(type, payload) {
  // payload.gps 已經是取得好的資料
  await api.breakOut(payload)
}
```

**關鍵原則**:
- ✅ 只在 UI 層使用一次 `useLocation()`
- ✅ Store 層只接收資料，不管理 reactive state
- ✅ 避免 state 分散在多個地方

---

## 未來 Geofence / Allowed Locations 整合點

### 整合點 1: UI Layer

```vue
<script setup>
async function handleBreakOut() {
  // Step 1: 取得 location (本票已完成)
  const gpsData = await getLocationIfRequired()
  
  // Step 2: 檢查 location policy (未來票)
  // const policyCheck = await checkLocationPolicy(gpsData)
  // if (!policyCheck.allowed) {
  //   showError('不在允許的打卡範圍內')
  //   return
  // }
  
  // Step 3: 執行打卡
  await store.punchWithLocation('BREAK_OUT', { gps: gpsData })
}
</script>
```

### 整合點 2: Store Layer

```javascript
// 未來可以加入 policy 參數
async punchWithLocation(type, payload, options = {}) {
  // options.policyResult - policy 檢查結果
  
  // 未來可以在這裡記錄 policy 檢查結果
  // if (options.policyResult) {
  //   payload.policy_check = options.policyResult
  // }
  
  await api.breakOut(payload)
}
```

### 整合點 3: Composable Layer

```javascript
// 未來可以建立 useLocationPolicy composable
export function useLocationPolicy() {
  const policy = ref(null)
  
  async function checkLocation(gpsData) {
    return await api.checkLocationPolicy(gpsData)
  }
  
  return {
    policy,
    checkLocation
  }
}
```

---

## 驗證情境

### TC-01: Mobile 外出打卡（允許定位）

```
前置條件: Mobile 裝置，允許定位權限
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」
4. 選擇原因
5. 點擊確認

預期結果:
✅ 顯示「定位中...」
✅ 成功取得 GPS
✅ 外出打卡成功
✅ 記錄包含 GPS 座標
```

### TC-02: Mobile 外出打卡（拒絕定位）

```
前置條件: Mobile 裝置，拒絕定位權限
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」
4. 拒絕定位權限

預期結果:
✅ 顯示錯誤：「請開啟定位權限後再外出打點」
✅ 外出打卡失敗
✅ 可以重試
```

### TC-03: PC 外出打卡

```
前置條件: PC
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」

預期結果:
✅ 不要求 GPS
✅ 直接外出打卡成功
✅ 記錄不包含 GPS

注意: 未來應改由 policy 決定是否要求定位
```

### TC-04: 回歸測試

```
驗證項目:
✅ 上班打卡：正常
✅ 下班打卡：正常
✅ 返回打卡：正常
✅ 不引入新的重複 geolocation 實作
```

---

## 明確留到後續的項目

### WP-11-12 Phase 2B（下一步）

**範圍**:
- 實作 Home.vue 修改
- 實作 attendance.js 修改
- 實作 locationAdapter 註解更新
- 整合測試
- 驗證功能

**不包含**:
- ❌ BREAK_IN 遷移（可選）
- ❌ 上班/下班打卡遷移（不需要）
- ❌ 刪除 locationAdapter（保留作為 bridge）

---

### WP-11-13: Location Policy（後續票）

**範圍**:
- Geofence 規則實作
- Allowed locations 資料模型
- Policy 驗證邏輯
- 後台管理 UI
- useLocationPolicy composable

**不包含**:
- ❌ 地圖顯示（WP-11-14）
- ❌ 位置分析（WP-11-15）

---

### WP-11-14: UI Enhancement（後續票）

**範圍**:
- 地圖顯示
- 位置標記
- 歷史軌跡
- 視覺化

---

### WP-11-15: OUT Checkpoints（後續票）

**範圍**:
- 後端 API 實作
- 前端完整 UI
- 列表管理

---

## Git 狀態

```
Commit: 54434a2
標題: docs: WP-11-12 Phase 2A 策略修正與設計文件
日期: 2026-03-08

新增文件:
- docs/WP-11-12_PHASE2_REVISED_STRATEGY.md
- docs/WP-11-12_PHASE2A_CODE_CHANGES.md
- docs/WP-11-13_LOCATION_POLICY_PREP.md
```

---

## Phase 2A 完成標準

### 已完成

- [x] ✅ 策略修正完成
- [x] ✅ GPS 兩層用途明確定義
- [x] ✅ UI / Store 責任切分明確
- [x] ✅ 避免雙重 state 的方法已定義
- [x] ✅ 未來 geofence 已有明確設計預留
- [x] ✅ 完整的程式碼修改指引
- [x] ✅ 測試驗證計劃
- [x] ✅ 文件已提交

### 待完成（Phase 2B）

- [ ] ⏳ Home.vue 程式碼修改
- [ ] ⏳ attendance.js 程式碼修改
- [ ] ⏳ locationAdapter 註解更新
- [ ] ⏳ 整合測試
- [ ] ⏳ 驗證功能
- [ ] ⏳ Bug fix（如有）

---

## 總結

### ✅ Phase 2A 成功完成

**成果**:
- 完成策略修正，避免雙重 state 問題
- 明確分離 GPS 兩層用途
- 為未來 location policy 預留完整設計
- 提供詳細的程式碼修改指引

**關鍵決策**:
1. **UI 層主導 location 取得** - 避免 state 管理混亂
2. **Store 層只處理業務邏輯** - 關注點分離
3. **GPS 兩層用途分離** - Runtime collection vs Policy
4. **保留 locationAdapter** - 作為 transitional bridge

**下一步**:
⏳ **開始 Phase 2B - 實作程式碼修改**

參考文件:
- `docs/WP-11-12_PHASE2A_CODE_CHANGES.md`
- `docs/WP-11-12_PHASE2_REVISED_STRATEGY.md`

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: ✅ Phase 2A 完成，準備 Phase 2B
