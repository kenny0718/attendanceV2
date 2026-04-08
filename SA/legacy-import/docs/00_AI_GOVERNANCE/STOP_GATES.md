# STOP GATES — AI Execution Hard Rules

> **文件狀態**: ACTIVE — P0/P1 強制執行
> **適用對象**: 所有 Cursor AI Session
> **覆蓋優先級**: 本文件所列 Gate 規則高於任何任務 prompt 中的相反指示
> **最後更新**: 2026-03-30

---

## 前置聲明

本文件定義的 Stop Gates 為**硬性停止條件（Hard Stop）**，不得以任何理由繞過或降級。

所有 Gate 在以下三個階段均須檢查：

| 階段 | 說明 |
|------|------|
| **Pre-Execution** | 任務開始前，讀取文件後，寫檔前 |
| **During Execution** | 每次寫入或修改操作前 |
| **Before Commit** | 任何提交或交付前 |

**觸發任何 Gate → STOP IMMEDIATELY → 回報違規 → 等待人工指示**

AI **MUST NOT** 自行判斷是否可以繼續。自行繼續屬違規行為。

---

## 違規回報格式（強制）

任何 Gate 觸發時，MUST 依以下格式回報，不得省略任何欄位：

```
[STOP GATE TRIGGERED]
Gate ID          : <GATE-ID>
Priority         : <P0 / P1>
File             : <違規檔案路徑（若適用）>
Violation        : <具體違規原因>
CorrectiveAction : <建議的修正行動>
Status           : STOPPED — Awaiting human instruction
```

回報後 **MUST NOT** 繼續任何修改，直到人工明確指示。

---

## GATE-READ-ORDER [P0]

### 觸發條件

任務開始前未完整依序讀取以下四份文件，或順序錯誤、有跳過。

### 唯一允許的讀取順序

```
1. docs/00_AI_GOVERNANCE/CURSOR_EXECUTION_CONTROL.md
2. docs/00_AI_GOVERNANCE/CURSOR_FRONTEND_SAFE_EDIT_RULES.md
3. docs/00_AI_GOVERNANCE/CURSOR_BACKEND_SAFE_EDIT_RULES.md
4. docs/00_AI_GOVERNANCE/AI_CONTEXT.md
```

**此為唯一允許的讀取順序。MUST 完整依序讀取，不得調換、跳過、或部分讀取。**

### 關於 CURSOR_READ_ORDER.md

- `docs/00_AI_GOVERNANCE/CURSOR_READ_ORDER.md` 目前仍存在於目錄中
- 若其列出的讀取順序與本規則有差異，**以本文件（STOP_GATES.md）為準**
- **FORBIDDEN**: 以 `CURSOR_READ_ORDER.md` 單獨作為讀取順序的唯一依據
- `CURSOR_READ_ORDER.md` 不得取代上方四份文件的強制讀取要求

### 關於 AI_READ_ORDER.md

- 若 `AI_READ_ORDER.md` 存在於任何路徑，均屬 **DEPRECATED（棄用文件）**
- **FORBIDDEN**: 將 `AI_READ_ORDER.md` 視為有效的讀取順序依據
- **FORBIDDEN**: 以 `AI_READ_ORDER.md` 取代或補充上方指定的四份文件

### 強制規則

- **REQUIRED**: 每個 AI Session 開始時 MUST 完整讀取上方四份文件
- **FORBIDDEN**: 未完成上方讀取順序即開始任何檔案修改
- **FORBIDDEN**: 聲稱「已在之前的 session 讀過」而跳過讀取

---

## GATE-FILE-SIZE [P0]

### 觸發條件

任一 `.py` 檔案行數超過 **400 行**，且任務要求對該檔案進行以下任一操作：

- 新增函式（function / method）
- 新增業務邏輯
- 擴張現有 method 的邏輯
- 新增 endpoint

### 強制規則

- **FORBIDDEN**: 對超過 400 行的 `.py` 檔案新增任何函式、業務邏輯、或擴張 method
- **FORBIDDEN**: 以「只加一點點」為由繞過本 Gate
- **REQUIRED**: 觸發本 Gate 時，MUST 先提出 Decomposition Plan
- **REQUIRED**: Decomposition Plan 須包含：建議拆分的子模組名稱、各子模組職責、拆分後預估行數
- **FORBIDDEN**: Decomposition Plan 未經人工批准前，不得修改該檔案

### 檢查方式

Pre-Execution 階段 MUST 執行：

```bash
wc -l <target_file.py>
```

若結果 > 400，立即觸發本 Gate。

---

## GATE-CROSS-MODULE [P0]

### 觸發條件

生產程式碼中存在跨 module 的直接 import，或任務要求新增此類 import。

### 模組邊界定義

依據 `AI_CONTEXT.md` 的模組劃分：

