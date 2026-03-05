# Next WP Ticket — WP-11-07 Phase 2 (API Integration)

**Selected WP:** WP-11-07 Phase 2 - API Integration  
**Reason:** UI MVP Phase 1 completed, ready to connect backend APIs  
**Priority:** 🔴 P0

---

## Completed WPs

### WP-11-07 Phase 1 — UI MVP (Frontend Scaffold + Mock UI)
**Date**: 2026-03-05  
**Status**: ✅ COMPLETED

**Deliverables**:
- ✅ Frontend project scaffold (25 files)
- ✅ Vue 3 + Vite + Tailwind CSS + Pinia 完整配置
- ✅ UI 設計系統落地（配色、共用元件）
- ✅ Punch Console 首頁完成（Mock 版本）
- ✅ API 串接結構準備完成
- ✅ Kickoff Report: `docs/WP-11-07_UI_MVP_KICKOFF.md`

**Key Achievement**:
- ✅ 4 個共用元件可重用
- ✅ 2 個 Pinia stores 管理狀態
- ✅ 完整的 API 客戶端架構
- ✅ Punch Console 可運行並展示完整打卡流程（Mock 數據）

**UI 功能**:
- ✅ 今日狀態顯示（4 張狀態卡）
- ✅ 打卡按鈕（上班/下班/外出/返回）
- ✅ 最近打卡記錄列表
- ✅ 按鈕禁用邏輯、Loading 動畫、成功提示

**Next**: WP-11-07 Phase 2 (API Integration)

---

## WP-11-07 Phase 2 — API Integration

### Goal
將 Punch Console 的 Mock 數據替換為真實後端 API 呼叫，實現完整的前後端串接。

**核心目標**:
- 串接 4 個核心 API endpoints
- 處理真實的錯誤情況
- 驗證完整的打卡流程

---

### Context
- Frontend scaffold 已完成（Phase 1）
- Backend API 已就緒並測試通過（WP-11-05D）
- API 客戶端結構已準備好
- 4 個核心 endpoints 可用：
  - POST /api/v1/attendance/punch-in
  - POST /api/v1/attendance/punch-out
  - GET /api/v1/attendance/current-status
  - GET /api/v1/attendance/history

---

### Scope

**In Scope:**
- 串接 punch-in/punch-out API
- 串接 current-status API
- 串接 history API
- 錯誤處理（409, 404, 403）
- Loading 狀態連接
- 成功/失敗提示

**Out of Scope:**
- ❌ JWT 認證（使用 header-based auth）
- ❌ GPS 定位功能
- ❌ 照片上傳功能
- ❌ 其他頁面（個人資料、請假、補打卡）

---

### Work Plan

#### 1. 修改 Attendance Store

**檔案**: `frontend/src/stores/attendance.js`

**需要修改的 actions**:

```javascript
// 1. punch(type) - 打卡
async punch(type) {
  this.isLoading = true
  this.error = null
  
  try {
    // 替換 Mock
    let data
    switch (type) {
      case 'IN':
        data = await attendanceApi.punchIn({ notes: '' })
        break
      case 'OUT':
        data = await attendanceApi.punchOut({ notes: '' })
        break
      // ... 其他類型
    }
    
    // 更新狀態
    this.todayStatus = {
      punch_in: data.punch_in_time,
      punch_out: data.punch_out_time,
      // ...
    }
    
    // 重新獲取記錄
    await this.fetchRecentLogs()
    
    return { success: true }
  } catch (error) {
    this.error = error.message
    throw error
  } finally {
    this.isLoading = false
  }
}

// 2. fetchTodayStatus() - 獲取今日狀態
async fetchTodayStatus() {
  this.isLoading = true
  try {
    const data = await attendanceApi.getCurrentStatus()
    
    if (data.has_open_session && data.session) {
      this.todayStatus = {
        punch_in: data.session.punch_in_time,
        punch_out: data.session.punch_out_time,
        is_punched_in: data.session.status === 'open',
        // ...
      }
    }
  } catch (error) {
    this.error = error.message
    console.error('獲取狀態失敗:', error)
  } finally {
    this.isLoading = false
  }
}

// 3. fetchRecentLogs() - 獲取最近記錄
async fetchRecentLogs() {
  this.isLoading = true
  try {
    const data = await attendanceApi.getHistory({ limit: 10, offset: 0 })
    
    this.recentLogs = data.sessions.map(session => ({
      id: session.session_id,
      timestamp: session.punch_in_time,
      attendance_type: 'IN', // 需要根據實際情況判斷
      status: 'success',
      is_late: false // 需要從 policy_evaluation 取得
    }))
  } catch (error) {
    this.error = error.message
    console.error('獲取記錄失敗:', error)
  } finally {
    this.isLoading = false
  }
}
```

#### 2. 處理錯誤情況

