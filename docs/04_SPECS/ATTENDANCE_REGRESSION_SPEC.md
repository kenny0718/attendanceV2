# Attendance Regression Spec

**文件版本：** 2.0  
**建立日期：** 2026-03-04  
**目的：** 定義 WP-11-05 的 8 個核心回歸測試場景  
**狀態：** ✅ READY FOR WP-11-05

---

## 文件目的

本文件為 WP-11-05 (Attendance Regression Tests) 提供完整的測試規格。

**使用時機：**
- WP-11-05 開始時，作為測試實作的唯一依據
- 每個測試場景都必須實作並通過

**不可做事項：**
- ❌ 不要在 WP-11-04B 實作這些測試（只做規格定義）
- ❌ 不要修改 API 或 Policy Engine（那些已在 WP-11-02, WP-11-03 完成）

---

## 核心回歸測試（最少 8 個）

### Test 1: NO_MATCH 未填原因 → 拒絕

**場景描述：**
員工打卡時間與政策不符（NO_MATCH），但未填寫原因，系統應拒絕該打卡記錄。

**前置條件：**
- 公司有預設政策：09:00-18:00
- 員工在 07:00 打卡（早於政策 2 小時）
- 未填寫 `reason` 欄位

**測試步驟：**
1. 建立公司 `company-test`
2. 建立使用者 `user-001`
3. 建立預設政策：work_start_time=09:00, work_end_time=18:00
4. 呼叫 `POST /api/v1/attendance/punch-in` at 07:00，不帶 `reason`

**預期結果：**
- HTTP 400 Bad Request
- Error code: `REASON_REQUIRED`
- Error message: "Punch time does not match policy, reason is required"
- 不建立 `attendance_sessions` 記錄

**驗證點：**
- ✅ API 返回 400
- ✅ Error code 正確
- ✅ DB 中無 session 記錄

---

### Test 2: NO_MATCH 有原因 → PENDING

**場景描述：**
員工打卡時間與政策不符（NO_MATCH），但有填寫原因，系統應建立 PENDING 狀態的記錄。

**前置條件：**
- 公司有預設政策：09:00-18:00
- 員工在 07:00 打卡（早於政策 2 小時）
- 填寫 `reason`: "需提早到公司準備會議"

**測試步驟：**
1. 建立公司 `company-test`
2. 建立使用者 `user-001`
3. 建立預設政策：work_start_time=09:00, work_end_time=18:00
4. 呼叫 `POST /api/v1/attendance/punch-in` at 07:00，帶 `reason`

**預期結果：**
- HTTP 201 Created
- 建立 `attendance_sessions` 記錄
- `status` = `PENDING_APPROVAL`（或類似狀態）
- `notes` = "需提早到公司準備會議"

**驗證點：**
- ✅ API 返回 201
- ✅ Session 記錄存在
- ✅ Status 為 PENDING
- ✅ Notes 正確儲存

---

### Test 3: APPROVED → 推導正確

**場景描述：**
PENDING 記錄被核准後，Policy Engine 應正確推導工時、遲到、早退、加班。

**前置條件：**
- 公司有預設政策：09:00-18:00, grace_period=15 分鐘
- 員工在 09:10 打卡上班（遲到 10 分鐘，在寬限期內）
- 員工在 18:30 打卡下班（加班 30 分鐘）
- 記錄狀態為 PENDING

**測試步驟：**
1. 建立 PENDING session: punch_in=09:10, punch_out=18:30
2. 呼叫 `POST /api/v1/attendance/sessions/{id}/approve`
3. 查詢 session，檢查 policy evaluation 結果

**預期結果：**
- `status` = `APPROVED`
- `is_late` = `false`（在寬限期內）
- `late_minutes` = `0`
- `is_early_leave` = `false`
- `is_overtime` = `true`
- `overtime_minutes` = `30`
- `work_minutes` = `540`（9 小時）

**驗證點：**
- ✅ Status 變更為 APPROVED
- ✅ Policy evaluation 結果正確
- ✅ 工時計算正確（540 分鐘）
- ✅ 遲到判定正確（false，因為在寬限期內）
- ✅ 加班判定正確（true，30 分鐘）

