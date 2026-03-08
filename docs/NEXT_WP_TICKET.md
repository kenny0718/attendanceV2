# Next WP Ticket: WP-11-12

**票號**: WP-11-12  
**標題**: Shared Location Module - useLocation Composable 實作  
**優先級**: P1  
**預計開始**: WP-11-11.5 QA Passed 後  
**狀態**: 待開始

---

## 前置條件

### 必須完成

- [ ] ✅ WP-11-11.5 QA passed
- [ ] ✅ 基線 tag / restore point 確認完成
  - 建議 tag: `qa-passed/wp-11-11.5` 或 `milestone/wp-11-11.5-qa-passed`
- [ ] ✅ 結案摘要已確認
- [ ] ✅ 主打卡流程穩定運行

### 明確排除項目

**重要聲明**: 以下功能**不屬於 WP-11-12 第一階段必做**（除非 spec 明定）

- ❌ out-checkpoints API 實作（後端）
- ❌ out-checkpoints 前端完整功能
- ❌ Geofencing 功能
- ❌ Location policy 實作
- ❌ 地圖 UI 整合
- ❌ Location analytics

---

## WP-11-12 目標

### 核心目標

實作可重用的 shared location module，取代臨時 locationAdapter。

### 具體交付物

1. **useLocation Composable**
   - `frontend/src/composables/useLocation.js`
   - Reactive state management
   - 統一錯誤處理
   - Loading state 管理
   - Retry 機制

2. **替換 locationAdapter**
   - 更新 `attendance.js` store
   - 更新 `Home.vue`
   - 刪除 `locationAdapter.js`

3. **測試**
   - 單元測試
   - 整合測試
   - E2E 測試（可選）

---

## WP-11-12 範圍

### Phase 1: Core Composable（第一階段）

**目標**: 實作基本的 useLocation composable

**包含**:
- ✅ 裝置類型判斷
- ✅ GPS 位置取得
- ✅ 錯誤處理
- ✅ Loading 狀態
- ✅ Retry 機制

**不包含**:
- ❌ Geofencing
- ❌ Location policy
- ❌ 地圖顯示
- ❌ 複雜的快取機制

---

### Phase 2: Adapter Replacement（第二階段）

**目標**: 替換所有 locationAdapter 引用

**包含**:
- ✅ 更新 attendance.js
- ✅ 更新 Home.vue
- ✅ 刪除 locationAdapter.js
- ✅ 回歸測試

**不包含**:
- ❌ 新增功能
- ❌ UI 改版

---

### Phase 3: Testing & Documentation（第三階段）

**目標**: 完整測試和文件

**包含**:
- ✅ 單元測試
- ✅ 整合測試
- ✅ 使用文件
- ✅ API 文件

---

## 設計文件

### 已完成的設計文件

1. ✅ `docs/ATTENDANCE_LOCATION_MODULE_SPEC.md`
   - useLocation composable API 設計
   - State management 策略
   - Error handling 統一方案

2. ✅ `docs/ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md`
   - 從 locationAdapter 遷移計劃
   - Store/Composable/View 職責劃分
   - 向後相容策略

3. ✅ `docs/ATTENDANCE_LOCATION_API_CONTRACT_DRAFT.md`
   - 現有 API contract 文件化
   - Payload 格式規範
   - 錯誤碼規範

4. ✅ `docs/ATTENDANCE_LOCATION_TEST_PLAN.md`
   - 測試矩陣
   - 單元測試計劃
   - 整合測試計劃

---

## 實作計劃

### Slice 1: Core Composable（3 天）

**Day 1**: 基礎結構
- 建立 `useLocation.js`
- 實作 `detectDeviceType()`
- 實作基本 state management

**Day 2**: GPS 功能
- 實作 `getCurrentLocation()`
- 實作錯誤處理
- 實作 loading state

**Day 3**: 測試
- 單元測試
- 整合測試
- 文件

---

### Slice 2: Store Integration（2 天）

**Day 1**: 替換 attendance.js
- 更新 `outCheckpointSubmit()`
- 移除 locationAdapter import
- 測試驗證

