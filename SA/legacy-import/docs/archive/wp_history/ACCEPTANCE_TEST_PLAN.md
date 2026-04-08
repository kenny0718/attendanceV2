# ACCEPTANCE TEST PLAN

**建立日期：** 2026-03-11
**版本：** v1.0
**基於：** SYSTEM_GROUND_TRUTH.md（2026-03-11 驗證基線）
**性質：** 官方系統驗收測試計劃 — 每個 WP 完成後的驗證程序

---

## 1. Purpose

本文件定義每個開發階段（Work Package）完成後的測試與驗證策略。

所有測試必須在真實 PostgreSQL 環境下執行，不得使用 Mock DB 或 SQLite。

**驗收原則：**
- 測試通過才視為 WP 完成
- 每個 WP 必須通過對應的驗收測試才可進入下一個 WP
- 測試結果必須記錄至 WORKSTREAM_STATUS_LEDGER.md
- 不得使用 Mock DB 或 SQLite 替代真實 PostgreSQL

---

## 2. Environment Verification

**對應 WP：** WP-C1-01
**目標：** 驗證 runtime 基礎設施可正確運作

### 2.1 PostgreSQL 連線驗證

**步驟：**

| 步驟 | 指令 | 預期結果 |
|------|------|---------|
| 1. 確認 PostgreSQL 服務運行 | pg_isready -h localhost -p 5432 | accepting connections |
| 2. 確認資料庫存在 | psql -U attendance_user -d attendance_test -c \dt | 連線成功 |
| 3. 執行 migration | alembic upgrade head | 無錯誤輸出 |
| 4. 確認 migration head | alembic current | 008_wp_11_13 |
| 5. 確認 heads 唯一 | alembic heads | 只顯示一個 head |
| 6. 確認 table 數量 | psql -c \dt | 正確 table 清單 |

**預期 Table 清單（最少 15 個）：**

- tenants
- users
- roles
- permissions
- user_roles
- company_memberships
- notifications
- audit_logs
- audit_retention_policies
- attendance_policies
- attendance_sessions
- attendance_punches
- company_entitlements
- support_company_assignments
- allowed_locations

**成功條件：**
- [ ] alembic upgrade head 無錯誤
- [ ] alembic heads 只顯示 008_wp_11_13
- [ ] 所有 table 建立完成
- [ ] PostgreSQL localhost:5432 可連線

### 2.2 Test Suite 可執行性驗證

**步驟：**

| 步驟 | 指令 | 預期結果 |
|------|------|---------|
| 1. 執行 business invariant 測試 | pytest tests/attendance/test_business_invariant.py -v | 記錄通過率 |
| 2. 執行 model constraints 測試 | pytest tests/attendance/test_model_constraints.py -v | 記錄通過率 |
| 3. 執行 migration 測試 | pytest tests/attendance/test_migration.py -v | 記錄通過率 |

**備注：** WP-C1-01 階段以取得基線通過率為目標，不要求 100% 通過。
基線通過率記錄後，後續 WP 完成後必須達到或超越此基線。

---

## 3. Authentication Verification

**對應 WP：** WP-C1-02（attendance）、WP-C1-03（audit/backup/notifications）
**目標：** 驗證所有模組已完成 JWT 身份驗證遷移

### 3.1 JWT 登入流程驗證

**步驟：**

| 步驟 | 方法 | Endpoint | 預期結果 |
|------|------|---------|---------|
| 1. 使用有效憑證登入 | POST | /api/auth/login | 200 + JWT token |
| 2. 解析 JWT payload | - | - | user_id, company_id, role 正確 |
| 3. 確認 token 格式 | - | - | Bearer token，HS256，900s expiry |

### 3.2 Attendance Endpoint JWT 驗證

**來源：** SYSTEM_GROUND_TRUTH.md 1.3（待遷移 endpoint 清單）

