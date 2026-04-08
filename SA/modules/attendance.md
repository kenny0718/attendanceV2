# attendance 模組 SDD

**模組名稱**：`attendance`  
**文件類型**：Module System Design Document  
**文件狀態**：Active / Canonical  
**最後整理日期**：2026-04-07  
**程式位置**：`backend/app/modules/attendance`  
**規格來源基線**：
- `docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md`
- `docs/attendance/architecture/*`
- `docs/attendance/remediation/*`
- `backend/app/modules/attendance/*` 實際程式碼

---

## 1. 這份文件是做什麼的？

這份文件是 `attendance` 模組的總覽文件。

如果你是第一次寫文件、第一次整理架構，請把它理解成：

- 先用這份看懂 `attendance` 整體在做什麼
- 再依你要修改的功能，去看更細的子文件

它要回答的核心問題：

1. `attendance` 模組到底負責什麼
2. 哪些功能其實是不同子域
3. 新功能該放哪裡
4. 哪些地方現在有衝突、風險、技術債
5. remediation 票據應該怎麼判讀

---

## 2. 模組定位

`attendance` 是整個系統最核心、也是目前最複雜的業務模組。

你可以把它理解成：

> 這個模組專門管理「員工實際發生的出勤事實」。

包含：

- 上班打卡
- 下班打卡
- 外出 / 返回
- session 開關閉
- 工時與政策判定
- 出勤查詢報表
- 打卡地點限制
- 部分 legacy 相容流程

### 它負責的事

- punch in / punch out
- break out / break in
- current status / history / session query
- session lifecycle（open / closed）
- canonical duration persistence
- break deduction derived calculation
- policy evaluation（遲到 / 早退 / 加班）
- reporting read model
- checkpoint
- location policy enforcement
- legacy attendance API 相容層

### 它不該負責的事

- 登入、JWT 發放、身份驗證
- company / entitlement source of truth
- 排班 CRUD
- 請假生命週期
- 通知資料表直接寫入
- 稽核主模組責任
- 跨模組任意直接寫別人的表

---

## 3. 與 SA2.1 的對應結論

根據 `docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md`，這個模組有幾個不能亂動的正式約束：

1. 所有 Tenant Data 必須受 `company_id` 隔離
2. `company_id` 不可來自 request body
3. API 驗證順序應是：
   - Scope Validation
   - Tenant Isolation
   - Feature Gate
   - Location Policy（若流程需要）
4. `attendance` 核心語意不可被其他模組改寫
5. reporting 是 consumer，不是 semantic owner
6. Location Policy 必須由後端 authoritative enforcement

白話說：

- 不能讓前端決定最終公司範圍
- 不能讓 reporting 反過來定義 canonical duration
- 不能每個 route 自己發明一套 boundary 規則

---

## 4. attendance 已拆成子文件

因為這個模組太大，之後如果只靠一份文件，很容易再次變成「AI 也看不懂、你也難維護」。

所以現在 `attendance` 已拆成：

### 4.1 `attendance.md`
這份是總覽。

適合你在以下情況先看：
- 還不確定功能屬於哪裡
- 想先知道整個 attendance 的責任與邊界
- 想先看整體風險與 remediation 狀態

### 4.2 `attendance-capture.md`
這份是交易寫入子文件。

適合你在以下情況看：
- 改 punch-in / punch-out
- 改 break-out / break-in
- 改 note update
- 改 checkpoint
- 改 session open / close

### 4.3 `attendance-reporting.md`
這份是查詢與報表子文件。

適合你在以下情況看：
- 改 sessions 查詢
- 改 user summary / company summary
- 改 boundary helper
- 改 reporting query contract

### 4.4 `attendance-policy.md`
這份是政策規則子文件。

適合你在以下情況看：
- 改遲到 / 早退 / 加班規則
- 改 schedule-aware 評估
- 改 canonical semantic
- 判讀 F6 / policy remediation

---

## 5. 正式子域拆解

| 子域 | 白話意思 | 主要檔案 | 備註 |
|---|---|---|---|
| `capture` | 真正把出勤事件寫進系統 | `api/punch.py`, `api/breaks.py`, `repo.py`, `service.py`, `punch_close_domain.py` | 核心交易流 |
| `reporting` | 把既有資料查出來、整理成報表 | `api/reporting.py`, `reporting_repo.py`, `reporting_service.py`, `api/reporting_helpers.py` | 唯讀子域 |
| `policy` | 算規則、算遲到早退加班、處理 schedule-aware | `policy_engine.py`, `policy_rules.py`, `policy_missing_segment.py`, `work_hour_engine.py` | 規則與語意核心 |
| `location` | 打卡地點限制 | `location_policy_service.py`, `admin_location_api.py`, `gps_utils.py` | 支援規則 |
| `checkpoint` | 特定 checkpoint 事件 | `api/checkpoints.py`, `checkpoint_repo.py` | 不等於 break |
| `legacy` | 舊版相容層 | `api/legacy.py`, `api.py` | 新功能不要優先塞這裡 |

