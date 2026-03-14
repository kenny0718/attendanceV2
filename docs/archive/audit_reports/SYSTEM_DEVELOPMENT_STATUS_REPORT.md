# 系統開發狀態評估報告

> WARNING: SUPERSEDED IN PART
> 本報告部分內容已被 docs/SYSTEM_GROUND_TRUTH.md（2026-03-11）更新取代。
> 已知有誤的欄位：
> - backup auth 方式：本報告原標為 JWT，實際為 Header（X-Company-ID）
> - Header auth endpoint 數：原標 18 個，實際為 24 個（含 admin_location 5 個）
> 其他結論請以 docs/SYSTEM_GROUND_TRUTH.md 為準。

**產出日期：** 2026-03-10（重建於 2026-03-11）
**審計範圍：** 全系統（backend / frontend / docs）
**目的：** 進入下一個開發工作前的完整現況評估
**報告性質：** READ-ONLY 評估，不包含開發計畫或修改建議

---

## 1. 執行摘要

系統目前處於 Gate 5（SA Compliance + Auth Migration）進行中階段。
核心業務邏輯（打卡流程）已實作並可運作，但 auth 機制、測試覆蓋、Feature Gate
等關鍵架構元素尚未完成 SA 規範要求的標準。

**整體 SA 符合度估算：約 60-65%**

主要完成項目：
- 打卡核心流程（punch_in/out/break_in/break_out）
- Location Policy 基礎設施（break_out 端點）
- Migration chain（HEAD: 008_wp_11_13）
- Frontend 基本功能（2 個路由，打卡操作）
- Tenant 基礎設施（JWT auth，tenants/customer_service 模組）

主要未完成項目：
- 全部 attendance/audit/backup/notifications 模組仍使用 Header auth
- Feature Gate 未套用至任何生產 endpoint
- Location Policy 只在 break_out，未覆蓋其他打卡動作
- 回歸測試 7/8 未實作
- admin_location 寫入端點無 RBAC
- Admin UI 不存在

---

## 2. Backend 模組狀態

### 2.1 attendance 模組

**狀態：** 功能可運作，Auth 待遷移

| 功能 | 狀態 |
|------|------|
| punch_in | 實作完成 |
| punch_out | 實作完成 |
| break_in | 實作完成 |
| break_out | 實作完成 + Location Policy |
| punch note 編輯 | 實作完成 |
| history / current-status | 實作完成 |
| Auth 機制 | Header X-Company-ID（待遷移至 JWT）|
| Feature Gate | 未套用 |
| Location Policy 覆蓋 | 只有 break_out |
| RBAC | 無（Header 無身份驗證）|

**Endpoint 數：** 10 個（全部使用 Header auth）

### 2.2 admin_location 模組

**狀態：** 功能實作，RBAC 缺失

| Endpoint | Method | RBAC 狀態 |
|----------|--------|-----------|
| / (create) | POST | TODO: 驗證管理員權限（L47）— 無 RBAC |
| / (list) | GET | 無 RBAC |
| /{id} | GET | 無 RBAC |
| /{id} | PUT | TODO: 驗證管理員權限（L166）— 無 RBAC |
| /{id} | DELETE | TODO: 驗證管理員權限（L207）— 無 RBAC |

**Endpoint 數：** 5 個（全部使用 Header auth，寫入端點無 RBAC）

### 2.3 audit 模組

**狀態：** 功能可運作，Auth 待遷移

| 功能 | 狀態 |
|------|------|
| 查詢 audit logs | 實作完成 |
| 匯出 audit logs | 實作完成 |
| retention policy 管理 | 實作完成 |
| purge | 實作完成 |
| Auth 機制 | Header X-Company-ID（待遷移）|
| 測試 DB | SQLite :memory:（非 PostgreSQL）|

**Endpoint 數：** 5 個（全部使用 Header auth）

### 2.4 backup 模組

