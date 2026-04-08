# customer_service 模組 SDD

**模組名稱**：`customer_service`  
**你可以把它理解成**：系統的「客服跨公司支援範圍模組」  
**程式位置**：`backend/app/modules/customer_service`

---

## 1. 這個模組是做什麼的？

`customer_service` 負責管理客服人員可以支援哪些公司。

白話說：

- 某個客服可以被指派去支援 A 公司
- 另一個客服可以支援 B 公司
- 這個模組就是管理這種支援範圍

---

## 2. 主要功能

### 2.1 Assigned Companies 查詢
用途：查客服目前被分配到哪些公司。

### 2.2 Support Assignment 建立
用途：把客服綁定到可支援的公司。

### 2.3 Support Assignment 移除
用途：取消客服對某公司的支援範圍。

---

## 3. 模組邊界

### `customer_service` 負責
- 客服可操作公司範圍
- support assignment 關係

### `customer_service` 不負責
- 一般 company admin 流程
- attendance / leave 業務
- tenant 主資料管理

一句話：

> 它管的是「客服可以碰哪些公司」，不是「公司自己的內部管理」。

---

## 4. 常見相關檔案

- `api.py`
- `service.py`
- `repo.py`
- `models.py`

---

## 5. 新功能應該放哪裡？

### 應放在 `customer_service`
- support assignment
- 客服 scope 驗證規則
- 客服支援公司列表

### 不應放在 `customer_service`
- tenant CRUD → `tenants`
- auth login → `auth`
- attendance 打卡 → `attendance`

---

## 6. 最容易寫錯的地方

1. 把 `customer_service` 跟 company admin 混為一談
2. 把客服 scope 規則散落到其他模組內
3. 沒有明確區分平台角色與公司內角色

---

## 7. 什麼情況一定要更新這份文件？

- support assignment 流程改了
- 客服 scope 驗證方式改了
- 角色模型改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `customer_service`（客服）是平台角色，不是一般公司內角色
- 客服只能操作被指派公司，不是全域萬能角色
- `customer_service` 的核心責任是 assignment scope（指派操作範圍），不應吞掉 `tenants` 或 `auth` 的主責任
- 與客服權限有關的高風險操作，應可被 `audit`（稽核）追溯
