# WP-INCIDENT: Cursor 0KB 寫檔事故修復方案報告

**文件類型：** Remediation Plan Report  
**建立日期：** 2026-03-29  
**建立依據：** WP-INCIDENT_CURSOR_0KB_ROOT_CAUSE_ATTRIBUTION.md  
**分析人：** Cursor AI Agent（依用戶指令，本輪僅產出方案，不修改任何檔案）  
**狀態：** PLAN ONLY — 尚未實施，待用戶確認後再推進

---

## 1. Summary（建議採用方案）

### 結論：採用 Option C — Operational Workflow 修法，同步推進 Option B 的治理文件強制化

**為什麼不是 Option A？**

`CURSOR_FRONTEND_SAFE_EDIT_RULES.md` 在事故發生前已存在，明文禁止 whole-file rewrite，要求 tmp → verify → rename 流程，但：
- conftest.py 仍被 0KB 覆蓋（事故 #7）
- AdminAttendanceView.vue 仍被截斷（事故 #5）
- Write tool 在調查報告本身的撰寫過程中即時重演 0KB（事故 #6）

規則已經存在，事故仍然發生。純粹增加規則文字（Option A）已被本專案的實際歷史否定。

**為什麼 Option B 不夠？**

Option B 只是讓規則「更正式」，但如果規則沒有嵌入每張票的執行流程，AI agent 在任務執行中仍會繞過它們。治理文件的強制化必須搭配流程閘門才有意義。

**為什麼 Option C 是正確方向？**

本專案 0KB 事故的根本原因是：每次寫入操作缺乏前中後驗證閘門。Option C 把驗證嵌入流程，讓每張票都有可查核的執行步驟與輸出紀錄，事故可在最早期被發現並停止，不會等到 commit 之後才被察覺。

**最終推進順序：**
1. 先建立 Operational Workflow（每張票的執行步驟，有前/中/後閘門）
2. 同步更新治理文件（加入強制風險分級與閘門規則）
3. 最後才是 Prompt 模板修改（第三優先，在流程穩定後才有意義）

---

## 2. Options Comparison（方案比較表）

| 評估維度 | Option A：Prompt-only | Option B：Governance + Prompt | Option C：Operational Workflow |
|---|---|---|---|
| **實施成本** | 低（只改規則文字） | 中（改文件 + 規則分級） | 高（改流程 + 模板 + 訓練閘門） |
| **風險降低效果** | **低**（已被本專案歷史否定） | 中（規則存在但無強制觸發） | **高**（每步有驗證閘門） |
| **對開發速度影響** | 極小（幾乎無感） | 小（多一些前置讀取） | 中（每張票多約 3~5 分鐘驗證） |
| **對 AI 行為的約束力** | 弱（可被繞過） | 中（規則在上下文中但非強制） | **強**（流程即約束，每步有輸出） |
| **可追蹤性** | 無 | 低（無法確認規則是否被執行） | **高**（每步有輸出可核查） |
| **適合本專案？** | 不適合（已失敗） | 部分（需配合 C） | 最適合 |
| **最大弱點** | AI 在任務中可忽略靜態規則 | 沒有執行階段強制機制 | 需要人工紀律配合才能維持 |

### Option A 為何不適合本專案

既有 `CURSOR_FRONTEND_SAFE_EDIT_RULES.md` 明文規定的規則已被違反 7 次。歷史已證明：單純的規則文字無法阻止 AI agent 在執行大型任務時退回 whole-file write 策略。Option A 只能讓規則「看起來更完整」，對實際行為沒有約束。

### Option B 為何不充分（但仍必要）

Option B 是必要條件，但不充分。治理文件的風險分級和強制規則是有價值的，但如果沒有對應的「流程閘門」在任務執行時強制觸發，這些規則仍是裝飾性的。Option B 必須作為 Option C 的一部分來實施，而不是獨立方案。

### Option C 的核心價值

Option C 把「驗證」從可選步驟變成必走的流程節點。當每張票的執行步驟都包含明確的「前/中/後」閘門時，AI agent 跳過驗證的空間被大幅壓縮。即使 AI agent 仍嘗試 whole-file write，流程中的 size/structure 驗證步驟也會在第一時間攔截。

---