| Endpoint | Method | 驗證項目 | 預期結果 |
|----------|--------|---------|---------|
| /v1/punch-in | POST | JWT Bearer token | 200 成功打卡 |
| /v1/punch-in | POST | 無 token | 401 Unauthorized |
| /v1/punch-in | POST | X-Company-ID header only | 401（header auth 已停用）|
| /v1/punch-out | POST | JWT Bearer token | 200 成功打卡 |
| /v1/punch-out | POST | 無 token | 401 Unauthorized |
| /v1/break-in | POST | JWT Bearer token | 200 |
| /v1/break-out | POST | JWT Bearer token | 200 |
| /v1/current-status | GET | JWT Bearer token | 200 + 狀態資料 |
| /v1/history | GET | JWT Bearer token | 200 + 歷史資料 |
| /v1/break-punches | GET | JWT Bearer token | 200 |
| /v1/punch/{id}/note | PATCH | JWT Bearer token | 200 |

### 3.3 Audit / Backup / Notifications JWT 驗證

| Endpoint | Method | 驗證項目 | 預期結果 |
|----------|--------|---------|---------|
| /api/audit/logs | GET | JWT Bearer token | 200 |
| /api/audit/logs | GET | 無 token | 401 |
| /api/audit/export | GET | JWT Bearer token | 200 |
| /api/audit/retention | GET | JWT Bearer token | 200 |
| /api/audit/retention | PUT | JWT Bearer token | 200 |
| /api/audit/purge | POST | JWT Bearer token | 200 |
| /api/backup/export | POST | JWT Bearer token | 200 |
| /api/backup/restore | POST | JWT Bearer token | 200 |
| /api/notifications | GET | JWT Bearer token | 200 |

### 3.4 Header Auth 已停用驗證

**關鍵測試：** 確認遷移後 X-Company-ID Header auth 不再有效

| 測試 | 方法 | Header | 預期結果 |
|------|------|--------|---------|
| Header-only 請求 | POST /v1/punch-in | X-Company-ID: xxx（無 JWT）| 401 |
| 無任何 auth | POST /v1/punch-in | 無 header | 401 |
| JWT + 正確 company | POST /v1/punch-in | Authorization: Bearer <token> | 200 |

**成功條件：**
- [ ] 所有 attendance endpoint 使用 JWT 可正常存取
- [ ] 無 JWT 的請求一律回傳 401
- [ ] 僅使用 X-Company-ID Header 的請求回傳 401
- [ ] audit / backup / notifications 同上

---

## 4. Regression Tests

**對應 WP：** WP-C1-04
**目標：** 8 個核心業務邏輯回歸測試全部通過

**現況（SYSTEM_GROUND_TRUTH.md V-08）：** 只有 Test 8 骨架，Test 1-7 未實作。

### 4.1 必要回歸測試清單

| Test # | 名稱 | 業務邏輯驗證重點 | 狀態 |
|--------|------|----------------|------|
| Test 1 | 遲到計算 | 員工超過政策規定上班時間打卡，系統正確標記遲到 | NOT_IMPLEMENTED |
| Test 2 | 早退計算 | 員工在政策規定下班時間前打卡下班，系統正確標記早退 | NOT_IMPLEMENTED |
| Test 3 | 加班計算 | 員工超過政策規定下班時間打卡，系統正確計算加班時數 | NOT_IMPLEMENTED |
| Test 4 | 待審核排除 | 狀態為 PENDING_APPROVAL 的 session 不計入統計 | NOT_IMPLEMENTED |
| Test 5 | 跨日 session 處理 | 跨越午夜的工作 session 正確歸屬與計算 | NOT_IMPLEMENTED |
| Test 6 | 休息時間計算 | break_in/break_out 時間正確從工作時數中扣除 | NOT_IMPLEMENTED |
| Test 7 | Tenant 隔離 | 不同公司的打卡資料完全隔離，不相互影響 | NOT_IMPLEMENTED |
| Test 8 | 跨午夜歸屬 | 跨午夜的打卡記錄正確歸屬至開始日期 | SKELETON_ONLY |