---

### Test 4: PENDING 不參與推導與日結

**場景描述：**
PENDING 狀態的記錄不應參與工時推導和日結算。

**前置條件：**
- 公司有 2 筆記錄：
  - Record A: APPROVED, work_minutes=480
  - Record B: PENDING, work_minutes=null（未推導）
- 執行日結算（例如 21:00）

**測試步驟：**
1. 建立 2 筆 session：一筆 APPROVED，一筆 PENDING
2. 呼叫日結算 API（或觸發日結算邏輯）
3. 查詢日結算結果

**預期結果：**
- 日結算只包含 APPROVED 記錄
- PENDING 記錄不參與統計
- 總工時 = 480 分鐘（只計算 Record A）

**驗證點：**
- ✅ PENDING 記錄不參與日結算
- ✅ 總工時只計算 APPROVED 記錄
- ✅ PENDING 記錄的 work_minutes 仍為 null

---

### Test 5: 21:00 日結缺卡正確

**場景描述：**
每日 21:00 執行日結算時，若員工有 punch-in 但無 punch-out（缺卡），應正確處理。

**前置條件：**
- 公司有預設政策：09:00-18:00
- 員工在 09:00 打卡上班
- 員工忘記打卡下班
- 當前時間為 21:00

**測試步驟：**
1. 建立 session: punch_in=09:00, punch_out=null, status=open
2. 執行日結算邏輯（模擬 21:00 觸發）
3. 查詢 session 狀態

**預期結果：**
- `status` = `MISSING_PUNCH_OUT`（或類似狀態）
- `punch_out_time` = null（不自動補卡）
- `work_minutes` = null（無法計算）
- 或者：自動關閉 session，但標記為異常

**驗證點：**
- ✅ Session 狀態變更為異常狀態
- ✅ 不自動補 punch_out（或有明確規則）
- ✅ 工時無法計算（或使用預設值）

**備註：** 具體行為依 SA v1.9 規範，如規範未定義，需在測試中明確決策並記錄。

---

### Test 6: approve pending → 該日重算

**場景描述：**
當 PENDING 記錄被核准後，該日的統計數據應重新計算。

**前置條件：**
- 2026-03-04 有 2 筆記錄：
  - Record A: APPROVED, work_minutes=480
  - Record B: PENDING, work_minutes=null
- 當日統計：total_work_minutes=480

**測試步驟：**
1. 核准 Record B
2. Policy Engine 推導 Record B: work_minutes=500
3. 查詢當日統計

**預期結果：**
- Record B 的 `status` = `APPROVED`
- Record B 的 `work_minutes` = `500`
- 當日統計重新計算：total_work_minutes=980（480+500）

**驗證點：**
- ✅ Record B 狀態變更為 APPROVED
- ✅ Record B 工時已推導
- ✅ 當日統計已更新

**備註：** 如果沒有即時統計 API，可以用查詢驗證（例如 `GET /api/v1/attendance/reports/daily-summary?date=2026-03-04`）

---

### Test 7: customer_service 未指派公司 → 403

**場景描述：**
Customer Service 角色只能存取已指派的公司，未指派的公司應返回 403。

**前置條件：**
- Customer Service 使用者 `cs-001`
- 已指派公司：`company-a`
- 未指派公司：`company-b`

**測試步驟：**
1. 建立 Customer Service 使用者 `cs-001`
2. 建立 `support_company_assignments`: user_id=cs-001, company_id=company-a
3. 使用 `cs-001` 的 JWT 呼叫 `GET /api/v1/attendance/sessions?company_id=company-b`

**預期結果：**
- HTTP 403 Forbidden
- Error code: `SCOPE_DENIED`
- Error message: "Customer service user is not assigned to this company"

**驗證點：**
- ✅ API 返回 403
- ✅ Error code 正確
- ✅ Scope 驗證生效（Scope → Tenant → Feature 順序）

---

### Test 8: cross-midnight（跨日工時歸屬）

**場景描述：**
員工在 3/31 23:00 打卡上班，在 4/1 02:00 打卡下班（跨日班次），工時應正確歸屬。

