# Next WP Ticket

**更新日期：** 2026-03-11（WP-C1-01 完成後更新）
**當前狀態：** WP-C1-01 VERIFIED；切換至 WP-C1-02

---

## 重要：模式切換

本文件從即日起切換為 **基線修正優先（Baseline-Fix-First）** 模式。

**不再推薦直接開發新功能**（reporting / leave / approval）。
**原因：**
1. 5 個模組仍使用 Header auth，存在嚴重安全漏洞（任何人可偽造身份）
2. Admin Location API 完全無 RBAC
3. 8 個回歸測試只有 1 個，且從未在真實 DB 執行通過
4. Tenant Isolation 測試使用 Mock DB，非真實驗證
5. 在不安全基線上開發新功能，等同將技術債翻倍

---

## 當前完成狀態（截至 2026-03-11，WP-C1-01 完成後）

| WP | 名稱 | 狀態 |
|----|------|------|
| WP-11-01 | Attendance Domain Model | COMPLETED（CODE_COMPLETE） |
| WP-11-02 | Punch In/Out API | COMPLETED（CODE_COMPLETE，auth 需轉換） |
| WP-11-03 | Policy Engine v1 | COMPLETED（CODE_COMPLETE） |
| WP-11-04A | Company Entitlements + Feature Flags | COMPLETED（CODE_COMPLETE） |
| WP-11-04B | Gate Ready Audit | COMPLETED |
| WP-11-05A | Attendance Models Sync | COMPLETED |
| WP-11-07~13 Step3A | Frontend UI 系列 | COMPLETED（CODE_COMPLETE） |
| WP-11-13 Manual QA | GPS + UI 人工測試 | BLOCKED（需環境） |
| **系統驗證基線建立** | SYSTEM_VERIFICATION_BASELINE | **COMPLETED（2026-03-11）** |
| **WP-C1-01** | PostgreSQL 環境建立 + Migration 驗證 | **VERIFIED（2026-03-11）** |

---

## 當前阻塞

### BLOCKER-1：全系統 Auth 雙軌制（P0）

5 個模組（attendance / audit / notifications / backup / admin_location）仍使用 X-Company-ID Header，無使用者身份驗證。

### BLOCKER-2：Admin Location API 無 RBAC（P0）

POST/PUT/DELETE `/api/v1/admin/allowed-locations` 的 RBAC 為 `# TODO`，普通員工可操作地點政策。

### BLOCKER-3：回歸測試基線缺失（P0）

8 個回歸測試只有 1 個（Test 8 骨架），且從未在真實 DB 執行通過。

### BLOCKER-4：Tenant Isolation 未在真實 DB 驗證（P0）

現有 `test_tenant_isolation.py` 使用 DummySession，非真實 PostgreSQL 驗證。

---

## 當前建議工作包：WP-C1-02

### WP-C1-02：Attendance 模組 JWT 身份驗證遷移

**前置條件：** WP-C1-01 VERIFIED ✅（2026-03-11）

**為什麼先做這個：**
- attendance 模組 10 個 endpoint 全部使用 Header auth，是最大的 P0 安全漏洞
- admin_location 3 個寫入 endpoint 完全無 RBAC，需同步修正
- 完成後解鎖 WP-C1-04（回歸測試）

**受影響 Endpoint（來源：SYSTEM_GROUND_TRUTH.md 1.3）：**

| Endpoint | 行號 |
|----------|------|
| POST /mock-create | L70-73 |
| POST /{id}/approve | L84-90 |
| POST /v1/punch-in | L109-115 |
| POST /v1/punch-out | L173-179 |
| GET  /v1/current-status | L266-270 |
| GET  /v1/history | L352-359 |
| POST /v1/break-out | L410-416 |
| POST /v1/break-in | L493-499 |
| GET  /v1/break-punches | L544-549 |
| PATCH /v1/punch/{id}/note | L607-613 |

**admin_location RBAC 缺口（SYSTEM_GROUND_TRUTH.md 2.1）：**

| Endpoint | 行號 | 現況 |
|----------|------|------|
| POST / (create) | L47 | TODO 驗證管理員權限 — 無 RBAC |
| PUT /{id} | L166 | TODO 驗證管理員權限 — 無 RBAC |
| DELETE /{id} | L207 | TODO 驗證管理員權限 — 無 RBAC |

**已知額外問題（WP-C1-01 發現）：**
- `AttendanceSessionRepository.close_session()` API 簽名與 test_business_invariant.py 不符
- datetime timezone mismatch 問題
- 以上需在 WP-C1-02 修正 auth 時一併確認

**Definition of Done：**
- [ ] attendance/api.py 所有 endpoint 改用 get_current_actor()
- [ ] get_current_company_id 在 attendance 模組中已移除
- [ ] admin_location_api.py 3 個寫入 endpoint 實作 RBAC
- [ ] 既有 attendance 測試更新為使用 JWT token
- [ ] 所有 attendance 測試在真實 DB 通過
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新
- [ ] MODULE_STATUS_MATRIX.md attendance auth 欄位更新為 VERIFIED

---

## 後續 WP 順序

```
WP-C1-01（DB 環境）✅ VERIFIED 2026-03-11
  ↓
WP-C1-02（Attendance Auth JWT 轉換）← 當前
  ↓
WP-C1-03（Auth 轉換 Batch 2：audit/notifications/backup）
  ↓
WP-C1-04（8 個回歸測試，真實 DB）
  ↓
WP-C1-05（Tenant Isolation 真實 DB 測試）
  ↓
WP-C1-06（Feature Gate 套用）
  ↓
WP-C1-07（API 文件補齊）
  ↓
[Phase 1 Complete — Gate 5 可宣告完成]
  ↓
WP-C2-01（Location Policy 擴展至所有打卡流程）
WP-11-13 Manual QA（同步執行）
  ↓
WP-C2-02（Reporting Backend）
```

---

**最後更新：** 2026-03-11
**更新原因：** WP-C1-01 VERIFIED，切換至 WP-C1-02
