# ACTIVE EXECUTION ORDER (SA2.1)

**Status**: ACTIVE SOT  
**Last Updated**: 2026-04-03  
**Source**: SA21_GAP_AUDIT_REPORT.md + SA21_REALIGNMENT_ROADMAP.md  
**Supersedes**: All prior WP control documents (archived in `docs/archive/260402/`)

---

## Purpose

本文件為 SA2.1 對齊後的**唯一開發執行順序來源**（Execution SOT）。

所有後續開發任務必須：
1. 依本文件 order 執行
2. 不可跳階段
3. depends_on 未完成不得開始
4. 任何新任務必須先更新本文件

---

## Rules

### 執行規則
- **P0 tickets** 必須全部完成，才能啟動 P1
- **P1 tickets** 必須達到 stable 狀態，才能啟動 P2
- **depends_on** 未完成的 ticket 不得開始
- 同一 phase 內的 ticket 可並行，但需遵守 depends_on 約束

### 修改規則
- 新增 ticket 必須明確標示來源（GAP REPORT / ROADMAP）
- 不得新增未在 GAP REPORT 或 ROADMAP 中出現的任務
- 任何 ticket 若涉及跨層改動（router + service + repo 同步）必須中止並重新切分
- 任何 ticket 若需要 whole-file rewrite 必須中止並重新切分

### 風險管理
- HIGH risk ticket 必須先完成 design/audit phase
- MEDIUM risk ticket 需要 code review 前置
- 若 runtime 證據不足，先標示 evidence gap，不可推測定論

---

## Execution Table

| order | ticket_id | name | type | status | depends_on | risk | can_start | phase |
|-------|-----------|------|------|--------|------------|------|-----------|-------|
| 1 | P0-1 | SOT Lock & Governance Update | docs | pending | - | LOW | YES | P0 |
| 2 | P0-2 | Frontend API Path Contract Alignment | audit | pending | P0-1 | MEDIUM | NO | P0 |
| 3 | P0-3 | Main Entry Boundary Plan & Design | design | pending | P0-1 | HIGH | NO | P0 |
| 4 | P1-1 | Attendance Service Boundary Split Plan | design | pending | P0-1, P0-3 | HIGH | NO | P1 |
| 5 | P1-2 | Reporting Router Thin-Layer Refine | design | pending | P0-1 | MEDIUM | NO | P1 |
| 6 | P1-3 | SchedulePage Decomposition Plan | design | pending | P0-1 | HIGH | NO | P1 |
| 7 | P2-1 | Leave Type Contract UX Alignment | design | pending | P1-1, P1-2 | MEDIUM | NO | P2 |

---

## Ticket Definitions

### P0-1: SOT Lock & Governance Update

**Goal**  
將新 SOT 文件（SA21_GAP_AUDIT_REPORT.md + SA21_REALIGNMENT_ROADMAP.md）正式納入開發讀取順序，並標記舊文件為 archived/superseded。

**Source**  
- ROADMAP: "SOT 對齊完成"
- GAP REPORT: "current source of truth statement"

**Do**
- 更新 `docs/00_AI_GOVERNANCE/CURSOR_READ_ORDER.md`，將新 SOT 加入強制讀取清單
- 在 `docs/03_WP_CONTROL/` 中新增 `_ARCHIVED_MANIFEST.md`，列出所有已歸檔文件與遷移說明
- 確認 `docs/archive/260402/` 目錄結構完整
- 更新本文件（ACTIVE_EXECUTION_ORDER.md）為正式 SOT

**Do NOT**
- 不修改任何 backend/frontend 程式碼
- 不刪除任何檔案（只標記為 archived）
- 不改變既有 API contract
- 不新增新的治理文件（只整理現有）

**Acceptance Criteria**
- CURSOR_READ_ORDER.md 已更新，新 SOT 在強制讀取清單中
- 舊文件已移至 archive 並有清晰索引
- 本文件（ACTIVE_EXECUTION_ORDER.md）已建立並可讀取

---

### P0-2: Frontend API Path Contract Alignment

**Goal**  
統一 frontend API wrapper 的路徑規則，消除 `baseURL + absolute path` 混用。

**Source**  
- GAP REPORT: "frontend API base path drift" (high-risk)
- ROADMAP: "API path contract 對齊治理"

**Do**
- 審計 `frontend/src/api/` 所有 wrapper 的路徑規格
- 確認 `client.js` 的 baseURL 設定與各 wrapper 的路徑一致性
- 特別檢查 `schedule.js` 的 `/api/v1/...` vs `attendance.js` 的 `/v1/...` 差異
- 產出「API Path Alignment Report」，列出所有不一致點與修正建議
- 不修改程式碼，只產出報告與修正清單

**Do NOT**
- 不改變 backend endpoint
- 不修改 frontend 程式碼（只做 audit）
- 不改變 API response contract
- 不新增新的 API wrapper

**Acceptance Criteria**
- API Path Alignment Report 已產出
- 所有路徑規格差異已列舉
- 修正建議已明確（可供後續 ticket 執行）