## 3. File Risk Classification（檔案風險分級）

### Level 1 — 高風險檔案（禁止 Whole-File Rewrite）

本專案中已有 0KB 事故紀錄，或具備以下特徵的檔案：
- 行數 > 100 行
- 被多個模組引用（破壞即全系統影響）
- 無法用 git restore 快速恢復（untracked）
- 結構複雜（Vue SFC 三段式、Python 多 class / 多 fixture）

| 檔案類型 | 具體範例 | 為何高風險 |
|---|---|---|
| Vue 大頁面（>200行） | `AdminAttendanceView.vue`、`AttendanceView.vue`、`Admin.vue` | SFC 三段結構，截斷即無法解析，事故 #5 即此類 |
| Python schema | `schemas.py`（attendance/schedule/tenants） | 多處引用，0KB 即全系統 import 失敗，事故 #1/#2 即此類 |
| Python core service | `attendance_service.py`、`schedule/service.py` | 業務邏輯核心，事故 #3（422行消失）即此類 |
| Python conftest | `backend/app/conftest.py` | pytest fixture 定義，0KB 即全部測試 ERROR，事故 #7 即此類 |
| Python core API router | `attendance/api.py`（backend router） | 接口定義，破壞即所有 endpoint 消失 |
| Python models | `attendance/models.py`、`schedule/models.py` | ORM 定義，破壞即所有 DB 操作失敗 |
| 核心治理文件 | `CURSOR_DEVELOPMENT_RULES.md`、`AI_CONTEXT.md` | 規則基準，改壞即失去所有 AI 治理 |
| Alembic migration | `alembic/versions/*.py` | 不可逆操作，覆蓋即資料結構風險 |

**Level 1 規則：**
- 禁止 whole-file rewrite（包含 Write tool 直接寫入完整內容）
- 強制任務前 git checkpoint（`git add -A && git commit -m "checkpoint"`）
- 強制僅使用 StrReplace 或精確局部 patch
- 強制修後驗證：`wc -l`、`head -20`、`tail -20`、`git diff --stat`
- 強制 0 bytes 即停，出 incident report，禁止繼續功能票
- 新建大型檔案必須分段建立（骨架 → 逐段補充），每段 git add

### Level 2 — 中風險檔案（謹慎操作，整檔需評估）

| 檔案類型 | 具體範例 | 為何中風險 |
|---|---|---|
| Pinia store | `attendanceStore.js`、`authStore.js` | 中型，前端多處引用 |
| Vue router | `frontend/src/router/index.js` | 結構固定但破壞影響所有導航 |
| API wrapper | `frontend/src/api/attendance.js`、`client.js` | 前端 API 封裝，改錯即全前端請求失效 |
| Python utils | `utils/date_utils.py` 等輔助函數 | 被多處引用，改錯影響範圍廣 |
| 中型 WP 報告 | `WP-S1-*.md`（進行中的工作票） | 需完整性，寫壞影響工作追蹤 |

**Level 2 規則：**
- Whole-file rewrite 需先確認行數（>100 行時禁止整檔覆蓋）
- 建議 git checkpoint（非強制但強烈推薦）
- 修後必查：`wc -l` 確認非 0，`git diff --stat` 確認範圍合理
- 不強制 StrReplace，但鼓勵局部 patch

### Level 3 — 低風險檔案（可整檔操作，但仍需基本驗證）

| 檔案類型 | 具體範例 | 說明 |
|---|---|---|
| 小型設定 | `.env.example`、`pytest.ini`、`.gitignore` | 行數少，結構簡單 |
| 小型測試 | 新建的單一功能測試（<50 行） | 獨立，改壞不影響其他 |
| 新建 docs | 新建的 incident report | 新建文件，無覆蓋風險 |
| 靜態資源 | `README.md`（非治理用途） | 純文字，無邏輯 |

**Level 3 規則：**
- Whole-file rewrite 允許
- 修後確認 size > 0（必須）
- 若寫後出現 0 bytes，仍需停止並回報（不得視為小事）

---

## 4. Recommended Rule Set（可落地規則集）

### A. 任務前（Pre-Task Rules）

