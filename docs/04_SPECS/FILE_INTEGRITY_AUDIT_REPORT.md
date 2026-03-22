# File Integrity Audit Report

**調查對象：** `backend/app/modules/tenants/api.py`、`backend/app/modules/tenants/schemas.py`  
**調查日期：** 2026-03-22  
**調查類型：** Read-only investigation — 無任何程式碼修改  
**調查人：** AI Audit Session  

---

## 1. Summary

### 問題描述

`tenants/api.py` 與 `tenants/schemas.py` 在多個 WP 開發週期中反覆出現 **0 bytes（空檔案）** 的狀態。每次 AI（Cursor）開始新的 WP 工作時，都需要先透過 `git restore` 還原這兩個檔案才能繼續開發。

### 發生頻率（依 git log 觀察）

| Commit | 日期 | Commit Message 中記錄的事件 |
|--------|------|------------------------------|
| `cdc4063` WP-S1-09C | 2026-03-20 18:45 | schemas.py was found empty (0 bytes) — restored from git HEAD |
| `60509ba` WP-S1-10B | 2026-03-21 13:20 | Git restore: schemas.py and api.py (were 0 bytes) |
| `dd26bfb` WP-S1-10C | 2026-03-21 13:32 | Git restore: api.py + schemas.py were 0 bytes at start |

**在 12 小時內（2026-03-20 18:45 到 2026-03-21 13:32）至少發生 3 次。WP-S1-10B 與 10C 在同一天、相差僅 12 分鐘各發生一次。**

---

## 2. Findings

### 2.1 Git 層分析

**關鍵發現：**

1. **兩個檔案在 git 中一直有內容**  
   查閱所有 commit 的 diff，每次 commit 時這兩個檔案都是正常的 append-only 增量 diff（只有 `+` 行，沒有 `-` 行），代表 0 bytes 問題**從未進入 git commit**。

2. **問題發生在 working tree，不在 git history**  
   0 bytes 狀態只存在於 AI 工作 session 期間的磁碟上，每次 commit 前已透過 `git restore` 修復。

3. **WP-S1-09B commit（`9c840188`）是可疑的起點**  
   該 commit 一次性包含了 `api.py` 和 `schemas.py` 的 76 + 37 行新增。Commit message 說明是「補齊 WP-S1-08A/B/C 和 09A 的 artifacts」，意味著這是一次補寫提交，可能在寫入過程中就已發生截斷。

4. **問題在 commit 之間的 session 轉換時發生**  
   WP-S1-09B 之前的 commit（`7467cd7`）的 `schemas.py` 已有 3,218 bytes。09B 提交後內容正常。但 09C 開始工作時 `schemas.py` 又回到 0 bytes，說明問題發生在「上一個 session 結束、下一個 session 開始」的時間點。

5. **git stash 存在**  
   `stash@{0}` 保存了舊的 attendance `api.py` WIP，與 tenants 無關，但說明有 stash 操作歷史，可能存在殘留風險。

**各 commit 的檔案大小演進：**

| Commit | api.py | schemas.py |
|--------|--------|------------|
| `7467cd7` WP-11-04A | 5,447 bytes | 3,218 bytes |
| `9c840188` WP-S1-09B | 正常（含 76 行新增） | 正常（含 37 行新增） |
| session 結束後（推測） | **0 bytes** | **0 bytes** |
| `cdc4063` WP-S1-09C commit | 正常（git restore 後 +114 行） | 正常（git restore 後 +55 行） |
| session 結束後（推測） | **0 bytes** | **0 bytes** |
| `60509ba` WP-S1-10B commit | 正常（git restore 後 +67 行） | 正常（git restore 後 +29 行） |
| 12 分鐘後（推測） | **0 bytes** | **0 bytes** |
| `dd26bfb` WP-S1-10C commit | 正常（git restore 後 +78 行） | 正常（git restore 後 +14 行） |
| 2026-03-22 現在 | 17,720 bytes | 8,752 bytes |

---

### 2.2 寫檔模式分析

`api.py` 與 `schemas.py` 的成長模式為高頻、漸進式 append——每個 WP 都對**同一個檔案**新增內容：

| WP | api.py 新增行數 | schemas.py 新增行數 |
|----|----------------|--------------------|
| WP-S1-09B | +76 行 | +37 行 |
| WP-S1-09C | +114 行 | +55 行 |
| WP-S1-10B | +67 行 | +29 行 |
| WP-S1-10C | +78 行 | +14 行 |

這正是觸發 Cursor IDE 寫檔問題的高風險模式：每次 AI 操作都需要對一個**越來越大的檔案**執行 full rewrite。

`api.py` 中存在 **4 處分散的 import block**（頂部 1 次 + mid-file 3 次），是 append 式開發積累的直接證據，也說明每次寫入時 AI 都在做完整的檔案重寫而非 patch。

---

### 2.3 Cursor / IDE 行為推測

**核心推測機制：**

Cursor AI 在執行「修改檔案」時有兩種模式：

- **StrReplace（patch 模式）**：只替換目標片段，風險低
- **Write（full overwrite 模式）**：先清空（truncate）再寫入全部內容

