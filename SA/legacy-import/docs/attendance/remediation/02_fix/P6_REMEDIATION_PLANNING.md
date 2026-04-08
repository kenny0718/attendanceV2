# P6 Remediation Planning Report

Status: Done

## 1. Summary

本報告依據既有 P1–P5 文件，將目前 Attendance remediation 問題收斂為可執行的 **fix ticket slicing**。

本次規劃的核心原則如下：

- 不重新分析問題，只收斂既有結論
- fix ticket 必須單一責任
- 避免單票同時觸碰多個高風險核心檔
- 先處理 **boundary owner / direct DB write / layer coupling** 等結構性風險
- 明確標記 **現在不該修** 的內容，避免修復票反向破壞 canonical 與既有 contract

綜合 P1–P5，現況可整理為：

1. **Semantic 基準已定案，不應再變動**
   - canonical = gross
   - break deduction = derived only
   - reporting = canonical consumer only

2. **Boundary 問題是目前最明確的前置 blocker**
   - P2 已確認 Taipei business-date owner 缺失
   - breaks 與 reporting 的 boundary contract 已分岔

3. **Breaks write path 與 layer boundary 已出現局部破口**
   - `update_punch_note()` 為 API direct DB write
   - `break-punches` 仍有 route-level boundary logic 與 direct ORM access

4. **Reporting 目前仍安全，但已出現 growth concentration**
   - 尚未越界成 semantic owner
   - 但 router/API 責任正在累積

5. **Coupling 問題已進入高風險核心檔層級**
   - `service.py`
   - `repo.py`
   - `policy_engine.py`
   - `api.py`
   - `api/breaks.py`

本報告最終建議採取：

- **先做最小安全修復集合**，只降低風險、不動 semantic
- **暫不進行大規模 decomposition / refactor**
- **高風險核心檔只允許極小、明確、可驗證的收斂票**

---

## 2. Issue Inventory

- issue: canonical semantic drift 風險仍存在，但語意本身已定案，不是待修語意決策
  - source: P1
  - category: Semantic

- issue: `work_hour_engine` ownership commentary 與正式 canonical owner 不完全一致
  - source: P1
  - category: Semantic

- issue: `canonical_minutes` / `work_minutes` / `duration_minutes` / `net_work_minutes` 命名並存，存在語意誤用風險
  - source: P1, P3_A1
  - category: Semantic

- issue: `punch_close_flow` vs `punch_close_domain` 命名存在 boundary drift risk
  - source: P1
  - category: Coupling

- issue: Attendance 模組內沒有明確單一 `Asia/Taipei` business-date owner
  - source: P2_A1
  - category: Boundary

- issue: `break-punches` 以 route 內 today 邏輯直接決定 boundary，明確不符合 Taipei business-date ownership
  - source: P2_A1, P2_A2
  - category: Boundary

- issue: reporting 與 breaks 使用不同 boundary contract，規則已分岔
  - source: P2_A2
  - category: Boundary

- issue: boundary responsibility 主要分散在 API / helper 層，尚未收斂成單一 owner
  - source: P2_A2
  - category: Boundary

- issue: breaks 相關 write path 僅部分集中，不是單一入口
  - source: P3_A2
  - category: Write Path

- issue: `update_punch_note()` 為 API direct DB write，繞過 repo / service
  - source: P3_A1, P3_A2
  - category: Write Path

- issue: breaks flow 存在 API direct ORM read/write，layer boundary 不穩
  - source: P3_A1, P5_A1
  - category: Write Path

- issue: break flow 與 missing-segment dry-run 有跨責任互動，雖未破壞 canonical，但屬邊界風險
  - source: P3_A1
  - category: Coupling

- issue: `punch_close_domain.py` schedule-aware path 以 `work_minutes` 寫入 `session.duration_minutes`，存在語意漂移風險
  - source: P3_A1
  - category: Semantic

- issue: reporting 仍為 consumer-only，但 `api/reporting.py` 已開始責任集中
  - source: P4_A1
  - category: Reporting

- issue: `api/reporting.py` 承擔 endpoint boundary、validation、permission gating、repo orchestration、display enrichment、response shaping，多責任逐漸集中
  - source: P4_A1
  - category: Reporting

- issue: reporting 對 canonical persisted duration 依賴很深，若未來越界會直接碰 semantic contract
  - source: P1, P4_A1
  - category: Reporting