---

## 6. 系統目錄關係圖

```text
backend/app/modules/attendance/
├── api.py
├── api/
│   ├── __init__.py
│   ├── legacy.py
│   ├── punch.py
│   ├── breaks.py
│   ├── checkpoints.py
│   ├── reporting.py
│   ├── reporting_helpers.py
│   ├── break_deduction.py
│   ├── anomaly_audit.py
│   └── helpers.py
├── repo.py
├── reporting_repo.py
├── reporting_service.py
├── service.py
├── punch_close_domain.py
├── work_hour_engine.py
├── policy_engine.py
├── policy_rules.py
├── policy_missing_segment.py
├── policy_schedule_support.py
├── policy_schedule_models.py
├── location_policy_service.py
├── admin_location_api.py
├── checkpoint_repo.py
├── attendance_punch_repo.py
├── models.py
├── schemas.py
└── tests/
```

---

## 7. 你之後要怎麼判斷功能放哪裡？

### 放 `attendance-capture.md` 管的範圍，如果它是：
- 打卡寫入
- break 事件寫入
- session 開關閉
- checkpoint
- note update

### 放 `attendance-reporting.md` 管的範圍，如果它是：
- sessions 查詢
- user summary
- company summary
- query range validation
- Taipei business-date boundary

### 放 `attendance-policy.md` 管的範圍，如果它是：
- 遲到 / 早退 / 加班規則
- schedule-aware 計算
- work hour engine
- canonical semantic
- remediation F5 / F6 / F11 / F12 判讀

---

## 8. 不可破壞的語意契約

### 8.1 canonical = gross
- `session.duration_minutes` 是 canonical persisted duration
- 目前語意基線是 `gross`

### 8.2 break deduction = derived only
- break deduction 可以算、可以顯示
- 但不應寫回 canonical 欄位

### 8.3 reporting = canonical consumer only
- reporting 只能讀 canonical persisted duration
- 不應自己改 semantic

### 8.4 Taipei business-date boundary 要有單一 owner
- 不可 breaks 一套、reporting 一套

---

## 9. 目前已知衝突與技術債

### 9.1 Boundary 衝突
- breaks 與 reporting 曾經有不同 boundary contract
- boundary owner 必須持續收斂，不能再散

### 9.2 Layer coupling 衝突
- `api/punch.py` 仍握有不少 orchestration
- `api/reporting.py` 也有責任集中現象
- `service.py` / `repo.py` 仍有 legacy / new 共居問題

### 9.3 Semantic drift 風險
- `work_minutes`、`duration_minutes`、`net_work_minutes` 等名稱並存
- schedule-aware path 仍可能誤把 `work_minutes` 當 canonical

---

## 10. 對 F6 的嚴謹結論

目前依實際程式判讀：

- `P6_F6` 的 dormant helper 風險已完成修補
- 主 `punch-out` live path 原本就不是走該 helper；目前 live path 由 `api/punch.py` 計算 `gross_minutes`，並經 `repo.close_session(..., duration_minutes=gross_minutes, ...)` 寫回 canonical duration
- 已有 targeted regression test 鎖住 `work_minutes` 不得再寫回 `duration_minutes`
- 已有 reporting smoke coverage 鎖住 canonical consumer 仍只讀 `duration_minutes`
- 已完成最小 repo-level inventory：`repo.py` 目前僅見 `AttendanceSessionRepository.close_session()` 寫入 `session.duration_minutes`，`attendance_punch_repo.py` 未見碰觸 canonical session duration
- `approve/pending` 後重算 owner 尚未盤出正式 attendance policy 重算路徑；此議題已獨立轉入 `R-APPROVE-PENDING-OWNER-INVENTORY`，不能再併入 `F6` 主 remediation 判定

所以現在若要判斷 F6 是否可進一步收斂，你要檢查五件事：

1. 程式中是否仍存在 `work_minutes -> duration_minutes` 寫入路徑
2. live punch-out canonical write 是否仍維持 `gross_minutes`
3. targeted tests 是否存在且通過
4. reporting canonical consumer smoke 是否存在且通過
5. remediation / tracker 文件是否已同步回寫

---

## 11. 你第一次寫文件，可以怎麼用這套？

你不用一開始就把文件寫得像論文。

你只要每次都把下面這幾件事講清楚：

1. 這個模組 / 子域負責什麼
2. 不負責什麼
3. 主要功能有哪些
4. 主要檔案在哪裡
5. 最容易寫錯的地方是什麼
6. 改完後要同步更新哪份文件

只要你每次都做到這幾點，這套文件就會越來越能用，而且你會越來越有能力自己讀、自己改、自己判斷。

---

## 12. 什麼情況要更新這份文件？

- `attendance` 整體責任改了
- 子域切分改了
- canonical semantic 改了
- 與 schedule / notifications / reporting 的關係改了
- remediation 狀態有正式結論了
