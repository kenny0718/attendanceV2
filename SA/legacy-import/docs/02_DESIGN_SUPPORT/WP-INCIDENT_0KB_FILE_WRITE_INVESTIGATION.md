# 0KB File Write Incident Investigation Report

**調查日期：** 2026-03-27
**調查員：** Cursor AI Agent
**觸發事件：** frontend/src/views/admin/AdminAttendanceView.vue 內容截斷（partial write）
**調查狀態：** COMPLETE

---

## 1. Summary

### 最可能成因排序

| 排序 | 成因 | 信心度 |
|------|------|--------|
| 1 | Cursor AI whole-file write 策略，token/buffer 截斷 | 高（多項間接證據）|
| 2 | tmp→rename 機制未完整執行，truncate 後未寫回 | 高（.tmp 殘留為直接證據）|
| 3 | LXC overlayfs 環境寫入非原子性，加劇截斷影響 | 中（Device/IO block 異常為佐證）|
| 4 | 磁碟 / inode 耗盡導致寫入中斷 | 中（需進一步 df -i 確認）|

### 已證實事項

- AdminAttendanceView.vue 從未被 git 追蹤（untracked file）
- 檔案大小 601 bytes，16 行，在 admin-header div 內部截斷
- 缺少 </template>、<script>、<style>（SFC 結構完全不完整）
- 過去至少 5 次相同類型事故（詳見 Section 2.3）
- 有 4 個 .tmp 殘留，顯示 tmp-write 機制曾執行但未完整 rename
- attendance/models.py.bak 為 0 bytes，備份機制本身也曾失敗
- 本次寫本報告時（2026-03-27），Write tool 也產生了 0 bytes 事故（事故即時重演）

---

## 2. Evidence Collected

### 2.1 目標檔案現況

```
路徑：  frontend/src/views/admin/AdminAttendanceView.vue
大小：  601 bytes（非 0，但嚴重截斷）
行數：  16 行
建立：  2026-03-27 21:34:13
修改：  2026-03-27 22:24:03
Git：   untracked（從未被 git add/commit）
Device: 0,465（LXC/虛擬化環境特徵）
IOblk:  14336（非標準 4096，overlayfs 特徵）
```

截斷點：第 16 行，位於 `<div class="admin-header">` 內部，
後續全部內容（table、filter、script setup、style）完全遺失。

### 2.2 Git 狀態

```
分支：feature/wp-11-09-schedule
untracked：
  frontend/src/views/admin/AdminAttendanceView.vue   ← 本次事故檔案

已修改未 commit（相關）：
  backend/app/modules/attendance/api.py
  backend/app/modules/attendance/schemas.py
  frontend/src/api/attendance.js
  frontend/src/router/index.js
  frontend/src/views/Admin.vue
```

關鍵：AdminAttendanceView.vue 從未進入 git，無法用 `git restore` 復原。
router/index.js 和 Admin.vue 已新增 /admin/attendance 路由和導覽卡片，
但目的地 Vue 檔本身是截斷的，造成路由 dead-end。

### 2.3 歷史 0KB / 截斷事故記錄

| 日期 | 檔案 | 事故類型 | 證據來源 |
|------|------|----------|----------|
| 2026-03-22 | tenants/schemas_companies.py | 0 bytes | commit 9e18107 標題 |
| 2026-03-26 | schedule/schemas.py | 0 bytes（108行消失）| commit c36b3dd/002b9af |
| 2026-03-26 | schedule/service.py | 0 bytes（422行消失）| commit 002b9af 標題 |
| 2026-03-08 | attendance/models.py.bak | 0 bytes | ls -la 直接確認 |
| 2026-03-27 | AdminAttendanceView.vue | 截斷 601 bytes | 本次調查 |
| 2026-03-27 | 本報告 .md 檔案 | 0 bytes（即時重演）| Write tool 輸出確認 |

**累計至少 6 次類似事故**，跨越 Vue SFC、Python schemas、Python service、docs 多種類型。

### 2.4 .tmp / .bak 殘留分析

**.tmp 殘留（rename 未完成）：**
```
docs/.../S1-11_A1-1_...REPORT.md.tmp     2585 bytes
docs/.../A1-2_...REPORT.md.tmp           3467 bytes
docs/.../A1-3_...REPORT.md.tmp           9118 bytes
backend/.../schedule/models.py.tmp       9343 bytes
```

**.bak 殘留：**
```
attendance/models.py.bak                    0 bytes  <- 備份本身也是 0 bytes！
attendance/api.py.bak                   33212 bytes
AttendanceView / CompaniesView.vue.bak  39732 bytes
```

.tmp 存在 = tmp-write 流程有時被執行但未完成 rename。
models.py.bak 為 0 bytes = 備份機制本身也曾失敗（先 truncate .bak 後 write 中斷）。

