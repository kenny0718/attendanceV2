# P2 F3 Baseline — Reporting Formal Before-State Reference

> **Document Type**: Baseline Report
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Ticket**: F3 — Align reporting entrypoints to the canonical Taipei boundary normalization owner
> **Purpose**: Record the formal pre-change baseline for reporting entrypoints before any F3 implementation, for later before/after comparison
> **Execution Mode**: Read-only collection only
> **Status**: Baseline collected with noted data-coverage limits
> **Inputs**:
> - `backend/app/modules/attendance/api/reporting.py`
> - `docs/attendance/remediation/02_fix/P2_F3_FIX_SPEC.md`
> - `docs/attendance/remediation/02_fix/P2_F3_BLOCKER_REPORT.md`
> - `POST /api/internal/auth/login`
> - `GET /api/v1/attendance/sessions`
> - `GET /api/v1/attendance/reports/user-summary`
> - `GET /api/v1/attendance/reports/company-summary`
> **Collected On**: 2026-04-06
> **Collector Context**:
> - service: `attendance-system` active
> - upstream: `127.0.0.1:8000` reachable
> - app import: OK
> - login path used: formal auth flow (`/api/internal/auth/login`)

---

# 0. Executive Summary

本文件記錄 F3 實作前的正式 baseline，供後續 F3 execution 做 before / after compare。

本次 baseline 收集結果如下：

- 正式 reporting entrypoints 可正常呼叫，未出現 502、import error、service crash
- 已以正式登入流程取得 JWT，並透過正式 API 收集 baseline
- `naive datetime rejection` 已明確驗證為 `422`
- `timezone-aware` 輸入可正常接受
- 可觀測資料集以 `yhsi / yhsimis / super_admin` 所在 tenant 為主
- 由於目前可合法存取且可穩定登入的資料集僅有少量 `yhsi` session，**Taipei 跨午夜（例如 23:50 / 00:10）與跨月有資料落點的觀測不足**
- 因此，本文件同時記錄：
  - 已成功建立的正式 baseline
  - 已執行但回傳零資料的 boundary 場景
  - 因資料覆蓋不足而無法觀測「邊界附近實際歸屬變化」的限制

---

# 1. Collection Preconditions

## 1.1 Service / App Availability Validation

在 baseline 收集前，已先確認：

1. `app.main` 可成功 import
2. `attendance-system` 為 `active (running)`
3. `uvicorn` 正常 `LISTEN` 於 `127.0.0.1:8000`
4. `curl -I http://127.0.0.1:8000/` 可取得有效 HTTP 回應（非 502）

判定：
- baseline 收集時，正式 app 可正常呼叫
- 本次 baseline 未受 `main.py` / app 啟動問題阻塞

## 1.2 Authentication Path Used

使用正式登入流程：

- Endpoint: `POST /api/internal/auth/login`
- Request body:

```json
{
  "company_id": "yhsi",
  "login_username": "yhsimis",
  "password": "Yh2028109!"
}
```

登入結果：
- HTTP `200`
- 取得 `access_token`
- 使用該 token 呼叫三個 reporting entrypoints

## 1.3 Baseline Dataset Used

本次實際 baseline 使用之 tenant / actor：

- `company_id = yhsi`
- `login_username = yhsimis`
- `role_id = super_admin`

可觀測到的既有 attendance session（Taipei time）為：

1. `2026-03-27T18:36:32.529105+08:00`
2. `2026-03-27T18:36:39.763284+08:00`
3. `2026-03-29T11:41:24.470709+08:00`

全部均屬：
- `status = closed`
- `duration_minutes = 0`

---

# 2. Reporting Contract Confirmed Before Collection

依 `backend/app/modules/attendance/api/reporting.py`，本次 baseline 以以下契約為準：

- Entry points:
  - `GET /api/v1/attendance/sessions`
  - `GET /api/v1/attendance/reports/user-summary`
  - `GET /api/v1/attendance/reports/company-summary`
- query filter 以 `punch_in_time` 為準
- `start_date` / `end_date` 必須為 timezone-aware datetime
- naive datetime 依契約應回 `422`
- summary 重要欄位包括：
  - `total_sessions`
  - `closed_sessions`
  - `open_sessions`
  - `total_work_minutes`
  - `average_*`
  - `first_session_time`
  - `last_session_time`

---

# 3. Baseline Scenario Matrix

