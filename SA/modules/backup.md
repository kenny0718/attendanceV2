# backup 模組 SDD

**模組名稱**：`backup`  
**你可以把它理解成**：系統的「公司級備份還原模組」  
**程式位置**：`backend/app/modules/backup`

---

## 1. 這個模組是做什麼的？

`backup` 專門處理公司級資料匯出與還原。

白話說：

- 針對某個 company 匯出資料
- 或把備份資料還原回某個 company 範圍

這類功能很敏感，因為它直接碰 tenant data。

---

## 2. 主要功能

### 2.1 Export Company Data
用途：匯出某個公司的資料。

### 2.2 Restore Company Data
用途：把資料還原到目標公司。

### 2.3 Tenant Consistency 驗證
用途：確保備份與還原不會破壞租戶隔離。

### 2.4 配合 Admin RBAC
用途：限制不是任何人都能做備份/還原。

---

## 3. 模組邊界

### `backup` 負責
- 資料匯出
- 資料還原
- 匯出/還原範圍驗證

### `backup` 不負責
- 一般業務流程
- attendance policy
- notifications 主流程

一句話：

> `backup` 是平台維運能力，不是一般業務功能。

---

## 4. 常見相關檔案

- `api.py`
- `service.py`
- `repo.py`
- `models.py`

---

## 5. 新功能應該放哪裡？

### 應放在 `backup`
- 匯出資料範圍調整
- 還原流程調整
- tenant consistency 驗證

### 不應放在 `backup`
- 稽核主查詢 → `audit`
- 公司管理 → `tenants`
- 身份驗證 → `auth`

---

## 6. 最容易寫錯的地方

1. 信任備份檔內原始 `company_id` 當成最終還原邊界
2. 忘記 tenant isolation 是第一級約束
3. 改了匯出/還原範圍卻沒同步 audit 與文件

---

## 7. 什麼情況一定要更新這份文件？

- 匯出/還原資料範圍改了
- 驗證規則改了
- RBAC 規則改了
- 與 audit 的關聯改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `backup / restore`（備份 / 還原）是 `SaaS` 核心治理能力之一
- 單公司 restore 不可污染其他公司資料
- 若備份資料混入其他 `company_id`，應 `fail fast`（立即失敗）
- `company consistency check`（公司一致性檢查）與 `FK closure check`（外鍵閉包檢查）應視為正式前置檢查，不是可有可無選項
