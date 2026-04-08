# 模組文件索引

> 這個目錄是給「第一次接手專案的人」與「之後會幫你開發的 AI」看的模組級文件區。  
> 讀這裡的目的不是看歷史，而是快速知道：**這個功能到底該放哪裡、不要放哪裡、改完後要回寫哪份文件。**

---

## 1. 怎麼使用這個目錄

如果你今天要改一個功能，請先做這個判斷：

1. 這個功能屬於哪個模組？
2. 它是交易寫入、查詢、管理功能，還是支援規則？
3. 它會不會碰到權限、租戶、feature gate、跨模組依賴？
4. 改完後應該更新哪份模組文件？

如果你答不出來，先不要改程式，先回頭看文件。

---

## 2. 建議閱讀順序

### 想先理解整個系統
1. `SA/README.md`
2. `SA/architecture/SYSTEM_SDD.md`
3. `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
4. `SA/governance/DOCUMENTATION_GOVERNANCE.md`
5. `SA/governance/MODULE_SPEC_TEMPLATE.md`

### 想改某個模組
先讀對應模組文件：

- `attendance.md`
- `attendance-capture.md`
- `attendance-reporting.md`
- `attendance-policy.md`
- `schedule.md`
- `auth.md`
- `tenants.md`
- `leave.md`
- `notifications.md`
- `audit.md`
- `backup.md`
- `customer_service.md`
- `frontend.md`

---

## 3. attendance 模組已拆成子文件

因為 `attendance` 太大、太容易讓 AI 寫錯地方，所以現在除了主文件外，再拆成 3 份子文件：

- `attendance.md`
  - attendance 模組總覽
  - 適合先了解整體責任、邊界、技術債
- `attendance-capture.md`
  - 打卡、session、break、checkpoint 這種交易寫入流程
- `attendance-reporting.md`
  - sessions / user summary / company summary / boundary helper
- `attendance-policy.md`
  - policy engine、schedule-aware、canonical semantic、風險票據

### 什麼時候看哪一份？

- 你要改 punch-in/out、break、note、checkpoint：看 `attendance-capture.md`
- 你要改報表、summary、查詢區間：看 `attendance-reporting.md`
- 你要改遲到/早退/加班、schedule-aware、canonical contract：看 `attendance-policy.md`
- 你不確定功能屬於哪裡：先看 `attendance.md`

---

## 4. 模組清單與白話用途

| 文件 | 這份文件是講什麼的 | 你什麼時候該看 |
|---|---|---|
| `attendance.md` | 出勤模組總覽 | 不確定 attendance 功能歸屬時 |
| `attendance-capture.md` | 打卡與 session 寫入流程 | 改打卡主流程時 |
| `attendance-reporting.md` | 出勤報表與查詢 | 改 summary / sessions / boundary 時 |
| `attendance-policy.md` | 政策規則與 schedule-aware | 改 policy / canonical semantic 時 |
| `schedule.md` | 排班模板與班表指派 | 改排班資料時 |
| `auth.md` | 登入與 JWT | 改登入或 token 時 |
| `tenants.md` | 公司、成員、entitlements | 改公司管理或會員時 |
| `leave.md` | 請假與審批 | 改請假流程時 |
| `notifications.md` | 事件轉通知 | 改通知寫入或事件訂閱時 |
| `audit.md` | 稽核查詢與匯出 | 改 audit query / export / retention 時 |
| `backup.md` | 公司級備份還原 | 改備份與還原時 |
| `customer_service.md` | 客服支援公司範圍 | 改客服 scope 時 |
| `frontend.md` | Vue 前端結構 | 改登入狀態、路由守衛、前端 API 時 |

---

## 5. 文件維護規則

只要發生以下任一種情況，就要更新對應模組文件：

- 新增 API
- 模組責任改變
- 權限 / scope / feature gate 改變
- 新增跨模組依賴
- 新增事件或修改事件契約
- query contract 改變
- canonical semantic 改變

---

## 6. Spec 模板與未來 spec-kit 接軌

本專案現在已建立模組 spec 模板：

- `SA/governance/MODULE_SPEC_TEMPLATE.md`

使用方式：

1. 新模組或新子域，先複製模板
2. 先填 metadata（如 `spec:id`、`source_of_truth`、`related_code_paths`）
3. 再填核心原則、功能規格、Formalized Semantic Block、驗證流程
4. 現在先用 Markdown 跑順
5. 之後若導入 `spec-kit`，就讓工具承接這套既有格式

目前第一份正式 spec 化範例是：

- `SA/modules/attendance-capture.md`

---

## 7. 給第一次寫文件的你

你不用一開始就寫得像架構師論文。

你只要每次都把下面幾件事寫清楚，文件就會越來越有用：

1. 這個模組負責什麼
2. 不負責什麼
3. 主要功能有哪些
4. 重要檔案在哪裡
5. 哪些地方最容易寫錯
6. 你這次改了什麼，需要同步改哪份文件

只要能做到這 6 點，之後不管是你自己、同事，還是 AI，都會比現在更容易看懂。

---

## 8. 已依目前 baseline 補充的閱讀指引（2026-04-08）

- 如果你在看 `attendance`，請先分清楚：`capture`（寫入）、`reporting`（唯讀查詢）、`policy`（規則與語意）
- 如果你在看平台能力，請一起對照：`auth`、`tenants`、`audit`、`backup`、`customer_service`
- `reporting`（報表）目前先視為 `attendance` 內的唯讀子域，不急著獨立模組
- `schedule`（排班）是預期工作時間來源，`attendance` 只消費它，不應改寫它
- 前端與前端 `precheck`（預檢）都不是最終安全邊界，最終合法性仍以後端為準