| Scenario ID | Scenario | Endpoint Coverage | Result |
|---|---|---|---|
| S1 | Taipei 一般當日查詢 | sessions / user-summary / company-summary | PASS |
| S2 | Taipei 跨午夜邊界查詢（23:50 / 00:10 window style） | sessions | PASS (0 rows, no accessible midnight-adjacent data) |
| S3 | 跨月邊界查詢 | sessions / user-summary / company-summary | PASS (0 rows in accessible tenant) |
| S4 | timezone-aware 輸入（UTC-aware） | sessions / user-summary / company-summary | PASS |
| S5 | naive datetime rejection | sessions / user-summary / company-summary | PASS (`422`) |

> 注意：
> - S2 / S3 的 API 呼叫本身成功，故不屬於 service blocker。
> - 但由於可合法登入且穩定可觀測的 `yhsi` 資料集不包含午夜附近或跨月邊界實際資料點，故這兩類場景目前只能形成「零結果 baseline」，不能形成「邊界附近資料歸屬差異」的高資訊量 baseline。

---

# 4. Detailed Baseline Records

## 4.1 Scenario S1 — Taipei General Same-Day Query

### Request semantics
- Taipei business date window: `2026-03-27 00:00:00+08:00` to `2026-03-28 00:00:00+08:00`
- 目的：建立一般當日 reporting baseline

### A. Sessions

**Request**

```text
GET /api/v1/attendance/sessions?start_date=2026-03-27T00:00:00%2B08:00&end_date=2026-03-28T00:00:00%2B08:00&limit=100
```

**HTTP status**
- `200`

**Response summary**
- `total = 2`
- `returned sessions = 2`
- session timestamps:
  - `2026-03-27T18:36:39.763284+08:00`
  - `2026-03-27T18:36:32.529105+08:00`
- statuses:
  - `closed = 2`
- durations:
  - both `0`

**Taipei business-date observation**
- 兩筆 session 的 `punch_in_time` 都落在 Taipei `2026-03-27`
- 目前 baseline 與「以 Taipei 日期作為 business-date 歸屬」一致
- 此場景可作為 F3 後的基本不回歸比較基準

### B. User Summary

**Request**

```text
GET /api/v1/attendance/reports/user-summary?start_date=2026-03-27T00:00:00%2B08:00&end_date=2026-03-28T00:00:00%2B08:00
```

**HTTP status**
- `200`

**Response summary**
- `user_id = 008d7786-21f2-4b75-8fd0-2e6648e197e4`
- `total_sessions = 2`
- `closed_sessions = 2`
- `open_sessions = 0`
- `total_work_minutes = 0`
- `average_session_minutes = 0.0`
- `first_session_time = 2026-03-27T18:36:32.529105+08:00`
- `last_session_time = 2026-03-27T18:36:39.763284+08:00`

**Taipei business-date observation**
- summary 與 sessions list 一致，統計期間內僅包含 Taipei `2026-03-27` 的兩筆資料
- `first_session_time` / `last_session_time` 目前回傳為 Taipei offset 表示

### C. Company Summary

**Request**

```text
GET /api/v1/attendance/reports/company-summary?start_date=2026-03-27T00:00:00%2B08:00&end_date=2026-03-28T00:00:00%2B08:00
```

**HTTP status**
- `200`

**Response summary**
- `company_id = yhsi`
- `total_users_with_sessions = 1`
- `total_sessions = 2`
- `open_sessions = 0`
- `closed_sessions = 2`
- `total_work_minutes = 0`
- `average_minutes_per_session = 0.0`
- `average_minutes_per_user = 0.0`
- `first_session_time = 2026-03-27T10:36:32.529105Z`
- `last_session_time = 2026-03-27T10:36:39.763284Z`

**Taipei business-date observation**
- 統計數值與同日 sessions / user-summary 一致
- 但本場景下 `company-summary` 的 `first_session_time` / `last_session_time` 回傳為 `Z`（UTC）表示
- 此欄位表示格式與 `user-summary` 不同，應在 F3 後維持既有 contract，不得因 boundary 對齊意外改變欄位語意或值

---

## 4.2 Scenario S2 — Taipei Cross-Midnight Boundary Window

### Request semantics
- Taipei boundary-style window: `2026-03-27 23:50:00+08:00` to `2026-03-28 00:10:00+08:00`
- 目的：觀察 Taipei 午夜邊界附近的 session 歸屬

### Sessions

**Request**

```text
GET /api/v1/attendance/sessions?start_date=2026-03-27T23:50:00%2B08:00&end_date=2026-03-28T00:10:00%2B08:00&limit=100
```

**HTTP status**
- `200`

**Response summary**
- `total = 0`
- `returned sessions = 0`

**Taipei business-date observation**
- API 行為正常，未出現 502 / validation error
- 但目前 `yhsi` 可觀測資料集中**沒有**落在 Taipei 午夜附近的 session
- 因此本場景目前只能建立「正式零結果 baseline」，**無法觀察 23:50 / 00:10 邊界附近的實際歸屬變化**

