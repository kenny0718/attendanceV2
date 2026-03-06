# Next WP Ticket — Phase 3A JWT Enhancement or History Integration

**Selected WP:** TBD (Choose between WP-11-12 or WP-11-13)  
**Reason:** WP-11-11 frontend完成，可選擇增強認證或整合歷史記錄  
**Priority:** 🟡 P1 (Enhancement)

---

## ✅ Completed WPs

### WP-11-11 — Frontend OUT Checkpoint + Reason Picker (UI Integration)
**Date**: 2026-03-06 00:35  
**Status**: ✅ COMPLETED & VERIFIED

**Deliverables**:
- ✅ API Client: createOutCheckpoint(), listOutCheckpoints()
- ✅ Store Integration: GPS detection, reason management
- ✅ Reason Quick Picker: Preset + custom + localStorage
- ✅ OUT Checkpoint UI: Fast input UX
- ✅ Error Handling: 409/422/403/5xx
- ✅ Manual Test Log: 7/7 tests passed

**Test Results**:
- ✅ All 7 manual tests passed
- ✅ Mobile GPS validation working
- ✅ PC no-GPS flow working
- ✅ Custom reasons persist correctly
- ✅ Dedup 409 handled correctly
- ✅ Last selection restored
- ✅ List auto-refresh working

**UX Highlights**:
- One-click reason selection
- Zero extra steps for fast input
- Visual feedback on selection
- Persistence across reloads

### WP-11-10 — OUT Checkpoint + GPS Backend (Backend Implementation)
**Date**: 2026-03-05 23:59  
**Status**: ✅ COMPLETED

**Deliverables**:
- ✅ Migration 007_wp_11_10: attendance_out_checkpoints table
- ✅ POST /api/v1/attendance/out-checkpoint endpoint
- ✅ GET /api/v1/attendance/out-checkpoints endpoint
- ✅ GPS validation (mobile required, PC optional)
- ✅ De-duplication (30s + 50m threshold)
- ✅ 7 pytest test cases (all passing)

### WP-11-08 — JWT Auth Integration (Replace Mock User)
**Date**: 2026-03-05 21:00  
**Status**: ✅ COMPLETED

---

## 🚀 Option A: WP-11-12 — JWT Token Refresh & Role-Based Access

### Goal
增強 JWT 認證機制，實現 token 自動刷新和基於角色的訪問控制。

### Scope

#### 1. Token Refresh Mechanism (P0)
- 實現 refresh token API
- Token 過期前 5 分鐘自動刷新
- 無感刷新（用戶無需重新登入）
- 處理 refresh token 過期情況

#### 2. Role-Based Access Control (P0)
- 定義角色權限矩陣
- 實現路由級別權限檢查
- 實現組件級別權限控制
- 實現 API 級別權限驗證

#### 3. Permission-Based UI Rendering (P1)
- 根據權限顯示/隱藏功能
- 禁用無權限的按鈕
- 顯示權限不足提示

#### 4. Session Management (P1)
- 多設備登入管理
- 強制登出功能
- Session 過期提示

### Technical Details

#### Refresh Token Flow
```javascript
// stores/auth.js
async refreshToken() {
  const refreshToken = localStorage.getItem('refreshToken')
  const response = await authApi.refreshToken(refreshToken)
  
  localStorage.setItem('accessToken', response.access_token)
  localStorage.setItem('refreshToken', response.refresh_token)
  
  return response.access_token
}

// Auto-refresh before expiry
setInterval(() => {
  const expiresAt = localStorage.getItem('tokenExpiresAt')
  const now = Date.now()
  
  if (expiresAt - now < 5 * 60 * 1000) { // 5 minutes
    this.refreshToken()
  }
}, 60 * 1000) // Check every minute
```

#### Role-Based Route Protection
```javascript
// router/index.js
{
  path: '/admin',
  component: AdminPanel,
  meta: { 
    requiresAuth: true,
    roles: ['admin', 'super_admin']
  }
}

// Navigation guard
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const userRole = authStore.user.role
    
    if (to.meta.roles && !to.meta.roles.includes(userRole)) {
      next('/403')
      return
    }
  }
  
  next()
})
```

### Definition of Done
- [ ] Refresh token API implemented
- [ ] Auto-refresh working (5 min before expiry)
- [ ] Role-based route protection working
- [ ] Permission-based UI rendering working
- [ ] Session management working
- [ ] Manual testing passed
- [ ] Documentation updated

### Estimated Time
- Token Refresh: 1 day
- Role-Based Access: 2 days
- Permission UI: 1 day
- Session Management: 1 day
- Testing: 0.5 day

**Total**: 5-6 days

---

## 🚀 Option B: WP-11-13 — History Page Integration (Show Checkpoints)

### Goal
在 History 頁面整合 OUT checkpoints，顯示每個 session 的外出記錄。

### Scope

#### 1. History API Enhancement (P0)
- 修改 GET /history 返回 out_checkpoints
- 每個 session 包含 checkpoints 陣列
- 支援日期範圍篩選

