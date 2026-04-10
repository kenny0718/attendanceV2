Title: Attendance Reporting Spec
Author: Johnny Lee
Version: 1.0
Date Created: 2026-04-08
Last Modified: 2026-04-08
spec:id: attendance.reporting.v1
status: active
module: attendance
subdomain: reporting
source_of_truth: SA/modules/attendance-reporting.md
related_code_paths:
  - backend/app/modules/attendance/api/reporting.py
  - backend/app/modules/attendance/api/reporting_helpers.py
  - backend/app/modules/attendance/reporting_repo.py
  - backend/app/modules/attendance/reporting_service.py
  - backend/app/modules/attendance/reporting_schemas.py
---

# Attendance Reporting 開發規格

> 本文件定義 `attendance` 模組中所有「唯讀查詢與報表」流程的正式規格。  
> 只要你要改的是 sessions 查詢、summary、報表視圖、boundary helper、employee / HR read model，就應先讀這份。

---

## 1. 文件定位

### 1.1 這份文件是給誰看的

- 你未來要修改 attendance 報表與查詢功能時
- 協助你開發 reporting 能力的 AI
- 要 review reporting 與 capture / policy 邊界的人

### 1.2 什麼情況要先看這份

- 你要修改 sessions 查詢
- 你要修改 user summary / company summary
- 你要修改 reporting 的時間區間處理
- 你要修改 Taipei business-date boundary
- 你要修改 response shaping
- 你要設計員工月視圖或 HR / 管理端列印視圖

### 1.3 它和其他文件的關係

- 主模組總覽：`SA/modules/attendance.md`
- 交易寫入規格：`SA/modules/attendance-capture.md`
- 規則語意規格：`SA/modules/attendance-policy.md`
- 模板來源：`SA/governance/MODULE_SPEC_TEMPLATE.md`

---

## 2. 目的與範圍

### 2.1 本文件負責的範圍

`attendance.reporting` 的責任是：

- 讀取既有出勤資料
- 提供 sessions 查詢
- 提供 user summary / company summary 聚合
- 提供 query validation 與 boundary helper
- 提供員工月視圖 read model
- 提供 HR / 管理端正式列印與異常檢查 read model

### 2.2 本文件不負責的範圍

這份文件不處理：

- punch in / punch out 寫入
- session close
- canonical semantic 決策
- break deduction 寫回
- 用報表邏輯偷偷修正原始交易資料

### 2.3 一句話理解

> reporting 子域只負責「解讀與呈現既有資料」，不負責「決定資料應該怎麼被寫」。

---

## 3. 核心原則

| 原則 | 定義 | 可驗證條件 |
|---|---|---|
| Read-Only Reporting | reporting 只能讀，不應寫 attendance 主資料 | 無 reporting route / service 直接修改交易資料 |
| Canonical Consumer Only | reporting 只能讀 canonical persisted duration | 不可由 reporting 定義 `duration_minutes` semantic |
| Single Boundary Owner | Taipei business-date boundary 必須由單一 owner 負責 | 不可在 breaks 與 reporting 各寫一套 today 規則 |
| Aware Datetime Only | 查詢時間輸入必須是 timezone-aware | naive datetime 應拒絕 |
| Employee / HR Split | 員工視角與 HR 視角必須分流 | 員工視圖不混入 HR 內部異常排查資訊 |
| Thin API Boundary | API 不應承擔查詢、聚合、權限、shape 全部責任 | query / aggregation / shape 有清楚分工 |

---

## 4. 功能規格

### 4.1 Sessions List

**用途**：列出某段時間內的出勤 sessions。  
**主要檔案**：`api/reporting.py`, `reporting_repo.py`

**必要行為**：
- 驗證查詢區間
- 依 actor / scope 限制查詢範圍
- 以唯讀方式回傳 session 列表

### 4.2 User Summary

**用途**：計算某個使用者在查詢區間內的摘要。  
**主要檔案**：`api/reporting.py`, `reporting_repo.py`, `reporting_service.py`

**必要行為**：
- 驗證 query range
- 讀取 canonical duration
- 由 service 進行聚合，不在 API 直接堆疊算法

### 4.3 Company Summary

**用途**：計算整家公司在查詢區間內的摘要。  
**主要檔案**：`api/reporting.py`, `reporting_repo.py`, `reporting_service.py`

**必要行為**：
- 需有 admin / management scope
- 受 tenant scope 限制
- 不可跨公司聚合

### 4.4 Employee Monthly View

**用途**：讓員工在手機上查看自己當月正式出勤紀錄。  
**主要檔案**：`api/reporting.py`, `reporting_service.py`, `reporting_schemas.py`

**必要行為**：
- 員工只看自己的資料
- 以正式有效紀錄為主
- 重點是簡單、清楚、可確認是否有問題

### 4.5 HR Review / Print View

**用途**：讓 HR / 管理端查看正式列印內容、異常資訊與管理檢查資料。  
**主要檔案**：`api/reporting.py`, `reporting_service.py`, `reporting_schemas.py`

**必要行為**：
- 正式列印與勞檢備查由 HR / 管理端處理
- 異常、缺卡、補卡、未核准加班資訊應集中在 HR 視圖
- 與員工視圖分流

### 4.6 Query Range Validation / Boundary Helper

**用途**：驗證 `start_date` / `end_date` 與處理 Taipei business-date boundary。  
**主要檔案**：`api/reporting_helpers.py`

