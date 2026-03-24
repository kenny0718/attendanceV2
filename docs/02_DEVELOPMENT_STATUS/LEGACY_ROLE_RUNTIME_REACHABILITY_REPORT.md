# LEGACY_ROLE_RUNTIME_REACHABILITY_REPORT

- 日期：2026-03-24
- 任務性質：Audit Only（僅檢查 runtime/token/flow 可達性）
- 範圍：`/opt/attendance-system/backend/app`
- Legacy roles：`manager`、`admin`、`hr`、`system_admin`

---

## 1. Summary

本次只做靜態程式流程追蹤與既有 live DB 盤點結果交叉判讀（不修改程式、不修改資料）。

結論重點：

1. Legacy mapping 在 runtime 仍存在，且屬於 auth-critical（尤其 `core/dependencies.py` 的 `_map_role_id_to_user_role`）。
2. `manager` 在目前系統中屬於**可明確達成（Definitely reachable）**：
   - 仍在 `roles` 主表（前次 live DB 報告）
   - 成員建立 API 允許建立 `manager` membership
   - attendance reporting 仍有 `manager` 分支
3. `admin`、`hr`：
   - mapping 與 attendance 分支仍在
   - 但目前 live DB（前次盤點）無主檔/assignment，且現行 API 不易再產生
   - 判定為「**Mapping exists but currently unreachable**」（以目前已證據為準）
4. `system_admin`：
   - 仍被映射為 `SUPER_ADMIN`
   - 若有有效 token 可直接進 super_admin 平台路徑
   - 但現行 login 流程無法直接產生（未證明有現行簽發路徑）
   - 判定「**Possibly reachable but unproven**」

---

## 2. Legacy role mapping inventory（Phase 1）

### 2.1 `backend/app/core/dependencies.py`

#### A) `_map_role_id_to_user_role(role_id)`（auth-critical）
- `system_admin -> UserRole.SUPER_ADMIN`
- `admin -> UserRole.COMPANY_USER`
- `manager -> UserRole.COMPANY_USER`
- `hr -> UserRole.COMPANY_USER`
- 未知 role 預設 `COMPANY_USER`（保守 fallback）

影響：
- 這是 token claim `role_id` 進入平台層授權路徑的關鍵入口，屬 auth-critical。

#### B) `get_current_actor()`（auth-critical）
- 先用 JWT `role_id` 做平台角色映射
- 若是 `COMPANY_USER`：會再從 membership 取 `active_role_id`
- 若是 `SUPER_ADMIN`：不查 membership，直接放行 super_admin 平台身分路徑

影響：
- `system_admin` 在這裡會被直接當成 super_admin 平台角色處理。

### 2.2 `backend/app/core/scope.py`

#### A) `Actor.is_admin()`（auth-critical）
- 現行 admin 判斷僅接受：`company_admin`、`hr_manager`
- 註解已明確標示 legacy `admin/manager/hr` 已移除

影響：
- 多數走 `assert_admin_scope()` 的路由不再接受 legacy 角色作為管理員。

### 2.3 `backend/app/modules/attendance/api.py`

#### A) `GET /api/v1/attendance/sessions` 分支（auth-critical）
- 仍有 legacy 判斷：`is_admin = actor.active_role_id in ("admin", "manager", "hr")`
- 若命中可查詢他人 sessions

影響：
- 這是目前仍直接使用 legacy role 值做授權決策的實際分支。

### 2.4 `backend/app/modules/backup/api.py`

#### A) docstring（描述性）
- 註解仍寫「admin / manager / hr 可用」

#### B) 真正授權路徑（auth-critical）
- 實際走 `assert_admin_scope(actor, company_id, db)`
- 該函式最終依賴 `Actor.is_admin()`，只認 `company_admin` / `hr_manager`

影響：
- backup/restore 的 legacy 敘述與實際授權邏輯不一致；runtime 以 `is_admin()` 為準。

### 2.5 `backend/app/modules/auth/service.py`

#### A) login token 產生（auth-critical）
- JWT `role_id` 直接來自 `membership.role_id`

影響：
- 只要 membership 有 legacy 值，token 就會帶 legacy 值；是否能進一步取得權限由後續 dependency/scope 分支決定。

### 2.6 `backend/app/modules/tenants/api_members.py`

#### A) 建立成員 role 驗證（auth-critical）
- 建立成員時會查 `roles.id == request.role_id`，不存在即 `422 INVALID_ROLE`

影響：
- 能否新增某 legacy role，取決於 `roles` 主表是否仍保留該值。

### 2.7 backup import/restore data replay

#### A) `backup/exporter.py` 與 `backup/importer.py`
- 目前只處理 `notifications`、`attendance_records`
- 不處理 `users` / `user_company_memberships` / `roles`

影響：
- backup restore 目前不會重播/重建 legacy membership role 值。

---

## 3. Runtime reachability matrix（Phase 2 + Phase 3）