- issue: legacy flow 與 new flow 在 `service.py` / `repo.py` 共檔共居
  - source: P5_A1
  - category: Coupling

- issue: `api.py` 與 `api/__init__.py` 同時像 router assembly surface，存在 mounting 歧義
  - source: P5_A1
  - category: Coupling

- issue: `api/punch.py` 在 punch-out 同時掌握 repo 與 service orchestration，close-flow owner 邊界不夠集中
  - source: P5_A1
  - category: Coupling

- issue: `policy_engine.py` 仍混有 basic / schedule-aware / façade 歷史層次，屬高風險核心檔
  - source: P5_A1
  - category: Coupling

- issue: schedule-aware new flow 測試覆蓋偏弱，形成結構盲區
  - source: P5_A1
  - category: Coupling

---

## 3. Fix Ticket Candidates

- ticket_id: P6_F1_BOUNDARY_OWNER_ALIGNMENT
  - description: 建立並收斂 Attendance 內單一 Taipei business-date boundary owner，先處理 breaks / reporting 的共用 contract 對齊，不碰 semantic
  - scope（檔案範圍）: `backend/app/modules/attendance/api/reporting_helpers.py`, `backend/app/modules/attendance/api/breaks.py`, boundary-related tests only
  - risk（Low / Medium / High）: Medium