| Module     | Path               |
|------------|--------------------|
| Auth       | `app/auth/`        |
| Attendance | `app/attendance/`  |
| Reporting  | `app/reporting/`   |
| WorkHour   | `app/workhour/`    |
| Core       | `app/core/`        |

### 強制規則

- **FORBIDDEN**: 生產程式碼中任何 module 直接 import 另一個非 `app.core` module 的內容
- **FORBIDDEN**: 例如 `app/attendance/` 中直接 `from app.reporting import ...`
- **FORBIDDEN**: 例如 `app/workhour/` 中直接 `from app.auth import ...`（`app.core` 除外）
- **ALLOWED**: 同 module 內部 import（same module imports）
- **ALLOWED**: 從 `app.core` import 共用工具、config、dependencies
- **REQUIRED**: Pre-Execution 階段發現既有跨 module import 違規，MUST 停止並回報，不得在違規狀態下繼續修改
- **REQUIRED**: 若任務本身要求建立跨 module 依賴，MUST 停止並回報，提出改用 `app.core` 的替代方案

---

## GATE-REPORTING-SCOPE [P1]

### 觸發條件

任務要求對 `app/reporting/` 相關檔案（特別是 `reporting.py` 或同等主檔案）進行以下任一操作：

- 新增 endpoint
- 新增 business logic
- 擴張現有 reporting 功能

### 鎖定條件

本 Gate 在以下條件解除前持續有效：

**Reporting Module Refactor 標記為 COMPLETE**

依據 `AI_CONTEXT.md`：Reporting Module Refactor 目前狀態為**未完成**。

### 強制規則

- **FORBIDDEN**: 在 Reporting Module Refactor 完成前，對 `reporting.py`（或 reporting module 主檔）新增任何 endpoint
- **FORBIDDEN**: 在 Reporting Module Refactor 完成前，對 `reporting.py` 新增任何 business logic
- **FORBIDDEN**: 以「緊急需求」或「小修改」為由繞過本 Gate
- **REQUIRED**: 若任務需要在 reporting 相關檔案加入功能，MUST 停止並回報衝突，說明與 Refactor 計畫的矛盾
- **REQUIRED**: 回報時須提供替代建議（例如：暫時在獨立的新檔案中實作，待 Refactor 完成後合併）

---

## Enforcement 區段

### 三階段強制執行

#### Pre-Execution（任務開始前）

MUST 依序完成以下檢查，任一失敗即 STOP：

1. **GATE-READ-ORDER**: 確認已讀完四份強制文件
2. **GATE-FILE-SIZE**: 若任務涉及 `.py` 檔案，確認目標檔案行數 ≤ 400
3. **GATE-CROSS-MODULE**: 確認任務不要求新增跨 module import
4. **GATE-REPORTING-SCOPE**: 確認任務不要求在 reporting 檔案新增功能

#### During Execution（修改過程中）

每次寫入前 MUST 重新確認：

- 寫入的內容不會引入跨 module import
- 寫入的內容不會使目標 `.py` 檔案超過 400 行且包含新函式
- 寫入的目標不是被鎖定的 reporting 檔案

#### Before Commit（提交前）

提交前 MUST 確認：

- 未修改任何 Forbidden Zone（`alembic/`、`tests/`、`.env*`、CI/CD 相關）
- 所有修改均在任務指定範圍內
- 無新增跨 module import

### 違規處理流程（MANDATORY）

```
1. 立即 STOP — 停止所有修改操作
2. 輸出 [STOP GATE TRIGGERED] 回報（使用本文件定義的回報格式）
3. 列出：違規檔案、違規原因、建議的 corrective action
4. 等待人工明確指示，MUST NOT 自行繼續
```

### 不可接受的行為（FORBIDDEN）

- **FORBIDDEN**: 自行判斷「這次違規可以忽略」
- **FORBIDDEN**: 以「任務緊急」為由繼續修改
- **FORBIDDEN**: 輸出回報後未等待人工指示即繼續
- **FORBIDDEN**: 只口頭提醒而不實際停止操作

---

## Scope Lock（本文件適用範圍）

本文件規則適用於所有在此專案執行的 AI Session。

以下範圍在任何情況下均受保護，Gate 違規時 MUST NOT 修改：

| 保護範圍 | 路徑 |
|----------|------|
| DB Migration | `alembic/` |
| Test Suite | `tests/` |
| Backend 生產程式碼 | `backend/` |
| Frontend 生產程式碼 | `frontend/src/` |
| Build Config | `*.config.js`, `vite.config.ts` |
| Env Files | `.env*` |
| CI/CD | `.github/`, `Dockerfile`, `docker-compose*` |

---

## 文件衝突處理

若本文件規則與其他治理文件出現衝突：

- **本文件（STOP_GATES.md）規則優先**
- MUST 停止並回報衝突，不得自行裁量
- 等待人工解決衝突後再繼續

---

*Last Updated: 2026-03-30*  
*文件狀態: ACTIVE — 不得自行修改或降級本文件的任何規則*
