# Reality Audit — Risk Report（風險報告）

**審查日期：** 2026-03-04  
**審查範圍：** `/opt/attendance-system` 完整 repo  
**風險分級：** P0 (阻斷) / P1 (嚴重) / P2 (中等)

---

## 風險分級定義

| 級別 | 定義 | 影響 |
|------|------|------|
| **P0** | 會阻止新環境啟動 / CI 爆炸 / 嚴重越權 | 立即修復 |
| **P1** | 資料漂移 / 測試不可信 / 維護成本爆炸 | 短期修復 |
| **P2** | 文件過時 / 命名混亂 / 小型技術債 | 中期改善 |

---

## P0 風險（阻斷級）

### P0-1：Migration Chain 狀態不明確

**Evidence：**
- 檔案：`backend/alembic/versions/001b_create_attendance_domain_v2_fixed.py`
- 檔案：`docs/MIGRATION_CHAIN_AUDIT_REPORT.md` (2026-03-04)
- 報告指出：001 (舊版) 有 table ordering bug，會導致 fresh DB rebuild 失敗
- 報告指出：001b (新版) 已修正，wp_11_04a 已指向 001b
- **但未驗證：** 實際 DB 的 `alembic_version` 是否正確

**Impact：**
- ❌ 無法確定 `alembic upgrade head` 在全新環境是否能執行
- ❌ 如果 DB 已有 001，再執行 001b 可能衝突（兩者都建立相同 tables）
- ❌ 新環境初始化可能失敗
- ❌ CI/CD pipeline 可能在 DB setup 階段爆炸

**Suggested Fix：**
1. 檢查實際 DB 狀態：
   ```bash
   psql -d attendance_db -c "SELECT * FROM alembic_version;"
   psql -d attendance_db -c "\dt attendance_*"
   ```
2. 如果 DB 已有 001：
   - 手動標記 001b 為已套用：`INSERT INTO alembic_version VALUES ('001b');`
   - 或：刪除 001 檔案，確保只有 001b
3. 如果 DB 沒有 001：
   - 直接執行 `alembic upgrade head`，應該會套用 001b
4. 在全新測試 DB 驗證 fresh rebuild：
   ```bash
   createdb attendance_test_fresh
   DATABASE_URL="postgresql://...attendance_test_fresh" alembic upgrade head
   ```

---

### P0-2：測試 DB 與 Migration 不一致

**Evidence：**
- 檔案：`docs/MIGRATION_CHAIN_AUDIT_REPORT.md`
- 報告第 2 節：「Test DB Used Manual SQL Instead of Alembic」
- 引用：「Migration wp_11_04a 被手動執行 via SQL，而非 alembic upgrade」
- 引用：「Migration 001 被跳過（有內部順序問題）」

**Impact：**
- ❌ 測試 DB 的 schema 可能與 migration 定義不一致
- ❌ `alembic current` 可能顯示錯誤狀態
- ❌ 測試結果不可信（測試的 schema 與生產不同）
- ❌ 未來 migration 可能因為 base 不一致而失敗

**Suggested Fix：**
1. 檢查測試 DB 的 alembic_version：
   ```sql
   SELECT * FROM alembic_version;
   ```
2. 如果缺少 wp_11_04a 或 001b：
   - 手動插入：`INSERT INTO alembic_version VALUES ('wp_11_04a_entitlements');`
3. 驗證 schema 一致性：
   ```bash
   # 比對測試 DB 與 migration 定義
   pg_dump -s -d attendance_test_db > test_schema.sql
   # 建立全新 DB 用 alembic
   createdb attendance_fresh
   alembic upgrade head
   pg_dump -s -d attendance_fresh > fresh_schema.sql
   diff test_schema.sql fresh_schema.sql
   ```
4. 如果不一致：重建測試 DB
   ```bash
   dropdb attendance_test_db
   createdb attendance_test_db
   alembic upgrade head
   ```

---

### P0-3：Auth 轉換未完成，兩種機制並存

**Evidence：**
- 檔案：`backend/app/modules/attendance/api.py` (line ~15)
- 檔案：`backend/app/modules/notifications/api.py` (line ~15)
- 檔案：`backend/app/modules/backup/api.py` (line ~15)
- 檔案：`backend/app/modules/audit/api.py` (line ~15)
- 這 4 個模組仍使用 `get_current_company_id(x_company_id: str = Header(..., alias="X-Company-ID"))`
- 檔案：`backend/app/modules/tenants/api.py` (line ~30)
- 檔案：`backend/app/modules/customer_service/api.py` (line ~25)
- 這 2 個模組使用 `get_current_actor(authorization: str = Header(...))`

