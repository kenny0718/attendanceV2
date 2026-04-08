# audit 模組 SDD

**模組名稱**：`audit`  
**你可以把它理解成**：系統的「稽核與追蹤模組」  
**程式位置**：`backend/app/modules/audit`

---

## 1. 這個模組是做什麼的？

`audit` 專門處理系統留下來的可追蹤紀錄。

白話說：

- 查系統紀錄
- 匯出紀錄
- 依保留政策清理舊資料

它的目的是讓你未來知道：

- 發生過什麼事
- 是誰做的
- 何時做的

---

## 2. 主要功能

### 2.1 Logs Query
用途：查 audit logs。

### 2.2 Export JSON / CSV
用途：把紀錄匯出供外部檢查。

### 2.3 Retention Policy
用途：控制資料保留時間。

### 2.4 Purge
用途：清除過期或不再保留的紀錄。

---

## 3. 模組邊界

### `audit` 負責
- 稽核資料
- 稽核查詢
- 稽核匯出
- 稽核保留與清理

### `audit` 不負責
- 一般業務決策
- 主要交易流程
- attendance / leave 主邏輯

一句話：

> `audit` 是治理模組，不是業務主流程模組。

---

## 4. 常見相關檔案

- `api.py`
- `service.py`
- `repo.py`
- `models.py`

---

## 5. 新功能應該放哪裡？

### 應放在 `audit`
- audit 查詢條件
- 匯出格式
- retention / purge 規則

### 不應放在 `audit`
- attendance 寫入主流程
- backup 還原主流程
- auth 登入邏輯

---

## 6. 最容易寫錯的地方

1. 用舊文件的 header-based tenant context 說法誤導實作
2. 把 audit 做成「任何事情都來這裡算」的雜物箱
3. 改了 RBAC 或 JWT 驗證卻沒同步文件

---

## 7. 什麼情況一定要更新這份文件？

- 匯出格式改了
- retention / purge 規則改了
- admin RBAC 改了
- JWT actor 驗證流程改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `audit`（稽核）必須承接高風險操作的追溯責任
- 至少應覆蓋：配對碼產生、密碼重設、裝置撤銷、可能影響 `company scope` 的設定變更、備份 / 還原等治理動作
- 稽核模組是治理模組，不是一般業務主流程模組