```
[PRE-1] 任務開始前必須確認目標檔案清單
  操作：列出本次任務將修改的所有檔案
  操作：對每個檔案標記風險等級（Level 1 / 2 / 3）
  操作：確認每個 Level 1 檔案目前大小（wc -l）並記錄原始行數

[PRE-2] 存在 Level 1 目標檔案時，必須先執行 git checkpoint
  命令：git add -A && git commit -m "checkpoint: before [task-name]"
  若 repo 有 untracked 核心檔，必須手動備份後才能繼續
  備份確認：cp target.vue target.vue.bak && wc -c target.vue.bak（確認 bak 非 0）

[PRE-3] 任何目標檔案若已為 0 bytes，必須立即停止
  停止原因：0 bytes 代表前次任務可能已觸發事故
  禁止行為：繼續進行任何功能修改
  必做行為：出 incident report，再請用戶確認後才繼續

[PRE-4] 大型 Level 1 檔案（>200 行）的新建任務，必須採用分段建立策略
  Step 1：只建立骨架（空 template + 空 script setup + 空 style）
  Step 2：git add 骨架版本
  Step 3：逐段填入內容，每段完成後確認大小
  禁止：一次輸出完整大型檔案內容

[PRE-5] 單一任務禁止同時修改超過 3 個 Level 1 檔案
  超過 3 個必須拆分成多張子票
```

### B. 修改中（In-Edit Rules）

```
[EDIT-1] Level 1 檔案禁止任何形式的 whole-file overwrite
  禁止：Write tool 對已存在的 Level 1 檔案直接寫入完整內容
  禁止：輸出完整檔案內容後要求用戶貼上覆蓋
  禁止：先刪除後重建
  允許：StrReplace 精確替換特定區段（old_string 必須唯一且有足夠上下文）
  允許：明確標示修改行號範圍的局部 patch

[EDIT-2] 任何修改若需輸出超過 200 行的完整檔案內容，視為 whole-file write 風險
  必須先詢問用戶：「確認要整檔覆蓋？目標檔案現在有 N 行。」
  等待用戶明確確認後才繼續

[EDIT-3] Vue SFC 修改必須保持三段結構完整性
  每次修改後必須確認：
    </template> 存在 → grep -c "</template>" == 1
    </script> 存在 → grep -c "</script>" >= 1
    </style> 存在（若原本有）→ grep -c "</style>" >= 1

[EDIT-4] Python 核心檔案修改必須保持 class / def 結構完整性
  修改後確認：
    class 定義數量與修改前相同
    主要 def 函數數量與修改前相同（或只增加，不減少）

[EDIT-5] 分段寫入時，每段完成後立即驗證大小
  命令：wc -c <file> 確認目前 size > 上一段 size
  若 size 未增加或為 0，立即停止並回報
```

### C. 修改後（Post-Edit Rules）

```
[POST-1] 每次修改後必須執行的基本驗證（所有 Level 1 / 2 檔案）
  a. 大小確認：wc -c <file>（結果必須 > 0，且不低於修改前的 50%）
  b. 行數確認：wc -l <file>（與修改前比較，若大幅減少須說明）
  c. 頭部確認：head -5 <file>（確認檔案開頭結構正常）
  d. 尾部確認：tail -5 <file>（確認檔案結尾完整，非截斷）
  e. 差異確認：git diff --stat（確認修改範圍合理）

[POST-2] Vue SFC 修改後必須額外確認
  grep -c "</template>" == 1
  grep -c "</script>" >= 1
  wc -l 行數不低於修改前（除非有明確刪除操作）

[POST-3] Python schema / conftest / service 修改後必須額外確認
  python -c "import ast; ast.parse(open('<file>').read())"（語法驗證）
  wc -l 不低於修改前
  所有 class 與主要 def 函數標頭仍存在

[POST-4] 以下情況不得宣稱「修改完成」
  a. 未執行 POST-1 完整驗證
  b. wc -c 結果為 0
  c. tail 顯示檔案在中間被截斷（無正常結尾）
  d. Vue SFC 缺少任一段（template / script / style）
  e. git diff --stat 顯示刪除行數超過預期

[POST-5] 大型任務完成後必須執行整體 git 狀態確認
  git status（確認無意外的 untracked 或 modified 核心檔）
  git diff --stat HEAD（確認整體修改範圍符合任務 scope）
```