當 AI 使用 Write 工具時，作業系統層的操作順序是：

```
open(file, 'w')   # 立即清空（truncate to 0 bytes）
write(content)    # 寫入內容
close()           # 關閉檔案
```

若 `write()` 步驟在以下情況失敗，檔案就會停留在 **0 bytes**：

- AI 生成的內容超過 context / token limit 被截斷
- Session 超時或 IDE 連線中斷
- AI 判斷「重新整理整個檔案」比較安全，但生成到一半就失敗
- 分段生成時，第一段成功清空、第二段失敗

**高風險場景：連續 session 的 full rewrite**

WP-S1-10B 和 10C 發生在同一天 13:20 和 13:32，相差僅 12 分鐘。在這麼短的時間內連續對同一檔案進行多次 full rewrite，極可能發生：

```
Session A 結束前：open('api.py', 'w') → 清空 → 寫入完成 → commit
Session B 開始時：open('api.py', 'w') → 清空 → 寫入失敗 → 0 bytes
```

---

### 2.4 風險最高原因（排序）

| 排名 | 原因 | 依據 |
|------|------|------|
| #1（最高） | Cursor Write 工具對長檔案執行 full overwrite，open('w') 先清空，若寫入未完成則留下 0 bytes | 每次事件都在 WP 開始時發現；AI_DEVELOPMENT_RULES.md §4、§5 已明確記錄此風險 |
| #2 | 同一 session 內 AI 多次修改同一檔案，第二次 Write 清空了第一次的結果，第二次生成又失敗 | WP-S1-10B 和 10C 在 12 分鐘內連續發生 |
| #3 | AI 誤判需要重整整個檔案並執行 truncate + rewrite，但因 token 生成中斷只完成了清空 | 這兩個檔案是 backend 中被最頻繁 append 修改的檔案 |
| #4 | 前一個 WP session 結束後，AI 執行了某個清理操作意外清空了這兩個檔案 | 每次都是「session 開始時發現 0 bytes」而非「session 中途」 |

---

## 3. Most Likely Root Cause

### Root Cause #1（最高可能性）

Cursor AI 對 `api.py` / `schemas.py` 執行 Write（full file overwrite）操作時，作業系統在 `open(file, 'w')` 時立即 truncate 到 0 bytes，而後續的 `write(content)` 因 token limit 耗盡、session 結束或生成失敗而未能完成，導致檔案停留在 0 bytes。

**支撐證據：**

- `AI_DEVELOPMENT_RULES.md` §4「Empty File Protection」與 §5「File Rewrite Safety」明確寫道這是已知風險
- 每次 0 bytes 事件都在「新 WP session 開始時」發現，符合「前一個 session 結束前執行了 Write 但未完成」的時序
- 這兩個檔案是整個 backend 中被 AI 最頻繁 append 修改的檔案（每個 WP 都要加新 endpoint）

### Root Cause #2（次高可能性）

在單一 WP session 中，AI 對同一個檔案執行了多次 Write 操作，第二次 `open(file, 'w')` 清空了第一次的結果，而第二次生成失敗或被截斷，造成 0 bytes。

**支撐證據：**

- WP-S1-10B 和 10C 在 12 分鐘內各發現一次 0 bytes，頻率異常高
- `api.py` 在每個 WP 都有多個 endpoint 被加入，AI 可能分多步寫入

---

## 4. Reproduction Hypothesis

### 可能的重現步驟

```
前置條件：
  - api.py 或 schemas.py 已有 200 行以上內容（約 8,000 bytes 以上）
  - 開始一個新的 Cursor AI session

觸發步驟：
  1. 指示 AI 對 api.py 新增一個完整的 endpoint
     （包含 imports、router decorator、handler、error handling）
  2. AI 選擇 Write 工具（full overwrite）而非 StrReplace（patch）
  3. AI 開始生成完整檔案內容
  4. 生成過程因任一原因中斷（token limit / 網路 / timeout）
  5. 結果：api.py = 0 bytes

最高風險組合：
  - 連續兩個 session 在 15 分鐘內都對同一個大型檔案執行 Write
  - 每次 session 都需要 append 100 行以上的新內容
```

---

## 5. Risk Assessment

### 對開發流程的影響

| 影響面向 | 說明 |
|----------|------|
| **開發進度** | 每次發生 0 bytes 事件，需要額外 5-15 分鐘進行 git restore 和驗證。已發生至少 3 次，合計損失約 30-45 分鐘 |
| **資料安全** | 若 0 bytes 在 commit 前未被發現直接提交，會導致功能喪失；雖然可用 git revert，但會打亂開發節奏 |
| **測試可靠性** | 0 bytes 的 api.py 會導致 uvicorn 啟動失敗，所有 API 測試都會失敗，可能被誤判為測試本身的問題 |
| **AI 協作信任** | 反覆發生的 0 bytes 事件會讓開發者對 AI 工具產生不信任，增加手動驗證的負擔 |
| **未來風險趨勢** | api.py 目前已達 17,720 bytes，schemas.py 已達 8,752 bytes，兩個檔案仍在成長，full rewrite 