| Legacy role | JWT/Token mapping | Dependency/Actor path | Attendance branch | Backup/Restore/Import flow | 分類 |
|---|---|---|---|---|---|
| `manager` | 會映射為 `COMPANY_USER` | `active_role_id` 可來自 membership | `active_role_id in (admin, manager, hr)` 可命中 | backup restore 不會重播 membership，但可經成員建立流程新增 | **Definitely reachable in runtime** |
| `admin` | 會映射為 `COMPANY_USER` | 需 membership 才會形成有效 `active_role_id` | 有 `admin` 分支，但需 `active_role_id=admin` 才能命中 | backup restore 不會重播 membership；現行 roles 主表也無 `admin` | **Mapping exists but currently unreachable** |
| `hr` | 會映射為 `COMPANY_USER` | 同上 | 有 `hr` 分支，但需 `active_role_id=hr` | backup restore 不會重播 membership；現行 roles 主表也無 `hr` | **Mapping exists but currently unreachable** |
| `system_admin` | 直接映射 `SUPER_ADMIN` | 走 super_admin 平台路徑（不靠 membership） | 非 attendance 的 legacy 判斷主軸 | backup/import 無直接關聯 | **Possibly reachable but unproven** |

---

## 4. Token / auth impact

1. 現行 login token 的 `role_id` 來源是 `membership.role_id`。
2. `manager`：
   - 因仍在 `roles` 主表（前次 live DB 報告），理論上可被建立成 membership，並由 login 發出 `role_id=manager` token。
3. `admin` / `hr`：
   - 前次 live DB 報告顯示不在 `roles` 主表，且 assignment 無存量。
   - 在現行 API 流程下，缺乏可驗證的新增來源。
4. `system_admin`：
   - 雖然 login 常規流程無已證明簽發來源，但 runtime mapping 仍接受並升為 `SUPER_ADMIN`。
   - 因此屬安全敏感保留點（不能視為純註解）。

---

## 5. Flow impact（attendance / import / restore / backup）

### 5.1 Attendance
- `sessions` 報表端點仍有 legacy `admin/manager/hr` 授權分支，屬實際 runtime 分支。
- 因此 legacy mapping 一旦有對應 `active_role_id`，會改變可查詢範圍（可查他人）。

### 5.2 Backup / Restore
- backup API 實際授權依 `assert_admin_scope`，不採 legacy `admin/manager/hr`。
- 目前 importer/exporter 不含 membership/roles，不會從備份重建 legacy role assignment。

### 5.3 Import / replay 類路徑
- 在目前程式中未見可將 legacy role 值大量回灌到 membership 的匯入流程。
- 故此來源目前為「未證明」。

---

## 6. Unsafe-to-remove / Maybe-safe / Likely-safe 判斷

### 6.1 Unsafe to remove（現在移除風險高）
1. `manager`
   - 原因：可由現行流程形成（roles 主表存在 + create_member role 驗證可通過 + attendance 分支會用到）
   - 結論：現在移除對應相容邏輯有風險。

2. `system_admin` mapping（`system_admin -> SUPER_ADMIN`）
   - 原因：屬 auth-critical mapping，若存在既有 token/外部簽發場景，會直接影響平台層權限
   - 結論：在未完成 token 簽發來源與歷史 token 失效策略驗證前，不建議直接刪。

### 6.2 Maybe safe after more checks
1. `admin`
2. `hr`

共同原因：
- mapping 與 attendance 分支雖在，但目前 live DB（前報告）無主檔/assignment 證據，且現行建立流程看起來不再產生。
- 仍需補做：
  - 實際 token 抽樣（近期活躍 token 是否有 `admin/hr`）
  - 外部簽發或舊客戶端 token 相容性確認
  - 任何離線匯入流程是否能寫入 legacy membership

### 6.3 Likely safe（現階段無）
- 本次未找到可直接判為「現在就可安全刪除」的 legacy 角色相容點。

---

## 7. Cleanup readiness assessment

綜合本次 runtime/token/flow 證據：

- `manager`：未達清理就緒（仍可被 runtime 命中）。
- `system_admin`：未達清理就緒（auth-critical mapping 仍可被有效 token 命中，來源未完全排除）。
- `admin`、`hr`：接近候選，但目前只能列為「可能可清理」，尚未到「可直接移除」。

整體判定：**尚未達到全面移除 legacy role 相容層的安全門檻**。

---

## 8. Recommended next step

1. 補一輪「真實 token/請求樣本」驗證（只讀）：
   - 抽查最近有效 token claim `role_id` 分佈（特別是 `manager/admin/hr/system_admin`）
2. 補一輪「外部簽發來源」確認：
   - 是否存在非 login API 的 JWT 簽發路徑
3. 若要分階段治理，建議順序：
   - 先處理 `admin/hr`（在完成 token/外部來源驗證後）
   - 再處理 `manager`（需先決定 roles 主表與 attendance 分支策略）
   - `system_admin` 最後處理（需先有完整 token 失效與回滾方案）

---

## 9. Audit constraints confirmation

- 未修改程式碼
- 未修改資料庫資料
- 未建立 migration
- 未刪除任何檔案
- 本次僅新增報告檔案
