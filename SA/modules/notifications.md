# notifications 模組 SDD

**模組名稱**：`notifications`  
**你可以把它理解成**：系統的「事件轉通知模組」  
**程式位置**：`backend/app/modules/notifications`

---

## 1. 這個模組是做什麼的？

`notifications` 不負責主業務決策，它負責把其他模組發出的事件轉成通知資料。

白話說：

- 某個模組完成一件事
- 發出事件
- `notifications` 收到後，把它存成通知紀錄
- 前端或使用者再去查通知

---

## 2. 主要功能

### 2.1 訂閱事件
用途：接收系統內事件。

### 2.2 落地通知資料
用途：把事件轉成通知紀錄保存。

### 2.3 提供通知查詢 API
用途：讓前端查通知資料。

### 2.4 目前主要事件
- `attendance.approved`

---

## 3. 模組邊界

### `notifications` 負責
- 事件消費
- 通知資料保存
- 通知查詢

### `notifications` 不負責
- 主業務是否成功
- attendance / leave / schedule 的核心決策
- 反向修改其他模組狀態

一句話：

> 它是「結果通知者」，不是「流程主導者」。

---

## 4. 常見相關檔案

- `api.py`
- `service.py`
- `repo.py`
- `models.py`
- 事件 subscriber 相關 wiring

---

## 5. 新功能應該放哪裡？

### 應放在 `notifications`
- 新事件訂閱者
- 通知格式調整
- 通知查詢 API

### 不應放在 `notifications`
- 出勤主流程控制
- 請假審批決策
- 直接修改 attendance 主資料

---

## 6. 最容易寫錯的地方

1. 把通知模組寫成主業務 orchestrator
2. 沒有事件就直接跨模組硬呼叫 repo
3. 改了通知 schema 卻沒同步處理舊資料或查詢契約

---

## 7. 什麼情況一定要更新這份文件？

- 新增/移除事件處理器
- 通知 schema 改了
- tenant isolation 規則改了
- 通知 API 契約改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `notifications`（通知）是事件 consumer，不是主業務決策者
- 優先透過事件匯流排承接跨模組結果，不應直接吞掉其他模組主責任
- 通知資料屬 read / delivery-oriented（查閱與傳遞導向）能力，不應反向修改 `attendance`、`leave`、`schedule` 主資料
- 若事件契約調整，應同步檢查 subscriber、通知 schema、查詢 API 與文件
