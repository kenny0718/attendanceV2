# Current System State

**建立日期：** 2026-03-17（WP-C1-07 COMPLETE 後更新）  
**基於：** 已確認的 repo scan（2026-03-17）+ pytest 27/28 PASS（1 pre-existing）  
**Repository：** `/opt/attendance-system`

---

## 1. Current WP（當前工作包）

**WP-C1-08 Phase 3 — Attendance 測試全面啟用**

- **Status：** CURRENT（WP-C1-07 已 COMPLETE）
- **內容：** attendance router_v1 JWT 遷移後的測試全面啟用
- **範圍：** Backend tests
- **前置條件：** WP-C1-07 COMPLETE ✅

---

## 2. Next WP（下一個工作包）

**Gate 5 完成宣告**

- **Status：** PLANNED（需 WP-C1-08 Phase 3 完成後）
- **內容：** Gate 5 完成宣告
- **範圍：** 全面驗收

---

## 3. Completed Core Modules（已完成核心模組）

| 模組 | 狀態 | 說明 |
|------|------|------|
| **Punch Engine** | ✅ STABLE | punch-in/out、session 建立、跨午夜規則、tenant isolation |
| **Break Engine** | ✅ STABLE | break-out/break-in、GPS 地點條件式驗證 |
| **Session Model** | ✅ STABLE | AttendanceSession 完整資料模型 |
| **Policy Engine** | ✅ STABLE | 遲到/早退/加班計算、Split Shift 支援 |
| **Timezone / Cross-midnight Rules** | ✅ STABLE | Session ownership = punch_in_time 的 Asia/Taipei 日期 |
| **Reporting Backend API** | ✅ COMPLETE | 三支 endpoint（WP-11-06，2026-03-14）|
| **Home UI** | ✅ STABLE | 主打卡頁、3-Card 佈局、mobile-first |
| **Authentication（JWT）** | ✅ STABLE | JWT-based auth，所有模組含 attendance router_v1 遷移完成（WP-C1-07）|
| **OUT Checkpoint Model/Repo** | ✅ PARTIAL | model/repo 存在，API endpoint 未建（WP-C1-09 gap）|
| **PostgreSQL Migration Chain** | ✅ VERIFIED | 21 tables，head = 009_wp_11_08（WP-C1-04，2026-03-17）|
| **Reporting UI** | ✅ COMPLETE | 三頁 UI（WP-11-07，2026-03-15）|
| **Leave Request System** | ✅ COMPLETE | 5 endpoints，tenant isolation（WP-11-08，2026-03-15）|
| **Auth JWT 遷移（audit/notifications/backup）** | ✅ COMPLETE | 78/78 tests PASS（WP-C1-03，2026-03-17）|
| **PostgreSQL 回歸驗證** | ✅ COMPLETE | 78/78 PASS，migration HEAD 確認（WP-C1-04，2026-03-17）|
| **Tenant Isolation 驗證** | ✅ COMPLETE | 39/39 PASS on PostgreSQL（WP-C1-05，2026-03-17）|
| **Attendance router_v1 JWT 遷移** | ✅ COMPLETE | 11/11 endpoints，12/12 tests PASS（WP-C1-07，2026-03-17）|

---

## 4. Partially Implemented Modules（部分完成模組）

| 模組 | 狀態 | 已完成部分 | 缺口 |
|------|------|-----------|------|
| **OUT Checkpoint API** | ⚠️ PARTIAL | model + repo 存在 | API endpoint 未建（404）|
| **router_v1 JWT 遷移** | ✅ COMPLETE | 所有 11 個 router_v1 endpoints 已遷移至 JWT Actor（WP-C1-07）| 舊版 router（mock-create/approve）維持 Header-based（向後相容）|
| **GPS / Location** | ⚠️ FOUNDATION | break-out 條件式驗證 | punch-in/out/break-in 無 location policy |
| **Feature Gate** | ✅ COMPLETE | 5 modules 22/22 tests PASS | WP-C1-06 COMPLETE 2026-03-17 |

---

## 5. Known Limitations（已知限制）

1. **OUT Checkpoint API 404** — WP-C1-09 只建 model/repo，未建 API endpoint
2. **router_v1 punch-in/punch-out/break-out** — 仍使用舊 X-Company-ID header（WP-C1-07 未完成）
3. **Feature Gate** — ✅ 已完成（WP-C1-06，2026-03-17）
4. **WP-11-13 Manual QA BLOCKED** — 需真實瀏覽器 + PostgreSQL 環境

---

## 6. Gate 5 Progress（開發進度）

**Gate 5 估計完成度：90%**

| 條件 | 狀態 |
|------|------|
| WP-C1-01 PostgreSQL 環境建立 | ✅ VERIFIED |
| WP-11-06 Reporting Backend API | ✅ COMPLETE |
| WP-11-07 Reporting UI Polish / QA | ✅ COMPLETE |
| WP-11-08 Leave Request System | ✅ COMPLETE |
| WP-C1-03 Auth 轉換 Batch 2 | ✅ COMPLETE（2026-03-17）|
| WP-C1-04 PostgreSQL 回歸測試 | ✅ COMPLETE（2026-03-17）|
| WP-C1-05 Tenant Isolation 真實 DB | ✅ COMPLETE（2026-03-17）|
| 所有模組使用 JWT auth | ✅ COMPLETE（WP-C1-07，router_v1 全面 JWT 遷移）|
| Feature Gate 套用 | ✅ COMPLETE（WP-C1-06，2026-03-17）|
| WP-11-13 Manual QA | ⛔ BLOCKED |

---

## 7. Tenant Isolation 狀態（WP-C1-05 結論）

**所有模組 Tenant Isolation 已驗證 ✅**

| 模組 | isolation 狀態 | 測試數 | 結果 |
|------|--------------|--------|------|
| attendance | ✅ VERIFIED | 9 | 9/9 PASS |
| audit | ✅ VERIFIED | 8 | 8/8 PASS |
| notifications | ✅ VERIFIED | 6 | 6/6 PASS |
| backup | ✅ VERIFIED | 6 | 6/6 PASS |
| leave | ✅ VERIFIED | 10 | 10/10 PASS |

**合計：39/39 PASS on PostgreSQL**

---

## 8. Architecture Summary（架構摘要）

- **Frontend：** Vue 3 + Pinia + Axios（mobile-first）
- **Backend：** FastAPI + SQLAlchemy + PostgreSQL
- **Auth：** JWT（Bearer token）
- **Timezone：** Asia/Taipei（cross-midnight 規則）
- **Migration HEAD：** `009_wp_11_08`（21 tables，2026-03-17 verified）

---

**此文件為當前系統狀態的單一真相來源（Single Source of Truth）。**

*本文件由 AI 依據 2026-03-17 實際執行結果更新。*  
*WP-C1-07 COMPLETE：attendance router_v1 JWT Migration，11/11 endpoints，12/12 tests PASS。*
