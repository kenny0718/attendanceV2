# SA Change Log

> 這份文件是 `SA/` 的總表索引。  
> 目的不是取代各模組 / 架構 / 治理文件，而是讓你快速知道：**你做過哪些事、何時做的、影響哪些模組、細節應該去哪一份文件找。**

---

## 1. 使用原則

- 這裡只記摘要與索引，不重複貼完整細節
- 每次開發、規劃、規則調整完成後，都要新增一筆紀錄
- 細節仍應回寫到對應文件：
  - `SA/modules/*.md`
  - `SA/architecture/*.md`
  - `SA/governance/*.md`
  - 必要時同步更新 `SA/SDD_PROGRESS_TRACKER.md`

---

## 2. 欄位說明

| 欄位 | 說明 |
|---|---|
| `Datetime` | 修改完成時間，格式：`YYYY-MM-DD HH:MM:SS +08:00` |
| `Title` | 本次事項標題 |
| `Status` | `spec_defined` / `docs_aligned` / `code_updated` / `tests_added` / `done` |
| `Modules` | 影響模組或文件範圍 |
| `Code` | `yes` / `no` |
| `Details` | 細節應查看的正式文件 |
| `Summary` | 一句話摘要 |

---

## 3. 總表紀錄

| Datetime | Title | Status | Modules | Code | Details | Summary |
|---|---|---|---|---|---|---|
| 2026-04-09 13:40:00 +08:00 | Upstream / streaming 正式模組 SDD 與 demo event 對齊 | `code_updated` | `upstream-streaming`, `frontend`, `architecture` | `yes` | `SA/modules/upstream-streaming.md`, `SA/modules/frontend.md`, `SA/architecture/SYSTEM_SDD.md`, `SA/SDD_PROGRESS_TRACKER.md` | 建立 upstream / streaming 正式模組 SDD，完成 backend / frontend skeleton 與 demo event 對齊。 |
| 2026-04-09 14:05:00 +08:00 | 員工首頁 streaming 狀態先移入個人服務驗證 | `code_updated` | `frontend` | `yes` | `frontend/src/components/Navbar.vue`, `frontend/src/components/attendance/PersonalServiceCard.vue` | 將系統 / 出勤狀態從頂部展示調整到個人服務區塊，作為首頁驗證版本。 |
| 2026-04-09 14:35:00 +08:00 | 員工首頁 IA 收斂：navbar 改為資訊列、功能入口收斂到個人服務 | `docs_aligned` | `frontend` | `no` | `SA/modules/frontend.md` | 確立員工端 navbar 不作為功能導覽列，功能入口集中至個人服務。 |
| 2026-04-09 14:50:00 +08:00 | 建立 SA 總表制度 | `docs_aligned` | `governance`, `SA index` | `yes` | `SA/CHANGELOG.md`, `SA/governance/DOCUMENTATION_GOVERNANCE.md` | 建立可追溯總表制度，要求每次事項都在總表留摘要索引，細節回寫各自正式文件。 |
| 2026-04-09 15:03:00 +08:00 | 公司識別與工商資料規格定義 | `docs_aligned` | `tenants`, `auth` | `no` | `SA/modules/tenants.md` | 定義 `company_id` 必填且可登入、`tax_id` 選填且可登入，並規範公司資料查詢採人工查核 / 半自動過渡模式。 |
| 2026-04-09 15:15:00 +08:00 | 公司登入識別規則跨模組文件對齊 | `docs_aligned` | `tenants`, `auth`, `tracker` | `no` | `SA/modules/tenants.md`, `SA/modules/auth.md`, `SA/SDD_PROGRESS_TRACKER.md` | 補齊 `auth` 與追蹤文件，使 `company_id` / `tax_id` 的欄位責任、登入識別與文件邊界一致。 |
| 2026-04-09 15:25:00 +08:00 | 公司後端欄位與管理畫面規劃補齊 | `docs_aligned` | `tenants`, `frontend`, `backend schema`, `tracker` | `no` | `SA/modules/tenants.md`, `SA/SDD_PROGRESS_TRACKER.md` | 依目前 code baseline 補齊 company model/schema 與 admin 公司管理畫面的欄位缺口與後續對齊規劃。 |
| 2026-04-10 10:30:00 +08:00 | Membership uses_schedule 與 login bootstrap 正式落地 | `code_updated` | `auth`, `tenants`, `frontend` | `yes` | `SA/modules/auth.md`, `SA/modules/tenants.md`, `backend/app/modules/auth/schemas.py`, `backend/app/modules/auth/service.py`, `backend/app/modules/tenants/api_members.py` | 將 `uses_schedule` 正式落到 membership、登入回應加入 membership bootstrap，並讓首頁依該欄位顯示「我的班表」。 |
| 2026-04-13 20:45:00 +08:00 | Tenants / Companies v3 Phase 1 backend 落地：公司主資料、detail、tax_id lookup | `code_updated` | `tenants`, `backend`, `onboarding`, `admin companies`, `migration` | `yes` | `SA/modules/tenants.md`, `SA/modules/tenants-v3-waiting-handoff.md`, `backend/alembic/versions/016_add_company_profile_fields_to_tenants.py`, `backend/app/modules/tenants/models.py`, `backend/app/modules/tenants/repo.py`, `backend/app/modules/tenants/service.py`, `backend/app/modules/tenants/api.py`, `backend/app/modules/tenants/api_onboarding.py`, `backend/app/modules/tenants/schemas.py`, `backend/app/modules/tenants/schemas_companies.py`, `backend/app/modules/tenants/schemas_onboarding.py`, `backend/app/modules/tenants/tests/test_companies_api.py`, `backend/app/modules/tenants/tests/test_onboarding_api.py` | 依正式 SDD 與 handoff 文件完成 Phase 1 backend：`Tenant` 新增公司主資料欄位、補 migration、建立 `detail` 與 `member_summary`、新增僅限 `super_admin` 的 `lookup-by-tax-id` stub contract、擴充 company create/update/onboarding schema 與 flow，並補上對應測試；角色判斷以 `company_admin` 為主，保留現行仍在用的 `hr_manager` 相容。 |
| 2026-04-13 21:20:00 +08:00 | Admin Companies / Onboarding frontend 串接 Tenants v3 backend | `code_updated` | `frontend`, `tenants`, `admin companies`, `onboarding`, `SA index` | `yes` | `SA/CHANGELOG.md`, `frontend/src/api/admin.js`, `frontend/src/views/admin/AdminOnboardingView.vue`, `frontend/src/views/admin/AdminCompaniesView.vue`, `frontend/src/components/admin/CompanyDetailPanel.vue`, `backend/app/modules/tenants/api.py`, `backend/app/modules/tenants/schemas_companies.py`, `backend/app/modules/tenants/schemas_onboarding.py` | 前端正式串接 Tenants v3 backend：onboarding 新增 `lookup-by-tax-id` 查詢入口與公司主資料欄位送出，company detail 改讀 `/api/admin/companies/{company_id}` 以顯示完整公司欄位與 `member_summary`，並在會員異動後重抓 detail，方便日後依 changelog 追查 backend / frontend contract 是否一致。 |
| 2026-04-14 18:16:01 +08:00 | Admin Companies / members 鏈路回復、migration 補齊與收尾驗證 | `done` | `tenants`, `backend`, `admin companies`, `members`, `migration`, `tests`, `SA index` | `yes` | `SA/CHANGELOG.md`, `SA/modules/tenants.md`, `backend/app/modules/tenants/repo.py`, `backend/app/modules/tenants/service.py`, `backend/app/modules/tenants/api.py`, `backend/alembic/versions/016_add_company_profile_fields_to_tenants.py`, `backend/scripts/dev/seed_admin_accounts.py`, `backend/scripts/dev/seed_yhsi_super_admin.py`, `backend/app/modules/tenants/tests/test_companies_api.py` | 回復 `TenantRepository` / `CompanyEntitlementRepository` 可用實作，修正 admin companies 列表、detail、members 鏈路於欄位與 repository 匯入異常造成的 500，補齊 tenant company profile migration 與 seed 對應，並完成最小回歸驗證：服務正常、Alembic 位於 `016` head、`/api/admin/companies*` 相關路徑回到 `200 OK`，`test_companies_api.py` 全數通過（23 passed）。 |
| 2026-04-14 18:23:36 +08:00 | SA 治理規則補充：使用者明示可調用資訊時必須先查證 | `docs_aligned` | `governance`, `SA index`, `AI collaboration` | `yes` | `SA/governance/DOCUMENTATION_GOVERNANCE.md`, `SA/CHANGELOG.md` | 補入正式治理規則：若使用者已明確指出某項資訊、環境、指令、remote、服務或資源可調用、可查詢或已有現成資料，AI 必須先實際查證再回應，不得以猜測、記憶或預設前提替代驗證。 |
| 2026-04-14 18:36:47 +08:00 | SA 治理規則補充：`+1 -N` 屬 AI 寫入責任，強制採候選檔與 diff gate | `docs_aligned` | `governance`, `SA index`, `AI collaboration`, `safe write` | `yes` | `SA/governance/DOCUMENTATION_GOVERNANCE.md`, `SA/CHANGELOG.md` | 明確規範 `+1 -N`、空檔、0KB、截斷與非預期大刪除屬 AI 寫入決策事故，不得歸因於使用者；高風險檔案強制採用「原檔 → 備份 → 候選檔 → diff gate → 完整性驗證 → 覆蓋正式檔」流程，禁止直接整檔覆寫正式檔。 |
| 2026-04-15 17:45:54 +08:00 | 全面移除公司 Logo 欄位、API、UI 與文件殘留 | `done` | `tenants`, `frontend`, `backend`, `onboarding`, `SA index` | `yes` | `SA/CHANGELOG.md`, `SA/modules/tenants.md`, `SA/modules/auth.md`, `SA/modules/tenants-v3-waiting-handoff.md`, `backend/app/modules/tenants/models.py`, `backend/app/modules/tenants/schemas_companies.py`, `backend/app/modules/tenants/schemas_onboarding.py`, `backend/app/modules/tenants/service.py`, `backend/app/modules/tenants/api.py`, `backend/app/modules/tenants/repo.py`, `backend/app/modules/tenants/tests/test_companies_api.py`, `backend/app/modules/tenants/tests/test_onboarding_api.py`, `frontend/src/api/admin.js`, `frontend/src/components/Navbar.vue`, `frontend/src/components/admin/CompanyDetailPanel.vue`, `frontend/src/views/admin/AdminCompaniesView.vue`, `frontend/src/views/admin/AdminOnboardingView.vue` | 依使用者要求全面移除公司 Logo 上傳與顯示能力，清除後端欄位、API、測試、前端管理畫面與文件中的 Logo / `logo_url` 契約，並同步保留本次移除紀錄於 SA 總表。 |

