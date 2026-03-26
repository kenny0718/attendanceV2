# Cursor Rule — Backend Safe Edit Rules (FastAPI / Multi-tenant)

## 適用範圍
所有 backend 程式碼：

- `backend/app/**/*.py`
- `backend/alembic/**/*.py`
- `backend/scripts/**/*.py`

特別高風險：
- `alembic/env.py`
- `app/core/*.py`（config / security / features）
- `app/modules/*/api.py`
- `app/modules/*/service.py`
- `app/modules/*/models.py`
- auth / JWT / dependency 相關檔案

---

# 🔴 核心原則（最高優先）

## 1. 強制 Patch-Style（禁止整檔重寫）
所有 Python 檔案修改必須：

- 採「最小差異修改（patch-style edit）」
- 禁止整檔覆蓋（full rewrite）
- 禁止先清空再重建
- 禁止重新生成整個檔案內容

若需要大改：
- 必須拆成多步驟
- 每步可驗證
- 不可一次重寫整個 module

---

## 2. 禁止在異常檔案上寫入
若檔案出現：

- 0 byte
- 明顯截斷
- import 區塊缺失
- class / function 結構不完整

👉 必須：

- 停止
- 回報
- 建議使用 git restore
- 禁止自行重建

---

## 3. 寫入安全機制（強制）
所有寫入必須：

1. 寫入 `.tmp`
2. 檢查大小（不可 0 byte）
3. rename 覆蓋
4. 重新讀取確認內容存在

任一步失敗 → **立即停止**

---

## 4. 禁止用對話內容覆蓋檔案
禁止：

- 用 ChatGPT / Cursor 對話中的程式碼覆蓋檔案
- 用「推測原本內容」重建檔案

必須以磁碟實際內容為準

---

# 🟡 FastAPI 結構安全規則

## 5. router 層不可重建
對 `api.py`：

允許：
- 新增 endpoint
- 修改單一 endpoint

禁止：
- 重寫整個 router
- 移除既有 endpoint
- 改 router prefix / tags

---

## 6. dependency / auth 不可破壞
特別保護：

- `get_actor_with_company`
- JWT actor flow
- role / permission 判斷

禁止：

- 改 dependency injection 行為
- 回退到 legacy header（X-Company-ID / X-User-ID）
- 修改 auth contract

---

## 7. service / repo 層限制
允許：

- 新增 function
- 修改單一邏輯

禁止：

- 重構整個 service
- 改 function signature（除非明確指定）
- 改資料流方向

---

## 8. models（ORM）限制
允許：

- 新增欄位（需對應 migration）

禁止：

- 刪除欄位
- 修改既有欄位型別
- 改 FK / relationship

除非：

- 有 migration
- 有明確 schema 票

---

# 🟠 Alembic / Migration 特別保護

## 9. env.py 絕對禁止風險操作
`backend/alembic/env.py`：

- 禁止整檔修改
- 禁止重建
- 禁止調整核心設定

只允許：
- 最小 import 修正（且需 audit）

---

## 10. migration 規則
允許：

- 新增 migration

禁止：

- 修改已存在 migration
- 重寫歷史 migration

---

# 🧠 Multi-tenant / JWT 規則（關鍵）

## 11. 不可破壞 Actor 模型
系統唯一權威來源：

- actor.active_company_id
- actor.active_role_id

禁止：

- 使用 request header 取代 actor
- 新增 X-Company-ID / X-User-ID 邏輯

---

## 12. 權限邏輯不可硬編碼

禁止：

```python
if role == "manager":
```

必須使用：

```python
actor.is_admin()
```
