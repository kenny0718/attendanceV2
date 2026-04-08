# P2 F3 Fix Spec — Align Reporting to Canonical Taipei Boundary Owner

> **Document Type**: Fix Specification
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Ticket**: F3 — Align reporting entrypoints to the canonical Taipei boundary normalization owner
> **Purpose**: Define how reporting should adopt the F1 Taipei business-date owner so that reporting and breaks share one boundary contract, without changing repo ownership or aggregation semantics
> **Execution Mode**: Specification only
> **Status**: Draft for human review
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
> - `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`
> - `docs/attendance/remediation/02_fix/P2_F2_EXECUTION_REPORT.md`
> - `backend/app/modules/attendance/api/reporting.py`
> - `backend/app/modules/attendance/api/reporting_helpers.py`
> - `backend/app/modules/attendance/reporting_repo.py`
> - `backend/app/modules/attendance/tests/test_reporting_sessions.py`
> - `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
> - `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件的唯一目的，是為 Phase 2 / F3 定義一份正式修正規格，使 reporting entrypoints：

- 不再僅依賴 legacy / generic UTC normalization
- 改為依附 F1 已建立的 canonical Taipei boundary normalization owner
- 與 F2 已完成的 `break-punches` 使用同一 boundary contract
- 同時維持 repo ownership、aggregation responsibility、Phase 1 canonical duration 不變

本文件只定義：
- F3 target
- 接線點
- responsibility split
- 風險
- acceptance criteria
- prohibited actions

本文件**不得**：
- 修改任何 code
- 產出 diff
- 直接實作 `reporting.py`
- 修改 `reporting_repo.py` / `repo.py`
- 順便處理 aggregation refactor
- 順便處理 Phase 1 canonical duration 問題

---

# 1. Background

依據已完成的 Phase 2 結果：

1. F1 已建立 canonical Taipei business-date owner：
   - `get_taipei_today(...)`
   - `build_taipei_business_date_boundary(...)`
2. F2 已讓 `break-punches` 接入該 owner
3. reporting 目前仍維持既有 flow：
   - API entry 接受 `start_date` / `end_date`
   - `_validate_datetime_range(...)` 僅驗證 timezone-aware
   - `_normalize_to_utc(...)` 僅做技術性 UTC conversion
4. reporting repo 目前只吃最終 UTC 邊界，未擁有 business-date owner
5. 既有 reporting tests 已大量建立「Taipei boundary 先由 caller 轉成 UTC 再送入 API」的測試模式

因此 F3 的核心任務不是改 repo，也不是改 aggregation，
而是：

- 讓 reporting 的 boundary ownership 對齊 F1 / F2
- 讓 reporting 與 breaks 使用同一 Taipei business-date contract
- 同時保留 repo 與 service 的既有責任分工

---

# 2. F3 Target Definition

## 2.1 Primary Target

F3 完成後，reporting entry 必須滿足：

- reporting 的 business-date boundary ownership 與 `break-punches` 完全一致
- reporting 不再只依賴 route-level / legacy normalization 作為語意 owner
- reporting 所使用的 date range 必須可被明確解釋為：
  - **Taipei-owned business boundary**
  - 再轉換成 canonical UTC query range

## 2.2 Scope of Reporting Endpoints

F3 目標適用於下列 entrypoints：
- `GET /api/v1/attendance/sessions`
- `GET /api/v1/attendance/reports/user-summary`
- `GET /api/v1/attendance/reports/company-summary`

## 2.3 Semantic Target

F3 完成後，reporting 內與「日 / 月 / 統計期間歸屬」相關的 boundary 語意必須正式代表：

- **a business date or date range interpreted in `Asia/Taipei`**

不是：
- generic timezone-aware 就算合法 owner
- UTC date 自動等同 business date
- caller 想傳什麼 timezone-aware 範圍都可被視為 business-date owner

## 2.4 Contract Unification Target

F3 完成後，`breaks` 與 `reporting` 必須共享：
- same business-date owner
- same Taipei midnight meaning
- same UTC range derivation semantics
- same half-open interval semantics

也就是：
- `>= start_utc`
- `< end_utc`

---

# 3. Current-State Assessment

## 3.1 Current Reporting Flow

目前 `reporting.py` 的 entry flow 為：

1. API 接受 `start_date` / `end_date`
2. `_validate_datetime_range(...)` 驗證 timezone-aware
3. `_normalize_to_utc(...)` 將輸入轉為 UTC
4. 將 `start_utc` / `end_utc` 傳給 `reporting_repo.py`
5. repo 僅以 `punch_in_time` 做 `>= start_utc`, `< end_utc` 過濾
6. aggregation 仍由既有 service / Python layer 處理

## 3.2 Why Current Flow Is Insufficient for Phase 2

