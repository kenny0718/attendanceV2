AI_DEVELOPMENT_PROTOCOL.md 建議內容（你也可以直接複製貼到 repo）

這份是「你要的開發協議」，Cursor 之後每個 Unit 都用它來約束自己。

docs/AI_DEVELOPMENT_PROTOCOL.md（內容草案）
AI Development Protocol（Cursor Execution Contract）
1. Purpose

本文件定義打卡系統V2專案中，Cursor AI 的強制開發協議。
目標：防止 scope creep、避免跳 Gate、避免自行改規格、確保每一步可驗證且可追蹤。

2. Authority & Conflict Rules
2.1 Authority order（由高到低）

docs/GATE_BASED_DEVELOPMENT.md（流程與單元驗收）

docs/SA_MODULE_SPECV1.7.md（模組邊界 / Tenant & Backup 硬規則）

docs/SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md（架構與隔離原則）

docs/ACCEPTANCE_CHECKLIST.md（驗收方法與核對）

docs/GATE_PROGRESS_TRACKER.md（進度狀態，必須更新）

2.2 Conflict handling（衝突處理）

若 Authority 文件之間對同一議題（例如 403 vs 404、skip 是否允許、SQLite vs Postgres）出現矛盾：

不得自行選邊站

必須建立決策文件：docs/DECISIONS/DECISION_<topic>_<yyyymmdd>.md

在決策完成前：停止該 Unit 的 implementation（只允許做 investigation/docs）

3. Hard Rules（不可違反）

Sequential Only： 嚴格依 Gate 0 → Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 5

One Unit at a Time： 一次只做 1 個 Unit（例如 G3-02），不得順手做下一個

No Silent Refactor： 除非 Unit 明確要求，禁止重構/改命名/搬檔

Schema via Alembic Only： production schema 變更只能用 Alembic migration（不得 runtime create_all()）

Verification Required： 每個 Unit 必須在 commit 前通過該 Unit 的 Acceptance Criteria

Evidence Required： 不接受口述 PASS，必須貼證據輸出（見第 5 節）

4. Scope Contract（每次 Unit 必須先寫清楚）

每次開始 Unit，必須先宣告：

4.1 Allowed（允許修改）

明確列出允許修改的資料夾/檔案（最多 10 個）

若超出：必須先停下來，提出「Scope Expansion Request」

4.2 Forbidden（禁止修改）

至少包含：

不在本 Unit 列出的模組禁止變更

不得修改 unrelated tests 讓 suite “看起來 PASS”

不得新增 skip 來通過 Gate（除非既有文件授權且有決策記錄）

4.3 Scope Expansion Request（擴範圍申請）

若發現必須改到 Forbidden 區域才能完成：

先停下來

提交擴範圍提案：原因 / 影響 / 替代方案 / 最小修改清單

等確認後再動手

5. Evidence Policy（每次回報必須貼的證據）

任何 “PASS / Complete” 都必須包含以下證據（至少貼最後 10 行 summary）：

5.1 Git evidence

git rev-parse --abbrev-ref HEAD

git status --porcelain

git log --oneline -5

5.2 Test evidence（依 Unit 的 Test Command）

必須貼 pytest ... 的 summary 行（passed/failed/skipped/warnings）

若有 skipped，必須用 pytest -q -rs 列出 skipped reason（只貼 SKIPPED 段落）

5.3 Migration evidence（若 Unit 涉及 Alembic）

alembic current

alembic heads

upgrade/downgrade 證據（依 Gate 指令）

6. Test Strategy（不得自行改寫）
6.1 Definitions

Unit tests： 針對單一模組/單一 service/repo 的快速測試

Regression tests： Gate 文件列出的回歸測試集合（不得縮小）

Integration tests： 若未在 Authority 文件定義，需建立決策文件後才可新增規範

6.2 DB Strategy

若 Authority 文件未明確規定 SQLite vs PostgreSQL：

AI 不得自行宣告「SQLite 是既定策略」

必須建立 docs/DECISIONS/DECISION_TEST_DB_STRATEGY_<date>.md

7. Unit Execution Template（固定回報格式）

每次完成 Unit 回報必須用以下格式：

Unit ID / Name

Goal

Actions（逐步）

Files changed（新增/修改清單）

Test commands run（完整命令）

Evidence outputs（貼 summary / 重要片段）

Acceptance criteria checklist（逐條 ✅/❌）

Commits（hash + message）

Tracker update（哪一行改成什麼狀態）

8. Stop Conditions（遇到以下情況必須停）

規格/回應語意（403/404/empty）不明或矛盾

需要跨模組修改才能讓測試過

需要新增 skip/xfail 才能讓測試過

Gate 驗收要求的 regression tests 失敗

變更檔案數量/範圍超出 Allowed

停止時只能做：

investigation

docs（DEV_NOTES / DECISIONS）
不得繼續改 production code。

9. Tracker Update Rules

完成 Unit 後必須更新 docs/GATE_PROGRESS_TRACKER.md：

Status → ✅ Complete

Commit → 填入 code commit（不是 docs commit）

Date → Asia/Taipei

Notes → 簡述驗收證據（例如 “pytest suite PASS”）