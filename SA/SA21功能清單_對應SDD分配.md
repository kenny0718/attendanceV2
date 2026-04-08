# SA21 功能清單對應 SDD 分配

> 用途：把你目前在 `SA/sa21-baseline/` 確認過的內容，整理成後續要回寫到哪份正式 `SDD`（系統設計文件）的對照表。  
> 你現在可以先只看這份，知道每個功能最後要落到哪裡。

---

## 1. 分配原則

先固定三個原則：

1. `sa21-baseline`（基線拆解）是需求確認層，不是最後正式 SDD。
2. `architecture/*.md`（架構文件）放系統級、跨模組、全平台規則。
3. `modules/*.md`（模組文件）放單一模組責任、邊界、流程、資料契約。

白話講：

> 先在 baseline 確認你要什麼，再把確認結果放回正確的正式文件。

---

## 2. `sa21-baseline` 各文件對應去哪裡

| baseline 文件 | 主要內容 | 主要回寫目標 |
|---|---|---|
| `SA/sa21-baseline/system-and-data.md` | 多租戶、資料分類、request context、tenant isolation | `SA/architecture/SYSTEM_SDD.md` |
| `SA/sa21-baseline/platform-and-saas.md` | auth、scope、roles、feature gate、audit、backup、customer_service | `SA/modules/auth.md`、`SA/modules/tenants.md`、`SA/modules/audit.md`、`SA/modules/backup.md`、`SA/modules/customer_service.md`、必要時補 `SA/architecture/SYSTEM_SDD.md` |
| `SA/sa21-baseline/attendance-domain.md` | attendance、location policy、trusted device、SSID evidence、核心語意邊界 | `SA/modules/attendance.md`、`SA/modules/attendance-capture.md`、`SA/modules/attendance-policy.md`、`SA/modules/attendance-reporting.md` |
| `SA/sa21-baseline/business-modules.md` | leave、notifications、reporting、approvals、dispatch、vehicles、accrual | `SA/modules/leave.md`、`SA/modules/notifications.md`、`SA/modules/attendance-reporting.md`；尚未正式成模組者先記在 `SA/architecture/SYSTEM_SDD.md` 或後續新模組文件 |
| `SA/sa21-baseline/validation-and-gap-seeds.md` | 必跑驗證、差距種子、現況對照入口 | `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`、`SA/architecture/SYSTEM_SDD.md`，必要時各模組 SDD 補「驗證重點 / 未落地項」 |

---

## 3. 系統級內容應回寫到哪裡

以下內容優先回寫到：
- `SA/architecture/SYSTEM_SDD.md`

### 3.1 一定屬於系統級的內容
- `multi-tenant architecture`（多租戶架構）
- `platform-first identity`（平台優先身份）
- `request context`（請求上下文）
- `company_id`（公司識別）權威來源
- `tenant isolation`（租戶隔離）
- `feature gate`（功能授權閘門）驗證順序
- 跨模組互動原則
- reporting 只讀原則

### 3.2 適合同步補進系統級矩陣的內容
- 模組邊界
- 控制關係
- 誰是 `semantic owner`（語意規則 owner）