**狀態：** 功能可運作，Auth 待遷移

| 功能 | 狀態 |
|------|------|
| export | 實作完成 |
| restore | 實作完成 |
| Auth 機制 | Header X-Company-ID（非 JWT）|
| 測試 DB | SQLite :memory: |

**Endpoint 數：** 2 個（Header auth，非 JWT）

### 2.5 notifications 模組

**狀態：** 基本功能可運作

| 功能 | 狀態 |
|------|------|
| 查詢通知 | 實作完成 |
| Auth 機制 | Header X-Company-ID（待遷移）|
| 測試 DB | SQLite :memory: |

**Endpoint 數：** 1 個

### 2.6 tenants 模組

**狀態：** JWT auth 完整，功能完成

| 功能 | 狀態 |
|------|------|
| entitlements 查詢/更新 | 實作完成 |
| plan defaults 套用 | 實作完成 |
| Auth 機制 | JWT Bearer（get_current_actor）|
| Feature Gate 基礎設施 | 存在（clear_cache 整合）|
| 測試 | 38 個 test functions |

### 2.7 customer_service 模組

**狀態：** JWT auth 完整，測試覆蓋缺失

| 功能 | 狀態 |
|------|------|
| 查詢指派公司 | 實作完成 |
| 指派/取消指派公司 | 實作完成 |
| Auth 機制 | JWT Bearer（get_current_actor）|
| 測試 | 0 個（無任何測試檔）|

### 2.8 auth 模組

**狀態：** 可運作（login endpoint）

| 功能 | 狀態 |
|------|------|
| login | 實作完成，回傳 JWT |
| token type | bearer |
| expiry | 900s (HS256) |

---

## 3. Auth 機制分布

### 3.1 模組 Auth 對照表

| 模組 | Auth 方式 | Endpoint 數 | 備註 |
|------|-----------|------------|------|
| attendance | Header X-Company-ID | 10 | 待遷移至 JWT |
| admin_location | Header X-Company-ID | 5 | 待遷移至 JWT |
| audit | Header X-Company-ID | 5 | 待遷移至 JWT |
| backup | Header X-Company-ID | 2 | 待遷移至 JWT |
| notifications | Header X-Company-ID | 1 | 待遷移至 JWT |
| tenants | JWT Bearer | 3 | 完成 |
| customer_service | JWT Bearer | 3 | 完成 |
| auth | N/A (login) | 1 | 完成 |

Header auth endpoint 總計: 23 個（不含 backup placeholder）
JWT auth endpoint 總計: 6 個

### 3.2 Header auth 實作細節

所有 Header auth endpoint 透過 tenant_context.py 的 get_current_company_id() 函數讀取：
  x_company_id: str = Header(..., alias="X-Company-ID")

缺少 header 時回傳 400 Bad Request。
任何知道 company_id 的人可直接設置 header 存取所有 Header auth 端點。

---

## 4. Feature Gate 狀態

| 項目 | 狀態 |
|------|------|
| feature_service.py 基礎設施 | 存在 |
| feature_gate_demo.py 示範 | 存在（3 個 require_enabled 呼叫）|
| tenants/service.py 整合 | 存在（clear_cache）|
| 生產 endpoint 套用 | 未套用（0 個呼叫）|

結論: Feature Gate 實作但完全未啟用。

---

## 5. Location Policy 狀態

| 打卡動作 | Location Policy | 行號 |
|---------|----------------|------|
| punch_in | 無 | L109 |
| punch_out | 無 | L173 |
| break_in | 無 | L493 |
| break_out | 有（條件式）| L445 |

Location Policy Service 存在（location_policy_service.py），
but 只在 break_out 中被呼叫。

---

## 6. Migration 狀態

HEAD: 008_wp_11_13（CREATE TABLE allowed_locations）
Chain: 單一線性，無分叉
Runtime: NOT VERIFIED（未執行 alembic upgrade head）