### 4.2 執行方式

pytest tests/attendance/test_regression.py -v --tb=short

### 4.3 執行環境要求

- PostgreSQL localhost:5432 可連線
- attendance_test 資料庫已 migrate 至 HEAD
- JWT auth 已完成（WP-C1-02 完成後）
- 測試使用 JWT token，非 X-Company-ID header

**成功條件：**
- [ ] Test 1 PASS
- [ ] Test 2 PASS
- [ ] Test 3 PASS
- [ ] Test 4 PASS
- [ ] Test 5 PASS
- [ ] Test 6 PASS
- [ ] Test 7 PASS
- [ ] Test 8 PASS
- [ ] pytest 輸出 8/8 PASSED

---

## 5. Tenant Isolation Verification

**對應 WP：** WP-C1-05
**目標：** 驗證多租戶資料隔離在真實 PostgreSQL 查詢層正確運作

**現況（SYSTEM_GROUND_TRUTH.md V-09）：** test_tenant_isolation.py 使用 DummySession，非真實 DB。

### 5.1 Tenant Isolation 測試場景

| 場景 | 驗證內容 | 預期結果 |
|------|---------|---------|
| Company A 存取自己的打卡記錄 | GET /v1/history（Company A JWT）| 只返回 Company A 資料 |
| Company B 存取自己的打卡記錄 | GET /v1/history（Company B JWT）| 只返回 Company B 資料 |
| Company A 嘗試存取 Company B 資料 | 直接 DB 查詢 company_id 篩選 | 返回空集合或 403 |
| Company A 打卡不影響 Company B | 同時打卡操作 | 各自獨立，不互相干擾 |
| Audit logs 隔離 | Company A 的 audit logs | 不含 Company B 資料 |
| Notifications 隔離 | Company A 的通知 | 不含 Company B 通知 |

### 5.2 執行方式

pytest tests/attendance/test_tenant_isolation.py -v

**執行環境要求：**
- 測試使用真實 PostgreSQL session（非 DummySession）
- 測試資料庫中預先建立 Company A 和 Company B 測試資料

**成功條件：**
- [ ] 全部 9 個（或更多）tenant isolation 測試 PASS
- [ ] 跨 company_id 資料存取確認被拒絕
- [ ] DummySession 已完全替換為真實 PostgreSQL session
- [ ] pytest 輸出顯示 PostgreSQL 連線（非 mock）

---

## 6. Location Policy Verification

**對應 WP：** WP-C2-01
**目標：** 驗證所有打卡動作（punch_in/out、break_in/out）均套用 Location Policy

**現況（SYSTEM_GROUND_TRUTH.md V-05, V-06）：**
目前只有 break_out 有條件式 location policy check（L445-461），
punch_in / punch_out / break_in 均無 location policy 驗證。

### 6.1 Location Policy 測試場景

| 場景 | 打卡動作 | GPS 位置 | 預期結果 |
|------|---------|---------|---------|
| 在允許範圍內打卡 | punch_in | 在 allowed_location 半徑內 | 200 打卡成功 |
| 在允許範圍內打卡 | punch_out | 在 allowed_location 半徑內 | 200 打卡成功 |
| 在允許範圍內打卡 | break_in | 在 allowed_location 半徑內 | 200 打卡成功 |
| 在允許範圍內打卡 | break_out | 在 allowed_location 半徑內 | 200 打卡成功 |
| 在允許範圍外打卡 | punch_in | 在 allowed_location 半徑外 | 403 位置不符 |
| 在允許範圍外打卡 | punch_out | 在 allowed_location 半徑外 | 403 位置不符 |
| 在允許範圍外打卡 | break_in | 在 allowed_location 半徑外 | 403 位置不符 |
| 在允許範圍外打卡 | break_out | 在 allowed_location 半徑外 | 403 位置不符 |
| 無地點政策設定 | punch_in | 任意位置 | 200（無限制）|
| 無地點政策設定 | punch_out | 任意位置 | 200（無限制）|
| 無地點政策設定 | break_in | 任意位置 | 200（無限制）|
| 無地點政策設定 | break_out | 任意位置 | 200（無限制）|

