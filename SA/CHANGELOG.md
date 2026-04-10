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

---

## 4. 維護規則

- 新增一筆紀錄時，不要刪除舊紀錄
- 依時間新到舊或舊到新擇一固定排序；目前採 **舊到新**
- 若同一主題後續又有新進展，可新增新列，不要覆蓋舊列
- 若一項工作只有細節文件、沒有總表紀錄，視為回寫未完成
