# auth 模組 SDD

**模組名稱**：`auth`  
**你可以把它理解成**：整個系統的「登入入口」  
**程式位置**：`backend/app/modules/auth`

---

## 1. 這個模組是做什麼的？

`auth` 專門處理「你是誰、能不能登入、登入後要發什麼 token」。

白話說：

- 使用者輸入帳號密碼
- 系統檢查這個人能不能登入
- 如果可以，就發 JWT 給前端

它是**身分入口**，不是業務模組。

---

## 2. 主要功能

### 2.1 Login API
用途：讓使用者登入系統。

### 2.2 Membership 查詢
用途：確認這個 user 在哪個 company 裡有身份。

### 2.3 Role 查詢
用途：確認登入後應該帶什麼角色資訊。

### 2.4 Token claims 輸出
用途：決定 JWT 內要放哪些必要資訊。

---

## 3. 你應該怎麼理解它的邊界

### `auth` 負責
- 登入
- 驗證帳密
- 建立 JWT
- 提供身份相關基礎資訊

### `auth` 不負責
- 出勤規則
- 排班規則
- 請假流程
- 公司資料管理
- 報表聚合

一句話：

> `auth` 只處理「身份」，不處理「業務」。

---

## 4. 常見相關檔案

- `api.py`：登入 API 入口
- `service.py`：登入流程與驗證邏輯
- `repo.py`：查 user / membership / role
- `models.py`：資料模型
- `schemas.py`：request / response 格式

---

## 5. 新功能應該放哪裡？

### 應放在 `auth`
- 登入方式調整
- JWT claim 調整
- company + login_username 驗證
- 身份建立邏輯

### 不應放在 `auth`
- company entitlement 管理 → 應放 `tenants`
- 打卡 / 出勤 → 應放 `attendance`
- 請假 → 應放 `leave`

---

## 6. 最容易寫錯的地方

1. 把 `auth` 當成公司管理模組用
2. 把 role / scope 規則寫死在登入 API 裡
3. 改了 JWT claims 卻沒有同步更新依賴它的其他模組

---

## 7. 什麼情況一定要更新這份文件？

- 登入流程改了
- JWT claim 結構改了
- membership 驗證改了
- role 來源改了
- 登入 API 契約改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `auth`（身分驗證）回答的是「你是誰」
- `scope validation`（操作範圍驗證）回答的是「你能不能操作這家公司」
- `auth` 不應單獨決定所有 `company scope`（公司操作範圍）
- `platform-first identity`（平台優先身份）與 `membership`（成員關係）應分開理解