### 6.2 GPS 計算驗證（Haversine）

**來源：** attendance/gps_utils.py calculate_distance()

| 測試 | 座標 | 半徑設定 | 預期結果 |
|------|------|---------|---------|
| 距離計算準確性 | 已知兩點座標 | N/A | 與標準 Haversine 計算結果一致 |
| 邊界值：剛好在邊界上 | distance == radius | radius | 允許（含邊界）|
| 邊界值：剛好超出邊界 | distance > radius | radius | 拒絕 |

**成功條件：**
- [ ] punch_in 有 location policy 檢查
- [ ] punch_out 有 location policy 檢查
- [ ] break_in 有 location policy 檢查
- [ ] break_out 有強制 location policy 檢查（非條件式）
- [ ] 所有場景測試通過

---

## 7. API Stability Tests

**目標：** 驗證核心 API endpoint 的請求/回應 schema 穩定

### 7.1 Attendance 核心 Endpoint Schema 驗證

**punch_in（POST /api/v1/punch-in）**

請求 Schema：
- timestamp（required）：ISO 8601 格式
- location（optional）：{latitude, longitude}
- note（optional）：string

回應 Schema（200）：
- session_id：UUID
- status：ACTIVE
- punch_in_time：ISO 8601

| 測試 | 輸入 | 預期回應 |
|------|------|---------|
| 正常打卡 | 有效 JWT + timestamp | 200 + session_id |
| 重複打卡 | 已有 ACTIVE session | 409 Conflict |
| 缺少 timestamp | 無 timestamp | 422 Validation Error |
| 無效 JWT | 過期 token | 401 Unauthorized |

**punch_out（POST /api/v1/punch-out）**

| 測試 | 輸入 | 預期回應 |
|------|------|---------|
| 正常打卡下班 | 有效 JWT + ACTIVE session | 200 + 計算工時 |
| 無 ACTIVE session | 無進行中 session | 404 / 400 |
| 無效 JWT | 過期 token | 401 Unauthorized |

**break_in（POST /api/v1/break-in）**

| 測試 | 輸入 | 預期回應 |
|------|------|---------|
| 正常開始休息 | 有效 JWT + ACTIVE session | 200 |
| 無 ACTIVE session | 未打卡 | 400 |

**break_out（POST /api/v1/break-out）**

| 測試 | 輸入 | 預期回應 |
|------|------|---------|
| 正常結束休息 | 有效 JWT + BREAK session | 200 |
| 在範圍外（location policy 啟用）| 有效 JWT + 錯誤位置 | 403 |

### 7.2 Admin Location Endpoint Schema 驗證

**來源：** SYSTEM_GROUND_TRUTH.md 2.1（RBAC 缺口待修復）

| Endpoint | 測試 | 預期結果 |
|----------|------|---------|
| POST /admin/allowed-locations | 管理員 JWT | 201 建立成功 |
| POST /admin/allowed-locations | 普通員工 JWT | 403 Forbidden |
| PUT /admin/allowed-locations/{id} | 管理員 JWT | 200 更新成功 |
| PUT /admin/allowed-locations/{id} | 普通員工 JWT | 403 Forbidden |
| DELETE /admin/allowed-locations/{id} | 管理員 JWT | 200 刪除成功 |
| DELETE /admin/allowed-locations/{id} | 普通員工 JWT | 403 Forbidden |
| GET /admin/allowed-locations | 任何有效 JWT | 200 列表 |