---

### P0-3: Main Entry Boundary Plan & Design

**Goal**  
拆出 `main.py` 的責任地圖，分離 startup wiring / demo hooks / debug endpoints，產出遷移設計。

**Source**  
- GAP REPORT: "`main.py` 責任過重" (high-risk)
- ROADMAP: "入口層責任收斂治理（設計與票分解）"

**Do**
- 分析 `backend/app/main.py` 的所有責任（app init / middleware / startup handlers / test event endpoints / router mounts）
- 產出「Main Entry Responsibility Map」，清晰區分：
  - production composition root（必須保留）
  - startup demo / test event（應分離）
  - router mount orchestration（應簡化）
- 設計分離方案（不實作），包括：
  - 新的目錄結構建議
  - 遷移步驟與風險評估
  - 各責任的新歸屬位置
- 產出「Main Entry Migration Plan」

**Do NOT**
- 不修改 `main.py` 程式碼
- 不改變啟動流程或路由掛載順序
- 不新增新的 endpoint
- 不刪除既有功能

**Acceptance Criteria**
- Main Entry Responsibility Map 已產出
- Main Entry Migration Plan 已產出
- 遷移風險已評估
- 後續實作 ticket 可基於此設計拆分

---

### P1-1: Attendance Service Boundary Split Plan

**Goal**  
定義 attendance close-flow 子域邊界，設計 missing-segment dry-run 與 punch 段推導的分離方案。

**Source**  
- GAP REPORT: "`attendance/service.py` 責任過寬" (high-risk)
- ROADMAP: "attendance service 邊界拆分"

**Depends On**
- P0-1 (SOT 已鎖定)
- P0-3 (main entry 邊界已清晰)

**Do**
- 分析 `backend/app/modules/attendance/service.py` 的所有責任
- 特別檢查 missing-segment dry-run input 建模與 punch 片段推導邏輯
- 產出「Attendance Service Responsibility Map」，區分：
  - core punch-in/out orchestration（必須保留）
  - missing-segment dry-run input 組裝（應分離為 adapter）
  - policy evaluation delegation（應保持）
- 設計分離方案，包括：
  - 新的 adapter/helper 層結構
  - service 與 adapter 的責任邊界
  - 遷移步驟與測試策略
- 產出「Attendance Service Split Plan」

**Do NOT**
- 不修改 `service.py` 程式碼
- 不改變 policy 計算語意
- 不搬動 policy 邏輯到 engine 或 repo
- 不改變 API contract

**Acceptance Criteria**
- Attendance Service Responsibility Map 已產出
- Attendance Service Split Plan 已產出
- 新 adapter 層的介面已定義
- 遷移風險已評估

---

### P1-2: Reporting Router Thin-Layer Refine

**Goal**  
確認 reporting router / service / repo 契約邊界，防止回流為單一大檔。

**Source**  
- GAP REPORT: "reporting 聚合責任雖已拆層，但仍需防膨脹" (medium-risk)
- ROADMAP: "reporting router 輕量化"

**Depends On**
- P0-1 (SOT 已鎖定)

**Do**
- 審計 `backend/app/modules/attendance/api/reporting.py` 的責任
- 檢查 `reporting_service.py` 與 `reporting_repo.py` 的邊界
- 確認 router 層是否仍保留過多流程組裝與 mapping 細節
- 產出「Reporting Layer Boundary Report」，列出：
  - 各層當前責任
  - 邊界清晰度評估
  - 潛在膨脹風險點
- 若發現邊界滲漏，產出「Reporting Refactor Plan」

**Do NOT**
- 不修改程式碼
- 不改變 response schema
- 不改變 query filter 規則
- 不新增新的 reporting 功能

**Acceptance Criteria**
- Reporting Layer Boundary Report 已產出
- 邊界清晰度已評估
- 若需要，Reporting Refactor Plan 已產出

---

### P1-3: SchedulePage Decomposition Plan

**Goal**  
規劃 `SchedulePage.vue` 的拆分策略，降低單頁責任密度。

**Source**  
- GAP REPORT: "`SchedulePage.vue` 體量與責任密度偏高" (high-risk)
- ROADMAP: "schedule view 去單點過載"

**Depends On**
- P0-1 (SOT 已鎖定)

**Do**
- 分析 `frontend/src/views/schedule/SchedulePage.vue` 的所有責任
- 按 template/assignment 子域拆分元件與狀態責任
- 產出「SchedulePage Responsibility Map」，區分：
  - template CRUD 邏輯
  - assignment CRUD 邏輯
  - inline edit 交互
  - UI state orchestration
- 設計拆分方案，包括：
  - 新的子元件結構
  - composable/store 邏輯分配
  - 狀態管理策略
- 產出「SchedulePage Decomposition Plan」

**Do NOT**
- 不修改 `SchedulePage.vue` 程式碼
- 不改變 API contract
- 不一口氣重寫整頁
- 不改變既有 UI 行為

