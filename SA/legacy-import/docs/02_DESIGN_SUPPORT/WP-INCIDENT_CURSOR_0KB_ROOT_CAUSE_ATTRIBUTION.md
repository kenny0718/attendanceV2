# Cursor 0KB 寫檔事故責任分析報告

**文件類型：** Root Cause Attribution Report  
**日期：** 2026-03-29  
**分析範圍：** /opt/attendance-system 專案內所有已知 0KB / truncate / 異常覆蓋事故  
**分析員：** Cursor AI Agent（依用戶指令，僅分析、不修改任何功能檔案）  
**狀態：** FINAL

---

## 1. Summary — 直接判定

### 核心問題回答

**「這些 0KB 事故，是否主要是 Cursor 編輯流程問題？」**

**判定：是。主因為 Cursor workflow，環境為次因（放大因素）。**

| 責任層 | 比例估計 | 說明 |
|--------|----------|------|
| Cursor whole-file write 策略 | ~55% | 大檔案一次輸出、token 截斷、truncate 後未完成寫回 |
| Cursor prompt / 流程不合規 | ~20% | 已有 safe edit rule 仍未遵守，規則形同虛設 |
| LXC / overlayfs 環境放大 | ~20% | 使截斷後的不可逆性更強，但不是觸發主因 |
| 其他（磁碟、race condition 等）| ~5% | 無直接證據，僅為假說 |

**明確判定：混合責任，但以 Cursor workflow 為主（合計約 75%）。**

---

## 2. Incident Inventory — 已知事故清單

依據 WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md 及各 WP 報告交叉整理：

| # | 日期 | 檔案 | 類型 | 事故類型 | 發生時任務 | Whole-File? | 大檔案? |
|---|------|------|------|----------|------------|-------------|--------|
| 1 | 2026-03-22 | tenants/schemas_companies.py | Python schema | **0 bytes** | 大 sync commit 推斷（commit 9e18107）| 很可能是 | 是 |
| 2 | 2026-03-26 | schedule/schemas.py | Python schema | **0 bytes（108行消失）** | 大 sync commit（25 檔，1779 insertions）| **是** | 是（108行）|
| 3 | 2026-03-26 | schedule/service.py | Python service | **0 bytes（422行消失）** | 同上大 sync commit | **是** | 是（422行）|
| 4 | 2026-03-08 | attendance/models.py.bak | Python bak | **0 bytes** | 備份機制本身失敗 | 備份寫入 | 是 |
| 5 | 2026-03-27 | AdminAttendanceView.vue | Vue SFC | **截斷 601 bytes（16行）** | S1-12 新建大型 Admin 頁面 | **是（新建）** | 是（新建大型SFC）|
| 6 | 2026-03-27 | WP-INCIDENT 調查報告 .md | Markdown docs | **0 bytes（即時重演）** | Write tool 寫本次調查報告 | **是** | 是（約5000 bytes）|
| 7 | 2026-03-28 | backend/app/conftest.py | Python conftest | **0 bytes** | 不明（最後正常版在 2026-03-12）| 很可能是 | 是（4361 bytes）|

**累計：7 次已知事故（含 1 次調查過程中的即時重演）**

**跨越類型：Vue SFC、Python schemas、Python service、Python conftest、Markdown docs、備份檔**

**共通特徵：幾乎全部為大檔案 / 新建整頁 / 重寫整份檔案場景。**

---

## 3. Cursor Responsibility Analysis

### 3.1 支持 Cursor 為主因的證據

#### 證據 A：「即時重演」是最強直接證據

> 來源：WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md §9

Write tool 在撰寫調查報告本身時（約 5000 bytes markdown）也產生了 0 bytes 事故。這不是環境偶發問題，而是：
- 同一個 Write tool
- 同一個環境
- 同一次 session
- 直接重演了被調查的事故模式

**這是 Cursor 工具層面系統性問題的直接確認。環境因素（LXC/overlayfs）在此事故中是固定不變的，但 Write tool 本身成功地再現了事故，因此環境不是唯一原因。**

---

#### 證據 B：.tmp 殘留 = tmp→rename 流程中斷

> 來源：WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md §2.4

現場有 4 個 .tmp 殘留：

```
docs/.../S1-11_A1-1_...REPORT.md.tmp     2585 bytes
docs/.../A1-2_...REPORT.md.tmp           3467 bytes
docs/.../A1-3_...REPORT.md.tmp           9118 bytes
backend/.../schedule/models.py.tmp       9343 bytes
```