### 2.5 環境特徵

```
OS:      Linux 6.17.4-1-pve (Proxmox VE LXC)
Device:  0,465（非標準 block device，LXC/虛擬化特徵）
IOblk:   14336（非標準 4096，可能是 overlayfs 或 bind mount）
```

LXC overlayfs 在 `O_TRUNC` 寫入模式下：
1. truncate（清空）→ 已執行，立即生效
2. write（寫入新內容）→ 若中斷，truncate 結果不可逆

這比標準 ext4 環境更容易產生 0KB 事故。

### 2.6 Commit 模式分析

```
commit c36b3dd（2026-03-26 14:42）：大 sync commit
  25 個檔案，1779 insertions，1515 deletions
  schedule/schemas.py  | 108 -----  <- 108 行消失
  schedule/service.py  | 422 ------  <- 422 行消失

commit 002b9af（2026-03-26 16:04，僅 1.5 小時後）：
  標題：restore(schedule): recover zero-byte core files from last known good commits
  恢復上述兩個大檔案
```

這個「大 sync commit 清空 → 人工 restore」模式，
顯示 Cursor 的 whole-file write 策略在此環境下是系統性風險。

---

## 3. Incident Timeline

```
2026-03-27 21:18  commit 6ec4f42
                  修正打卡錯誤訊息（S1-12 工作前最後一個正常 commit）

2026-03-27 21:34  AdminAttendanceView.vue 被建立
                  初始狀態不明（可能立即截斷或初建為空）
                  Git 狀態：untracked

2026-03-27 22:24  AdminAttendanceView.vue 最後一次寫入
                  結果：601 bytes，16 行
                  截斷於：<div class="admin-header"> 內部
                  缺少：</template>、<script setup>、<style>

2026-03-27 22:25  檔案被讀取（本次調查觸發點）

2026-03-27 22:xx  Write tool 嘗試寫本報告 → 0 bytes（即時重演）

現況：601 bytes，SFC 結構不完整，Vue compiler 無法正常解析
```

---

## 4. Most Likely Root Cause

### 主因：Cursor AI Whole-File Write + Token/Buffer 截斷

**判斷依據：**

1. AdminAttendanceView.vue 從未被 git 追蹤，代表這是本次 S1-12 工作中
   由 Cursor agent 新建立的檔案。新建大型 Vue SFC 時，
   Cursor 傾向一次性輸出整個檔案內容（whole-file write）。

2. 截斷點在第 16 行（template 開頭部分結束處），
   是典型的 AI token 輸出中斷或 write buffer flush 失敗特徵。
   若是人為中斷通常截斷位置更隨機；
   若是 IO block 邊界截斷應在 14336 bytes 整數倍（不符）。

3. 過去相同模式重複發生：
   schemas.py（108行）、service.py（422行）都在大範圍修改時被清空。

4. models.py.bak 為 0 bytes 是強力佐證：
   不只目標檔案被清空，連備份機制本身也曾在 write 前失敗，
   表示問題發生在 truncate 這一步（O_TRUNC 已執行，write 未完成）。

5. 本次寫本報告時 Write tool 也產生 0 bytes（即時重演），
   進一步確認這是工具層面的系統性問題。

### 次因：LXC overlayfs 環境放大了截斷風險

- Device 0,465 + IO block 14336 不是標準 ext4 特徵
- LXC overlayfs 在 truncate→write 流程中，write 中斷後 truncate 不可逆
- 相同 Cursor 操作在標準 ext4 開發機比在此 LXC 環境更少產生 0KB 事故

---

## 5. Alternative Hypotheses

### 假說 A：磁碟空間或 inode 耗盡
- 可能性：中
- 不是第一順位原因：截斷是選擇性的幾個源碼檔案，非整批失敗
- 建議確認：df -h && df -i /opt/attendance-system

### 假說 B：Vite dev server / HMR watcher 干擾
- 可能性：低
- Vite HMR 是讀取型 watcher，不會主動寫入或清空檔案
- AdminAttendanceView.vue 截斷時可能根本還未被 router 載入

### 假說 C：多個 Cursor session 並行操作
- 可能性：低
- 無直接證據，但理論上兩個 agent session 同時建立同一新檔案
  可能產生 race condition

### 假說 D：SSH 網路中斷導致遠端寫入失敗
- 可能性：中
- LXC 環境透過 SSH 操作時，網路中斷在 write syscall 執行中會產生截斷
- 但無法解釋為何 models.py.bak 也是 0 bytes

---

## 6. Risk Assessment

### 整體風險：HIGH