**必要行為**：
- 拒絕 naive datetime
- 產出正確的 Taipei business-date UTC range
- 作為 shared boundary owner，不讓多處分岔

---

## 5. Formalized Semantic Block

```yaml
scope:
  module: attendance
  subdomain: reporting
  responsibility:
    - sessions_query
    - user_summary
    - company_summary
    - employee_monthly_view
    - hr_review_print_view
    - query_validation
    - business_date_boundary_helper
  non_responsibility:
    - punch_write
    - session_close
    - canonical_semantic_ownership
    - break_deduction_writeback
    - transaction_data_repair

contracts:
  read_only:
    reporting_mutates_attendance_data: false
  canonical_consumer:
    canonical_field: session.duration_minutes
    semantic_override_allowed: false
  boundary_owner:
    timezone: Asia/Taipei
    single_owner_required: true
  input_validation:
    aware_datetime_required: true
  scope_rules:
    employee_view_self_only: true
    company_summary_requires_admin_scope: true

validation_rules:
  - rule: reporting_is_read_only
    description: reporting 不可修改 attendance 主資料
    verification: no reporting write path exists
  - rule: canonical_consumer_only
    description: reporting 不可重新定義 duration semantic
    verification: summary reads canonical duration_minutes only
  - rule: boundary_owner_singleton
    description: Taipei business-date boundary 不可多處分叉
    verification: helper is reused instead of duplicated
  - rule: employee_hr_split
    description: 員工視圖與 HR 視圖需分流
    verification: employee response excludes HR-only anomaly payload

change_triggers:
  update_spec_when:
    - reporting_api_changed
    - summary_algorithm_changed
    - boundary_helper_changed
    - employee_view_changed
    - hr_review_contract_changed
```

---

## 6. 開發與驗證流程

### 6.1 開發步驟

1. 先判斷這次改動是 sessions、summary、view model，還是 boundary / validation
2. 確認這次改動屬於 read-side，而不是 write-side 補救
3. 若有碰到 canonical semantic 或 boundary owner，先同步讀 `attendance-policy.md`
4. 優先在既有 `reporting_repo.py` / `reporting_service.py` 路徑內完成改動
5. 改完後同步回寫本文件與主模組文件（若邊界有變）

### 6.2 最低驗證清單

#### Sessions 驗證
- 可依範圍查出 sessions
- scope / company 限制正確
- 不發生資料寫回

#### Summary 驗證
- user summary / company summary 聚合正常
- 只使用 canonical `duration_minutes`
- 不在 reporting 內重定義 gross / net semantic

#### Boundary 驗證
- naive datetime 會被拒絕
- Taipei business-date boundary 解析一致
- 不與其他子域各自實作 today 規則

#### View Model 驗證
- 員工只看自己的正式資料
- HR 視圖可看到正式列印與異常檢查資訊
- 員工視圖與 HR 視圖分流

---

## 7. 依賴與共用元件

### 7.1 可依賴
- `app.core.dependencies`
- `app.core.scope`
- `app.core.feature_service`
- `attendance.reporting_repo`
- `attendance.reporting_service`
- `attendance.api.reporting_helpers`
- canonical attendance session / summary read model

### 7.2 不應承擔
- attendance write orchestration
- policy semantic ownership
- break deduction persistence
- transaction-side remediation

### 7.3 共用元件

| 元件 | 功能 | 強制性 |
|---|---|---|
| `reporting_repo.py` | reporting read query owner | ✅ |
| `reporting_service.py` | 聚合與 summary owner | ✅ |
| `api/reporting_helpers.py` | boundary / datetime helper | ✅ |
| actor / scope dependencies | 限制查詢範圍 | ✅ |

---

## 8. Do / Don’t

### Do
- 讓 reporting 保持唯讀
- 使用 canonical persisted duration
- 維持單一 boundary owner
- 讓員工視圖與 HR 視圖分流
- 把聚合邏輯留在 reporting service

### Don’t
- 不要在 reporting 內偷偷重定義 canonical duration
- 不要把 boundary logic 散寫到各 endpoint
- 不要直接在 reporting 做 transaction-side 補救邏輯
- 不要把員工查閱畫面做成 HR 除錯畫面
- 不要讓 API 越改越胖

### 最容易踩雷的錯誤
1. 在 reporting 裡重新定義 gross / net semantic
2. boundary helper 到處複製
3. response shaping、權限、查詢、聚合全堆在 API
4. 把員工視圖與 HR 異常檢查混在一起

---

## 9. 回寫規則

當發生以下任一情況，必須更新本文件：

- sessions / summary API 契約改變
- reporting query contract 改變
- boundary helper 改變
- employee monthly view 改變
- HR review / print view 改變
- canonical consumer 行為改變

若變更影響跨子域或跨模組邊界，還要同步更新：

- `SA/modules/attendance.md`
- 必要時 `SA/modules/attendance-policy.md`
- 必要時 `SA/architecture/MODULE_BOUNDARY_MATRIX.md`

---

## 10. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `attendance.reporting`（報表子域）是唯讀子域，不得做狀態變更
- 員工端 P0 以手機查看自己當月正式紀錄為主
- HR / 管理端 P0 承擔正式列印、勞檢備查與異常檢查
- `reporting` 不得成為 canonical semantic owner
- 若 boundary helper 或 canonical consumer contract 改變，必須同步更新 reporting / policy / 主模組文件