可同步檢查：
- `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- `SA/architecture/MODULE_CONTROL_RELATION_SDD.md`

---

## 4. 平台模組內容應回寫到哪裡

## 4.1 `auth`（身分驗證）
回寫到：
- `SA/modules/auth.md`

應補內容：
- `login`（登入）
- `JWT issuance`（JWT 權杖發放）
- `login identity validation`（登入身份驗證）
- 平台身份與公司操作範圍的銜接

## 4.2 `tenants`（公司 / 租戶管理）
回寫到：
- `SA/modules/tenants.md`

應補內容：
- `company`（公司）主資料
- `memberships / members`（成員關係 / 成員）
- `feature entitlements`（功能授權）
- onboarding（開通流程）

## 4.3 `customer_service`（客服支援範圍）
回寫到：
- `SA/modules/customer_service.md`

應補內容：
- `assignment scope`（指派範圍）
- 客服只能操作被指派公司
- 非全域萬能角色

## 4.4 `audit`（稽核）
回寫到：
- `SA/modules/audit.md`

應補內容：
- 高風險操作追蹤
- 匯出
- `retention`（保存政策）
- 配對碼 / 密碼重設 / 裝置撤銷等敏感動作稽核

## 4.5 `backup`（備份 / 還原）
回寫到：
- `SA/modules/backup.md`

應補內容：
- 單公司匯出
- 單公司還原
- `company consistency check`（公司一致性檢查）
- `FK closure check`（外鍵閉包 / 關聯完整性檢查）

---

## 5. attendance 相關內容應回寫到哪裡

## 5.1 `attendance.md`
回寫：
- attendance 核心責任
- `semantic owner`（核心語意 owner）
- 與 `leave / accrual / dispatch / reporting` 的邊界

## 5.2 `attendance-capture.md`
回寫：
- `punch in / punch out`（上班打卡 / 下班打卡）
- `break out / break in`（休息離開 / 休息返回）
- 交易寫入流程
- `location policy check`（打卡前地點規則檢查）

## 5.3 `attendance-policy.md`
回寫：
- `PENDING_APPROVAL / APPROVED IN`（待審 / 核准上班）語意
- 地點合法性與待審規則
- `SSID evidence`（SSID 輔助證據）處理原則
- trusted device 是否參與判定

## 5.4 `attendance-reporting.md`
回寫：
- 員工手機看自己當月紀錄
- `HR / 管理端`（人資 / 管理端）正式列印與異常檢查
- 員工視角與 HR 視角分流
- reporting 只讀，不作為核心規則 owner

---

## 6. 其他業務模組內容應回寫到哪裡

## 6.1 `leave`（請假）
回寫到：
- `SA/modules/leave.md`

重點：
- 只處理請假流程
- 不改壞 attendance 核心語意

## 6.2 `notifications`（通知）
回寫到：
- `SA/modules/notifications.md`

重點：
- 訂閱事件
- 事件轉通知
- 不承擔主流程決策

## 6.3 `reporting`（報表）
目前先落在：
- `SA/modules/attendance-reporting.md`

原因：
- 現況 reporting 仍主要屬於 attendance 查詢子域
- 若未來獨立成模組，再另外拆出正式 `reporting` 模組文件

## 6.4 尚未正式成模組者
例如：
- `approvals`（審批）
- `dispatch`（派工）
- `vehicles`（車輛）
- `accrual`（額度 / 補休 / 餘額管理）

現階段建議：
- 先記在 `SA/architecture/SYSTEM_SDD.md`
- 或記在 `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`
- 等你確認要做，再獨立開 `SA/modules/*.md`

---

## 7. 驗證與現況比對要回寫到哪裡

## 7.1 驗證基線
優先落點：
- `SA/architecture/SYSTEM_SDD.md`
- 各模組 `SDD` 補充「不可破壞規則 / 驗證重點」

## 7.2 尚未落地功能種子
優先落點：
- `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`

白話講：

> 一份是講規則，一份是講現在做到哪裡。

---

## 8. 你現在怎麼使用這份文件

你現在只要這樣看就好：

1. 先在 `SA/sa21-baseline/` 確認要 / 不要 / 延後
2. 用這份對照表看：確認後應該回寫去哪裡
3. 等你確認一輪後，我再幫你正式回寫 `modules/*.md` 與 `architecture/*.md`

---

## 9. 目前先採用的回寫優先順序

建議順序：

1. `SA/architecture/SYSTEM_SDD.md`
2. `SA/modules/attendance.md`
3. `SA/modules/attendance-reporting.md`
4. `SA/modules/auth.md`
5. `SA/modules/tenants.md`
6. `SA/modules/backup.md`
7. `SA/modules/audit.md`
8. `SA/modules/customer_service.md`
9. `SA/modules/leave.md`
10. `SA/modules/notifications.md`

原因：
- 先把系統級規則固定
- 再把你最在意的 attendance / reporting 固定
- 最後補平台與其他模組
