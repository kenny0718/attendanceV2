# Next WP Ticket — WP-11-06 or UI MVP

**Selected WP:** WP-11-06 (Reporting) or WP-11-07 (UI MVP)  
**Reason:** WP-11-05D completed, backend ready for UI development  
**Priority:** 🔴 P0

---

## Completed WPs

### WP-11-05D — Security Hardening + Docs Relocation + UI Readiness
**Date**: 2026-03-05  
**Status**: ✅ COMPLETED

**Deliverables**:
- ✅ Docs relocation: All references unified under `/opt/attendance-system/docs/`
- ✅ P0 Hardening: Production guard for `punch_time` parameter
- ✅ Security tests: 3 new tests (20/20 total tests passed)
- ✅ UI Readiness Report: `docs/WP-11-05D_UI_READINESS.md`

**Security Enhancement**:
- ✅ `is_testing()` 加入 `APP_ENV` 優先檢查
- ✅ Production/prod 環境永不允許 `punch_time` (即使 TESTING=true)
- ✅ 雙重檢查機制：APP_ENV → pytest modules → TESTING env var

**Test Results**:
- ✅ 20/20 punch API tests passed
- ✅ 3 new security tests:
  1. Production env rejects punch_time even with TESTING=true
  2. Test env allows punch_time (pytest auto-detection)
  3. Omitting punch_time works in all environments

**UI Readiness**:
- ✅ Backend API 完全準備好支援 UI 開發
- ✅ 4 個核心 endpoints 已就緒
- ✅ 無 P0 缺口

**Next**: UI MVP 或 WP-11-06 (Reporting)

---

## Option A: WP-11-07 — UI MVP (Punch Console)

### Goal
實作最小可用的打卡介面，驗證完整的前後端流程。

**核心功能**:
- Punch Console 單頁應用
- 顯示當前打卡狀態
- Punch In/Out 按鈕
- 顯示 policy evaluation 結果

---

### Context
- Backend API 已完成並測試通過 (20/20 tests)
- 4 個核心 endpoints 已就緒：
  - POST /api/v1/attendance/punch-in
  - POST /api/v1/attendance/punch-out
  - GET /api/v1/attendance/current-status
  - GET /api/v1/attendance/history

---

### Scope

**In Scope:**
- 單頁 Punch Console UI
- 整合 Current Status API
- 整合 Punch In/Out API
- 基本錯誤處理 (409, 404, 403)
- 簡單的 UI 樣式

**Out of Scope:**
- ❌ JWT Authentication (使用 header-based auth)
- ❌ Approval Workflow UI
- ❌ Advanced features (GPS, photo, offline)

---

### Expected Files

**New Files:**
```
frontend/src/pages/PunchConsole.tsx (or .vue/.jsx)
frontend/src/services/attendanceApi.ts
frontend/src/components/PunchButton.tsx
frontend/src/components/StatusDisplay.tsx
```

**Modified Files:**
```
frontend/src/App.tsx (routing)
frontend/package.json (dependencies)
docs/NEXT_WP_TICKET.md (update after completion)
```

---

### Acceptance Criteria

- [ ] 可以成功 Punch In
- [ ] 可以成功 Punch Out
- [ ] 顯示當前狀態 (open/closed)
- [ ] 顯示已打卡時間
- [ ] 錯誤訊息友善 (409, 404)
- [ ] UI 基本美觀

---

### Dependencies

**Prerequisite WPs:**
- ✅ WP-11-05D — COMPLETED

**Blocks:**
- WP-11-08 (JWT Integration)
- WP-11-09 (Approval Workflow UI)

---

## Option B: WP-11-06 — Attendance Reporting v1

### Goal
實作考勤報表功能，提供管理者查看員工打卡記錄。

**核心功能**:
- 員工打卡記錄查詢
- 日期範圍篩選
- 匯出 CSV/Excel
- 統計資訊 (遲到/早退/加班)

---

### Context
- Backend API 已有 history endpoint
- 需要新增報表相關 API
- 需要實作統計邏輯

---

### Scope

**In Scope:**
- 報表查詢 API
- 統計資訊 API
- CSV 匯出功能

**Out of Scope:**
- ❌ 報表 UI (留給後續 WP)
- ❌ 進階篩選 (部門/職位)

---

## 建議選擇

**建議優先**: **WP-11-07 (UI MVP)**

**理由**:
1. ✅ Backend API 已完全準備好
2. ✅ 可以快速驗證完整流程
3. ✅ 提供可見的成果展示
4. ✅ 為後續 UI 開發建立基礎

**WP-11-06 (Reporting)** 可以在 UI MVP 完成後再進行，因為：
- 報表功能相對獨立
- 需要先有基本 UI 框架
- 管理者功能優先級較低

---

**Ready to Start:** Yes (兩個選項都可以開始)  
**Blocker:** None  
**Assignee:** Frontend Team (WP-11-07) or Backend Team (WP-11-06)  
**Status:** ⏳ NEXT