### D. 事故處理（Incident Rules）

```
[INC-1] 發現任何 Level 1 / 2 檔案為 0 bytes 時的第一動作
  Step 1：立即停止所有功能修改
  Step 2：保全事故現場副本
    cp <file> <file>.incident_YYYYMMDD
    wc -c <file>.incident_YYYYMMDD（確認副本確實被建立，即使是 0 bytes）
  Step 3：確認有無可用備份來源
    git log --oneline <file>（找最後一個非 0 的 commit）
    ls <file>.bak <file>.tmp（確認有無殘留備份）
  Step 4：出 incident report（先於任何 restore 操作）
    必須記錄：事故時間、檔案路徑、發現方式、最後正常 commit
  Step 5：等待用戶確認 restore 策略後才執行 restore

[INC-2] 再次出現 0KB 事故時的升級處理
  若本修復方案實施後仍再發 0KB：
  a. 必須暫停當前功能票
  b. 出新的 incident report，記錄「修復方案失效」事實
  c. 判斷是否需要升級到更嚴格的保護措施（見 Section 6 驗證計畫）

[INC-3] .tmp 殘留的處理規則
  發現 .tmp 殘留時，必須先確認對應正本的完整性
  若正本完整（wc -l > 0，結構正常）→ 可安全刪除 .tmp
  若正本不完整或 0 bytes → .tmp 是備援來源，用 .tmp 恢復後再刪除

[INC-4] 禁止在 incident 期間繼續功能開發
  從發現 0KB 到完成 incident report 並獲得用戶確認之前，
  禁止進行任何功能修改，包含「順手修一個小地方」。
```

---

## 5. Template Change Recommendations（模板修改建議）

以下為應新增或修改的模板清單。本節只說明「哪個模板該加什麼段落」，不直接修改任何文件。

### 5.1 通用 Cursor 任務模板（CURSOR_TASK_TEMPLATE）

應新增以下強制段落，放在任務描述最前面：

```
## Pre-Task Checklist（任務前必做）
- [ ] 列出本次將修改的所有檔案，並標記風險等級（L1 / L2 / L3）
- [ ] 確認所有目標檔案目前均非 0 bytes（wc -c 確認）
- [ ] 若有 Level 1 目標檔案 → 執行 git checkpoint 後才繼續
- [ ] 若任務涉及新建 >200 行檔案 → 確認採用分段建立策略

## Post-Task Checklist（任務後必驗）
- [ ] wc -c 所有修改檔案（均須 > 0）
- [ ] wc -l 與修改前比較（大幅減少須說明）
- [ ] head -5 / tail -5 確認頭尾正常
- [ ] git diff --stat 確認修改範圍符合預期
- [ ] 若任何檔案為 0 bytes → 立即停止，出 incident report
```

應新增的段落位置：任務描述開頭（Pre-Task）與結尾（Post-Task）
應移除的段落：任何允許「整檔輸出後貼上覆蓋」的指示

### 5.2 Vue 頁面修改模板（VUE_PAGE_EDIT_TEMPLATE）

現有 `CURSOR_FRONTEND_SAFE_EDIT_RULES.md` 已有部分規則，但缺乏以下具體操作段落：

應新增：
```
## Vue SFC 修改前必做
1. 確認目標 .vue 檔案大小：wc -c <file>（不可為 0）
2. 確認三段結構存在：
   grep -c "</template>" <file>  # 應為 1
   grep -c "</script>" <file>   # 應為 >= 1
3. 記錄原始行數：wc -l <file>  # 作為驗證基準
4. 若行數 > 200，確認採用 StrReplace 局部 patch，禁止整檔覆蓋

## Vue SFC 修改後必驗
1. grep -c "</template>" <file>  # 仍為 1
2. grep -c "</script>" <file>   # 仍為 >= 1
3. wc -l <file>  # 不低於修改前（除非有明確刪除操作）
4. tail -10 <file>  # 確認 </style> 或 </script> 為最後幾行之一
```

