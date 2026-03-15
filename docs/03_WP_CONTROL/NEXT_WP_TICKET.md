# Next WP Ticket

**更新日期：** 2026-03-15（WP-11-07 COMPLETE；WP-11-08 成為當前 WP）  
**當前狀態：** WP-11-07 COMPLETE；當前 WP：WP-11-08 Leave Request System (PLANNED)

---

## WP-11-06 Reporting Backend — COMPLETE ✅

**完成日期：** 2026-03-14  
**狀態：** COMPLETE

### 完成 API

| Endpoint | 狀態 |
|----------|------|
| `GET /api/v1/attendance/sessions` | COMPLETE |
| `GET /api/v1/attendance/reports/user-summary` | COMPLETE |
| `GET /api/v1/attendance/reports/company-summary` | COMPLETE |

### 驗收記錄

- OpenAPI `/docs` 顯示三支 endpoint ✅
- UI 三頁（Sessions / User Summary / Company Summary）可正常呼叫 API ✅
- Tenant isolation 已驗證 ✅

### 備注

初始 runtime 問題：uvicorn reloader 孤兒 worker（PID 1856041，2026-03-11 16:58 啟動）導致 `api.py` 修改後未 reload。
以 clean restart 解決，無需修改任何程式碼。
詳見：`docs/WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md`

---

## 當前完成狀態（截至 2026-03-14）

| WP | 名稱 | 狀態 |
|----|------|------|
| WP-11-01 | Attendance Domain Model | COMPLETED |
| WP-11-02 | Punch In/Out API | COMPLETED |
| WP-11-03 | Policy Engine v1 | COMPLETED |
| WP-11-04A | Company Entitlements + Feature Flags | COMPLETED |
| WP-11-04B | Gate Ready Audit | COMPLETED |
| WP-11-05A | Attendance Models Sync | COMPLETED |
| **WP-11-06** | **Reporting Backend API** | **COMPLETE（2026-03-14）** |
| **WP-11-07** | **Reporting UI Polish / QA** | **COMPLETE（2026-03-15）** |
| WP-11-07~13 Step3A | Frontend UI 系列 | COMPLETED |
| WP-11-13 Manual QA | GPS + UI 人工測試 | BLOCKED（需環境） |
| **系統驗證基線建立** | SYSTEM_VERIFICATION_BASELINE | **COMPLETED（2026-03-11）** |
| **WP-C1-01** | PostgreSQL 環境建立 + Migration 驗證 | **VERIFIED（2026-03-11）** |
| **WP-C1-07** | Attendance API JWT 遷移 | **COMPLETED（2026-03-12）** |
| **WP-C1-08 Phase 1** | Attendance Test Re-Enable 基線驗證 | **VERIFIED（2026-03-12）** |
| **WP-C1-08 Phase 2** | Fixture Layer 修復 | **FIXTURE_COMPLETE（2026-03-12）** |
| **WP-C1-09** | OUT Checkpoint API | **DONE（2026-03-12）** |

---

## 已完成 WP：WP-11-07 — Reporting UI Polish / QA ✅ COMPLETE

**完成日期：** 2026-03-15  
**狀態：** COMPLETE

### WP-11-07 Completion Notes

- ✅ Reporting UI pages verified（Sessions / CompanySummary / UserSummary 三頁均驗收通過）
- ✅ BUG-01 fixed（`stores/reporting.js` response 解構正確，無多餘 `.data` 取用）
- ✅ WARN-01 cleaned（`sessionsFilters` dead state 已移除）
- ✅ Timezone display confirmed（Asia/Taipei，dayjs.tz 全域設定正確）
- ✅ Loading / Error / Empty states verified（四態完整實作）
- ✅ API endpoints 正確呼叫（`/api/v1/attendance/sessions`、`/reports/company-summary`、`/reports/user-summary`）

---

## 當前 WP：WP-11-08 — Leave Request System（PLANNED）

**Status：** PLANNED  
**前置條件：** WP-11-07 COMPLETE ✅  
**內容：** 員工請假申請、主管審核流程、請假記錄查詢  
**範圍：** Backend API + Frontend UI + Tenant Isolation

> 本 WP 開始前需建立完整 Spec 文件並更新 NEXT_WP_TICKET.md。

---

## 後續 WP 順序

```
WP-11-06（Reporting Backend）✅ COMPLETE 2026-03-14
  ↓
WP-11-07（Reporting UI Polish / QA）✅ COMPLETE 2026-03-15
  ↓
WP-11-08（Leave Request System）← 當前 WP
  ↓
WP-C1-03（Auth 轉換 Batch 2：audit/notifications/backup）
  ↓
WP-C1-04（8 個回歸測試，真實 DB）
  ↓
WP-C1-05（Tenant Isolation 真實 DB 測試）
  ↓
WP-C1-06（Feature Gate 套用）
  ↓
[Phase 1 Complete — Gate 5 可宣告完成]
```

---

**最後更新：** 2026-03-15  
**更新原因：** WP-11-07 COMPLETE（2026-03-15）；WP-11-08 成為當前 WP