| 2026-04-16 09:10:00 +08:00 | Auth / Schedule 真 JWT 測試鏈路修正與文件回寫 | `done` | `auth`, `schedule`, `tests`, `SA index` | `yes` | `SA/CHANGELOG.md`, `SA/modules/auth.md`, `SA/modules/schedule.md`, `backend/app/modules/schedule/tests/test_schedule_real_jwt_e2e.py` | 修正真 JWT E2E 測試基線：補齊 `roles`、`users`、`user_company_memberships`、`company_entitlements` seed，對齊 `schedule.core` feature key，並確認 access token 測試需帶 `session_id` claim；相關 auth + schedule 測試主鏈驗證通過（47 passed）。 |
| 2026-04-16 10:12:29 +08:00 | SA 治理規則補充：高風險文件正式回寫必須走 `.tmp` 候選檔覆蓋流程 | `docs_aligned` | `governance`, `SA index`, `AI collaboration`, `safe write` | `yes` | `SA/governance/DOCUMENTATION_GOVERNANCE.md`, `SA/CHANGELOG.md` | 補入正式規則：`SA`、`SDD`、治理文件與 `CHANGELOG` 的正式回寫，必須實際走「正式檔 reread → 秒級備份 → `.tmp` 候選檔 → diff gate → 完整性驗證 → `.tmp` 覆蓋正式檔 → reread 確認」流程，不得簡化成直接 patch 正式檔或只口頭承諾使用 `.tmp`。 |

---

## 4. 維護規則

- 新增一筆紀錄時，不要刪除舊紀錄
- 依時間新到舊或舊到新擇一固定排序；目前採 **舊到新**
- 若同一主題後續又有新進展，可新增新列，不要覆蓋舊列
- 若一項工作只有細節文件、沒有總表紀錄，視為回寫未完成