應新增：新建大型 Vue SFC 的分段策略說明：
```
## 新建大型 Vue SFC 標準流程
Step 1：寫骨架（約 15 行）
  <template><div></div></template>
  <script setup></script>
  <style scoped></style>
Step 2：git add 骨架（立即保全）
Step 3：在 <script setup> 內加入 import 和 reactive state
Step 4：git add
Step 5：在 <template> 內逐區塊填入 HTML 結構
Step 6：每個主要區塊完成後 wc -l 確認增長正常，git add
Step 7：最後加入 <style> 內容
Step 8：最終驗證三段結構完整，git commit
```

### 5.3 Python Backend 核心檔案修改模板（PYTHON_CORE_EDIT_TEMPLATE）

應新增以下段落，適用於 schemas.py / service.py / conftest.py / models.py / api.py：

```
## Python 核心檔案修改前必做
1. 確認檔案大小：wc -c <file>（不可為 0）
2. 記錄 class / def 數量：
   grep -c "^class " <file>   # 記錄 class 數量
   grep -c "^    def \|^def " <file>  # 記錄主要 def 數量
3. 記錄行數：wc -l <file>
4. 執行 git checkpoint

## Python 核心檔案修改後必驗
1. wc -c <file>（不可為 0，不低於修改前 50%）
2. python -c "import ast; ast.parse(open('<file>').read()); print('syntax OK')"
3. grep -c "^class " <file>  # 不低於修改前
4. grep -c "^    def \|^def " <file>  # 不低於修改前（除非有明確刪除）
5. tail -5 <file>  # 確認結尾正常（非截斷）
```

應明確禁止：對 conftest.py / schemas.py / service.py 使用 Write tool 整檔覆蓋。
應明確要求：以上任何一個檔案修改後，語法驗證（ast.parse）為必做步驟。

### 5.4 事故調查模板（INCIDENT_INVESTIGATION_TEMPLATE）

現有 `WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md` 可作為模板基礎。
應標準化以下段落結構：

```
## 事故調查報告標準段落

1. Summary（事故摘要）
   - 事故時間
   - 受影響檔案與大小
   - 最可能成因（初步判斷）
   - 目前狀態（OPEN / RESOLVED）

2. Evidence Collected（證據清單）
   - 受影響檔案的 wc -c / wc -l 輸出
   - git log --oneline <file>（最後幾個 commit）
   - ls -la <file>（timestamps）
   - 相關 .tmp / .bak 殘留清單

3. Timeline（時間線重建）
   - 最後一個正常 commit 時間
   - 事故被發現時間
   - 中間發生的操作

4. Root Cause（根因判斷）
   - 主因（含信心度）
   - 次因
   - 排除的假說

5. Immediate Actions（立即處置）
   - 保全副本（cp .incident_YYYYMMDD）
   - Restore 策略與來源
   - Restore 後驗證步驟

6. Prevention（防範建議）
   - 針對此次事故的具體防範
   - 對應到本修復方案的哪條規則
```

應新增的強制欄位：「本次事故對應修復方案中哪條規則失效？」
這確保每次事故都能回饋到規則改善循環中。

### 5.5 Restore / Rescue 模板（RESTORE_RESCUE_TEMPLATE）

現有 `WP-INCIDENT_CONFTEST_PY_RESTORE_REPORT.md` 可作為模板基礎。
應標準化以下段落結構：

```
## Restore 操作標準流程

Step 1：確認事故現場已保全
  ls -la <file>.incident_YYYYMMDD
  wc -c <file>.incident_YYYYMMDD

Step 2：尋找可用 restore 來源（優先順序）
  a. git show <commit>:<file> > /tmp/restore_candidate
  b. ls <file>.bak（確認非 0 bytes）
  c. ls <file>.tmp（確認非 0 bytes）
  d. 人工重建（最後手段）

Step 3：驗證 restore 候選
  wc -c /tmp/restore_candidate（必須 > 0）
  head -10 /tmp/restore_candidate（確認內容正確）
  tail -10 /tmp/restore_candidate（確認結尾正常）
  （若為 Python）python -c "import ast; ast.parse(open('/tmp/restore_candidate').read())"
  （若為 Vue）grep -c "</template>" /tmp/restore_candidate == 1

Step 4：執行 restore
  cp /tmp/restore_candidate <file>
  wc -c <file>（確認 restore 後非 0）

Step 5：Restore 後驗證
  wc -l <file>（確認行數合理）
  （若為 Python）執行相關 pytest 確認基礎功能正常
  （若為 Vue）確認 SFC 三段結構完整

Step 6：git commit
  git add <file>
  git commit -m "restore(<module>): recover <file> from <source>"

Step 7：出 restore report
  記錄 restore 來源、大小、驗證結果、後續風險
```