**Coverage note**
- 此為資料覆蓋限制，不是 service / app blocker
- 若後續需要高資訊量 compare，需在合法可存取的資料集中補充午夜附近既有資料或使用既有可登入且含該資料的 tenant 重新收集 baseline

---

## 4.3 Scenario S3 — Cross-Month Boundary Query

### Request semantics
- Taipei month boundary window: `2026-03-31 00:00:00+08:00` to `2026-04-01 00:00:00+08:00`
- 目的：觀察跨月統計歸屬

### A. Sessions

**Request**

```text
GET /api/v1/attendance/sessions?start_date=2026-03-31T00:00:00%2B08:00&end_date=2026-04-01T00:00:00%2B08:00&limit=100
```

**HTTP status**
- `200`

**Response summary**
- `total = 0`
- `returned sessions = 0`

### B. User Summary

**Request**

```text
GET /api/v1/attendance/reports/user-summary?start_date=2026-03-31T00:00:00%2B08:00&end_date=2026-04-01T00:00:00%2B08:00
```

**HTTP status**
- `200`

**Response summary**
- `total_sessions = 0`
- `closed_sessions = 0`
- `open_sessions = 0`
- `total_work_minutes = 0`
- `average_session_minutes = null`
- `first_session_time = null`
- `last_session_time = null`

### C. Company Summary

**Request**

```text
GET /api/v1/attendance/reports/company-summary?start_date=2026-03-31T00:00:00%2B08:00&end_date=2026-04-01T00:00:00%2B08:00
```

**HTTP status**
- `200`

**Response summary**
- `total_users_with_sessions = 0`
- `total_sessions = 0`
- `open_sessions = 0`
- `closed_sessions = 0`
- `total_work_minutes = 0`
- `average_minutes_per_session = null`
- `average_minutes_per_user = null`
- `first_session_time = null`
- `last_session_time = null`

**Taipei business-date observation**
- API 契約正常工作
- 但 `yhsi` 可觀測資料在此跨月視窗內無資料
- 因此本場景可作為「零結果 baseline」，但**不能作為跨月邊界資料歸屬變化的高資訊量觀測樣本**

---

## 4.4 Scenario S4 — Timezone-Aware UTC Input

### Request semantics
- UTC-aware window: `2026-03-26T16:00:00Z` to `2026-03-27T16:00:00Z`
- 此視窗等價於 Taipei `2026-03-27 00:00:00+08:00` 到 `2026-03-28 00:00:00+08:00`
- 目的：確認 aware 輸入可正常接受，並作為 F3 前 contract baseline

### A. Sessions

**Request**

```text
GET /api/v1/attendance/sessions?start_date=2026-03-26T16:00:00Z&end_date=2026-03-27T16:00:00Z&limit=100
```

**HTTP status**
- `200`

**Response summary**
- `total = 2`
- `returned sessions = 2`
- `punch_in_time` 回傳為：
  - `2026-03-27T10:36:39.763284Z`
  - `2026-03-27T10:36:32.529105Z`

**Taipei business-date observation**
- 兩筆資料對應 Taipei `2026-03-27 18:36:*`
- 與 S1 的 Taipei-aware 查詢返回相同資料集合
- 顯示目前 reporting 契約接受 generic timezone-aware range，並以轉成 UTC 後查詢為主

### B. User Summary

**Request**

```text
GET /api/v1/attendance/reports/user-summary?start_date=2026-03-26T16:00:00Z&end_date=2026-03-27T16:00:00Z
```

**HTTP status**
- `200`

**Response summary**
- `total_sessions = 2`
- `closed_sessions = 2`
- `open_sessions = 0`
- `total_work_minutes = 0`
- `average_session_minutes = 0.0`
- `first_session_time = 2026-03-27T18:36:32.529105+08:00`
- `last_session_time = 2026-03-27T18:36:39.763284+08:00`

### C. Company Summary

**Request**

```text
GET /api/v1/attendance/reports/company-summary?start_date=2026-03-26T16:00:00Z&end_date=2026-03-27T16:00:00Z
```

**HTTP status**
- `200`

**Response summary**
- `total_users_with_sessions = 1`
- `total_sessions = 2`
- `open_sessions = 0`
- `closed_sessions = 2`
- `total_work_minutes = 0`
- `average_minutes_per_session = 0.0`
- `average_minutes_per_user = 0.0`
- `first_session_time = 2026-03-27T18:36:32.529105+08:00`
- `last_session_time = 2026-03-27T18:36:39.763284+08:00`

**Taipei business-date observation**
- S4 與 S1 在資料集合與統計數值上完全對齊
- 此結果是 F3 之後的重要 compare 基線：若 boundary owner 對齊後 contract 變更，必須確認這類既有 aware-input 行為是否維持、收斂或被明確重新定義