**前置條件：**
- 公司有夜班政策：23:00-07:00
- 員工在 2026-03-31 23:00 打卡上班
- 員工在 2026-04-01 02:00 打卡下班

**測試步驟：**
1. 建立夜班政策：work_start_time=23:00, work_end_time=07:00
2. 呼叫 `POST /api/v1/attendance/punch-in` at 2026-03-31 23:00
3. 呼叫 `POST /api/v1/attendance/punch-out` at 2026-04-01 02:00
4. 查詢 session 和工時歸屬

**預期結果：**
- Session 建立成功
- `punch_in_time` = 2026-03-31 23:00 UTC
- `punch_out_time` = 2026-04-01 02:00 UTC
- `work_minutes` = 180（3 小時）
- **工時歸屬日期：** 2026-03-31（以 punch_in 日期為準）

**驗證點：**
- ✅ Session 建立成功
- ✅ 工時計算正確（180 分鐘）
- ✅ 工時歸屬日期正確（3/31，不是 4/1）
- ✅ Policy evaluation 正確（無遲到、無早退）

**工時歸屬規則（明確定義）：**
- **規則 1（推薦）：** 以 `punch_in_time` 的日期為準
  - 範例：3/31 23:00 上班 → 4/1 02:00 下班 → 歸屬 3/31
- **規則 2（備選）：** 以 `punch_out_time` 的日期為準
  - 範例：3/31 23:00 上班 → 4/1 02:00 下班 → 歸屬 4/1
- **規則 3（複雜）：** 依政策的 `work_start_time` 判斷
  - 範例：若政策為 23:00-07:00，則 23:00-23:59 歸 3/31，00:00-07:00 歸 4/1

**本規格採用規則 1：** 以 `punch_in_time` 的日期為準（最簡單、最直觀）

---

## 額外測試場景（可選，但建議實作）

### Test 9: double punch prevention（重複打卡）

**場景描述：**
員工已有 open session，再次打卡上班應被拒絕。

**前置條件：**
- 員工在 09:00 打卡上班（session 狀態為 open）
- 員工在 09:30 再次嘗試打卡上班

**測試步驟：**
1. 呼叫 `POST /api/v1/attendance/punch-in` at 09:00（成功）
2. 呼叫 `POST /api/v1/attendance/punch-in` at 09:30（應失敗）

**預期結果：**
- HTTP 400 Bad Request
- Error code: `DUPLICATE_PUNCH_IN`
- Error message: "User already has an open session"

**驗證點：**
- ✅ 第二次打卡被拒絕
- ✅ 只有一個 open session

---

### Test 10: tenant isolation negative test（跨公司查不到資料）

**場景描述：**
Company A 的使用者無法查詢 Company B 的出勤記錄。

**前置條件：**
- Company A 有 session: id=session-a
- Company B 有 session: id=session-b
- 使用者屬於 Company A

**測試步驟：**
1. 使用 Company A 的 JWT 呼叫 `GET /api/v1/attendance/sessions/{session-b}`

**預期結果：**
- HTTP 404 Not Found（不洩漏資訊）
- 或 HTTP 403 Forbidden

**驗證點：**
- ✅ 無法存取其他公司的資料
- ✅ 不洩漏資料是否存在

---

### Test 11: policy fallback（無政策時 fallback）

**場景描述：**
公司沒有設定政策時，使用預設政策。

**前置條件：**
- 公司沒有任何 `attendance_policies` 記錄
- 員工在 09:00 打卡上班

**測試步驟：**
1. 確認公司無政策記錄
2. 呼叫 `POST /api/v1/attendance/punch-in` at 09:00

**預期結果：**
- Session 建立成功
- 使用預設政策（例如 09:00-18:00）
- Policy evaluation 使用預設值

**驗證點：**
- ✅ Session 建立成功
- ✅ 使用預設政策
- ✅ Policy evaluation 正確

---

### Test 12: edge case（缺 punch-out）

**場景描述：**
員工打卡上班後，忘記打卡下班，session 保持 open 狀態。