**Day 2**: 替換 Home.vue
- 更新 `onMounted()`
- 移除 locationAdapter import
- 回歸測試

---

### Slice 3: Cleanup & Documentation（1 天）

**Day 1**: 清理和文件
- 刪除 `locationAdapter.js`
- 更新使用文件
- 最終測試
- Code review

---

## 驗收標準

### 功能驗收

- [ ] useLocation composable 實作完成
- [ ] 所有 locationAdapter 引用已替換
- [ ] locationAdapter.js 已刪除
- [ ] 主打卡流程正常運行

### 測試驗收

- [ ] 單元測試通過（覆蓋率 > 80%）
- [ ] 整合測試通過
- [ ] 回歸測試通過（主打卡流程）

### 文件驗收

- [ ] API 文件完整
- [ ] 使用範例清晰
- [ ] 遷移指南完整

---

## 風險評估

### 高風險

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 破壞現有打卡功能 | 高 | 中 | 完整回歸測試，保留 locationAdapter 作為備份 |
| API 不相容 | 高 | 低 | 遵循現有 API contract |

### 中風險

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 效能問題 | 中 | 低 | 效能測試，優化 reactive state |
| 測試覆蓋不足 | 中 | 中 | 補充單元測試和整合測試 |

---

## 不包含項目（重要）

### 明確排除

以下功能**不在 WP-11-12 範圍內**：

1. **out-checkpoints 完整功能**
   - 後端 API 實作
   - 前端完整 UI
   - 列表顯示和管理
   - **理由**: 屬於獨立功能，需要獨立票次

2. **Geofencing**
   - 範圍驗證
   - 地理圍欄設定
   - **理由**: 屬於 Phase 3: Policy Migration

3. **Location Policy**
   - 精度要求
   - 位置驗證規則
   - **理由**: 屬於 Phase 3: Policy Migration

4. **地圖 UI**
   - 地圖顯示
   - 位置標記
   - 歷史軌跡
   - **理由**: 屬於 Phase 4: UI Enhancement

5. **Analytics**
   - 位置分析
   - 異常偵測
   - **理由**: 屬於 Phase 4: UI Enhancement

---

## 後續票次規劃

### WP-11-13: Location Policy（預計）

**目標**: 實作 location policy 和 geofencing

**前置條件**:
- WP-11-12 完成
- useLocation composable 穩定運行

**包含**:
- Geofencing 實作
- 精度驗證
- 範圍驗證
- Policy engine

---

### WP-11-14: UI Enhancement（預計）

**目標**: 增強 location UI

**前置條件**:
- WP-11-13 完成
- Location policy 穩定運行

**包含**:
- 地圖整合
- 位置顯示
- 歷史軌跡

---

### WP-11-15: out-checkpoints 完整功能（預計）

**目標**: 實作 out-checkpoints 完整功能

**前置條件**:
- WP-11-12 完成
- 產品需求明確

**包含**:
- 後端 API 實作
- 前端完整 UI
- 列表管理
- 編輯/刪除功能

---

## 開始前檢查清單

### 環境準備

- [ ] WP-11-11.5 QA passed tag 已建立
- [ ] 開發環境正常運行
- [ ] 測試環境可用

### 文件準備

- [ ] 設計文件已審查
- [ ] API contract 已確認
- [ ] 測試計劃已確認

### 團隊準備

- [ ] 開發人員已分配
- [ ] Code review 流程已確認
- [ ] QA 資源已確認

---

## 參考文件

- `docs/WP-11-11.5_CLOSURE_SUMMARY.md` - WP-11-11.5 結案摘要
- `docs/ATTENDANCE_LOCATION_MODULE_SPEC.md` - useLocation 規格
- `docs/ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md` - 重構計劃
- `docs/ATTENDANCE_LOCATION_API_CONTRACT_DRAFT.md` - API 規範
- `docs/ATTENDANCE_LOCATION_TEST_PLAN.md` - 測試計劃
- `docs/GATE_PROGRESS_TRACKER.md` - 進度追蹤

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: 待開始  
**前置票次**: WP-11-11.5
