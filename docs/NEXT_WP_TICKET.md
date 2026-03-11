# Next WP Ticket

**更新日期：** 2026-03-11  
**當前狀態：** 系統驗證基線已建立；切換為「基線修正優先」模式

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

## 當前完成狀態（截至 2026-03-11）

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

## 下一個建議工作包：WP-C1-01

### WP-C1-01：建立 PostgreSQL 測試環境 + Migration 驗證

**為什麼先做這個：**
- 這是所有後續工作的基礎
- 不需要修改程式碼，只需要環境設定
- 完成後立即解鎖 WP-C1-02 和回歸測試執行
- 可在 30-60 分鐘內完成

**執行步驟：**

```bash
# 1. 確認 PostgreSQL 服務狀態
psql --version

# 2. 建立測試資料庫
createdb attendance_db

# 3. 設定 DATABASE_URL
export DATABASE_URL="postgresql+psycopg2://postgres:password@127.0.0.1:5432/attendance_db"

# 4. 執行 migration
cd /opt/attendance-system/backend
python -m alembic upgrade head

# 5. 確認 migration 結果
python -m alembic current
python -m alembic heads

# 6. 確認所有 table 建立
psql -d attendance_db -c "\dt"

# 7. 執行 migration smoke test
pytest tests/test_migration_smoke.py -v
```

**Definition of Done：**
- [ ] `alembic upgrade head` 執行成功（008_wp_11_13 為 head）
- [ ] `alembic heads` 只顯示一個 head
- [ ] 所有 15 個 table 正確建立
- [ ] migration smoke test 通過
- [ ] `WORKSTREAM_STATUS_LEDGER.md` 更新

---

## 後續 WP 順序

```
WP-C1-01（DB 環境）
  ↓
WP-C1-02（Attendance Auth JWT 轉換）
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
  ...
```

---

**最後更新：** 2026-03-11  
**更新原因：** 系統驗證基線建立後，切換為基線修正優先模式

---

## System Reality Verification v2 複核結果（2026-03-11）

**經 System Reality Verification v2 複核後，下一 WP 維持不變：WP-C1-01**

複核新發現（CODE_CONFIRMED）：
- backup auth 確認為 Header（非 JWT）→ Header auth 模組從 4 個修正為 5 個
- Header auth 端點總數從 18 個修正為 **24 個**（含 admin_location 5 個端點）
- Feature Gate 確認完全未套用至任何生產 endpoint
- Location Policy 確認只在 break-out 有效（非全部打卡流程）
- admin_location 3 個寫入端點確認為純 TODO（無 RBAC 代碼）
- test_regression.py 確認只有 1 個 test function（Test 8 骨架），且使用 Header auth

以上發現均強化「必須先完成 WP-C1-01 建立環境基線」的判斷，優先順序不變。

**權威依據：** `docs/SYSTEM_REALITY_REPORT_v2.md`（2026-03-11）
