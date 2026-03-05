# Next WP Ticket — Frontend OUT Checkpoint Integration

**Selected WP:** WP-11-11 Frontend OUT Checkpoint + GPS Integration  
**Reason:** WP-11-10 backend完成，需要前端整合  
**Priority:** 🟡 P1 (Feature Integration)

---

## ✅ Completed WPs

### WP-11-10 — OUT Checkpoint + GPS Backend (Backend Implementation)
**Date**: 2026-03-05 23:59  
**Status**: ✅ COMPLETED

**Deliverables**:
- ✅ Migration 007_wp_11_10: attendance_out_checkpoints table
- ✅ AttendanceOutCheckpoint model with GPS fields
- ✅ POST /api/v1/attendance/out-checkpoint endpoint
- ✅ GET /api/v1/attendance/out-checkpoints endpoint
- ✅ GPS validation (mobile required, PC optional)
- ✅ De-duplication (30s + 50m threshold)
- ✅ 7 pytest test cases (all passing)
- ✅ Implementation report

**Test Results**:
- ✅ All 7 tests passing
- ✅ Multi-checkpoint submission works
- ✅ GPS validation enforced
- ✅ De-dup logic working (409 response)
- ✅ Tenant isolation verified

### WP-11-08 — JWT Auth Integration (Replace Mock User)
**Date**: 2026-03-05 21:00  
**Status**: ✅ COMPLETED

**Deliverables**:
- ✅ 前端新增 Login flow（拿 token / 保存）
- ✅ axios interceptor 使用真 token + company context
- ✅ 移除 authStore.mockUser 依賴
- ✅ 路由保護（未登入不可進 Home）
- ✅ 測試文件：`docs/WP-11-08_AUTH_INTEGRATION_REPORT.md`

### WP-11-07 Phase 2 — API Integration (Mock → Real API)
**Date**: 2026-03-05 20:09  
**Status**: ✅ VERIFIED & COMPLETED

---

## 🚀 WP-11-11 — Frontend OUT Checkpoint + GPS Integration

### Goal
整合 WP-11-10 後端 API，實現前端外出打卡功能與 GPS 定位。

### Scope

#### 1. API Integration (P0)
- 新增 `api/attendance.js` 方法：
  - `createOutCheckpoint(deviceType, gps, notes)`
  - `getOutCheckpoints(limit, offset, sessionId)`
- 處理 409 (DUPLICATE_CHECKPOINT) 錯誤
- 處理 422 (GPS_REQUIRED) 錯誤

#### 2. GPS Geolocation (P0)
- 建立 `composables/useGeolocation.js`
- 自動偵測裝置類型 (mobile/pc)
- 獲取 GPS 座標 (latitude, longitude, accuracy)
- 處理用戶拒絕定位
- 顯示定位狀態（獲取中/成功/失敗）

#### 3. UI Components (P0)
- 更新 `Home.vue`：
  - 啟用「外出」按鈕
  - 顯示 GPS 狀態指示器
  - 顯示最近的 checkpoint 列表
- 新增 `OutCheckpointButton.vue`：
  - 外出打卡按鈕
  - GPS 獲取中的 loading 狀態
  - 錯誤提示（GPS 未開啟、重複打卡）

#### 4. Error Handling (P0)
- 409 錯誤：顯示「請勿重複打卡」
- 422 錯誤：顯示「請開啟定位後再外出打卡」
- GPS 獲取失敗：顯示「無法獲取定位，請檢查權限」
- 網路錯誤：顯示「網路連線失敗」

#### 5. History Integration (P1)
- 在 History 頁面顯示 OUT checkpoints
- 每個 session 下方顯示 checkpoint 列表
- 顯示 GPS 座標（可選）
- 顯示裝置類型 (mobile/pc)

### Technical Details

#### API Endpoints
```javascript
// POST /api/v1/attendance/out-checkpoint
await attendanceApi.createOutCheckpoint({
  device_type: 'mobile',
  gps: {
    latitude: 25.0330,
    longitude: 121.5654,
    accuracy: 15.5,
    captured_at: new Date().toISOString(),
    provider: 'gps'
  },
  notes: 'Checkpoint at Building A'
})

// GET /api/v1/attendance/out-checkpoints
await attendanceApi.getOutCheckpoints({
  limit: 50,
  offset: 0,
  session_id: 'xxx'
})
```

#### Geolocation Composable
```javascript
// composables/useGeolocation.js
export function useGeolocation() {
  const getCurrentPosition = async () => {
    return new Promise((resolve, reject) => {
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
        (error) => reject(error),
        { enableHighAccuracy: true, timeout: 10000 }
      )
    })
  }
  
  const getDeviceType = () => {
    return /Mobile|Android|iPhone/i.test(navigator.userAgent) ? 'mobile' : 'pc'
  }
  
  return { getCurrentPosition, getDeviceType }
}
```

### Test Plan

#### Manual Testing
1. **Mobile 裝置測試**：
   - 開啟定位 → 外出打卡 → 成功 (201)
   - 關閉定位 → 外出打卡 → 錯誤 (422)
   - 30秒內重複打卡 → 錯誤 (409)

2. **PC 裝置測試**：
   - 無定位 → 外出打卡 → 成功 (201)
   - 有定位 → 外出打卡 → 成功 (201, 帶 GPS)

3. **History 測試**：
   - 查看 History → 顯示 checkpoints
   - 每個 session 顯示多個 checkpoints

#### Automated Testing (Optional)
- Vitest unit tests for composables
- Cypress E2E tests for user flow

### Definition of Done

- [ ] API methods added to `api/attendance.js`
- [ ] `useGeolocation` composable created
- [ ] 外出按鈕啟用並可用
- [ ] GPS 狀態顯示正確
- [ ] 錯誤處理完整 (409, 422, GPS 失敗)
- [ ] History 顯示 checkpoints
- [ ] Manual testing passed (mobile + PC)
- [ ] Documentation updated

### Estimated Time
- API Integration: 0.5 day
- GPS Composable: 1 day
- UI Components: 1 day
- Error Handling: 0.5 day
- History Integration: 1 day
- Testing: 0.5 day

**Total**: 4-5 days

---

## Alternative: Phase 3A JWT Enhancement

如果不優先做前端整合，可以考慮：

### WP-11-12 — JWT Token Refresh & Role-Based Access

**Scope**:
- Refresh token mechanism
- Token auto-refresh (5 min before expiry)
- Role-based route protection
- Permission-based UI rendering

**Priority**: 🟢 P2  
**Estimated Time**: 2-3 days

---

## 🎯 Recommendation

**推薦執行**: WP-11-11 Frontend OUT Checkpoint Integration

**理由**:
1. WP-11-10 後端已完成，前端整合是自然的下一步
2. GPS 功能對用戶體驗提升明顯
3. 完整的 OUT checkpoint 功能可以立即使用
4. 測試和驗證可以同步進行

**Blocker**: None (WP-11-10 已完成)  
**Assignee**: Frontend Team  
**Status**: 🎯 READY TO START

---

**Document Version:** 12.0  
**Last Updated:** 2026-03-05 23:59  
**Next Review:** WP-11-11 kickoff or alternative selection
