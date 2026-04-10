# attendance 模組 SDD

Title: Attendance Module Spec
Author: Johnny Lee
Version: 1.0
Date Created: 2026-04-07
Last Modified: 2026-04-09
spec:id: attendance.module.v1
status: active
module: attendance
source_of_truth: SA/modules/attendance.md
related_code_paths:
  - backend/app/modules/attendance/api.py
  - backend/app/modules/attendance/api/punch.py
  - backend/app/modules/attendance/api/breaks.py
  - backend/app/modules/attendance/api/checkpoints.py
  - backend/app/modules/attendance/api/reporting.py
  - backend/app/modules/attendance/repo.py
  - backend/app/modules/attendance/service.py
  - backend/app/modules/attendance/reporting_repo.py
  - backend/app/modules/attendance/reporting_service.py
  - backend/app/modules/attendance/punch_close_domain.py
  - backend/app/modules/attendance/policy_engine.py
  - backend/app/modules/attendance/work_hour_engine.py
---

# Attendance 模組開發規格

> 本文件定義 `attendance` 模組的正式主模組規格。  
> 這份文件負責回答整體責任、子域邊界、正式語意契約、跨子域風險與 remediation owner；真正的實作 owner 則回指到 `capture / reporting / policy` 三份子 spec。

---

## 1. 文件定位

### 1.1 這份文件是給誰看的

- 第一次接手 `attendance` 模組的你
- 協助你開發 attendance 的 AI
- 要 review attendance 與其他模組邊界的人
- 要判斷某個需求應落在哪個子域的人

### 1.2 什麼情況先看這份

- 你還不確定功能屬於 `capture`、`reporting` 還是 `policy`
- 你要先理解 `attendance` 整體責任與邊界
- 你要判讀 remediation 票據目前屬於哪個 owner
- 你要確認 `attendance` 與 `schedule`、`auth`、`tenants`、`notifications` 的關係

### 1.3 它和其他文件的關係