**成功條件：**
- [ ] 所有 punch_in / punch_out / break_in / break_out 測試通過
- [ ] admin_location RBAC 測試通過（管理員/員工角色正確區分）
- [ ] 錯誤回應碼正確（401/403/404/409/422）
- [ ] 回應 schema 符合預期格式

---

## 8. Frontend End-to-End Tests

**對應 WP：** WP-11-13 Manual QA（BLOCKED，需真實瀏覽器 + PostgreSQL 環境）
**目標：** 驗證前端操作與後端 API 的完整整合

**現況（SYSTEM_GROUND_TRUTH.md V-12）：**
目前有效前端路由僅 2 個（/ 和 /login）。
Admin UI、Reporting UI、Leave/Approval UI 均不存在。

### 8.1 Login 流程

| 步驟 | 操作 | 預期結果 |
|------|------|---------|
| 1 | 開啟 /login 頁面 | Login 表單顯示 |
| 2 | 輸入有效帳號密碼 | 成功登入，導向 / |
| 3 | 確認 localStorage/token | JWT token 已存儲 |
| 4 | 重新整理頁面 | 維持登入狀態（token 有效）|
| 5 | 輸入無效帳號密碼 | 顯示錯誤訊息，不導向 |
| 6 | token 過期後操作 | 自動導向 /login |

### 8.2 Punch 動作

| 步驟 | 操作 | 預期結果 |
|------|------|---------|
| 1 | 點擊打卡上班 | 呼叫 POST /v1/punch-in，顯示成功 |
| 2 | 確認狀態更新 | 畫面顯示 ACTIVE 狀態 |
| 3 | 點擊打卡下班 | 呼叫 POST /v1/punch-out，顯示成功 |
| 4 | 確認狀態更新 | 畫面顯示 COMPLETED 狀態 |
| 5 | 重複打卡上班 | 顯示錯誤（已有進行中 session）|

### 8.3 Location Capture

| 步驟 | 操作 | 預期結果 |
|------|------|---------|
| 1 | 打卡時請求 GPS 權限 | 瀏覽器顯示位置請求彈窗 |
| 2 | 允許位置存取 | GPS 座標傳送至後端 |
| 3 | 拒絕位置存取 | 適當錯誤處理（非崩潰）|
| 4 | Location Policy 不符 | 顯示 403 位置錯誤訊息 |
| 5 | Location Policy 符合 | 打卡成功 |

### 8.4 Break Tracking

| 步驟 | 操作 | 預期結果 |
|------|------|---------|
| 1 | 打卡上班後點擊休息 | 呼叫 POST /v1/break-in |
| 2 | 確認休息狀態 | 畫面顯示 ON_BREAK 狀態 |
| 3 | 點擊結束休息 | 呼叫 POST /v1/break-out |
| 4 | 確認狀態回復 | 畫面顯示 ACTIVE 狀態 |
| 5 | break-out 含 GPS 驗證 | GPS 座標正確傳送，location policy 執行 |

### 8.5 Manual QA 執行環境

**必要條件：**
- 真實瀏覽器（Chrome / Firefox，支援 Geolocation API）
- PostgreSQL localhost:5432 可連線且已 migrate
- JWT auth 已完成（WP-C1-02 後）
- 前端 dev server 運行中

**成功條件：**
- [ ] Login 流程完整通過
- [ ] Punch in/out 操作成功
- [ ] GPS 位置擷取正常
- [ ] Location Policy 403 錯誤正確顯示
- [ ] Break in/out 操作成功

---

## 9. Release Criteria

**系統進入下一階段的條件**

### 9.1 Phase 1 Release Criteria（進入 Phase 2 的條件）