目前 flow 的問題不在 repo query shape，
而在於 boundary ownership 仍然模糊：

- `_normalize_to_utc(...)` 是技術性轉換
- 不是 business-date owner
- `_validate_datetime_range(...)` 只驗證 aware / naive
- 沒有保證輸入一定代表 Taipei business boundary

因此目前 reporting 的 contract 比 F2 breaks 鬆：

- breaks：已明確依附 Taipei owner
- reporting：仍可能接受只是 timezone-aware、但語意上不是 Taipei business boundary 的輸入

這是 F3 要對齊的核心問題。

---

# 4. Wiring Strategy

## 4.1 Required Wiring Principle

F3 的接線原則必須是：

- reporting 的 boundary owner 必須在 API / helper normalization boundary layer 被明確決定
- repo 仍只接收最終 `start_utc` / `end_utc`
- aggregation 層不應承擔 boundary owner 責任

## 4.2 Required Wiring Point

F3 的主要接線點應在：
- `backend/app/modules/attendance/api/reporting.py`

具體而言，應落在三個 reporting entrypoints 內、現有 `_validate_datetime_range(...)` / `_normalize_to_utc(...)` 的前後責任邊界上。

## 4.3 Recommended Ownership Split

### API Layer should do
- 接收 request 的 date / datetime range 輸入
- 判斷該輸入是否代表 business-date query semantics
- 將 business-date semantics 委派給 F1 owner
- 取得 canonical `start_utc` / `end_utc`
- 將 canonical UTC boundary 傳給 repo

### Helper Layer should do
- 擁有 Taipei business-date owner
- 提供 Taipei boundary normalization contract
- 將 business-date semantics 轉成 canonical UTC range
- 保持 pure / deterministic / testable

### Repo Layer should do
- 只接受 `start_utc` / `end_utc`
- 維持 `punch_in_time >= start_utc`, `punch_in_time < end_utc`
- 不擁有 business-date owner

### Aggregation Layer should do
- 僅對已過濾出的 sessions 做統計
- 不參與 boundary owner 決策
- 不自行重新歸類日期範圍

## 4.4 Reporting Helpers Adjustment Policy

### Must remain true
- `reporting_helpers.py` 仍應作為唯一 Taipei boundary owner 所在地

### Preferred
- 若 F3 需要 reporting helper 層補充極小型 wrapper / contract exposure，應只做：
  - owner call composition
  - business-date boundary normalization
  - 不混入 DB / aggregation / response shaping

### Allowed
- 保持 `get_taipei_today(...)` / `build_taipei_business_date_boundary(...)` 不變，僅在 reporting.py 改用它們

### Not recommended
- 在 `reporting.py` 自己重寫 Taipei boundary 規則
- 在 repo 層補 boundary owner
- 在 service / aggregation 層偷偷做 boundary 歸屬修補

結論：
- `reporting_helpers.py` **可保持不變**
- 若需調整，也只能是極小型 owner exposure / composition，不能演變成第二套規則

---

# 5. Risk Assessment

## 5.1 User-Visible Risk

F3 可能直接影響：
- sessions list 的查詢結果歸屬
- user-summary / company-summary 的統計期間
- Taipei midnight / cross-day / cross-month 邊界附近的 session 是否被納入

因此 F3 屬於明確的使用者可見修正。

## 5.2 Expected Behavior Changes

### A. Sessions list may shift at Taipei midnight

若目前 reporting 接受的是 technically-aware 但語意不嚴格的 boundary，
則在 F3 後：
- 台北 `00:00 ~ 07:59` 附近的 session 歸屬可能改變
- `punch_in_time` 落在 UTC 前一日、但 Taipei 已隔日者，將被歸回 Taipei 正確日期

### B. User summary may change near day / month edges

`user-summary` 的：
- `total_sessions`
- `total_work_minutes`
- `first_session_time`
- `last_session_time`

在邊界附近可能產生修正性變化，原因是期間歸屬被拉回 Taipei business boundary。

### C. Company summary may change near boundary edges

`company-summary` 的：
- `total_sessions`
- `closed_sessions`
- `open_sessions`
- `total_work_minutes`
- `average_minutes_per_session`
- `average_minutes_per_user`
- `total_users_with_sessions`

在邊界附近也可能出現修正性變化。

### D. Cross-day / Cross-month behavior will become stricter and more consistent

月末 / 月初、日末 / 日初附近的 reporting 結果，
將與 F2 的 breaks boundary contract 對齊。

## 5.3 Why This Risk Is Acceptable

這些變化屬於：
- **預期中的修正性變化**
- 不是新功能規則
- 不是 aggregation 規則改寫
- 而是將 reporting 拉回 Phase 2 已明確定義的 Taipei business-date contract