- 交易寫入 owner：`SA/modules/attendance-capture.md`
- 唯讀查詢 owner：`SA/modules/attendance-reporting.md`
- 規則語意 owner：`SA/modules/attendance-policy.md`
- 排班模組：`SA/modules/schedule.md`
- 系統級邊界：`SA/architecture/SYSTEM_SDD.md`
- 模組邊界矩陣：`SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- 追蹤狀態：`SA/SDD_PROGRESS_TRACKER.md`
- 模板來源：`SA/governance/MODULE_SPEC_TEMPLATE.md`

---

## 2. 目的與範圍

### 2.1 本文件負責的範圍

`attendance` 模組負責：

- 管理員工實際發生的出勤事實
- 管理 session lifecycle（open / closed）
- 管理 punch / break / checkpoint 等交易事件
- 保存 canonical duration persistence
- 提供 reporting read model
- 提供 late / early / overtime 等 policy evaluation 所需核心能力
- 執行 location policy enforcement
- 承接必要的 legacy attendance compatibility surface

### 2.2 本文件不負責的範圍

這個模組不負責：

- 登入、JWT 發放、身份驗證
- company / entitlement source of truth
- 排班 CRUD 與班表 source of truth
- 請假生命週期管理
- 通知模組主流程與通知資料表直接寫入
- 稽核模組主責任
- 跨模組任意直接寫別人的表

### 2.3 一句話理解

> `attendance` 管的是「員工實際怎麼出勤」，不是「應該怎麼排班」或「如何登入」。

---

## 3. 核心原則

| 原則 | 定義 | 可驗證條件 |
|---|---|---|
| Tenant Isolation | 所有 tenant data 必須受 `company_id` 隔離 | `company_id` 不可由 request body 決定 |
| Actor-Derived Identity | `company_id` / `user_id` 應來自 actor | route 不可信任 body override |
| Canonical Protected | `session.duration_minutes` 是 canonical persisted duration | derived minutes 不得寫回 canonical |
| Reporting Is Consumer Only | reporting 只能讀 canonical，不可反定義 semantic | `reporting` 不成為 semantic owner |
| Schedule Provides Baseline | `schedule` 提供 expected work baseline | `attendance` 只消費 schedule，不反寫 schedule semantic |
| Single Boundary Owner | business-date / today boundary 不可多處分岔 | breaks / reporting 不可各維護一套 today 規則 |
| Child Specs Own Details | 主文件負責總覽與 owner mapping，細節由子 spec 承擔 | 新需求應先落到對應子 spec |

---

## 4. 子域拆解與 owner 對應

### 4.1 `capture` 子域

**負責內容**：
- punch in / punch out
- break out / break in
- note update
- checkpoint
- session open / close

**正式 owner 文件**：`SA/modules/attendance-capture.md`

**不要在主文件展開的細節**：
- 交易寫入步驟
- repo-owned persistence path
- close flow 驗證清單
- checkpoint / break 的實作細節

### 4.2 `reporting` 子域

**負責內容**：
- sessions 查詢
- user summary
- company summary
- employee monthly view
- HR review / print view
- query validation 與 Taipei business-date boundary helper

**正式 owner 文件**：`SA/modules/attendance-reporting.md`

**不要在主文件展開的細節**：
- response shaping
- summary aggregation 細節
- 員工 / HR read model 欄位設計
- boundary helper 的具體驗證細節

### 4.3 `policy` 子域

**負責內容**：
- late / early / overtime evaluation
- schedule-aware evaluation
- work hour calculation
- missing segment rules
- canonical semantic guard

**正式 owner 文件**：`SA/modules/attendance-policy.md`

**不要在主文件展開的細節**：
- rule engine orchestration 細節
- schedule-aware helper 細節
- remediation F6 的測試實作細節

### 4.4 其他輔助區塊

| 區塊 | 作用 | 備註 |
|---|---|---|
| `location` | 打卡地點限制 | 支援規則，不獨立成主子域 |
| `checkpoint` | 特定 checkpoint 事件 | 歸 `capture` write-side 管轄 |
| `legacy` | 舊版相容層 | 新功能不要優先塞進去 |

---

## 5. 功能放置判斷規則

### 5.1 放到 `attendance-capture.md`，如果它是
- 打卡寫入
- break 事件寫入
- session 開關閉
- checkpoint 建立
- note update

### 5.2 放到 `attendance-reporting.md`，如果它是
- sessions 查詢
- user summary / company summary
- employee monthly view / HR print view
- query range validation
- Taipei business-date boundary helper

### 5.3 放到 `attendance-policy.md`，如果它是
- late / early / overtime 規則
- schedule-aware 計算
- work hour engine
- canonical semantic guard
- remediation `F5 / F6 / F11 / F12`

### 5.4 不確定時的處理順序
1. 先看這份主文件確認子域邊界
2. 再去對應 owner 子 spec
3. 若發現跨子域衝突，再回寫主文件與 tracker

---

## 6. 正式語意契約

### 6.1 Canonical = Gross
- `session.duration_minutes` 是 canonical persisted duration
- 目前正式語意基線為 `gross`

### 6.2 Break Deduction = Derived Only
- break deduction 可以計算、可以顯示
- 但不得寫回 canonical 欄位

### 6.3 Reporting = Canonical Consumer Only
- reporting 只能讀 canonical persisted duration
- 不得自行重定義 canonical semantic

### 6.4 Schedule Provides Baseline
- `schedule` 提供 expected work time / normalized windows / baseline
- `attendance.policy` 依 baseline 做判定
- `attendance` 不應改寫 `schedule` semantic

### 6.5 Taipei Business-Date Boundary Requires Single Owner
- business-date / today boundary 必須單一 owner
- 不可 breaks 一套、reporting 一套

---

## 7. 與其他模組的關係

| 模組 | 關係 | 不可越界事項 |
|---|---|---|
| `auth` | 提供身份與驗證前置能力 | attendance 不負責 JWT 發放 |
| `tenants` | 提供 company / membership / entitlement source of truth | attendance 不成為 tenant source of truth |
| `schedule` | 提供 expected work baseline | attendance 不反寫 schedule semantic |
| `leave` | 可能影響出勤解讀，但不是 attendance owner | attendance 不接手 leave lifecycle |
| `notifications` | 消費事件或結果 | attendance 不直接承擔通知主流程 |
| `audit` | 負責稽核與追溯 | attendance 不成為 audit 主模組 |

---

## 8. 目前已知衝突與技術債

### 8.1 Boundary 衝突
- breaks 與 reporting 曾出現不同 boundary contract
- boundary owner 仍需持續收斂

### 8.2 Layer Coupling 衝突
- `api/punch.py` 仍握有不少 orchestration
- `api/reporting.py` 也仍有責任集中現象
- `service.py` / `repo.py` 仍有 legacy / new 共居問題

### 8.3 Semantic Drift 風險
- `work_minutes`、`duration_minutes`、`net_work_minutes` 等名稱並存
- schedule-aware path 若失守，仍可能把 derived 值誤當 canonical

### 8.4 Legacy Surface 治理壓力
- legacy attendance API 仍存在相容層
- 新功能若再持續塞入 legacy surface，將增加後續退場成本

---

## 9. Remediation 與 owner 對應

| 問題 / 票據 | 正式 owner | 說明 |
|---|---|---|
| `R-LEGACY-ATTENDANCE-API` | `attendance.md` 主文件 + legacy surface 治理 | 主文件負責界定擴張停止與退場方向 |
| `R-APPROVE-PENDING-OWNER-INVENTORY` | `attendance.md` 主文件 | 先釐清 owner，再決定是否拆入子域 |
| `R-BOUNDARY-AND-LAYER-COUPLING` | 主文件總覽，子域各自承接修正 | 需依 capture / reporting / policy 再拆子議題 |
| `R-F6-SCHEDULE-AWARE-CANONICAL-GUARD` | `attendance-policy.md` | 由 policy 子域負責 canonical guard |

### 9.1 F6 目前正式結論
- dormant helper canonical drift 風險已完成修補
- live `punch-out` path 仍維持 `gross_minutes -> duration_minutes`
- reporting smoke 仍確認 canonical consumer 只讀 `duration_minutes`
- `approve/pending` 後重算 owner 不再混入 F6 主 remediation，改追 `R-APPROVE-PENDING-OWNER-INVENTORY`

---

## 10. 開發與驗證流程

### 10.1 開發步驟
1. 先判斷需求屬於哪個子域
2. 若不確定，先讀本主文件再對照子 spec
3. 在對應 owner 子 spec 與程式路徑內落地
4. 若影響跨子域邊界，回寫主文件與 tracker
5. 若影響 canonical / boundary / schedule baseline，必須同步檢查相鄰子 spec

### 10.2 最低驗證清單
- 這次改動有清楚 owner，沒有跨子域亂放
- `company_id` / `user_id` 仍由 actor 衍生
- canonical duration semantic 未被破壞
- reporting 未被誤改為 semantic owner
- 若涉及 boundary，仍維持單一 owner
- 若涉及 remediation，tracker 與對應 spec 已同步

---

## 11. Do / Don’t

### Do
- 把主文件當成總覽與 owner map
- 把細節落在 `capture / reporting / policy` 子 spec
- 改跨子域邊界時同步更新 tracker
- 對 canonical / boundary / schedule baseline 保持保守

### Don’t
- 不要把主文件寫成第二份 capture / reporting / policy 詳規
- 不要讓 reporting 成為 semantic owner
- 不要把 derived minutes 寫回 canonical
- 不要把 schedule 主責任拉進 attendance
- 不要再擴張 legacy surface 而不寫退場說明

---

## 12. 回寫規則

當發生以下任一情況，必須更新本文件：

- `attendance` 整體責任改變
- 子域拆分或 owner mapping 改變
- canonical semantic 改變
- 與 `schedule` / `notifications` / `reporting` / `policy` 的關係改變
- remediation 有新的正式結論或 owner 重新界定

若是子域細節改變，還必須同步更新：

- `SA/modules/attendance-capture.md`
- `SA/modules/attendance-reporting.md`
- `SA/modules/attendance-policy.md`
- `SA/SDD_PROGRESS_TRACKER.md`

---

## 13. 已依目前 baseline 回寫的正式結論（2026-04-09）

- `attendance` 主文件現在定位為總覽與 owner mapping 文件，不再重複承擔子域細部規格
- `capture`、`reporting`、`policy` 三個子域已是正式 owner spec
- `canonical = gross`、`break deduction = derived only`、`reporting = canonical consumer only` 仍是不可破壞基線
- `schedule` 是 expected work baseline source of truth，`attendance` 只能消費，不應改寫
- `R-APPROVE-PENDING-OWNER-INVENTORY` 仍維持獨立追蹤，不併回 `F6`
