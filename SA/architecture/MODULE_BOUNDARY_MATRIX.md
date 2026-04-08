# 模組邊界矩陣

## 1. 用途

本文件定義目前系統各模組的責任、可依賴關係、禁止事項，以及已觀察到的重疊風險。

---

## 2. 模組矩陣

| 模組 | 核心責任 | 可依賴 | 不應承擔 | 目前風險 |
|---|---|---|---|---|
| auth | 登入、JWT、身分驗證 | core, tenants repo/model | 業務流程 | 低 |
| tenants | 公司、會員、entitlements、onboarding | core, auth models/repo | 出勤/請假業務 | 中 |
| attendance | 打卡、session、policy、reporting、work-hour、location | core, schedule baseline | 公司管理、身份驗證 | 高 |
| schedule | 班別模板、班別指派、baseline | core | 直接主導 attendance punch flow | 中 |
| leave | 請假申請與審核 | core | 公司管理、打卡計算 | 低 |
| notifications | 事件轉通知記錄 | core event bus | 主業務決策 | 低 |
| audit | 稽核查詢、匯出、retention、purge | core | 一般業務計算 | 低 |
| backup | 公司級備份還原 | core | 業務規則判斷 | 中 |
| customer_service | 客服公司指派與 scope | core | 一般 tenant 內部業務 | 低 |
| frontend | UI、路由守衛、狀態、API 消費 | backend API | 後端權威驗證 | 中 |

> 補充：`attendance`（出勤）是核心語意 owner；`reporting`（報表）目前作為 attendance 內的唯讀子域，不得反向定義核心語意。

---

## 3. 關鍵依賴原則

### 3.1 允許的依賴方向
- 所有模組都可依賴 `core`
- 前端只依賴後端公開 API，不依賴後端實作
- notifications 應透過事件訂閱取得資訊
- attendance 可讀取 schedule baseline，但不應吞掉 schedule 的主責任

### 3.2 應避免的依賴
- 模組直接操作其他模組資料表
- 模組直接承接其他模組 service 主責任
- 將跨模組協調邏輯長期放在 API 層

---

## 4. 重疊風險清單

### 4.1 attendance vs schedule
重疊點：
- 排班 baseline 已進入 attendance policy 計算
- 若未控制好，出勤判定規則會逐步把班表主責任吸過去

規則：
- `schedule` 負責定義排班資料
- `attendance` 只消費排班結果做出勤判定

### 4.2 attendance vs reporting
重疊點：
- reporting 目前仍掛在 attendance 模組內
- 若繼續成長，會讓 attendance 成為全能模組

規則：
- 短期可維持在 attendance 子域
- 中期需明確區分 write path 與 read/report path

### 4.3 audit / notifications / backup 文件與實作不同步
重疊點：
- 文件曾描述舊 header-based tenant context
- 程式已改為 JWT actor

規則：
- 以程式現況為準，文件必須回寫同步

---

## 5. 新功能歸屬判斷規則

### 放在 attendance，如果它是：
- session/punch/break/out checkpoint
- work hour calculation
- attendance policy evaluation
- attendance reporting
- attendance location enforcement

### 放在 schedule，如果它是：
- shift template lifecycle
- shift assignment lifecycle
- work schedule source data

### 放在 tenants，如果它是：
- tenant CRUD
- company members
- onboarding
- entitlements

### 放在 auth，如果它是：
- login
- token
- membership identity validation

### 放在 audit / backup / notifications，如果它是：
- 記錄、匯出、保留、還原、事件落地

---

## 6. 邊界變更觸發條件

若出現以下任一情況，必須更新本文件：
- 新增跨模組同步呼叫
- 一個模組開始讀寫另一模組主資料
- 模組內出現第二條平行實作路徑
- API 層不再只是薄層，而成為實質 orchestrator