.tmp 存在代表 Cursor 確實執行了「寫到 .tmp」這個步驟，但後續的 rename 步驟未完成。rename 未完成的可能原因：
- token/buffer 耗盡，寫入中途停止
- session 中斷後沒有 cleanup
- Write tool 內部 error handling 不完整

**4 個殘留 .tmp 是 tmp→rename 流程結構性不完整的物理證據。**

---

#### 證據 C：models.py.bak 為 0 bytes = truncate 先於 write

> 來源：WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md §2.4

```
attendance/models.py.bak    0 bytes
```

備份機制本身也產生了 0 bytes。這表示：
1. truncate（清空 .bak）→ 已執行，成功
2. write（寫入備份內容）→ 中斷，未完成

這是 O_TRUNC 模式下「先清空後寫入」策略的直接風險：truncate 是不可逆的，write 一旦中斷就留下空檔案。**不只目標檔案，連備份本身的寫入機制也有相同問題，代表問題在寫入行為本身，而非特定檔案類型。**

---

#### 證據 D：commit 模式顯示「大 sync → 立即 restore」循環

> 來源：WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md §2.6

```
commit c36b3dd（2026-03-26 14:42）：25 個檔案，1779 insertions，1515 deletions
  schedule/schemas.py  | 108 lines 消失
  schedule/service.py  | 422 lines 消失

commit 002b9af（2026-03-26 16:04，1.5 小時後）：
  「restore(schedule): recover zero-byte core files from last known good commits」
```

這個「大範圍 sync commit 清空 → 人工 restore」模式清晰地顯示：
- Cursor 在大型操作時習慣整批輸出（whole-file write 到多個檔案）
- 輸出過程中某些檔案被截斷為 0 bytes
- 使用者被迫花時間手動 restore

**這個循環在本專案已至少發生 2 次（schemas + service，都在同一個 commit），是系統性問題而非偶發。**

---

#### 證據 E：截斷點符合 AI token 輸出中斷特徵

> 來源：WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md §4

AdminAttendanceView.vue 截斷於第 16 行（template 開頭部分結束處），後續全部內容消失。調查報告排除其他假說：
- 若是人為中斷：截斷位置更隨機
- 若是 IO block 邊界截斷：應在 14336 bytes 整數倍（實際 601 bytes，不符）
- 符合 AI token 輸出中斷或 write buffer flush 失敗特徵

---

#### 證據 F：已有 safe edit rule 仍然發生事故

> 來源：CURSOR_FRONTEND_SAFE_EDIT_RULES.md

專案在事故發生前已明確規定：
- 「禁止整檔覆蓋（full rewrite）」
- 「禁止先清空再重建」
- 「寫入 .tmp → 檢查大小 → rename 覆蓋 → 重新讀取確認」
- 「若檔案為 0 byte / 結構缺失 → 必須停止、回報」

**這些規則存在的情況下，事故仍然發生，代表 Cursor agent 在執行時並未遵守既有規則，規則的存在本身不足以防止事故。**

### 3.2 最可疑行為模式排序

| 排序 | 行為模式 | 信心度 | 直接證據 |
|------|----------|--------|----------|
| 1 | Whole-file write（大型新建/重寫）| 高 | 事故 #2/#3/#5/#6 全為此模式 |
| 2 | Token/buffer 截斷後 truncate 結果保留 | 高 | 截斷點特徵 + .bak 0 bytes 佐證 |
| 3 | tmp→rename 流程未完整執行 | 高 | 4 個 .tmp 殘留為物理證據 |
| 4 | 大 sync commit（多檔同時輸出）| 高 | commit c36b3dd 25 檔同時受影響 |
| 5 | safe edit rule 未被遵守 | 高 | 規則存在仍發生事故，即時重演確認 |

### 3.3 信心度評估

**Cursor 為主因：高信心度（85%+）**

根據：
- 1 次即時重演（同環境、同工具、同次 session）
- 4 個 .tmp 殘留（流程中斷物理證據）
- 備份本身也 0 bytes（問題在寫入行為而非特定檔案）
- 大 sync commit 模式反覆出現
- 規則存在仍未被遵守

---

## 4. Environment Responsibility Analysis

### 4.1 環境特徵

> 來源：WP-INCIDENT_0KB_FILE_WRITE_INVESTIGATION.md §2.5

```
OS:      Linux 6.17.4-1-pve（Proxmox VE LXC）
Device:  0,465（非標準 block device，LXC/虛擬化特徵）
IOblk:   14336（非標準 