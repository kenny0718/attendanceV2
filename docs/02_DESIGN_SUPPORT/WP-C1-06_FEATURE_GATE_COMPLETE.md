# WP-C1-06 Feature Gate 套用 — COMPLETE

**完成日期：** 2026-03-17  
**Git Commit：** 41df744  
**Git Tag：** attendance-v2-wp-c1-06-final  
**負責人：** AI session（Cursor）  
**前置條件：** WP-C1-05 COMPLETE ✅

---

## 1. 完成摘要

本 WP 完成所有 5 個核心模組 API 的 Feature Gate 套用，並建立 22 個自動化測試全部通過。

---

## 2. 修改清單

### 2.1 core/features.py — 新增模組層級 FeatureKeys

```python
ATTENDANCE_CORE = "attendance.core"
LEAVE_CORE = "leave.core"
AUDIT_CORE = "audit.core"
NOTIFICATIONS_CORE = "notifications.core"
BACKUP_CORE = "backup.core"
```

PLAN_DEFAULTS 更新：Basic / Pro 所有核心 gate 預設 `True`（不破壞現有 tenant）。

### 2.2 各模組 API Feature Gate 套用

| 模組 | Gate 函式 | 覆蓋 Endpoint 數 | 套用方式 |
|------|----------|-----------------|----------|
| `attendance/api.py` | `_require_attendance_feature()` | 11 | 從 git 還原 + 新增函式定義 + 12 次呼叫 |
| `leave/api.py` | `_require_leave_feature()` | 5 | 已存在，確認覆蓋完整 |
| `audit/api.py` | `_require_audit_feature()` | 5 | 已存在（WP-C1-03 時建立），確認 |
| `notifications/api.py` | feature gate 內嵌 | 1 | 已存在，確認 |
| `backup/api.py` | `_require_backup_feature()` | 2 | 已存在，確認 |

### 2.3 main.py — 掛載 feature_gate_demo router

```python
from app.modules.attendance.feature_gate_demo import router as attendance_gate_demo_router
app.include_router(attendance_gate_demo_router)
```

### 2.4 新增測試檔案（22 個測試，22/22 PASS）

| 檔案 | 測試數 | 測試內容 |
|------|--------|----------|
| `attendance/tests/test_feature_gate.py` | 6 | enabled pass / disabled 403 / schema 一致性 |
| `leave/tests/test_feature_gate.py` | 5 | create/list/pending/approve/schema |
| `audit/tests/test_feature_gate.py` | 5 | logs/export/retention/schema |
| `notifications/tests/test_feature_gate.py` | 3 | enabled/disabled/schema |
| `backup/tests/test_feature_gate.py` | 3 | export disabled/enabled/restore disabled |

---

## 3. 驗證結果

### 3.1 Feature Gate 測試

```
22/22 tests PASSED
- attendance: 6/6 PASS
- leave: 5/5 PASS
- audit: 5/5 PASS
- notifications: 3/3 PASS
- backup: 3/3 PASS
```

### 3.2 Gate 拒絕 schema（一致）

```json
HTTP 403
{
  "detail": {
    "code": "FEATURE_DISABLED",
    "feature": "<feature_key>",
    "message": "Feature '<key>' is not enabled for company '<id>'"
  }
}
```

### 3.3 已知既有失敗（非本票引入）

- `test_regression.py::test_8_cross_midnight`：punch_time 被 API 忽略（既有問題，與 feature gate 無關）
- `test_migration.py`：缺少 alembic 模組（非 venv 環境）
- `test_phase1.py`：缺少 requests 模組（整合測試）

---

## 4. 完成判定

✅ **WP-C1-06 正式宣告 COMPLETE**

驗收條件：
- [x] 所有 5 個核心模組 API 套用 feature gate
- [x] Feature disabled → HTTP 403 FEATURE_DISABLED
- [x] Gate 拒絕 schema 一致（code / feature / message）
- [x] 22/22 自動化測試通過
- [x] feature_gate_demo router 已掛載至 main.py
- [x] git commit 41df744 已建立
- [x] git tag attendance-v2-wp-c1-06-final 已建立

---

## 5. 下一步

**下一個 WP：WP-C1-07（若未完成）或 Phase 1 宣告完成**

根據 NEXT_WP_TICKET.md 的 WP