- ticket_id: P6_F2_BREAK_PUNCHES_BOUNDARY_REALIGN
  - description: 將 `break-punches` 查詢對齊既定 Taipei boundary contract，消除 route-level today ownership 分岔
  - scope（檔案範圍）: `backend/app/modules/attendance/api/breaks.py`, `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
  - risk（Low / Medium / High）: Medium

- ticket_id: P6_F3_BREAK_NOTE_WRITE_PATH_REPOIZATION
  - description: 收斂 `update_punch_note()` 的 direct DB write，讓 break note update 回到單一路徑的 persistence contract
  - scope（檔案範圍）: `backend/app/modules/attendance/api/breaks.py`, `backend/app/modules/attendance/repo.py`, related break note tests
  - risk（Low / Medium / High）: Medium

- ticket_id: P6_F4_BREAKS_READ_LAYER_CLEANUP
  - description: 收斂 breaks read path 的 API direct ORM access，避免 break flow 同時存在 repo path 與直查 path
  - scope（檔案範圍）: `backend/app/modules/attendance/api/breaks.py`, `backend/app/modules/attendance/repo.py`, break read tests
  - risk（Low / Medium / High）: Medium

- ticket_id: P6_F5_PUNCH_OUT_ORCHESTRATION_BOUNDARY_GUARD
  - description: 將 punch-out close-flow 的 owner boundary 明文化並收斂到單一 orchestration surface，避免 API 同時掌握 repo 與 service 流程控制
  - scope（檔案範圍）: `backend/app/modules/attendance/api/punch.py`, `backend/app/modules/attendance/service.py`, `backend/app/modules/attendance/punch_close_domain.py`, targeted tests
  - risk（Low / Medium / High）: High

- ticket_id: P6_F6_SCHEDULE_AWARE_CANONICAL_GUARD
  - description: 消除 schedule-aware path 中 `work_minutes` 寫入 canonical 欄位的語意漂移風險，僅做 canonical guard，不改 semantic decision
  - scope（檔案範圍）: `backend/app/modules/attendance/punch_close_domain.py`, targeted schedule-aware tests
  - risk（Low / Medium / High）: High

- ticket_id: P6_F7_REPORTING_BOUNDARY_THINNING
  - description: 降低 `api/reporting.py` 的責任集中度，只處理 reporting router growth risk，不改 aggregation semantic
  - scope（檔案範圍）: `backend/app/modules/attendance/api/reporting.py`, `backend/app/modules/attendance/reporting_service.py`, reporting tests
  - risk（Low / Medium / High）: Medium

- ticket_id: P6_F8_ROUTER_ASSEMBLY_AUTHORITY_CLARIFICATION
  - description: 釐清 `api.py` 與 `api/__init__.py` 的 router assembly authority，降低 mounting ambiguity
  - scope（檔案範圍）: `backend/app/modules/attendance/api.py`, `backend/app/modules/attendance/api/__init__.py`, router tests
  - risk（Low / Medium / High）: Medium

- ticket_id: P6_F9_LEGACY_NEW_REPO_FILE_SPLIT_PLAN
  - description: 將 `repo.py` 內 legacy/new 共居問題拆成獨立治理票，僅做安全拆分規劃與最小遷移，不觸碰 canonical close path
  - scope（檔案範圍）: `backend/app/modules/attendance/repo.py`, import callers around repo
  - risk（Low / Medium / High）: High

- ticket_id: P6_F10_LEGACY_NEW_SERVICE_FILE_SPLIT_PLAN
  - description: 將 `service.py` 內 legacy/new 共居問題拆成獨立治理票，降低跨世代責任混居風險
  - scope（檔案範圍）: `backend/app/modules/attendance/service.py`, legacy/new callers around service
  - risk（Low / Medium / High）: High

- ticket_id: P6_F11_POLICY_ENGINE_EXPANSION_STOP_GUARD
  - description: 對 `policy_engine.py` 僅做 freeze-compatible guard 型修復，避免再吸入新責任；不做 policy semantic 變更
  - scope（檔案範圍）: `backend/app/modules/attendance/policy_engine.py`, policy-related tests
  - risk（Low / Medium / High）: High

- ticket_id: P6_F12_SCHEDULE_AWARE_TEST_COVERAGE_TICKET
  - description: 補 schedule-aware new flow 的最低必要覆蓋，讓高風險路徑具可驗證性
  - scope（檔案範圍）: schedule-aware tests only
  - risk（Low / Medium / High）: Low

### Ticket Slicing Judgment

上述 tickets 的切法遵守以下原則：

- 每張票只解一件事
- 不把 boundary、write path、reporting growth、legacy/new split 混成單票
- 高風險核心檔的票獨立存在，不與低風險票綁在一起
- 先做能降低風險但不改 semantic 的票

---

## 4. Execution Order

1. **P6_F1_BOUNDARY_OWNER_ALIGNMENT**
2. **P6_F2_BREAK_PUNCHES_BOUNDARY_REALIGN**
3. **P6_F12_SCHEDULE_AWARE_TEST_COVERAGE_TICKET**
4. **P6_F3_BREAK_NOTE_WRITE_PATH_REPOIZATION**
5. **P6_F4_BREAKS_READ_LAYER_CLEANUP**
6. **P6_F8_ROUTER_ASSEMBLY_AUTHORITY_CLARIFICATION**
7. **P6_F7_REPORTING_BOUNDARY_THINNING**
8. **P6_F5_PUNCH_OUT_ORCHESTRATION_BOUNDARY_GUARD**
9. **P6_F6_SCHEDULE_AWARE_CANONICAL_GUARD**
10. **P6_F11_POLICY_ENGINE_EXPANSION_STOP_GUARD**
11. **P6_F9_LEGACY_NEW_REPO_FILE_SPLIT_PLAN**
12. **P6_F10_LEGACY_NEW_SERVICE_FILE_SPLIT_PLAN**

### 執行順序判定原則

- **先做 boundary owner**：因為 P2 已明確 BLOCK，且 breaks / reporting 之間規則已分岔
- **再做 breaks 的最小讀寫收斂**：這些票風險比 close-flow 小，但能先降低 API direct DB / direct ORM 風險
- **中段處理 router / reporting growth**：先讓 assembly 與 reporting 不再持續擴張
- **後段才碰 close-flow / schedule-aware / policy_engine**：這些都是 High risk 核心區，必須在前置結構風險收斂後再做
- **legacy/new file split 類票最後做**：這是最接近治理性拆分的工作，不應在前面執行

---

## 5. Dependency Notes

### 必須先做的票

- `P6_F1_BOUNDARY_OWNER_ALIGNMENT`
  - 是 `P6_F2_BREAK_PUNCHES_BOUNDARY_REALIGN` 的前置票
  - 沒有 boundary owner，直接修 `break-punches` 只會止血，不會解分岔

- `P6_F12_SCHEDULE_AWARE_TEST_COVERAGE_TICKET`
  - 是 `P6_F6_SCHEDULE_AWARE_CANONICAL_GUARD` 與 `P6_F11_POLICY_ENGINE_EXPANSION_STOP_GUARD` 的風險前置票
  - 因 P5 已指出 schedule-aware 路徑測試偏弱

### 可並行票

以下可以在前置依賴成立後並行：

- `P6_F3_BREAK_NOTE_WRITE_PATH_REPOIZATION`
- `P6_F4_BREAKS_READ_LAYER_CLEANUP`
- `P6_F8_ROUTER_ASSEMBLY_AUTHORITY_CLARIFICATION`
- `P6_F7_REPORTING_BOUNDARY_THINNING`

理由：

- 都不是 canonical semantic 票
- 可以分別處理 write path、read path、router assembly、reporting growth
- 雖然都屬中風險，但彼此責任相對獨立

### 必須最後做的票

- `P6_F9_LEGACY_NEW_REPO_FILE_SPLIT_PLAN`
- `P6_F10_LEGACY_NEW_SERVICE_FILE_SPLIT_PLAN`

理由：

- 這兩張票雖然必要，但接近結構治理票
- 容易牽動 import path、caller 關係與測試依賴
- 不應在 boundary / write path / canonical guard 尚未穩定前執行

### High-risk 票之間的關係

- `P6_F5_PUNCH_OUT_ORCHESTRATION_BOUNDARY_GUARD`
- `P6_F6_SCHEDULE_AWARE_CANONICAL_GUARD`
- `P6_F11_POLICY_ENGINE_EXPANSION_STOP_GUARD`

這三張票不可合併成單票，原因：

- 一張票對 close-flow owner boundary
- 一張票對 schedule-aware canonical drift
- 一張票對 policy engine freeze-compatible guard

若合併，將同時碰 `api/punch.py`、`service.py`、`punch_close_domain.py`、`policy_engine.py`，風險過高。

---

## 6. Do-Not-Fix List

以下內容 **現在不應該修**：

- canonical = gross
- `session.duration_minutes` 的 canonical semantic
- break deduction = derived only 的正式決議
- reporting aggregation semantic（以 persisted canonical duration 聚合）
- policy semantic 本身
- 將 net minutes 升格為 canonical
- 任何把 break-adjusted duration 寫回 canonical 的設計
- `repo.close_session()` 的 canonical persistence contract 本身
- `policy_engine.py` 的大規模重構
- `service.py` / `repo.py` 的一次性大拆分
- reporting router / repo / service 的大規模重寫
- 大型 legacy removal
- 大規模 router 重建
- 對多個高風險核心檔的聯動 refactor
- 任何跨票一次處理 boundary + canonical + reporting + policy 的綜合修復

### Do-Not-Fix 原則

P6 的核心不是「一次把技術債做完」，而是：

- 固定語意
- 固定不可動契約
- 只切出最小、安全、可驗證的票

因此所有會造成 semantic 漂移、wide refactor、core file 大面積連動的事項，現階段都列入 Do-Not-Fix。

---

## 7. Minimal Safe Fix Set（建議先做）

建議先做的 **最小安全修復集合** 如下：

1. **P6_F1_BOUNDARY_OWNER_ALIGNMENT**
   - 理由：P2 明確 BLOCK，且屬後續所有 boundary 修復的前置基準

2. **P6_F2_BREAK_PUNCHES_BOUNDARY_REALIGN**
   - 理由：直接止住最明確的 boundary 錯位點

3. **P6_F3_BREAK_NOTE_WRITE_PATH_REPOIZATION**
   - 理由：收斂最明確的 API direct DB write

4. **P6_F4_BREAKS_READ_LAYER_CLEANUP**
   - 理由：降低 breaks flow 的 API direct ORM path，讓 read/write 契約更穩

5. **P6_F12_SCHEDULE_AWARE_TEST_COVERAGE_TICKET**
   - 理由：為後續高風險 canonical guard 票提供最低必要驗證面

### 為何這組是最小安全集合

這組票有以下特性：

- 不改 semantic
- 不碰 canonical formal decision
- 不直接大改 `policy_engine.py`
- 不直接大拆 `service.py` / `repo.py`
- 優先解掉已被 audit 明確標示的
  - boundary blocker
  - API direct DB write
  - breaks layer direct ORM path
  - schedule-aware coverage blind spot

### 這組票能降低哪些風險

可降低：

- Taipei boundary owner 缺失
- breaks / reporting boundary 分岔
- breaks API 直寫 DB 的 controllability 風險
- breaks API direct ORM access 的 layer coupling
- schedule-aware high-risk path 的不可驗證性

### 這組票暫時不處理哪些事

暫不處理：

- legacy/new service split
- legacy/new repo split
- policy engine 歷史層次清理
- reporting router growth 的中長期治理
- close-flow owner boundary 的完整收斂

也就是說，這組票的目標不是做完 remediation，而是先把 **最容易出事、但又能低回歸風險處理的項目** 壓住。
