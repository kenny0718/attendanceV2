# DEVELOPMENT_EXECUTION_PLAN.md

## Purpose

本文件定義系統後續的依序開發執行計畫，基於 `MODULE_STATUS_MATRIX.md` 和 `SYSTEM_VERIFICATION_BASELINE.md` 的真實狀態建立。  
不可跳步，不可並行執行同層依賴的工作包。

## Scope

覆蓋 Phase 1（基線修正）、Phase 2（attendance domain 完成）、Phase 3（Phase 2+ 擴展）。

## Source of Truth

- `SYSTEM_VERIFICATION_BASELINE.md`（CODE SCAN 結果）
- `MODULE_STATUS_MATRIX.md`（模組狀態）
- `SA_MODULE_SPEC_v2.0.md`（架構規範）

## Last Updated

2026-03-11

---

## P0 阻塞清單（必須先解決，不解決不可進入任何新功能）

| ID | 阻塞項目 | 影響範圍 | 不解決的風險 |
|----|----------|----------|-------------|
| P0-1 | attendance/audit/notifications/backup 仍用 Header auth | 4 個模組 18 個 endpoint | 任何人可偽造 X-Company-ID 存取所有打卡/稽核/通知資料 |
| P0-2 | Admin Location API 完全無 RBAC | /api/v1/admin/allowed-locations 5 個端點 | 普通員工可建立/刪除/修改地點政策 |
| P0-3 | 8 個回歸測試只有 1 個實作，且未在真實 DB 執行 | Gate 5 完成條件 | 無法驗證打卡核心業務邏輯正確性 |
| P0-4 | Tenant Isolation 測試使用 Mock DB | 跨租戶安全性 | 無法驗證真實 DB 層面的隔離有效性 |

---

## 開發層次架構

```
C1. 修基線層（Phase 1）
├─ 不可跳過
├─ 任何 C2/C3 工作依賴此層完成
└─ 預估：5-8 個工作天

C2. Attendance Domain 完成層（Phase 2 前段）
├─ 依賴 C1 完成
├─ attendance 核心功能收尾
└─ 預估：3-5 個工作天

C3. Phase 2 擴展層
├─ 依賴 C1 + C2 完成
├─ 新模組實作
└─ 預估：依模組數量，每個 3-5 天
```

---

## C1. 修基線層（Phase 1 — Architecture Alignment）

**完成標準：**
- SA 符合度 > 95%
- 所有模組使用 JWT
- Scope 驗證統一
- Feature Gate 套用至核心 endpoint
- 8 個回歸測試在真實 DB 通過
- Tenant Isolation 測試在真實 DB 通過

---

### WP-C1-01：建立 PostgreSQL 測試環境 + Migration 驗證

**目標：** 確保 `alembic upgrade head` 在 fresh DB 可執行，建立後續所有測試的基礎環境。

**不可跳過原因：** 所有後續測試、Auth 轉換驗證、回歸測試都依賴可用的 DB 環境。

**具體工作：**
1. 建立 PostgreSQL 測試資料庫
2. 執行 `alembic upgrade head`，確認 8 個 migration 全部成功
3. 確認 `attendance_out_checkpoints` 表存在（migration 007 殘留，需記錄但不移除）
4. 確認 `alembic heads` 只顯示一個 head（008_wp_11_13）
5. 記錄執行結果到 `WORKSTREAM_STATUS_LEDGER.md`

**預期交付物：**
- 可用的測試 PostgreSQL DB
- migration 執行報告（success/fail log）
- WORKSTREAM_STATUS_LEDGER.md 更新

**依賴：** 無  
**後續：** WP-C1-02

---

### WP-C1-02：Attendance Auth JWT 轉換（WP-11-06）

**目標：** 將 `attendance/api.py` 從 Header auth 轉換為 JWT + `get_current_actor()`，並補齊 Scope 驗證與 Feature Gate。

**不可跳過原因：** attendance 模組是系統核心，Header auth 讓任何人可偽造身份打卡。

**具體工作：**
1. `attendance/api.py`：所有 endpoint 改用 `get_current_actor()` 取代 `get_current_company_id()`
2. 從 `actor.company_memberships` 取得 company_id（非 Header）
3. 加入 Scope 驗證（`assert_company_scope(actor, company_id, db)`）
4. 加入 Feature Gate（`attendance.punch_in_out`）
5. `admin_location_api.py`：補齊 RBAC 驗證（只允許 admin/manager role）
6. 更新所有 attendance 測試，改用 JWT token 而非 Header
7. 確認 tests 在測試 DB 執行通過

**預期交付物：**
- 更新後的 `attendance/api.py`
- 更新後的 `admin_location_api.py`（補齊 RBAC）
- 更新後的所有 attendance 測試檔
- 測試執行報告

**依賴：** WP-C1-01  
**後續：** WP-C1-03

---

### WP-C1-03：Auth 轉換 Batch 2（audit / notifications / backup）

**目標：** 將剩餘 3 個模組從 Header auth 轉換為 JWT + Actor。

**不可跳過原因：** 以 WP-C1-02 為範本，批次轉換，確保全系統 auth 統一。

**具體工作：**
1. `audit/api.py`：改用 `get_current_actor()`，加入 Scope + Feature Gate（audit.query / audit.export）
2. `notifications/api.py`：改用 `get_current_actor()`
3. `backup/api.py`：改用 `get_current_actor()`，加入 Scope + Feature Gate（backup.export / backup.restore）
4. 更新所有相關測試
5. 執行測試確認通過
6. 從代碼中移除或標記 `tenant_context.py` 的舊 Header 依賴（保留檔案但加上棄用標記）

**預期交付物：**
- 更新後的 audit / notifications / backup api.py
- 更新後的相關測試
- 測試執行報告

**依賴：** WP-C1-02  
**後續：** WP-C1-04

---

### WP-C1-04：8 個回歸測試實作 + 真實 DB 執行（WP-11-05）

**目標：** 實作所有 8 個 attendance 核心回歸測試，並在真實 PostgreSQL DB 執行通過。

**不可跳過原因：** 這是 Gate 5 