**Impact：**
- ⚠️ 兩種認證機制並存，增加維護成本
- ⚠️ Header-based 無法驗證使用者身份（只有 company_id）
- ⚠️ Header-based 無法實作 RBAC（沒有 role 資訊）
- ⚠️ 可能造成安全漏洞（client 可任意指定 X-Company-ID）
- ⚠️ 新舊 API 行為不一致，容易混淆

**Suggested Fix：**
1. 決策：是否要統一為 JWT？
   - 如果是：執行 `docs/AUTH_TRANSITION_PLAN.md` 的剩餘批次
   - 如果否：明確文件化「哪些 API 用 Header，哪些用 JWT」
2. 如果統一為 JWT：
   - 修改 attendance/api.py：`actor: Actor = Depends(get_current_actor)`
   - 修改 notifications/api.py：同上
   - 修改 backup/api.py：同上
   - 修改 audit/api.py：同上
   - 更新所有測試：改用 JWT token
3. 如果保留 Header（暫時）：
   - 在 `tenant_context.py` 加強驗證：
     - 檢查 tenant 是否存在（已有，在 `get_current_company_id_with_membership`）
     - 檢查 tenant 是否 active（已有）
     - 但仍無法驗證使用者身份

---

## P1 風險（嚴重級）

### P1-1：Header-based Tenant Context 無使用者驗證

**Evidence：**
- 檔案：`backend/app/core/tenant_context.py`
- 函數：`get_current_company_id(x_company_id: str = Header(...))`
- 只驗證 tenant 存在 + active，不驗證使用者是否有權限存取該 tenant
- 函數：`get_current_company_id_with_membership(x_company_id, x_user_id, ...)`
- 有驗證 membership，但需要額外的 `X-User-ID` header

**Impact：**
- ⚠️ 使用 `get_current_company_id` 的 API（4 個模組）無使用者驗證
- ⚠️ Client 可以任意指定 `X-Company-ID`，只要該 tenant 存在且 active
- ⚠️ 無法實作「使用者只能存取所屬公司」的限制
- ⚠️ 可能造成越權存取（user A 存取 company B 的資料）

**Suggested Fix：**
1. 短期：改用 `get_current_company_id_with_membership`
   - 需要額外傳 `X-User-ID` header
   - 會驗證 user 是否有該 company 的 membership
2. 長期：統一改用 JWT + Actor
   - JWT 包含 user_id + company_memberships
   - `get_current_actor` 自動驗證
   - 不需要 client 傳 company_id（從 JWT 取得）

---

### P1-2：文件與實作不同步

**Evidence：**
- 檔案：`docs/STATUS_MATRIX.md` (2026-03-02)
- 內容：「auth 模組不存在」
- 實際：`backend/app/modules/auth/` 已存在，有 6 個檔案
- 檔案：`docs/DEVELOPMENT_ORDER.md`
- 內容：定義 17 個 WPs
- 檔案：`docs/GATE_PROGRESS_TRACKER.md`
- 內容：顯示 20 個 WPs，17/20 完成
- ⚠️ 矛盾：兩份文件對 WP 總數說法不同

**Impact：**
- ⚠️ 開發者無法信任文件
- ⚠️ 新成員 onboarding 困難（文件過時）
- ⚠️ 可能做出錯誤決策（基於過時資訊）
- ⚠️ 浪費時間查證「文件說的是真的嗎？」

**Suggested Fix：**
1. 更新 `STATUS_MATRIX.md`：
   - 標記 auth 模組為「✅ 已完成」
   - 更新 tenants 模組狀態
   - 更新 customer_service 模組狀態
2. 統一 WP 定義：
   - 決定是 17 個還是 20 個
   - 在 `DEVELOPMENT_ORDER.md` 補上缺少的 WPs
   - 或在 `GATE_PROGRESS_TRACKER.md` 說明額外的 3 個 WPs 是什麼
3. 建立文件更新流程：
   - 每次完成 WP 時，同步更新相關文件
   - 或：建立「文件審查」checklist

---

### P1-3：Migration 001 (舊版) 仍存在於 repo