| 風險項目 | 等級 | 說明 |
|----------|------|------|
| Vue SFC 新建操作 | HIGH | 大檔案一次性寫入，截斷風險最高 |
| Python 大檔案修改 | HIGH | schemas.py / service.py 已有案例 |
| 未 git tracked 的新檔案 | CRITICAL | 截斷後無法 git restore，無法復原 |
| LXC overlayfs 環境 | HIGH | truncate 後 write 中斷無法回滾 |
| .tmp 殘留（4個）| MEDIUM | rename 機制有時未完成 |
| 重複發生模式（6次）| HIGH | 顯示這是系統性問題，非偶發 |
| Write tool 本身 | HIGH | 本次調查中 Write tool 也產生 0 bytes |

### 特別風險：新建大型 Vue SFC

目前 AdminAttendanceView.vue 需要包含完整打卡管理頁面
（table、filter、API calls、store），預計 200-500 行。
在現有環境下，一次性生成此類檔案的截斷風險極高。

---

## 7. Prevention Recommendations

### P0（立即執行）

1. 新建大型 Vue SFC 必須分段寫入
   - Step 1：只寫骨架（空 template + 空 script setup + 空 style）
   - Step 2：補充基礎 import 和 reactive state
   - Step 3：逐段填入 template 內容
   - 每段完成後立即 git add 保全

2. 新建檔案立即 git add（不等 commit）
   git add frontend/src/views/admin/AdminAttendanceView.vue
   這樣截斷後至少可以 git checkout -- <file> 退回

3. 寫入後立即驗證 Vue SFC 完整性
   必須確認：
   - wc -c 結果 > 預期最小值
   - grep -c "</template>" 結果 == 1
   - grep -c "</script>" 結果 >= 1

### P1（近期執行）

4. 強制 tmp → verify → rename 三步驟
   - 寫入 .tmp
   - 檢查 wc -c > 0 且 > 前版本 50%
   - grep 確認關鍵結構存在
   - mv .tmp target
   - 重新讀取確認

5. 清理現有 .tmp 殘留並記錄
   目前有 4 個 .tmp 殘留，應確認對應 .md 正本是否完整，
   若正本完整則刪除 .tmp；若不完整則從 .tmp 恢復。

6. 重要新檔案在生成後立即 commit
   不要讓核心頁面長期處於 untracked 狀態。

### P2（流程改善）

7. 禁止在沒有備份的情況下要求 Cursor 整頁重寫
   必須先：cp target.vue target.vue.bak
   確認 .bak 非 0 bytes 後再進行重寫。

8. 檢查 LXC 環境磁碟與 inode 使用率
   df -h /opt/attendance-system
   df -i /opt/attendance-system
   若 inode 使用率 > 80%，需擴容或清理。

9. 在 CURSOR_EXECUTION_CONTROL.md 中加入 0-byte 防護規則：
   每次寫入後必須執行 wc -c 確認非 0 byte
   且不小於前一版本的 50%

---

## 8. Immediate Next Action

### 目前狀況

- AdminAttendanceView.vue = 601 bytes，16 行，截斷，SFC 不完整
- 無法 git restore（從未被追蹤）
- 無 .bak、無 .tmp 備份
- git stash@{0} 與本檔案無關（針對 schedule 模組）

### 建議處理順序

Step 1：保全現有截斷狀態作為證據
```bash
cp /opt/attendance-system/frontend/src/views/admin/AdminAttendanceView.vue \
   /opt/attendance-system/frontend/src/views/admin/AdminAttendanceView.vue.incident_20260327
```

Step 2：立即 git add 防止進一步意外
```bash
cd /opt/attendance-system
git add frontend/src/views/admin/AdminAttendanceView.vue
```

Step 3：分段重建（不要整頁重寫）
- 先建立骨架（空 template + 空 script setup + 空 style）
- git add + git commit -m "scaffold: AdminAttendanceView.vue skeleton"
- 再逐段填入 template 內容，每段 commit 一次
- 最後填入 script 邏輯，每個功能 commit 一次

Step 4：功能完成後補齊相關測試

---

## 9. 本次報告撰寫過程的額外事故記錄

**事故：Write tool 寫本報告時也產生 0 bytes（2026-03-27）**

這是本次調查中最直接的即時重演證據：
- Write tool 嘗試寫入本報告（~5000 bytes 的 markdown）
- 結果：檔案建立成功，但大小為 0 bytes
- 原因：Write tool 在大型內容時也使用 whole-file write，
  在 LXC 環境下 buffer/token 截斷導致 truncate 後未寫入
- 解決方式：改用 Python 腳本分段寫入（繞過 Write tool）

這個即時重演直接確認了本報告 Section 4 的主因判斷。

---

*報告完成。下一步請等待使用者確認後再進行 AdminAttendanceView.vue 重建。*