**前置條件：**
- 員工在 09:00 打卡上班
- 員工忘記打卡下班
- 當前時間為 20:00（未到日結算時間）

**測試步驟：**
1. 呼叫 `POST /api/v1/attendance/punch-in` at 09:00
2. 查詢 session 狀態

**預期結果：**
- Session 狀態為 `open`
- `punch_out_time` = null
- `work_minutes` = null（無法計算）

**驗證點：**
- ✅ Session 保持 open
- ✅ 工時無法計算

---

## 測試實作指引（WP-11-05）

### 測試檔案結構

**建議檔案：** `backend/app/modules/attendance/tests/test_regression.py`

**結構：**
```python
"""Attendance Regression Tests

WP-11-05: 8 個核心回歸測試 + 4 個額外測試

依據：docs/ATTENDANCE_REGRESSION_SPEC.md
"""

import pytest
from datetime import datetime, time
from uuid import uuid4

# Test 1: NO_MATCH 未填原因 → 拒絕
def test_no_match_without_reason_rejected():
    """Test 1: NO_MATCH 未填原因 → 拒絕"""
    pass

# Test 2: NO_MATCH 有原因 → PENDING
def test_no_match_with_reason_pending():
    """Test 2: NO_MATCH 有原因 → PENDING"""
    pass

# Test 3: APPROVED → 推導正確
def test_approved_policy_evaluation_correct():
    """Test 3: APPROVED → 推導正確"""
    pass

# Test 4: PENDING 不參與推導與日結
def test_pending_not_in_daily_summary():
    """Test 4: PENDING 不參與推導與日結"""
    pass

# Test 5: 21:00 日結缺卡正確
def test_daily_close_missing_punch_out():
    """Test 5: 21:00 日結缺卡正確"""
    pass

# Test 6: approve pending → 該日重算
def test_approve_pending_recalculate_daily():
    """Test 6: approve pending → 該日重算"""
    pass

# Test 7: customer_service 未指派公司 → 403
def test_customer_service_unassigned_company_403():
    """Test 7: customer_service 未指派公司 → 403"""
    pass

# Test 8: cross-midnight（跨日工時歸屬）
def test_cross_midnight_work_hours_attribution():
    """Test 8: cross-midnight（跨日工時歸屬）"""
    pass

# Test 9 (Optional): double punch prevention
def test_double_punch_prevention():
    """Test 9: double punch prevention（重複打卡）"""
    pass

# Test 10 (Optional): tenant isolation negative test
def test_tenant_isolation_cross_company():
    """Test 10: tenant isolation negative test（跨公司查不到資料）"""
    pass

# Test 11 (Optional): policy fallback
def test_policy_fallback_to_default():
    """Test 11: policy fallback（無政策時 fallback）"""
    pass

# Test 12 (Optional): edge case（缺 punch-out）
def test_missing_punch_out_edge_case():
    """Test 12: edge case（缺 punch-out）"""
    pass
```

---

### 測試資料準備

**Fixtures:**
```python
@pytest.fixture
def test_company(db):
    """建立測試公司"""
    tenant = Tenant(id="company-test", name="Test Company", is_active=True)
    db.add(tenant)
    db.commit()
    return tenant

@pytest.fixture
def test_user(db):
    """建立測試使用者"""
    user = User(
        id=uuid4(),
        display_name="Test User",
        password_hash="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def test_policy(db, test_company):
    """建立測試政策"""
    policy = AttendancePolicy(
        id=uuid4(),
        company_id=test_company.id,
        name="Default Policy",
        work_start_time=time(9, 0),
        work_end_time=time(18, 0),
        grace_period_minutes=15,
        is_active=True,
        is_default=True
    )
    db.add(policy)
    db.commit()
    return policy
```

---

### 測試執行命令

```bash
# 執行所有回歸測試
cd backend
pytest app/modules/attendance/tests/test_regression.py -v

# 執行特定測試
pytest app/modules/attendance/tests/test_regression.py::test_cross_midnight_work_hours_attribution -v

# 執行並顯示詳細輸出
pytest app/modules/attendance/tests/test_regression.py -v -s
```

