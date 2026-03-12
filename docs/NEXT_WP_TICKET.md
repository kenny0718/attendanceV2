# Next WP Ticket

**更新日期：** 2026-03-12（WP-C1-08 Phase 2 Fixture Layer 完成後更新）  
**當前狀態：** WP-C1-08 Phase 2 FIXTURE_COMPLETE；準備 Phase 3 實作修復

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

## 當前完成狀態（截至 2026-03-12，WP-C1-08 Phase 2 完成後）

| WP | 名稱 | 狀態 |
|----|------|------|
| WP-11-01 | Attendance Domain Model | COMPLETED |
| WP-11-02 | Punch In/Out API | COMPLETED |
| WP-11-03 | Policy Engine v1 | COMPLETED |
| WP-11-04A | Company Entitlements + Feature Flags | COMPLETED |
| WP-11-04B | Gate Ready Audit | COMPLETED |
| WP-11-05A | Attendance Models Sync | COMPLETED |
| WP-11-07~13 Step3A | Frontend UI 系列 | COMPLETED |
| WP-11-13 Manual QA | GPS + UI 人工測試 | BLOCKED（需環境） |
| **系統驗證基線建立** | SYSTEM_VERIFICATION_BASELINE | **COMPLETED（2026-03-11）** |
| **WP-C1-01** | PostgreSQL 環境建立 + Migration 驗證 | **VERIFIED（2026-03-11）** |
| **WP-C1-07** | Attendance API JWT 遷移 | **COMPLETED（2026-03-12）** |
| **WP-C1-08 Phase 1** | Attendance Test Re-Enable 基線驗證 | **VERIFIED（2026-03-12）** |
| **WP-C1-08 Phase 2** | Fixture Layer 修復 | **FIXTURE_COMPLETE（2026-03-12）** |
| **WP-C1-09** | OUT Checkpoint API | **DONE（2026-03-12）** |

---

## 當前阻塞

### BLOCKER-1：全系統 Auth 雙軌制（P0）
5 個模組（attendance / audit / notifications / backup / admin_location）中，attendance 已完成 JWT 遷移（WP-C1-07），其餘 4 個模組待處理。

### BLOCKER-2：Admin Location API 無 RBAC（P0）
POST/PUT/DELETE `/api/v1/admin/allowed-locations` 的 RBAC 為 `# TODO`。

### BLOCKER-3：3 個已識別的產品層缺失（Phase 3 目標）
詳見 `WP-C1-08_REMAINING_FAILURE_RECLASSIFICATION.md`。

---

## 當前建議工作包：WP-C1-08 Phase 3

### WP-C1-08 Phase 3：產品層缺失修復（3 個 defect 群組）

**前置條件：** WP-C1-08 Phase 2 FIXTURE_COMPLETE ✅（2026-03-12）

**為什麼現在做這個：**
- Fixture 層已完整建立，可直接進入產品修復
- 3 個修復項目邊界清晰，風險可控
- 完成後可解鎖 18 個測試全部通過

**實作順序（依風險由低至高）：**

### Priority 1：WP-C1-10 — location_id support in create_punch()

**範圍：** `backend/app/modules/attendance/repo.py` only  
**目標測試：** `test_break_out_enforcement.py` 5 個失敗測試  
**預計工時：** 30 分鐘  
**風險：** 🟢 LOW

```
修復項目：
- 加入 location_id 參數至 create_punch() 方法簽名
- 確認 AttendancePunch model 有 location_id 欄位
- 如無欄位則加入 migration
```

**Definition of Done：**
- [ ] test_break_out_enforcement.py：6/6 PASS

---

### Priority 2：WP-C1-11 — cross-midnight duration_minutes fix

**範圍：** `backend/app/modules/attendance/repo.py` close_session()  
**目標測試：** `test_regression.py` 1 個失敗測試  
**預計工時：** 1 小時  
**風險：** 🟡 LOW-MEDIUM

```
修復項目：
- 調查 close_session() duration 計算邏輯
- 修正跨午夜 datetime 差值計算（timezone-aware）
- duration = (punch_out_time - punch_in_time).total_seconds() / 60
```

**Definition of Done：**
- [ ] test_regression.py：1/1 PASS
- [ ] duration_minutes == 180 for cross-midnight scenario

---

### Priority 3：WP-C1-09 — out-checkpoint endpoint implementation

**範圍：** `backend/app/modules/attendance/api.py` + repo  
**目標測試：** `test_out_checkpoint.py` 7 個失敗測試  
**預計工時：** 2-3 小時  
**風險：** 🟡 MEDIUM

```
修復項目：
- 新增 POST /api/v1/attendance/out-checkpoint
- 新增 GET /api/v1/attendance/out-checkpoints
- 實作 GPS 驗證邏輯（mobile 需要 GPS）
- 實作 dedup 邏輯（30s + 50m window）
- 從 repo.py.backup 恢復 OutCheckpointRepository
```

**Definition of Done：**
- [ ] test_out_checkpoint.py：7/7 PASS

---

## Phase 3 完成後總體目標

```
當前通過：183 passed（全套件）
當前 Phase 2 target 通過：1/14（test_break_out_outside_allowed_location_fails）
Phase 3 完成後目標：183 + 13 = ~196 passed
```

---

## 後續 WP 順序

```
WP-C1-01（DB 環境）✅ VERIFIED 2026-03-11
  ↓
WP-C1-07（Attendance Auth JWT 轉換）✅ COMPLETED 2026-03-12
  ↓
WP-C1-08 Phase 1（基線驗證）✅ VERIFIED 2026-03-12
  ↓
WP-C1-08 Phase 2（Fixture Layer）✅ FIXTURE_COMPLETE 2026-03-12
  ↓
WP-C1-10（location_id support）← Priority 1
WP-C1-11（cross-midnight duration fix）← Priority 2
WP-C1-09（out-checkpoint endpoint）✅ DONE 2026-03-12
  ↓
WP-C1-08 Phase 3 VERIFIED（全 18 個 Phase 2/3 測試通過）
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
  ↓
WP-C2-01（Location Policy 擴展至所有打卡流程）
WP-11-13 Manual QA（同步執行）
  ↓
WP-C2-02（Reporting Backend）
```

---

**最後更新：** 2026-03-12  
**更新原因：** WP-C1-09 OUT Checkpoint API DONE；下一張建議票：WP-C1-03

---

## 下一張建議票：WP-C1-03

### WP-C1-03：Auth 轉換 Batch 2（audit / notifications / backup 模組）

**Priority：** P0（安全性）  
**前置條件：** WP-C1-07（attendance JWT 遷移）✅、WP-C1-09 ✅  
**預估複雜度：** Medium（3 個模組，pattern 已由 WP-C1-07 確立）

**背景：**  
WP-C1-07 完成了 attendance 模組的 Header auth → JWT Actor 遷移，建立了可重用的遷移 pattern。
auit、notifications、backup 三個模組仍使用 `X-Company-ID` Header auth，存在身份偽造漏洞（P0）。

**目標：**
1. `audit/api.py`：`get_current_company_id` → `get_actor_with_company`
2. `notifications/api.py`：同上
3. `backup/api.py`：同上
4. 每個模組補充對應測試（沿用 WP-C1-07 的測試 pattern）

**驗收條件：**
- 三個模組所有 endpoint 均使用 JWT Actor
- 現有測試不退步
- `X-Company-ID` Header 在三個模組中完全移除

**下一步之後：** WP-C1-04（8 個回歸測試，真實 DB）