**Acceptance Criteria**
- SchedulePage Responsibility Map 已產出
- SchedulePage Decomposition Plan 已產出
- 新元件結構已設計
- 遷移風險已評估

---

### P2-1: Leave Type Contract UX Alignment

**Goal**  
定義 leave type 可選資料來源契約，移除手動 UUID 輸入依賴。

**Source**  
- GAP REPORT: "leave frontend/backend contract 弱對齊" (medium-risk)
- ROADMAP: "leave type UX 對齊（避免 UUID 手輸）"

**Depends On**
- P1-1 (attendance service 邊界已清晰)
- P1-2 (reporting 邊界已確認)

**Do**
- 分析 `frontend/src/views/LeaveRequestView.vue` 與 backend leave type model 的契約
- 定義「leave type 可選清單」契約（只先定義，不先擴功能）
- 產出「Leave Type Contract Design」，包括：
  - leave type 資料來源（backend endpoint）
  - 前端選項清單的 UI 規格
  - 提交流程的改動
- 評估實作成本與風險

**Do NOT**
- 不修改程式碼
- 不破壞既有 create request flow
- 不新增新的 leave type
- 不改變 leave 審核流程

**Acceptance Criteria**
- Leave Type Contract Design 已產出
- 前後端契約已明確
- 實作成本已評估

---

## Phase Gates

### P0 Done 定義

P0 phase 完成時，系統應滿足：

1. **SOT 已鎖定**
   - 新 SOT 文件已納入強制讀取順序
   - 舊文件已歸檔並有清晰索引
   - 開發團隊已確認新 SOT

2. **API Path Contract 已審計**
   - 所有 frontend API wrapper 的路徑規格已列舉
   - 不一致點已明確
   - 修正建議已產出

3. **Main Entry 邊界已設計**
   - 責任地圖已產出
   - 遷移計畫已設計
   - 風險已評估

**P0 完成標誌**：上述三項全部完成，且無 blocker issue

---

### P1 Start 條件

P1 phase 可開始當且僅當：

1. P0 全部完成
2. 無 blocker issue
3. 設計文件已通過 review

**P1 預期交付**：
- Attendance Service Split Plan
- Reporting Layer Boundary Report
- SchedulePage Decomposition Plan

---

### P2 Start 條件

P2 phase 可開始當且僅當：

1. P1 全部達到 stable 狀態
2. 所有設計文件已通過 review
3. 無 blocker issue

**P2 預期交付**：
- Leave Type Contract Design
- 後續功能擴張的基礎

---

## Source Mapping

### P0-1: SOT Lock & Governance Update
- **Source**: ROADMAP § "SOT 對齊完成"
- **Source**: GAP REPORT § "current source of truth statement"

### P0-2: Frontend API Path Contract Alignment
- **Source**: GAP REPORT § "frontend API base path drift" (high-risk)
- **Source**: ROADMAP § "API path contract 對齊治理"

### P0-3: Main Entry Boundary Plan & Design
- **Source**: GAP REPORT § "`main.py` 責任過重" (high-risk)
- **Source**: ROADMAP § "入口層責任收斂治理（設計與票分解）"

### P1-1: Attendance Service Boundary Split Plan
- **Source**: GAP REPORT § "`attendance/service.py` 責任過寬" (high-risk)
- **Source**: ROADMAP § "attendance service 邊界拆分"

### P1-2: Reporting Router Thin-Layer Refine
- **Source**: GAP REPORT § "報表聚合責任雖已拆層，但仍需防膨脹" (medium-risk)
- **Source**: ROADMAP § "reporting router 輕量化"

### P1-3: SchedulePage Decomposition Plan
- **Source**: GAP REPORT § "`SchedulePage.vue` 體量與責任密度偏高" (high-risk)
- **Source**: ROADMAP § "schedule view 去單點過載"

### P2-1: Leave Type Contract UX Alignment
- **Source**: GAP REPORT § "leave frontend/backend contract 弱對齊" (medium-risk)
- **Source**: ROADMAP § "leave type UX 對齊（避免 UUID 手輸）"

---

## Important Notes

### What Must NOT Be Touched Early

根據 ROADMAP，以下項目在 P0 未完成前不可動：

1. 不可先動核心打卡語意（punch ownership / policy baseline semantics）
2. 不可先做 `main.py` 大重構
3. 不可先做跨模組大型搬遷（attendance ↔ schedule ↔ reporting 混改）
4. 不可在 P0 未完成前啟動新大功能擴張

### Stop Conditions

任一 ticket 若出現以下情況必須中止：

1. 涉及跨層改動（router + service + repo 同步）
2. 需要 whole-file rewrite
3. 無法保持既有 API contract
4. runtime 證據不足

---

## Maintenance

本文件應定期更新：

- 每個 ticket 完成後，更新 status 為 completed
- 若新增 ticket，必須明確標示來源
- 若發現新的 blocker，應立即更新並通知團隊
- 每月進行一次 alignment review

---

**Last Review**: 2026-04-03  
**Next Review**: 2026-05-03  
**Owner**: Architecture Team