完整 chain:
  004 -> 3532deda024c -> 005 -> 002 -> 003 -> 001b
  -> wp_11_04a_entitlements -> 006 -> 007_wp_11_10 -> 008_wp_11_13

---

## 7. 測試覆蓋狀態

### 7.1 Attendance 回歸測試

| Test | 狀態 |
|------|------|
| Test 1-7 | 不存在 |
| Test 8 | 骨架存在（test_regression.py L51），使用 Header auth |

### 7.2 模組測試 DB 類型

| 模組 | 測試 DB | 問題 |
|------|---------|------|
| attendance（部分）| PostgreSQL hardcoded | 需真實 DB 才能執行 |
| attendance（部分）| DummySession Mock | 不驗證真實 DB 層 |
| audit | SQLite :memory: | 無法驗證 PostgreSQL 特有行為 |
| backup | SQLite :memory: | 無法驗證 PostgreSQL 特有行為 |
| notifications | SQLite :memory: | 無法驗證 PostgreSQL 特有行為 |
| tenants | override_get_db | 可接受 |
| customer_service | 無測試 | 完全無覆蓋 |

### 7.3 測試函數總數（按模組）

| 模組 | test functions |
|------|---------------|
| attendance | ~115 |
| audit | 10 |
| backup | 10 |
| notifications | ~4 |
| tenants | 38 |
| core | 22 |
| customer_service | 0 |

---

## 8. Frontend 狀態

### 8.1 路由

| Path | Component | 狀態 |
|------|-----------|------|
| / | Home.vue | 存在 |
| /login | Login.vue | 存在 |

有效路由: 2 個。

### 8.2 功能完成度

| 功能 | 狀態 |
|------|------|
| Login / Auth store（JWT）| 完成 |
| 打卡操作（punch_in/out/break）| 完成 |
| Location Policy 403 處理 | 完成 |
| punch note 編輯 | 完成 |
| GPS break-out | 完成 |
| Admin UI | 不存在 |
| Reporting UI | 不存在 |
| Leave/Approval UI | 不存在 |

---

## 9. Gate 5 進度評估

Gate 5 要求: SA Compliance + Auth Migration

| 項目 | 要求 | 現況 | 狀態 |
|------|------|------|------|
| JWT auth（attendance）| 全部 endpoint | 0/10 | 未完成 |
| JWT auth（audit）| 全部 endpoint | 0/5 | 未完成 |
| JWT auth（backup）| 全部 endpoint | 0/2 | 未完成 |
| JWT auth（notifications）| 全部 endpoint | 0/1 | 未完成 |
| Feature Gate 套用 | 關鍵 endpoint | 0 | 未完成 |
| Location Policy（全打卡）| 4 個動作 | 1/4 | 部分完成 |
| admin_location RBAC | 寫入端點 | 0/3 | 未完成 |
| 回歸測試通過 | 8 個測試 | 0/8 通過 | 未完成 |
| Tenant Isolation 驗證 | 真實 DB | DummySession | 未完成 |

**Gate 5 整體: 未完成**

---

## 10. 下一步建議

建議先執行 WP-C1-01（PostgreSQL 環境建立 + Migration 驗證）：

1. 確認 postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test 可連線
2. 執行 alembic upgrade head，確認 migration chain 正常
3. 執行 test_business_invariant.py 和 test_model_constraints.py 取得真實通過率
4. 建立後續 auth 遷移（WP-C1-02）的基礎

後續優先順序：
  WP-C1-01（DB 環境）-> WP-C1-02（attendance JWT）-> WP-C1-03（批次 auth）-> WP-C1-04（回歸測試）

---

**本報告基於 2026-03-10 系統狀態，重建於 2026-03-11。**
**部分欄位已依 SYSTEM_GROUND_TRUTH.md 驗證結果修正。**
**權威依據請參考 docs/SYSTEM_GROUND_TRUTH.md（2026-03-11）。**