**在 Home.vue 中**:

```javascript
const handlePunch = async (type) => {
  try {
    await attendanceStore.punch(type)
    
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    // 根據錯誤類型顯示不同訊息
    let message = '打卡失敗'
    
    if (error.status === 409) {
      message = '已有打開的打卡記錄'
    } else if (error.status === 404) {
      message = '找不到打開的打卡記錄'
    } else if (error.status === 403) {
      message = '無權限執行此操作'
    } else {
      message = error.message || '未知錯誤'
    }
    
    alert(message) // 或使用更好的 toast 組件
  }
}
```

#### 3. 測試 API 串接

**測試步驟**:
1. 確保後端服務運行（port 8000）
2. 啟動前端開發服務器（port 5173）
3. 測試打卡流程：
   - 上班打卡 → 檢查狀態更新
   - 下班打卡 → 檢查狀態更新
   - 查看記錄列表
4. 測試錯誤情況：
   - 重複打卡 → 應顯示 409 錯誤
   - 未打卡就下班 → 應顯示 404 錯誤

---

### Expected Files

**Modified Files:**
```
frontend/src/stores/attendance.js    # 替換 Mock 為真實 API
frontend/src/views/Home.vue          # 改善錯誤處理
frontend/src/api/attendance.js       # 可能需要調整 API 路徑
docs/NEXT_WP_TICKET.md               # 更新下一步
docs/GATE_PROGRESS_TRACKER.md        # 記錄完成
```

**New Files:**
```
docs/WP-11-07_PHASE2_COMPLETION_REPORT.md  # 完成報告
```

---

### Acceptance Criteria

- [ ] 上班打卡成功，狀態卡即時更新
- [ ] 下班打卡成功，狀態卡即時更新
- [ ] 外出/返回打卡成功（如果後端支援）
- [ ] 頁面載入時自動獲取今日狀態
- [ ] 最近記錄列表顯示真實數據
- [ ] 重複打卡顯示友善錯誤訊息（409）
- [ ] 未打卡就下班顯示友善錯誤訊息（404）
- [ ] Loading 狀態正確顯示
- [ ] 成功提示正確顯示

---

### Dependencies

**Prerequisite WPs:**
- ✅ WP-11-07 Phase 1 — COMPLETED
- ✅ WP-11-05D — COMPLETED (Backend API ready)

**Blocks:**
- WP-11-08 (JWT Authentication Integration)
- WP-11-09 (GPS Location Feature)
- WP-11-10 (Other Pages: Profile, Leave, Reports)

---

### API Endpoints Reference

#### 1. Punch In
```
POST /api/v1/attendance/punch-in
Headers: X-Company-ID, X-User-ID
Body: { notes?: string, location?: { latitude, longitude } }
Response: { session_id, user_id, company_id, punch_in_time, status }
```

#### 2. Punch Out
```
POST /api/v1/attendance/punch-out
Headers: X-Company-ID, X-User-ID
Body: { notes?: string, location?: { latitude, longitude } }
Response: { session_id, punch_out_time, duration_minutes, policy_evaluation }
```

#### 3. Current Status
```
GET /api/v1/attendance/current-status
Headers: X-Company-ID, X-User-ID
Response: { has_open_session, session?, elapsed_minutes? }
```

#### 4. History
```
GET /api/v1/attendance/history?limit=10&offset=0
Headers: X-Company-ID, X-User-ID
Response: { sessions: [...], total, limit, offset }
```

---

### Known Issues & Solutions

#### Issue 1: CORS 錯誤
**Solution**: 確保後端 FastAPI 已配置 CORS middleware

#### Issue 2: 401 Unauthorized
**Solution**: 
- MVP 階段：確保 API 不要求 JWT token
- 或在 `api/client.js` 中暫時移除 Authorization header

#### Issue 3: Tenant Headers 缺失
**Solution**: 確保 `authStore.mockUser` 有正確的 `company_id` 和 `id`

---

## Alternative: WP-11-06 — Attendance Reporting v1

如果 API 串接遇到阻礙，可以先做報表功能（獨立模組）。

### Goal
實作考勤報表功能，提供管理者查看員工打卡記錄。

**核心功能**:
- 員工打卡記錄查詢
- 日期範圍篩選
- 匯出 CSV/Excel
- 統計資訊

---

## 建議選擇

**建議優先**: **WP-11-07 Phase 2 (API Integration)**

**理由**:
1. ✅ Frontend scaffold 已完成
2. ✅ Backend API 已就緒並測試通過
3. ✅ 可以快速驗證完整流程
4. ✅ 為後續功能建立基礎

**預估時間**: 1-2 天

---

**Ready to Start:** Yes  
**Blocker:** None (需確保後端服務運行)  
**Assignee:** Frontend Team  
**Status:** ⏳ NEXT