**Evidence：**
- 檔案：`backend/alembic/versions/` 目錄
- 可能存在：`001_create_attendance_domain_v2.py` (舊版，有 bug)
- 已存在：`001b_create_attendance_domain_v2_fixed.py` (新版，已修正)
- 報告：`docs/MIGRATION_CHAIN_AUDIT_REPORT.md` 建議「deprecate 001」

**Impact：**
- ⚠️ 如果 001 仍存在，可能造成混淆
- ⚠️ 開發者可能不知道該用哪一個
- ⚠️ 如果 001 的 `down_revision` 仍指向 003，會與 001b 衝突（兩者都從 003 分支）
- ⚠️ Alembic 可能偵測到 multiple heads

**Suggested Fix：**
1. 檢查 001 是否存在：
   ```bash
   ls -la backend/alembic/versions/001_*.py
   ```
2. 如果存在：
   - 選項 A：刪除 001（如果確定沒有 DB 套用過）
   - 選項 B：修改 001 的 `down_revision = 'DEPRECATED'`（讓 alembic 跳過）
   - 選項 C：在 001 檔案開頭加註解：「DEPRECATED: Use 001b instead」
3. 驗證沒有 multiple heads：
   ```bash
   alembic heads
   # 應該只顯示一個 head: wp_11_04a_entitlements
   ```

---

### P1-4：測試執行狀態未驗證

**Evidence：**
- 檔案：`backend/conftest.py` + 7 個模組的 `conftest.py`
- 未檢視內容，不確定測試 DB 如何建立
- 報告：`docs/MIGRATION_CHAIN_AUDIT_REPORT.md` 提到測試 DB 手動執行 SQL
- 未執行：`pytest` 驗證測試是否能通過

**Impact：**
- ⚠️ 不確定測試是否能執行
- ⚠️ 不確定測試覆蓋率
- ⚠️ 不確定 CI 是否會炸掉
- ⚠️ 可能有 import errors 或 fixture 問題

**Suggested Fix：**
1. 執行測試收集：
   ```bash
   cd backend
   python -m pytest --collect-only
   ```
2. 執行完整測試：
   ```bash
   python -m pytest -v
   ```
3. 檢查 conftest.py 內容：
   - 是否有跳 migration？
   - 是否有手動 SQL？
   - 是否有 fixture 衝突？
4. 如果測試失敗：
   - 記錄失敗原因
   - 修復或標記為 known issue

---

### P1-5：Policy Engine 檔案過大

**Evidence：**
- 檔案：`backend/app/modules/attendance/policy_engine.py`
- 大小：24,685 bytes (24KB)
- 這是單一檔案，可能包含大量邏輯

**Impact：**
- ⚠️ 單一檔案過大，難以維護
- ⚠️ 可能違反 Single Responsibility Principle
- ⚠️ 測試困難（如果邏輯耦合）
- ⚠️ Code review 困難

**Suggested Fix：**
1. 檢視檔案內容：
   ```bash
   wc -l backend/app/modules/attendance/policy_engine.py
   # 估計 ~600-800 行
   ```
2. 評估是否需要拆分：
   - 如果是單一 class，可能 OK
   - 如果是多個 functions，考慮拆成多個檔案
3. 可能的拆分方式：
   - `policy_engine/calculator.py` (計算邏輯)
   - `policy_engine/validator.py` (驗證邏輯)
   - `policy_engine/rules.py` (規則定義)

---

## P2 風險（中等級）

### P2-1：設定檔缺少 .env 範例

**Evidence：**
- 檔案：`backend/app/core/config.py`
- 使用 `os.getenv("DATABASE_URL", "預設值")`
- 使用 `os.getenv("JWT_SECRET_KEY", "預設值")`
- 但 repo 中沒有 `.env.example` 或 `.env.template`

**Impact：**
- 😕 新成員不知道需要設定哪些環境變數
- 😕 可能使用預設值（含硬編碼密碼）部署到生產
- 😕 JWT secret key 使用預設值（不安全）

