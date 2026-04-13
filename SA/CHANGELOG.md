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
| 2026-04-09 14:20:00 +08:00 | 公司品牌欄位與前台顯示規則定義 | `docs_aligned` | `tenants`, `frontend` | `no` | `SA/modules/tenants.md`, `SA/modules/frontend.md` | 定義公司品牌欄位 `name`、`display_name`、`logo_url`，並規劃前台顯示優先順序 `logo_url > display_name > name`。 |
| 2026-04-09 14:35:00 +08:00 | 員工首頁 IA 收斂：navbar 改為資訊列、功能入口收斂到個人服務 | `docs_aligned` | `frontend` | `no` | `SA/modules/frontend.md` | 確立員工端 navbar 不作為功能導覽列，功能入口集中至個人服務。 |
| 2026-04-09 14:50:00 +08:00 | 建立 SA 總表制度 | `docs_aligned` | `governance`, `SA index` | `yes` | `SA/CHANGELOG.md`, `SA/governance/DOCUMENTATION_GOVERNANCE.md` | 建立可追溯總表制度，要求每次事項都在總表留摘要索引，細節回寫各自正式文件。 |
| 2026-04-09 15:03:00 +08:00 | 公司識別與工商資料規格定義 | `docs_aligned` | `tenants`, `auth` | `no` | `SA/modules/tenants.md` | 定義 `company_id` 必填且可登入、`tax_id` 選填且可登入，並規範公司資料查詢採人工查核 / 半自動過渡模式。 |
| 2026-04-09 15:15:00 +08:00 | 公司登入識別規則跨模組文件對齊 | `docs_aligned` | `tenants`, `auth`, `tracker` | `no` | `SA/modules/tenants.md`, `SA/modules/auth.md`, `SA/SDD_PROGRESS_TRACKER.md` | 補齊 `auth` 與追蹤文件，使 `company_id` / `tax_id` 的欄位責任、登入識別與文件邊界一致。 |
| 2026-04-09 15:25:00 +08:00 | 公司後端欄位與管理畫面規劃補齊 | `docs_aligned` | `tenants`, `frontend`, `backend schema`, `tracker` | `no` | `SA/modules/tenants.md`, `SA/SDD_PROGRESS_TRACKER.md` | 依目前 code baseline 補齊 company model/schema 與 admin 公司管理畫面的欄位缺口與後續對齊規劃。 |
| 2026-04-10 10:30:00 +08:00 | Membership uses_schedule 與 login bootstrap 正式落地 | `code_updated` | `auth`, `tenants`, `frontend` | `yes` | `SA/modules/auth.md`, `SA/modules/tenants.md`, `backend/app/modules/auth/schemas.py`, `backend/app/modules/auth/service.py`, `backend/app/modules/tenants/api_members.py` | 將 `uses_schedule` 正式落到 membership、登入回應加入 membership bootstrap，並讓首頁依該欄位顯示「我的班表」。 |
| 2026-04-13 13:49:00 +08:00 | SA tenants 規格分流比對檔建立（Plan A / Plan B） | `docs_aligned` | `tenants`, `comparison`, `recovery` | `yes` | `SA/modules/TENANTS.MD_PlanA`, `SA/modules/tenants.mb_planB`, `SA/modules/tenants.md`, `SA/CHANGELOG.md` | 從 Git 提交 `014a52a` 抽出 `tenants.md` 完整版作為 Plan A，並切出第 9 章以後的重點規格作為 Plan B，供人工比對是否回填正式 `tenants.md`。 |
| 2026-04-13 14:05:30 +08:00 | tenants 正式檔回填 Plan A 完整版 | `docs_aligned` | `tenants`, `recovery`, `comparison` | `yes` | `SA/modules/tenants.md`, `SA/modules/TENANTS.MD_PlanA`, `SA/modules/tenants-v3-waiting-handoff.md`, `SA/CHANGELOG.md` | 依人工確認，將 `TENANTS.MD_PlanA` 的完整內容覆蓋回正式 `tenants.md`，使正式 SDD 恢復到包含 company detail、tax_id lookup、多據點 location 分流與 Phase 1 管理摘要規格的版本。 |
| 2026-04-13 14:32:00 +08:00 | SA 正式文件 admin 用語最小收斂 | `docs_aligned` | `tenants`, `customer_service`, `attendance-reporting` | `no` | `SA/modules/tenants.md`, `SA/modules/customer_service.md`, `SA/modules/attendance-reporting.md`, `SA/CHANGELOG.md` | 僅收斂正式語意模糊字樣：將 `admin 雜物箱` 改為管理後台表述，將泛稱 `company admin` 改為公司內管理角色表述，並將 reporting 中的 `company admin scope check` 改為公司管理層 scope check；未更動歷史報告、`/admin` 產品區名稱與既有正式角色碼。 |
| 2026-04-13 15:05:00 +08:00 | pytest migration smoke 最小收尾完成 | `done` | `backend tests`, `SA index` | `yes` | `backend/tests/test_migration_smoke.py`, `SA/CHANGELOG.md` | 將 migration smoke 測試的 `EXPECTED_HEAD` 對齊到 `015_remove_legacy_manager_role`，並完成單檔驗證 `3 passed`，確認這輪 pytest 收尾缺口已補上。 |
| 2026-04-13 15:25:00 +08:00 | Git remote 確認規則納入 SA 治理 | `docs_aligned` | `governance`, `git workflow` | `no` | `SA/governance/DOCUMENTATION_GOVERNANCE.md`, `SA/CHANGELOG.md` | 明定每開一個新的 chat，只要任務牽涉 Git / commit / push / remote，都必須先確認本次操作目標 remote 與同步目標（如 `origin`、`github`），不得自行假設只推其中一個。 |
| 2026-04-13 15:40:00 +08:00 | 高風險檔案修改方式改為先驗證再寫入 | `docs_aligned` | `governance`, `safe edit workflow` | `no` | `SA/governance/DOCUMENTATION_GOVERNANCE.md`, `SA/CHANGELOG.md` | 將高風險檔案 SOP 改為先做可安全修改判定，再允許 patch；若讀檔異常、命中失敗、目標不唯一或無法保證小 diff，必須停止，不得升級成整段或整檔覆寫。 |

---

## 4. 維護規則

- 新增一筆紀錄時，不要刪除舊紀錄
- 依時間新到舊或舊到新擇一固定排序；目前採 **舊到新**
- 若同一主題後續又有新進展，可新增新列，不要覆蓋舊列
- 若一項工作只有細節文件、沒有總表紀錄，視為回寫未完成