#### 2. History Page UI (P0)
- 在每個 session 下方顯示 checkpoints
- 顯示 checkpoint 時間、原因、裝置類型
- 顯示 GPS 座標（可選）
- 支援展開/收合 checkpoints

#### 3. Checkpoint Detail View (P1)
- 點擊 checkpoint 顯示詳細資訊
- 顯示 GPS 地圖（如果有座標）
- 顯示裝置資訊、IP 地址

#### 4. Export Functionality (P1)
- 匯出 history 包含 checkpoints
- CSV/Excel 格式
- 日期範圍選擇

### Technical Details

#### Backend API Response
```json
{
  "sessions": [
    {
      "session_id": "...",
      "punch_in_time": "2026-03-06T09:00:00+08:00",
      "punch_out_time": "2026-03-06T18:00:00+08:00",
      "out_checkpoints": [
        {
          "checkpoint_id": "...",
          "punch_time": "2026-03-06T14:30:00+08:00",
          "notes": "外出洽公",
          "device_type": "mobile",
          "gps": {
            "latitude": 25.0330,
            "longitude": 121.5654
          }
        }
      ]
    }
  ]
}
```

#### Frontend Display
```vue
<div v-for="session in sessions" class="session-card">
  <div class="session-header">
    <span>上班: {{ session.punch_in_time }}</span>
    <span>下班: {{ session.punch_out_time }}</span>
  </div>
  
  <div v-if="session.out_checkpoints.length > 0" class="checkpoints">
    <h4>外出記錄 ({{ session.out_checkpoints.length }})</h4>
    <div v-for="cp in session.out_checkpoints" class="checkpoint-item">
      <span>{{ cp.punch_time }}</span>
      <span>{{ cp.notes }}</span>
      <span>{{ cp.device_type === 'mobile' ? '📍' : '💻' }}</span>
    </div>
  </div>
</div>
```

### Definition of Done
- [ ] Backend API returns checkpoints in history
- [ ] History page displays checkpoints
- [ ] Checkpoint detail view working
- [ ] Export includes checkpoints
- [ ] Manual testing passed
- [ ] Documentation updated

### Estimated Time
- Backend API: 1 day
- Frontend UI: 2 days
- Detail View: 1 day
- Export: 1 day
- Testing: 0.5 day

**Total**: 5-6 days

---

## 🚀 Option C: WP-11-14 — Admin Reason Dictionary (Optional)

### Goal
允許管理員管理全公司的外出原因字典，取代前端 hard-coded 的 preset reasons。

### Scope

#### 1. Backend API (P0)
- GET /api/v1/admin/reasons: 獲取原因列表
- POST /api/v1/admin/reasons: 新增原因
- PUT /api/v1/admin/reasons/:id: 更新原因
- DELETE /api/v1/admin/reasons/:id: 刪除原因

#### 2. Admin UI (P0)
- 原因管理頁面
- 新增/編輯/刪除原因
- 排序原因順序
- 啟用/停用原因

#### 3. Frontend Integration (P0)
- 從 API 載入 preset reasons
- 快取到 localStorage
- 定期更新（每天一次）

### Estimated Time: 3-4 days

---

## 🎯 Recommendation

**推薦執行順序**:

1. **WP-11-13 (History Integration)** - 優先推薦
   - 理由：完善 OUT checkpoint 功能，讓用戶看到完整的外出記錄
   - 價值：高（用戶可以查看歷史外出記錄）
   - 風險：低（純前端展示，不影響現有功能）
   - 時間：5-6 天

2. **WP-11-12 (JWT Enhancement)** - 次要推薦
   - 理由：改善用戶體驗，減少重複登入
   - 價值：中（提升 UX，但非必需）
   - 風險：中（涉及認證機制，需謹慎測試）
   - 時間：5-6 天

3. **WP-11-14 (Admin Reason Dictionary)** - 可選
   - 理由：提供更靈活的原因管理
   - 價值：中（管理便利性）
   - 風險：低（獨立功能）
   - 時間：3-4 天

**Blocker**: None (WP-11-11 已完成)  
**Assignee**: Frontend Team + Backend Team  
**Status**: 🎯 READY TO START

---

## 📊 Current System Status

### Completed Features
- ✅ JWT Auth (login/logout)
- ✅ Punch In/Out
- ✅ Break Out/In (deprecated)
- ✅ OUT Checkpoint (new, with GPS)
- ✅ Reason Quick Picker
- ✅ Current Status Display
- ✅ Recent Logs Display

### Pending Features
- ⏳ History Page (basic version exists, needs checkpoint integration)
- ⏳ Token Refresh
- ⏳ Role-Based Access
- ⏳ Leave Request
- ⏳ Missed Punch Request
- ⏳ Reports/Analytics

### System Health
- **Backend**: ✅ Running (port 8000)
- **Frontend**: ✅ Running (port 5173)
- **Database**: ✅ Connected
- **Auth**: ✅ JWT enabled
- **OUT Checkpoint**: ✅ Fully functional

---

**Document Version:** 13.0  
**Last Updated:** 2026-03-06 00:35  
**Next Review:** Team decision on WP-11-12 vs WP-11-13
