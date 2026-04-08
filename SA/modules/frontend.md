# frontend 模組 SDD

**模組名稱**：`frontend`  
**你可以把它理解成**：系統的「使用者操作介面」  
**程式位置**：`frontend/`

---

## 1. 這個模組是做什麼的？

前端是 Vue 3 SPA，負責讓使用者操作系統。

白話說：

- 顯示畫面
- 保存登入狀態
- 導頁
- 呼叫後端 API
- 做使用者體驗層的權限限制

但它不是最終安全邊界。

---

## 2. 主要功能

### 2.1 Auth Store 與 Session Restore
用途：保存 JWT、登入狀態、重新整理頁面後恢復 session。

### 2.2 Route Guard
用途：控制哪些角色可以進哪些頁。

### 2.3 API Client 包裝
用途：統一送 token、處理錯誤、呼叫後端。

### 2.4 頁面模組
目前主要包含：
- attendance
- reporting
- schedule
- admin
- leave

---

## 3. 主要區塊

- `src/api/`：API 封裝
- `src/stores/`：Pinia 狀態管理
- `src/router/`：路由與 route guard
- `src/views/`：頁面
- `src/components/`：共用元件

---

## 4. 模組邊界

### `frontend` 負責
- 畫面呈現
- 頁面流程
- 呼叫 API
- UX 層角色限制

### `frontend` 不負責
- 最終權限判定
- tenant isolation 權威驗證
- 核心業務規則最終決策

一句話：

> 前端可以幫忙擋畫面，但真正的安全與權限仍要靠後端。

---

## 5. 新功能應該放哪裡？

### 應放在 `frontend`
- 新頁面
- route guard
- API client 行為
- store 狀態流程

### 不應放在 `frontend`
- 最終 RBAC 規則
- attendance canonical semantic
- feature entitlement 真正授權邏輯

---

## 6. 最容易寫錯的地方

1. 以前端 localStorage 的角色當成最終權限依據
2. 前端偷偷複製一份後端規則，導致兩邊越來越不一致
3. API 契約改了卻沒同步改 store 與 view

---

## 7. 什麼情況一定要更新這份文件？

- route guard 改了
- 登入保存格式改了
- API client 改了
- 前端角色判斷改了
- 大型頁面結構改了

---

## 8. 已依目前 baseline 回寫的正式結論（2026-04-08）

- 前端不是最終安全邊界，最終權限、tenant isolation、feature gate 仍由後端 authoritative enforcement（權威判定）
- 前端可以做 `precheck`（預檢）與 UX 提示，但不能作為最終合法性依據
- 員工端 P0 重點是手機查看自己當月正式出勤紀錄
- `HR / 管理端` 報表應與員工端查閱視角分流，不應混成同一個前端使用情境