---

# 6. Scope and Boundaries

## 6.1 Allowed Future Change Scope for F3

F3 未來實作可觸及：
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`（僅限最小必要 helper exposure / composition）
- 與 reporting boundary 直接相關的 tests

## 6.2 Forbidden Files for F3

F3 明確禁止修改：
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/reporting_service.py`（除非另立票，不得順便改 aggregation）
- `backend/app/main.py`
- 任何 schema / migration 檔

## 6.3 Scope Lock

F3 只處理：
- reporting boundary ownership 對齊
- reporting 與 breaks contract convergence

F3 不處理：
- repo convergence
- aggregation refactor
- canonical duration 欄位語意重整
- Phase 1 canonical duration 修復
- 其他 unrelated reporting cleanup

---

# 7. Acceptance Criteria

## 7.1 Boundary Source Acceptance

F3 完成後，必須能證明：

1. reporting entry 不再只依賴 `_normalize_to_utc(...)` 作為 business-date owner
2. reporting boundary 來自 F1 canonical Taipei owner
3. reporting 與 breaks 使用同一 owner contract

## 7.2 Semantic Acceptance

F3 完成後，必須成立：

1. Taipei midnight ownership 正確
2. cross-day ownership 依 Taipei boundary 判定
3. cross-month ownership 依 Taipei boundary 判定
4. reporting 與 breaks 在同一 business date 上結果不應出現 owner-level 分岔

## 7.3 Query Acceptance

F3 完成後，reporting repo 仍必須只吃：
- `start_utc`
- `end_utc`

且 query shape 維持：
- `>= start_utc`
- `< end_utc`

## 7.4 Aggregation Acceptance

F3 完成後，必須能證明：
- sessions list 未破壞 pagination / scope / tenant isolation
- user-summary aggregation 未被破壞
- company-summary aggregation 未被破壞
- 任何 summary 變化若發生，必須可被解釋為 boundary 修正，而不是 aggregation regression

## 7.5 Consistency Acceptance

F3 完成後，必須能證明：
- breaks / reporting 對同一 Taipei business boundary 的理解完全一致
- 不再存在：
  - breaks 用 Taipei owner
  - reporting 用 legacy normalization
  的 contract split

---

# 8. Test Strategy Requirements

F3 未來實作若進行，測試至少應覆蓋：

## 8.1 Sessions Endpoint
- Taipei midnight session ownership
- UTC 前一日但 Taipei 已隔日
- cross-month session ownership
- query shape 仍為 `>= start_utc`, `< end_utc`

## 8.2 User Summary
- boundary 修正後 `total_sessions` / `total_work_minutes` 合理
- open session / NULL duration 不受影響
- 與既有 aggregation 規則一致

## 8.3 Company Summary
- boundary 修正後 company totals 合理
- `total_users_with_sessions` 去重規則不被破壞
- 平均值欄位僅受 boundary inclusion 影響，不受 aggregation algorithm 變動影響

## 8.4 Cross-Endpoint Consistency
- 同一 Taipei day boundary 下：
  - breaks
  - sessions
  - user-summary
  - company-summary
  對資料歸屬必須可相互解釋

---

# 9. Prohibited Actions

F3 實作時明確禁止：

1. 不可修改 `reporting_repo.py`
2. 不可修改 `repo.py`
3. 不可修改 schema / migration
4. 不可同時做 aggregation 重構
5. 不可影響 Phase 1 canonical duration contract
6. 不可在 route 內重寫第二套 Taipei boundary 規則
7. 不可把 boundary owner 下沉到 repo
8. 不可用 ad hoc datetime 轉換取代 F1 owner
9. 不可順便整理 unrelated reporting code

---

# 10. Recommended Execution Direction

若進入 F3 實作，建議採用最小接線策略：

1. 保留 reporting repo 完全不動
2. 保留 aggregation service 完全不動
3. 在 reporting entry / helper boundary layer 完成 owner 對齊
4. 只替換 boundary source
5. 以測試證明：
   - boundary corrected
   - aggregation preserved
   - breaks/reporting contract unified

---

# 11. Final Spec Result

本次 P2 / F3 規格可總結為：

- reporting 必須在 entry / normalization layer 對齊 F1 canonical Taipei boundary owner
- repo 仍只吃 canonical UTC boundaries
- aggregation 不得被順便重構
- 與 breaks 的 boundary contract 必須完全一致
- 所有可見差異若發生，應被視為 **Taipei boundary 對齊造成的修正性變化**，而非新規則引入

一句話總結：

**P2 F3 的正式目標，是讓 reporting 與 breaks 共用同一個 Taipei business-date owner，修正 boundary ownership，而不動 repo、schema、aggregation、canonical duration。**
