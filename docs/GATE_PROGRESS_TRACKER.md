# Gate Progress Tracker

**最後更新：** 2026-03-11

---

## ⚠️ 重要狀態說明

本文件於 2026-03-11 更新，反映「系統驗證基線建立」後的真實狀態。

**狀態分類說明：**
- `COMPLETED`：有明確的程式碼 + 文件記錄
- `CODE_COMPLETE`：程式碼存在，但 runtime 未驗證（特別標注）
- `NOT_VERIFIED`：測試存在但從未在真實 DB 通過
- `BLOCKED`：有明確阻塞原因
- `NOT_STARTED`：尚未開始

---

## Gate 5 — Frontend UI Phase

**狀態：** IN_PROGRESS（Phase 1 基線修正未完成）

---

### Backend WP 完成狀態

| WP | 名稱 | 狀態 | 備注 |
|----|------|------|------|
| WP-11-01 | Attendance Domain Model | COMPLETED | code scan 確認；runtime NOT_VERIFIED |
| WP-11-02 | Punch In/Out API | CODE_COMPLETE | auth 使用 Header，需 WP-C1-02 修正 |
| WP-11-03 | Policy Engine v1 | CODE_COMPLETE | runtime NOT_VERIFIED |
| WP-11-04A | Company Entitlements + Feature Flags | CODE_COMPLETE | Feature Gate 套用 MISSING |
| WP-11-04B | Gate Ready Audit | COMPLETED | 部分結論已被 SYSTEM_VERIFICATION_BASELINE 更新 |
| WP-11-05 | Attendance Regression Tests | PARTIAL — 1/8 實作，0/8 在真實 DB 通過 | **P0 缺口** |
| WP-11-05A | Attendance Models Sync | COMPLETED | |
| WP-11-06 / WP-C1-02 | Auth 轉換 Batch 1（attendance） | NOT_STARTED | **P0** |
| WP-C1-03 | Auth 轉換 Batch 2-4（audit/notifications/backup） | NOT_STARTED | **P0** |
| WP-C1-04 | 回歸測試真實 DB 執行 | NOT_STARTED | 依賴 WP-C1-02 |
| WP-C1-05 | Tenant Isolation 真實 DB 驗證 | NOT_STARTED | 依賴 WP-C1-04 |
| WP-C1-06 | Feature Gate 套用至所有 API | NOT_STARTED | |
| WP-C1-07 / WP-15 | API 文件補充 | NOT_STARTED | |
| WP-C1-01 | PostgreSQL 環境建立 + Migration 驗證 | NOT_STARTED | **建議下一個執行** |

---

### Frontend WP 完成狀態

| WP | 名稱 | 狀態 | 備注 |
|----|------|------|------|
| WP-11-07 | UI MVP Kickoff | COMPLETED | |
| WP-11-08 | JWT Auth Integration | COMPLETED | |
| WP-11-10 | OUT Checkpoint Feature | COMPLETED+REMOVED | migration 007 殘留 table |
| WP-11-11.5 | GPS Legacy Cleanup | CLOSED | |
| WP-11-12 Ph1 | useLocation Composable | COMPLETED | |
| WP-11-12 Ph2B | BREAK_OUT Integration | CLOSED | |
| WP-11-13 Step2 | Backend Location Policy | CODE_COMPLETE | commit d8eb797 |
| WP-11-13 Step3A | Frontend Integration | CODE_COMPLETE | |
| WP-11-13 Manual QA | 瀏覽器 GPS + UI 人工測試 | BLOCKED | 需真實瀏覽器 + PostgreSQL 環境 |

---

### 新建文件狀態（2026-03-11）

| 文件 | 狀態 |
|------|------|
| docs/SYSTEM_VERIFICATION_BASELINE.md | ✅ 新建（2026-03-11） |
| docs/MODULE_STATUS_MATRIX.md | ✅ 新建（2026-03-11） |
| docs/DEVELOPMENT_EXECUTION_PLAN.md | ✅ 新建（2026-03-11） |
| docs/ACCEPTANCE_PLAN.md | ✅ 新建（2026-03-11） |
| docs/TEST_STRATEGY_MASTER.md | ✅ 新建（2026-03-11） |
| docs/WORKSTREAM_STATUS_LEDGER.md | ✅ 新建（2026-03-11） |
| docs/NEXT_WP_TICKET.md | ✅ 更新（切換為基線修正優先模式） |

---

### Gate 5 完成條件

- [ ] Phase 1 基線修正完成（WP-C1-01 ~ WP-C1-07）
- [ ] WP-11-13 Manual QA 通過
- [ ] SA 符合度 > 95%（目前約 65-70%）
- [ ] 8 個回歸測試在真實 DB 通過（目前 0/8）
- [ ] 5 個 Tenant Isolation 測試在真實 DB 通過（目前 0/5）
- [ ] 所有模組使用 JWT auth（目前 2/7）
- [ ] Feature Gate 套用至所有核心 API（目前 0%）

---

### 當前位置

- **剛完成：** 系統驗證基線建立（2026-03-11）
- **當前阻塞：** 4 個 P0 技術債（見 NEXT_WP_TICKET.md）
- **建議下一步：** WP-C1-01（PostgreSQL 環境建立 + Migration 驗證）
- **Gate 5 估計完成度：** 40%（基線修正工作包尚未開始）

---

### 已知文件不一致（需後續修正）

| 文件 | 問題 | 狀態 |
|------|------|------|
| SYSTEM_DEVELOPMENT_STATUS_REPORT.md | backup auth 方式誤標為 JWT | Superseded by MODULE_STATUS_MATRIX.md |
| ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md | WP-11-04B 狀態仍為 CURRENT | 需更新 |
| REALITY_AUDIT_STATUS_INVENTORY.md | 未含 migration 006/007/008 | 已過期，Superseded |
| SA_REALITY_GAP_REPORT.md | 未反映 WP-11-13 實作 | 已過期，Superseded |

---

## System Reality Verification v2 修正（2026-03-11）

以下結論經 code scan 重新確認，修正舊有錯誤記載：

| 項目 | 舊記載 | 新確認（CODE_CONFIRMED） |
|------|--------|-------------------------|
| Header auth 模組數 | 未明確列出 admin_location | **5 個**：attendance / audit / notifications / backup / admin_location |
| backup auth 方式 | JWT（SYSTEM_DEVELOPMENT_STATUS_REPORT 錯誤） | **Header（X-Company-ID）** |
| 回歸測試狀態 | PARTIAL（測試檔建立） | **1/8 實作（只有 Test 8 骨架），使用 Header auth，0/8 在真實 DB 通過** |
| Feature Gate | 基礎設施完整 | **完全未套用至任何生產 endpoint** |
| Tenant Isolation 測試 | 存在 | **test_tenant_isolation.py 使用 DummySession（Mock），非真實 DB** |
| Location Policy 整合 | BREAK_OUT 已完成 | **只有 break-out；punch-in/out/break-in 均無 location policy check** |

### 下一步建議（經 v2 驗證後不變）

**WP-C1-01（PostgreSQL 環境建立 + Migration 驗證）** 仍為正確的下一步。

權威依據：`docs/SYSTEM_REALITY_REPORT_v2.md`（2026-03-11）
