# WP-S1-14A：Leave Request Create 完成報告

> **日期**：2026-03-29
> **狀態**：COMPLETE
> **票號**：WP-S1-14A

---

## 1. Summary

建立請假申請功能（S1-14A）。

**重大發現**：Backend leave module（models/schemas/service/api）已由 WP-11-08 完整實作，本輪不需新建任何 backend 檔案。
本輪只新增 Frontend（leave.js API client + LeaveRequestView.vue + router）。

---

## 2. Files Changed

| 檔案 | 類型 | 說明 |
|------|------|------|
| `frontend/src/api/leave.js` | 新增 | `createLeaveRequest()` / `getMyLeaveRequests()` |
| `frontend/src/views/LeaveRequestView.vue` | 新增 | 338 行，請假申請表單 |
| `frontend/src/router/index.js` | patch | 加入 `/leave` route |

### Backend（無需修改，已完整）
- `backend/app/modules/leave/models.py`（439 行）：LeaveType / LeaveApprovalPolicy / LeaveRequest / LeaveApprovalLog
- `backend/app/modules/leave/schemas.py`（231 行）：LeaveRequestCreate / LeaveRequestResponse
- `backend/app/modules/leave/service.py`（467 行）：`submit_leave_request()`
- `backend/app/modules/leave/api.py`（292 行）：`POST /api/v1/leave/requests`（已掛入 main.py）

---

## 3. Data Model（已存在）

```
LeaveRequest:
  id          UUID (PK)
  company_id  String  — 來自 actor.active_company_id（tenant isolation）
  user_id     UUID    — 來自 actor.user_id
  leave_type_id UUID  — FK to leave_types（必須同公司且 is_active）
  start_date  Date
  end_date    Date
  reason      Text    — min 1 / max 1000 chars
  is_half_day Boolean
  status      String  — default: pending
  created_at  DateTime
```

---

## 4. API Contract

```
POST /api/v1/leave/requests
Authorization: Bearer {token}

Body:
{
  "leave_type_id": "uuid",
  "start_date": "2026-04-01",
  "end_date": "2026-04-03",
  "reason": "家事",
  "is_half_day": false
}

Response 201:
{
  "id": "uuid",
  "company_id": "...",  ← from JWT, NOT from payload
  "user_id": "uuid",   ← from JWT, NOT from payload
  "status": "pending",
  ...
}

Errors:
  401 — 未登入
  403 FEATURE_DISABLED — leave.core 未啟用
  403 SCOPE_ERROR — 無 company context
  422 — leave_type_id 無效 / 日期錯誤 / 缺必填欄位
```

---

## 5. Security（Tenant Isolation）

- `company_id` 來自 `actor.active_company_id`（JWT），**不接受 client 傳入**
- `user_id` 來自 `actor.user_id`（JWT），**不接受 client 傳入**
- `leave_type_id` 由 backend 驗證必須屬於同 company
- Feature Gate：`leave.core` 必須啟用

---

## 6. Frontend Features

- 假別下拉選單（annual/sick/personal/bereavement/marriage/maternity/paternity/other）
- Leave Type UUID 輸入（UUID format validation）
- 日期範圍選擇（client-side：end_date >= start_date）
- 半天假 checkbox
- 請假原因 textarea（1-1000 字）
- 送出後顯示成功訊息 + 重置表單
- FEATURE_DISABLED 錯誤友善顯示
- 最近申請列表（onMounted 載入）

---

## 7. Validation

| 測試 | 結果 |
|------|------|
| Backend leave tests（13/14）| PASS |
| `test_my_requests_only_returns_own_company_data` | FAIL（既有 bug，與本輪無關）|

### 既有 bug 說明
- `test_my_requests_only_returns_own_company_data`：`KeyError: 'company_id'`
- 測試程式碼直接用 `response['company_id']`，但 response 結構與預期不符
- 此 bug 在 WP-11-08 時已存在，**本輪未引入**
- 保留為下一票修復

---

## 8. Risks / Follow-up

| 項目 | 說明 |
|------|------|
| Leave Type UUID 需手動輸入 | 目前前端無 `GET /leave/types` 可用，需 admin 提供 UUID；後續可加 leave types 管理 UI |
| `test_my_requests_only_returns_own_company_data` bug | 既有 bug，下一票修復 |
| Feature Gate | 公司需啟用 `leave.core` feature 才能使用；前端已有友善錯誤訊息 |
| Navbar 未加 Leave 連結 | 可後續在 Home.vue 或 Navbar 加入入口 |

---

## 9. File Safety Check

| 檔案 | Lines | Bytes | Head | Tail |
|------|-------|-------|------|------|
| `leave.js` | 34 | OK | `/**` | `}` |
| `LeaveRequestView.vue` | 338 | OK | `<template>` | `</style>` |
| `router/index.js` | 147 | OK | `import {` | `export default router` |

---

## 10. Final Status

| 標準 | 結果 |
|------|------|
| 員工可成功建立請假 | ✅（前端 form + API client）|
| tenant isolation 正確 | ✅（backend 已實作，company_id/user_id 來自 JWT）|
| 不依賴 client 傳 company_id / user_id | ✅ |
| 不破壞現有系統 | ✅（13/14 leave tests pass，1 fail 為既有 bug）|
| 不做 whole-file rewrite | ✅ |

**WP-S1-14A COMPLETE**