應明確禁止：在 Step 3 驗證通過前執行 restore。
應明確禁止：restore 後跳過 Step 5 驗證直接繼續功能開發。

---

## 6. Validation Plan（驗證修法是否有效）

### 6.1 追蹤指標定義

修法是否有效，不能只靠「沒有再發生」來判斷。以下為可量化的追蹤指標：

| 指標 | 測量方式 | 目標值 | 測量頻率 |
|---|---|---|---|
| 0KB 事故次數 | 每張票完成後查 `find . -size 0 -name "*.py" -o -size 0 -name "*.vue"` | 0 次 / 3 張票 | 每張票結束時 |
| Pre-Task Checklist 執行率 | 每張票 commit message 或 WP report 中是否有 checkpoint 記錄 | 100% | 每張票 |
| Post-Task 驗證執行率 | 每張票是否有 wc -c / wc -l 輸出記錄 | 100% | 每張票 |
| Level 1 檔案 whole-file write 次數 | git log 中是否出現大量行數驟降的 commit | 0 次 / 3 張票 | 每週回顧 |
| .tmp 殘留數量 | `find . -name "*.tmp"` | 0 個 | 每張票結束時 |
| Restore 操作次數 | WP report 中出現 "restore" 關鍵字的次數 | 趨勢下降 | 每月 |

### 6.2 未來 3~5 張票的追蹤計畫

**Ticket 1（下一張票）：**
- 目標：驗證 Pre-Task Checklist 是否被執行
- 驗證方式：票完成後確認有無 git checkpoint commit 記錄
- 驗證方式：確認所有修改檔案的 wc -c 輸出已記錄在 WP report 中
- Pass 條件：無 0KB 事故，有 checkpoint commit，有 post-edit wc 記錄

**Ticket 2：**
- 目標：驗證 Level 1 檔案是否確實使用局部 patch
- 驗證方式：`git log --all --oneline -- "*.vue" "*/schemas.py" "*/service.py" "conftest.py"`
- 驗證方式：對每個 Level 1 檔案的 commit，確認 diff 行數變化合理（無驟降至 0）
- Pass 條件：無 Level 1 整檔覆蓋，無 0KB

**Ticket 3：**
- 目標：驗證新建大型 Vue SFC 是否採用分段策略
- 驗證方式：git log 中新建 Vue 檔案的 commit 歷史（應有多個小 commit，而非一次完整）
- Pass 條件：新建大型 .vue 有骨架 commit + 後續 append commit

**Ticket 4~5：**
- 目標：判斷流程是否已穩定
- 驗證方式：統計 3~5 張票間的 0KB 事故總次數
- Pass 條件：0 次 0KB 事故，Pre/Post checklist 執行率 100%

### 6.3 判定新規則有效的條件

以下全部達成才可宣稱「修復方案有效」：

```
[VALID-1] 連續 5 張功能票，0KB 事故次數為 0
[VALID-2] 連續 5 張票，每張票均有 git checkpoint commit 記錄（Level 1 任務）
[VALID-3] 連續 5 張票，每張票均有 post-edit wc -c 記錄
[VALID-4] git log 中無 Level 1 檔案的大量行數驟降 commit
[VALID-5] find . -name "*.tmp" 持續為 0（無殘留）
```

任何一條未達成，不得宣稱方案有效。

### 6.4 再發時的升級策略

若本修復方案實施後仍再發 0KB：

**第 1 次再發：**
- 出 incident report，記錄「哪條規則失效、為何失效」
- 針對失效規則進行強化（更具體的操作指示）
- 不更換整體方案

**第 2 次再發（同類型）：**
- 判斷是否需要在 CI/CD 層加入自動化防護
  - 例：git pre-commit hook，對 Level 1 檔案偵測 0 bytes 並阻止 commit
  - 例：自動化腳本在每次 AI 操作後執行 `find . -size 0` 並告警
