# leave 模組 SDD

**模組名稱**：`leave`  
**你可以把它理解成**：系統的「請假與審批模組」  
**程式位置**：`backend/app/modules/leave`

---

## 1. 這個模組是做什麼的？

`leave` 負責處理請假申請與審批。

白話說：

- 員工送請假
- 系統保存請假申請
- 管理者查看待審核清單
- 最後 approve / reject

---

## 2. 主要功能

### 2.1 建立請假申請
用途：員工送出請假資料。

### 2.2 個人請假列表
用途：查自己的請假紀錄。

### 2.3 待審批清單
用途：給管理者看有哪些請假要審。

### 2.4 Approve / Reject
用途：完成審核決策。

### 2.5 Feature Gate
目前核心 gate：`leave.core`

---

## 3. 模組邊界

### `leave` 負責
- 請假申請生命週期
- 請假審核流程
- 與請假資料直接相關的查詢

### `leave` 不負責
- 打卡 session
- 出勤工時計算
- attendance canonical duration

一句話：

> `leave` 管的是「請假」，不是「出勤打卡」。

---

## 4. 常見相關檔案

- `api.py`
- `service.py`
- `repo.py`
- `models.py`
- `schemas.py`

---

## 5. 新功能應該放哪裡？

### 應放在 `leave`
- 新的請假狀態
- 審批規則
- 請假列表查詢
- 請假 feature gate

### 不應放在 `leave`
- attendance 遲到/早退規則
- 排班模板
- 公司管理

---

## 6. 最容易寫錯的地方

1. 把 attendance 的異常判定硬塞到 leave 裡
2. 把請假與排班耦合成單一模組
3. 改了請假流程卻沒同步確認 tenant / role / feature gate

---

## 7. 什麼情況一定要更新這份文件？

- 請假流程改了
- 審核規則改了
- feature gate 改了
- tenant isolation / scope 規則改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `leave`（請假）只管理請假流程與審批生命週期
- `leave` 不應反向改寫 `attendance`（出勤）核心語意
- 若未來需要較抽象的 `approvals`（審批）能力，應先釐清是否為共用引擎，不要直接把 `leave` 當成所有審批的母模組
- `leave` 與 `schedule`、`attendance` 可以互相參考背景資料，但不應混成單一業務邏輯層