| 條件 | 對應 WP | 驗收方式 | 狀態 |
|------|---------|---------|------|
| PostgreSQL 環境可用，migration HEAD 正確 | WP-C1-01 | Section 2 驗收通過 | ⬜ |
| 所有 P0 安全問題解決（24 個 endpoint 使用 JWT）| WP-C1-02/03 | Section 3 驗收通過 | ⬜ |
| 8 個回歸測試全部 PASS | WP-C1-04 | Section 4 驗收通過 | ⬜ |
| Tenant Isolation 在真實 DB 驗證 | WP-C1-05 | Section 5 驗收通過 | ⬜ |
| Feature Gate 套用至所有核心 API | WP-C1-06 | 功能分級測試通過 | ⬜ |
| API 文件完整 | WP-C1-07 | 文件審查通過 | ⬜ |
| admin_location RBAC 實作 | WP-C1-02 | Section 7.2 驗收通過 | ⬜ |

**Phase 1 Release 決策：** 以上所有條件達成後，Gate 5 宣告完成。

### 9.2 Phase 2 Release Criteria（進入 Phase 3 的條件）

| 條件 | 對應 WP | 驗收方式 | 狀態 |
|------|---------|---------|------|
| 所有打卡動作套用 Location Policy | WP-C2-01 | Section 6 驗收通過 | ⬜ |
| Reporting Backend API 可用 | WP-C2-02 | API 測試通過 | ⬜ |
| WP-11-13 Manual QA 通過 | Manual QA | Section 8 驗收通過 | ⬜ |

### 9.3 不可接受的 Release 狀態

- 任何 P0 安全問題未解決
- 回歸測試有任何 FAIL 或 SKIP（未說明原因）
- 測試使用 Mock DB（非真實 PostgreSQL）
- Header auth 仍可存取任何 API endpoint
- Tenant Isolation 未在真實 DB 驗證

---

## 10. Test Execution Record Template

每次執行驗收測試後，必須填寫以下記錄並更新至 WORKSTREAM_STATUS_LEDGER.md：

**執行日期：** YYYY-MM-DD
**對應 WP：** WP-[ID]
**執行環境：**
- PostgreSQL 版本：
- Python 版本：
- pytest 版本：

**測試結果摘要：**

| 測試群組 | 總數 | PASS | FAIL | SKIP | 備注 |
|---------|------|------|------|------|------|
| Environment Verification | - | - | - | - | |
| Authentication Verification | - | - | - | - | |
| Regression Tests | 8 | - | - | - | |
| Tenant Isolation | 9+ | - | - | - | |
| Location Policy | - | - | - | - | |
| API Stability | - | - | - | - | |

**結論：** PASS / FAIL
**阻塞項目（若有）：** 
**下一步：** 

---

## 11. Known Gaps（截至 2026-03-11 基線）

以下為目前已知的測試缺口，需在對應 WP 中修復：

| 缺口 ID | 描述 | 影響 | 修復 WP |
|--------|------|------|--------|
| GAP-01 | test_regression.py Test 1-7 未實作 | 無法執行 8 個回歸測試 | WP-C1-04 |
| GAP-02 | test_tenant_isolation.py 使用 DummySession | Tenant Isolation 未真實驗證 | WP-C1-05 |
| GAP-03 | audit/backup/notifications 測試使用 SQLite | 無法驗證 PostgreSQL 特有行為 | WP-C1-03 |
| GAP-04 | customer_service 無任何測試 | 完全無測試覆蓋 | WP-C1-03 |
| GAP-05 | punch_in/out/break_in 無 location policy | 3/4 打卡動作無位置驗證 | WP-C2-01 |
| GAP-06 | Feature Gate 完全未套用 | SaaS 功能分級無效 | WP-C1-06 |
| GAP-07 | admin_location 無 RBAC | 任何員工可管理地點政策 | WP-C1-02 |
| GAP-08 | WP-11-13 Manual QA BLOCKED | GPS 端對端流程未驗證 | WP-C2-01 後 |

---

*本文件由系統驗證基線建立後生成（2026-03-11）。*
*權威依據：docs/SYSTEM_GROUND_TRUTH.md。*