- 評估是否需要把 Write tool 限制為禁止對 Level 1 檔案使用

**第 3 次再發：**
- 升級到完全禁止 Write tool 對任何已存在檔案操作
- 所有現有檔案修改一律使用 StrReplace
- 評估是否需要引入外部 file integrity monitoring

---

## 7. Final Recommendation（最終建議）

### 7.1 下一步最應先做的一件事

**先建立 Operational Workflow，具體說：把 Pre-Task / Post-Task Checklist 加入每張票的標準結構。**

原因：
- 這是成本最低、效果最直接的第一步
- 不需要修改任何 production code
- 不需要修改任何治理文件（先驗證流程，再固化到文件）
- 即使規則文字沒有更新，只要每張票開始前都做 Pre-Task 確認，大部分 0KB 事故都可以在第一時間被攔截

### 7.2 三步推進順序

**Step 1（立即，本輪）：建立執行流程**
- 在每張 WP ticket 的描述中，加入標準化的 Pre-Task 和 Post-Task Checklist
- 確認下一張票（WP-S1-13 或其後）的 ticket 描述已包含這兩個 checklist
- 這不需要修改任何治理文件，只需要改任務描述的格式

**Step 2（近期，下 1~2 張票）：更新治理文件**
- 在 `CURSOR_FRONTEND_SAFE_EDIT_RULES.md` 中加入 Level 1 / 2 / 3 風險分級表
- 在 `CURSOR_DEVELOPMENT_RULES.md` 中加入強制 git checkpoint 規則
- 新增通用任務模板（CURSOR_TASK_TEMPLATE）作為每張票的起點
- 在執行流程已驗證有效後，再固化到治理文件，確保文件反映實際有效的流程

**Step 3（穩定後）：優化 Prompt 模板**
- 在執行流程穩定（5 張票無 0KB）之後，再回頭優化各 prompt 模板的文字
- 包含：Vue 頁面修改模板、Python 核心修改模板、事故調查模板、Restore 模板
- Prompt 模板修改應反映已被驗證有效的流程，而不是事先猜測什麼有效

### 7.3 為何不先改 Prompt 模板

本專案的歷史已清楚顯示：先寫規則（prompt 文字）無法防止事故。
正確順序是：先有可執行的流程閘門 → 驗證有效 → 再固化成文件和模板。
如果反過來，只是在已失效的規則基礎上再加更多文字，沒有實質效果。

### 7.4 本報告的後續使用方式

本報告（WP-INCIDENT_CURSOR_0KB_REMEDIATION_PLAN.md）應：
- 在每次 0KB 事故後被引用（確認哪條規則失效）
- 在每張票完成後被查核（驗證指標是否達成）
- 在 Step 2 執行時作為治理文件更新的依據
- 在 Step 3 執行時作為模板修改的基準

本報告不應被當成「已完成」就擱置。它是一個活文件，應隨著驗證結果持續更新。

---

## Appendix：本報告與既有文件的對應關係

| 本報告章節 | 對應既有文件 | 說明 |
|---|---|---|
| Section 3 風險分級 | `CURSOR_FRONTEND_SAFE_EDIT_RULES.md` | 現有規則缺乏明確分級，應補充 |
| Section 4A Pre-Task | `CURSOR_DEVELOPMENT_RULES.md` §14 | 現有 Session Handoff 規則缺乏 checkpoint 要求 |
| Section 4B In-Edit | `CURSOR_FRONTEND_SAFE_EDIT_RULES.md` §1-4 | 現有規則原則正確但缺操作細節 |
| Section 4C Post-Edit | `CURSOR_FRONTEND_SAFE_EDIT_RULES.md` §驗證段落 | 現有驗證項目缺乏行數/頭尾驗證 |
| Section 4D Incident | `WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md` §8 | 現有建議已有部分，需標準化 |
| Section 5 模板 | `docs/archive/notes/` Cursor 任務模板 | 現有模板需根本性更新 |
| Section 6 驗證 | `GATE_PROGRESS_TRACKER.md` | 應加入 0KB 事故追蹤欄位 |

---

*本報告完成。下一步：等待用戶確認後，依 Section 7.2 的三步順序推進。*  
*本輪未修改任何 production code、治理文件或 prompt 模板。*