**Suggested Fix：**
1. 建立 `.env.example`：
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   JWT_SECRET_KEY=change-me-in-production-min-32-chars
   ```
2. 在 README 說明如何設定環境變數
3. 在 CI/CD 文件說明必要的環境變數

---

### P2-2：Migration 檔名編號混亂

**Evidence：**
- 檔案：`backend/alembic/versions/`
- 執行順序：004 → 3532deda024c → 005 → 002 → 003 → 001b → wp_11_04a
- 檔名編號：004, 005, 002, 003, 001b (不反映執行順序)

**Impact：**
- 😕 開發者看檔名會誤以為 001 最早執行
- 😕 `ls` 排序與執行順序不同
- 😕 容易混淆

**Suggested Fix：**
1. 接受現狀（Alembic 用 `down_revision` 決定順序，不用檔名）
2. 在每個 migration 檔案開頭加註解：
   ```python
   # EXECUTION ORDER: 1/7 (First migration)
   ```
3. 未來新 migration 使用 timestamp 命名（Alembic 預設）

---

### P2-3：缺少 pyproject.toml

**Evidence：**
- 檔案：`backend/requirements.txt` 存在
- 檔案：`backend/pyproject.toml` 不存在

**Impact：**
- 😕 無法使用現代 Python 工具（poetry, pip-tools）
- 😕 無法定義 dev dependencies 與 prod dependencies
- 😕 無法定義專案 metadata

**Suggested Fix：**
1. 如果不需要：保持現狀（requirements.txt 夠用）
2. 如果需要：建立 `pyproject.toml`：
   ```toml
   [project]
   name = "attendance-system-v2"
   version = "0.1.0"
   dependencies = [
       "fastapi>=0.104.0",
       # ... 其他
   ]
   ```

---

### P2-4：EventBus 訂閱者只有 1 個

**Evidence：**
- 檔案：`backend/app/modules/notifications/event_handlers.py`
- 訂閱：`attendance.approved` → 建立通知
- 檔案：`backend/app/modules/attendance/service.py`
- 發布：`attendance.approved`

**Impact：**
- 😕 EventBus 機制建立了，但使用率低
- 😕 可能有其他跨模組互動仍用 direct import（違反 SA_MODULE_SPEC）

**Suggested Fix：**
1. 檢查是否有其他跨模組互動：
   ```bash
   grep -r "from app.modules" backend/app/modules/*/service.py
   ```
2. 如果有：改用 EventBus
3. 如果沒有：保持現狀（EventBus 已可用，未來可擴充）

---

### P2-5：部分文件使用英文，部分使用中文

**Evidence：**
- 檔案：`docs/GATE_PROGRESS_TRACKER.md` (英文)
- 檔案：`docs/MIGRATION_CHAIN_AUDIT_REPORT.md` (中英混合)
- 程式碼註解：大部分中文
- Docstring：部分英文，部分中文

**Impact：**
- 😕 風格不一致
- 😕 國際化困難（如果未來需要）

**Suggested Fix：**
1. 決定統一語言（中文或英文）
2. 逐步統一（低優先度）
3. 或：接受現狀（團隊內部溝通無礙即可）

---

## 風險總結

### 按嚴重度統計

| 級別 | 數量 | 必須修復 |
|------|------|----------|
| P0 | 3 | ✅ 是 |
| P1 | 5 | ⚠️ 建議 |
| P2 | 5 | 😊 可選 |

### Top 3 P0 風險

1. **P0-1：Migration Chain 狀態不明確**
   - 影響：新環境無法初始化
   - 修復時間：1-2 小時（驗證 + 修正）

2. **P0-2：測試 DB 與 Migration 不一致**
   - 影響：測試結果不可信
   - 修復時間：2-4 小時（重建測試 DB + 驗證）

3. **P0-3：Auth 轉換未完成，兩種機制並存**
   - 影響：安全風險 + 維護成本
   - 修復時間：1-2 天（轉換 4 個模組 + 更新測試）

### 建議優先順序

1. **立即處理（本週）：**
   - P0-1：驗證 migration chain
   - P0-2：驗證測試 DB 狀態

2. **短期處理（2 週內）：**
   - P0-3：決策 Auth 轉換策略
   - P1-1：加強 tenant context 驗證
   - P1-4：執行完整測試驗證

3. **中期處理（1 個月內）：**
   - P1-2：更新過時文件
   - P1-3：清理 migration 001
   - P1-5：評估 policy_engine 拆分

4. **長期改善（有空再做）：**
   - P2 系列：文件、命名、設定檔優化

---

**文件版本：** 1.0  
**產出日期：** 2026-03-04  
**審查者：** Claude Opus 4.6 (Cursor AI)
