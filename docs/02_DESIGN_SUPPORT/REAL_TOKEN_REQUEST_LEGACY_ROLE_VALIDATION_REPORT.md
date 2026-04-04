# REAL_TOKEN_REQUEST_LEGACY_ROLE_VALIDATION_REPORT

- 日期：2026-03-24
- 任務性質：Audit Only（真實 token / request 樣本驗證）
- 範圍：`/opt/attendance-system`
- Legacy roles：`manager`、`admin`、`hr`、`system_admin`

---

## 1. Summary

本次優先使用「真實 runtime 證據」驗證 legacy role 是否出現在 token / request context。

主要結論：

1. **真實樣本（backend.log）已確認的登入角色只有 `employee`**，未看到 legacy 角色登入成功紀錄。  
2. **無法直接取得 token 原文（JWT 字串）或 decode 後 claims 日誌**，因此無法對每筆真實 token 做逐一 claim 驗證。  
3. 以「目前 live DB + 真實登入紀錄 + 現行簽發程式」交叉推論：
   - `admin` / `hr` / `system_admin` 目前沒有真實命中證據，且現況下難以由 live data 產生。
   - `manager` 目前雖無真實命中樣本，但因 `roles` 主表仍有 `manager`，仍屬可生成候選（需更多真實樣本證明是否真的被使用）。
4. `system_admin -> SUPER_ADMIN` 仍是 auth-critical 映射，雖未觀測到真實命中，仍不能直接判定可安全移除。

---

## 2. Token issuance / actor construction flow（Phase 1）

### 2.1 Token issuance
- 檔案：`backend/app/modules/auth/service.py`
- 關鍵：登入時 token claim 的 `role_id` 直接取 `membership.role_id`
- 關鍵程式：
  - `token_claims["role_id"] = membership.role_id`
  - `create_access_token(token_claims, expires_in=900)`

### 2.2 Token decode + actor build
- 檔案：`backend/app/core/dependencies.py`
- 流程：
  1. 從 Authorization 取 Bearer token
  2. `decode_access_token`
  3. 讀取 `payload.role_id`
  4. `_map_role_id_to_user_role(role_id)` 做平台層映射
  5. 依平台角色與 membership/support assignment 生成 `Actor`

### 2.3 Legacy mapping / normalization 入口
- 檔案：`backend/app/core/dependencies.py`
- `_map_role_id_to_user_role` 仍接受：
  - `system_admin -> SUPER_ADMIN`
  - `admin -> COMPANY_USER`
  - `manager -> COMPANY_USER`
  - `hr -> COMPANY_USER`

### 2.4 Request-side role branch
- 檔案：`backend/app/modules/attendance/api.py`
- `sessions` 報表仍有 legacy 判斷：
  - `is_admin = actor.active_role_id in ("admin", "manager", "hr")`

---

## 3. Real evidence sources checked（Phase 2）

### 3.1 真實日誌樣本（已檢查）
- 來源：`/opt/attendance-system/backend.log`
- 觀測到 7 筆登入成功紀錄（`Login successful`）
- 7 筆 `role=` 全為 `employee`
- 範例行：
  - `8006`, `12796`, `22024`, `30956`, `31953`, `32434`, `33905`

### 3.2 日誌中的 token/actor 直接證據（已嘗試）
- 未找到可直接使用的：
  - JWT token 原文
  - token decode 後 claims 明文
  - `Actor created` 日誌樣本
  - `active_role_id=` runtime 日誌

### 3.3 近端真實來源（live DB，唯讀）
- `user_company_memberships.role_id`：`company_admin`(2), `employee`(1)
- 未出現：`manager` / `admin` / `hr` / `system_admin`
- `roles` 主表仍含 `manager`

> 本次未改任何資料；僅做唯讀查詢與日誌檢視。

---

## 4. Legacy role validation matrix（Phase 3）

| Legacy role | Found in real token/request sample? | Can current live data still generate it? | Runtime mapping still auth-critical? | 判定 |
|---|---|---|---|---|
| `manager` | NO（未在真實登入樣本中看到） | POSSIBLE（`roles` 仍有 `manager`，可作為 membership role 來源候選） | YES（attendance legacy 分支 + mapping 仍在） | maybe safe（未證明可直接清） |
| `admin` | NO | NO（目前 roles/master 與 membership 均無） | YES（mapping 與分支仍在） | maybe safe |
| `hr` | NO | NO（目前 roles/master 與 membership 均無） | YES（mapping 與分支仍在） | maybe safe |
| `system_admin` | NO | NO/POSSIBLE（live data 無；但若外部 token 帶入可被映射） | YES（直接映射 SUPER_ADMIN） | not yet provable（偏 unsafe） |

判讀補充：
- `Found in real token/request sample` 這欄以**實際可讀到的 runtime 證據**為準。  
- `Can current live data still generate it` 這欄以**目前 DB + 現行登入簽發路徑**為準。  

---

## 5. Confirmed real-sample hits

### 5.1 Confirmed
- 真實登入成功樣本中的角色：**僅 `employee`**（7/7）

### 5.2 Not found in real samples
- `manager`: 未命中
- `admin`: 未命中
- `hr`: 未命中
- `system_admin`: 未命中

---

## 6. Static-only / unproven paths

以下路徑目前無真實樣本可證明或反證，只能列為未證明：

1. `system_admin` 真實 token 命中
   - 程式映射存在，但無實際 token/claim 樣本。
2. `manager` 真實 request actor 命中
   - 程式分支存在，且主表仍有 `manager`；但缺乏真實 actor 日誌或請求樣本。
3. 外部簽發 token / service-to-service token
   - 本次未找到可用的真實樣本或可讀取路徑證據。

---

## 7. Cleanup readiness assessment

以本票「真實樣本」角度：

- 已證實：當前可見登入樣本沒有 legacy role（僅 `employee`）。
- 仍未證實：
  - `manager` 是否在其他真實請求中被使用
  - `system_admin` 是否有外部 token 命中

因此目前結論：

- `admin` / `hr`：**maybe safe**（但仍需補更多真實 token/request 樣本）
- `manager`：**maybe safe（偏保守）**，尚未達可直接清理的證據門檻
- `system_admin`：**not yet provable（偏 unsafe）**，因為是高權限映射點

整體：**尚不建議直接做全面 legacy cleanup**。

---

## 8. Recommended next step

1. 增加可觀測性（audit log）但不改授權邏輯：
   - 記錄 decode 後 `role_id`（脫敏）與 `active_role_id` 命中統計
2. 抽樣最近 N 天真實請求（若有 API gateway/access log）做角色分佈統計
3. 針對 `system_admin` 追加「簽發來源證據」：
   - 是否存在非 login API 的 token 來源
4. 蒐齊上述證據後再進下一張 cleanup 決策票

---

## 9. Constraints confirmation

- 未修改程式碼
- 未修改資料
- 未建立 migration
- 未刪除任何檔案
- 本次僅新增報告檔