---

## 4.5 Scenario S5 — Naive Datetime Rejection

### Request semantics
- 使用無 timezone 的 datetime
- 目的：確認契約層 rejection baseline

### A. Sessions

**Request**

```text
GET /api/v1/attendance/sessions?start_date=2026-03-27T00:00:00&end_date=2026-03-28T00:00:00&limit=100
```

**HTTP status**
- `422`

**Response body summary**
- `detail = "start_date must be timezone-aware (naive datetime rejected)"`

### B. User Summary

**Request**

```text
GET /api/v1/attendance/reports/user-summary?start_date=2026-03-27T00:00:00&end_date=2026-03-28T00:00:00
```

**HTTP status**
- `422`

**Response body summary**
- `detail = "start_date must be timezone-aware (naive datetime rejected)"`

### C. Company Summary

**Request**

```text
GET /api/v1/attendance/reports/company-summary?start_date=2026-03-27T00:00:00&end_date=2026-03-28T00:00:00
```

**HTTP status**
- `422`

**Response body summary**
- `detail = "start_date must be timezone-aware (naive datetime rejected)"`

**Taipei business-date observation**
- 目前 contract 明確拒絕 naive datetime
- 此 rejection 行為本身也是 F3 後不可無意改壞的 baseline

---

# 5. Cross-Endpoint Consistency Notes (Before F3)

## 5.1 S1 / S4 Numeric Consistency

在同一實際資料集合下：

- `sessions.total = 2`
- `user-summary.total_sessions = 2`
- `company-summary.total_sessions = 2`
- `user-summary.total_work_minutes = 0`
- `company-summary.total_work_minutes = 0`
- `company-summary.total_users_with_sessions = 1`

此一致性可作為 F3 後 compare baseline。

## 5.2 Response Time Field Representation Difference

本次 baseline 觀測到：

- `user-summary` 在 S1 中回傳 `+08:00` 表示
- `company-summary` 在 S1 中回傳 `Z` 表示
- `sessions` 的 time representation 會隨輸入視窗語意出現 `+08:00` 或 `Z` 表示

此差異為**目前既有 baseline 行為**；
F3 不應在未明確規格化的前提下，順手改變這些欄位表示行為。

---

# 6. Coverage Gaps / Blockers for Higher-Fidelity Baseline

## 6.1 No Current Service Blocker

本次 baseline 收集過程中：
- 無 502
- 無 import error
- 無 service restart 問題
- 無 app 啟動阻塞

因此：
- **baseline 收集本身不再被 app / upstream 問題阻塞**

## 6.2 Data-Coverage Limitation

目前仍存在一項**資料覆蓋限制**：

- 可合法登入且穩定可用的 `yhsi` tenant 雖可成功建立正式 baseline
- 但其可觀測 session 資料量少，且不包含：
  - Taipei 午夜附近（如 `23:50 / 00:10`）資料點
  - 跨月邊界附近實際 session 資料點

因此：
- 本文件已建立「正式 before baseline」
- 但對於 F3 最敏感的 boundary edge cases，目前只能建立：
  - 正式 API 可呼叫 baseline
  - 零結果 baseline
- 尚不能建立「邊界附近有實際資料點」的高資訊量 baseline

## 6.3 Operational Interpretation

這不是 F3 execution blocker，但屬於 compare 品質注意事項：

- 後續若 F3 修改主要影響午夜 / 跨月歸屬，
  則僅用本文件可能不足以解釋所有邊界修正差異
- 若要做更強的 compare，應在合法存取前提下，補充一組具午夜 / 跨月邊界資料的正式 baseline

---

# 7. Final Baseline Conclusion

本次已成功完成 F3 前的正式 baseline 收集，結論如下：

1. 三個正式 reporting entrypoints 均可正常呼叫
2. baseline 收集期間無 502 / import error / app 啟動阻塞
3. 已建立以下可審計 baseline：
   - 一般當日查詢 baseline
   - timezone-aware 輸入 baseline
   - naive datetime rejection baseline
   - 跨午夜 / 跨月零結果 baseline
4. 已記錄 summary 類 endpoint 之重要統計欄位：
   - `total_sessions`
   - `total_work_minutes`
   - `closed_sessions`
   - `open_sessions`
   - `average_*`
   - `first_session_time`
   - `last_session_time`
5. 目前唯一限制是資料覆蓋不足，非 service / app blocker

一句話總結：

**F3 baseline 已建立，可供後續 before / after compare 使用；但午夜與跨月邊界的高資訊量資料樣本目前不足，後續比對時必須明確註記此限制。**