---

### 測試覆蓋率目標

**最少要求：** 8/8 核心測試通過  
**建議目標：** 12/12 測試通過（含額外測試）

---

## 驗收標準（WP-11-05 Exit Criteria）

### 必須滿足（P0）

- ✅ 8/8 核心回歸測試實作完成
- ✅ 8/8 核心回歸測試通過
- ✅ 測試報告已產出（`docs/WP-11-05_REGRESSION_TEST_REPORT.md`）
- ✅ Cross-midnight 場景驗證通過（Test 8）

### 建議滿足（P1）

- ✅ 12/12 測試通過（含額外測試）
- ✅ 測試覆蓋率 > 80%
- ✅ 所有測試有清晰的註解和文件

---

## 附錄

### A. Cross-Midnight 工時歸屬規則（詳細說明）

**問題：** 員工在 3/31 23:00 上班，4/1 02:00 下班，工時應歸屬哪一天？

**規則 1（本規格採用）：以 punch_in_time 的日期為準**
- 優點：簡單、直觀、易於理解
- 缺點：可能與薪資計算習慣不符（某些公司以下班日期為準）
- 範例：
  - 3/31 23:00 上班 → 4/1 02:00 下班 → 歸屬 3/31
  - 3/31 23:00 上班 → 4/1 07:00 下班 → 歸屬 3/31

**規則 2（備選）：以 punch_out_time 的日期為準**
- 優點：符合某些公司的薪資計算習慣
- 缺點：可能造成混淆（上班日期與歸屬日期不同）
- 範例：
  - 3/31 23:00 上班 → 4/1 02:00 下班 → 歸屬 4/1
  - 3/31 23:00 上班 → 4/1 07:00 下班 → 歸屬 4/1

**規則 3（複雜）：依政策的 work_start_time 判斷**
- 優點：最精確，符合業務邏輯
- 缺點：實作複雜，需要額外邏輯
- 範例：
  - 若政策為 23:00-07:00（夜班）
  - 3/31 23:00-23:59 → 歸屬 3/31
  - 4/1 00:00-07:00 → 歸屬 4/1
  - 需要拆分工時

**本規格採用規則 1**，理由：
1. 最簡單、最直觀
2. 符合大多數系統的實作習慣
3. 易於測試和驗證
4. 如未來需要變更，可在 Policy Engine 中調整

---

### B. PENDING 狀態處理規則

**PENDING 狀態的記錄：**
- ❌ 不參與工時推導（work_minutes = null）
- ❌ 不參與日結算
- ❌ 不參與統計報表
- ✅ 可被核准（approve）
- ✅ 核准後重新推導工時
- ✅ 核准後參與統計

**核准流程：**
1. 管理員呼叫 `POST /api/v1/attendance/sessions/{id}/approve`
2. 系統變更 `status` = `APPROVED`
3. Policy Engine 推導工時、遲到、早退、加班
4. 更新 `work_minutes`, `is_late`, `late_minutes`, `is_overtime`, `overtime_minutes`
5. 觸發該日統計重新計算（如有即時統計）

---

### C. 日結算邏輯（21:00）

**日結算觸發時機：** 每日 21:00（或可設定）

**日結算處理邏輯：**
1. 查詢所有 `status = 'open'` 的 sessions
2. 檢查 `punch_out_time` 是否為 null
3. 若為 null：
   - 選項 A：變更 `status` = `MISSING_PUNCH_OUT`，不計算工時
   - 選項 B：自動補 `punch_out_time` = 政策的 `work_end_time`，計算工時
   - 選項 C：自動補 `punch_out_time` = 當前時間（21:00），計算工時
4. 統計當日所有 `APPROVED` 記錄的工時

**本規格建議選項 A**（最保守）：
- 不自動補卡（避免錯誤）
- 標記為異常狀態
- 需要管理員手動處理

---

**文件版本：** 2.0  
**建立日期：** 2026-03-04  
**維護者：** 架構團隊  
**狀態：** ✅ READY FOR WP-11-05

---

**END OF ATTENDANCE_REGRESSION_SPEC.md**
