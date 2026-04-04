# WP-TEST-FIX: test_reporting_sessions user_a.id.id Patch Report

**日期：** 2026-03-28
**執行人：** Cursor AI Agent
**任務：** 修正 test_reporting_sessions.py 的 user_a.id.id typo
**Commit：** ad588a6
**狀態：** PARTIAL（typo 已修，新的失敗原因已識別）

---

## 1. Summary

- `user_a.id.id` → `user_a.id` 已全部修正（15 處，非原估的 3 處）
- AttributeError: 'UUID' object has no attribute 'id' 已消除
- 新的失敗原因：403 Forbidden（actor dependency override 問題，超出本輪 scope）
- 3 個測試從 AttributeError 進步到 assert 403 == 422/200

---

## 2. Files Changed

| 檔案 | 變更 | 說明 |
|------|------|------|
| backend/app/modules/attendance/tests/test_reporting_sessions.py | 15 處 replace | user_a.id.id → user_a.id |

---

## 3. Exact Fixes

**搜尋結果：** 15 處（非原估的 3 處）

行號：243, 252, 266, 281, 289, 302, 314, 319, 324, 353, 370, 382, 394, 406, 415

**修正前：** `make_actor(COMPANY_A, user_a.id.id)`
**修正後：** `make_actor(COMPANY_A, user_a.id)`

**修正後殘留：** 0 處

---

## 4. Validation

### 目標測試執行結果

| 測試 | 修正前 | 修正後 |
|------|--------|--------|
| SES-11 naive datetime 422 | AttributeError: user_a.id.id | assert 403 == 422 |
| SES-06 tenant isolation | AttributeError: user_a.id.id | assert 403 == 200 |
| SES-12 company_admin cross-user | AttributeError: user_a.id.id | assert 403 == 200 |

**AttributeError 已消除：YES**

### 新的失敗原因

所有 3 個測試收到 **403 Forbidden**，分析如下：

```
HTTP Request: GET /api/v1/attendance/sessions → 403 Forbidden
```

**根本原因：** `override_actor_dependency` 在這些測試中沒有正確生效。
測試使用混合方式（部分用 `hdr()` helper，部分用 `override_actor_dependency`），
導致 JWT actor 驗證失敗而回傳 403。

這是測試基礎設施問題（actor override 機制），超出本輪修正 scope。

---

## 5. Risks / Follow-up

| 項目 | 狀態 | 說明 |
|------|------|------|
| user_a.id.id typo | RESOLVED | 15 處全部修正 |
| 403 Forbidden（actor override）| 待處理 | override_actor_dependency 未正確覆蓋 get_actor_with_company |
| 全量 SES-01~SES-12 動態測試 | BLOCKED | 需先解決 actor override 問題 |

### 下一輪建議

確認 `override_actor_dependency` 的實作是否正確覆蓋 `get_actor_with_company` dependency，
或確認 `hdr()` helper 的使用方式是否與現有 JWT 驗證流程相容。

---

*本輪成功標準達成：15 處 user_a.id.id typo 已修正，AttributeError 已消除。*
*新的失敗原因（403）已識別，留待下一輪處理。*
