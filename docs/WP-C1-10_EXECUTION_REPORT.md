# WP-C1-10 Execution Report — System-wide JWT Alignment

**執行日期：** 2026-03-18  
**票號：** WP-C1-10  
**性質：** Blocking Gap Resolution（GAP-C1-001 + GAP-C1-003）  
**狀態：** COMPLETE  

---

## 1. Files Changed

| 檔案 | 修改目的 |
|------|----------|
| backend/app/modules/attendance/api.py | 舊 router mock-create/approve 遷移至 JWT Actor；router_v1 全部 11 endpoints 完整遷移 |
| backend/app/modules/leave/api.py | 全部 5 endpoints 從 get_current_company_id/user_id 遷移至 get_actor_with_company |
| backend/app/modules/leave/tests/test_feature_gate.py | override_all_auth_dependencies to override_actor_dependency |
| backend/app/modules/leave/tests/test_tenant_isolation.py | override_all_auth_dependencies to override_actor_dependency; 加入 CompanyEntitlement fixture |
| backend/app/modules/attendance/docs.md | 更新至 v2.2；反映 WP-C1-10 全面 JWT Actor 遷移完成 |

---

## 2. JWT Alignment Result

### attendance 舊 router（GAP-C1-001）

**狀態：** COMPLETE

- /api/attendance/mock-create：get_current_company_id to get_actor_with_company
- /api/attendance/{id}/approve：get_current_company_id + get_current_user_id to get_actor_with_company
- router_v1 全部 11 endpoints 同步完成遷移
- 舊式 import 已移除，無殘留

### leave module（GAP-C1-003）

**狀態：** COMPLETE

- 全部 5 endpoints（create, my-requests, pending, approve, reject）完成遷移
- 各 endpoint body 加入 company_id = actor.active_company_id + user_id = str(actor.user_id) 提取
- 舊式 import 已移除，無殘留

### Canonical Pattern



**殘留 legacy auth 入口：無。**

---

## 3. Test Result

### attendance test_api.py: 5/5 PASS

| 測試 | 結果 |
|------|------|
| test_mock_create_attendance | PASS |
| test_approve_attendance_success | PASS |
| test_approve_attendance_without_approved_by | PASS |
| test_approve_attendance_missing_employee_id | PASS |
| test_approve_emits_event | PASS |

### leave test_feature_gate.py: 5/5 PASS

| 測試 | 結果 |
|------|------|
| test_create_request_feature_disabled | PASS |
| test_my_requests_feature_disabled | PASS |
| test_pending_feature_disabled | PASS |
| test_approve_feature_disabled | PASS |
| test_gate_rejection_schema_consistent | PASS |

### leave test_tenant_isolation.py: 8/9 PASS

| 測試 | 結果 | 說明 |
|------|------|------|
| TestLeaveQueryIsolation::test_my_requests_only_returns_own_company_data | FAIL | Pre-existing：KeyError: company_id（response schema 問題），與 JWT 遷移無關 |
| TestLeaveQueryIsolation::test_pending_list_only_returns_own_company_data | PASS | |
| TestLeaveIdAccessIsolation::test_company_b_cannot_approve_company_a_request | PASS | |
| TestLeaveIdAccessIsolation::test_company_b_cannot_reject_company_a_request | PASS | |
| TestLeaveSubmitIsolation::test_cannot_use_other_company_leave_type | PASS | |
| TestLeaveSubmitIsolation::test_submit_with_own_company_leave_type_succeeds | PASS | |
| TestLeaveRepoIsolation::test_get_leave_request_by_id_enforces_company_id | PASS | |
| TestLeaveRepoIsolation::test_get_user_leave_requests_enforces_company_id | PASS | |
| TestLeaveRepoIsolation::test_get_leave_type_by_id_enforces_company_id | PASS | |

**Pre-existing FAIL 確認：** 該測試在 git stash（原版）時已是 FAIL，與本票無關。

**總結：** 18/19 PASS（1 pre-existing FAIL）

---

## 4. Docs Sync Result

| 項目 | 結果 |
|------|------|
| attendance/docs.md updated | YES（v2.1 to v2.2，Section 3.1/3.2 更新）|
| leave docs updated | N/A — file not found（leave module 無 docs.md）|

---

## 5. Scope Control Confirmation

| 項目 | 結果 |
|------|------|
| production code changed | YES（attendance/api.py + leave/api.py JWT auth 遷移）|
| API behavior changed | NO（endpoint contract 不變，僅 auth dependency 替換）|
| test files changed | YES（leave test_feature_gate.py + test_tenant_isolation.py，直接受 JWT 遷移影響）|
| repo cleanup performed | NO |
| OUT Checkpoint implemented | NO |

---

## 6. Final Recommendation

- **WP-C1-10：COMPLETE**
  - GAP-C1-001（attendance 舊 router JWT）：RESOLVED
  - GAP-C1-003（leave JWT 遷移）：RESOLVED

- **可進入 WP-C1-11**（OUT Checkpoint API Implementation，解決 GAP-C1-002）

- **JWT Residual Gap：無**
  - attendance 全部 13 endpoints：JWT Actor COMPLETE
  - leave 全部 5 endpoints：JWT Actor COMPLETE
  - audit / backup / notifications：已於 WP-C1-03 完成

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-10 JWT Alignment COMPLETE
