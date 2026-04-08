# tenants 模組 SDD

**模組名稱**：`tenants`  
**你可以把它理解成**：系統的「公司與租戶管理中心」  
**程式位置**：`backend/app/modules/tenants`

---

## 1. 這個模組是做什麼的？

`tenants` 管理的是「公司這個租戶單位」本身。

白話說：

- 公司資料在這裡管理
- 公司成員在這裡管理
- 功能開關（entitlements）也在這裡管理
- onboarding 也屬於這裡

---

## 2. 主要功能

### 2.1 Company CRUD
用途：建立與管理公司資料。

### 2.2 Members 管理
用途：管理公司內有哪些成員、成員的基本設定。

### 2.3 Onboarding
用途：處理公司開通或初始設定流程。

### 2.4 Feature Entitlements
用途：決定這家公司能不能用某些功能。

---

## 3. 模組邊界

### `tenants` 負責
- 公司資料
- 公司成員
- onboarding
- entitlements

### `tenants` 不負責
- 登入驗證本身 → `auth`
- 出勤規則 → `attendance`
- 請假流程 → `leave`

一句話：

> 只要是「公司這個租戶單位的設定」，優先看是不是應該放在 `tenants`。

---

## 4. 常見相關檔案

- `api.py`
- `api_members.py`
- `api_onboarding.py`
- `api_entitlements.py`
- `service.py`
- `repo.py`
- `models.py`

---

## 5. 新功能應該放哪裡？

### 應放在 `tenants`
- company CRUD
- members 管理
- entitlement 管理
- onboarding

### 不應放在 `tenants`
- login token 發放
- attendance policy
- leave approval lifecycle

---

## 6. 最容易寫錯的地方

1. 把 `tenants` 跟 `auth` 混在一起
2. 把公司管理頁面的所有東西都塞進 `tenants`，導致它變成超大 admin 雜物箱
3. entitlements 改了卻沒同步確認 feature gate 使用者

---

## 7. 什麼情況一定要更新這份文件？

- 公司資料模型改了
- members 管理改了
- onboarding 流程改了
- entitlement / feature 流程改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `tenants`（租戶 / 公司管理）是 company 治理的 source of truth（正式權威來源）
- `feature entitlements`（功能授權）應作為 `feature gate`（功能閘門）判定來源
- `membership`（成員關係）應和一般業務資料分開理解
- `company_id`（公司識別）不應由前端 request body 當成權威來源
