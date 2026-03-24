# Cursor Rule — Vue 頁面安全修改規則

## 適用範圍
所有 `.vue` 檔案，特別是：
- `frontend/src/views/**/*.vue`
- `frontend/src/components/**/*.vue`

尤其是：
- 含 `<template> + <script setup> + <style scoped>` 的 Vue SFC
- 表單頁
- dashboard / admin 頁
- 含 SVG icon / 多段 card / 多區塊 header 的頁面

---

## 核心原則

### 1. 禁止整檔重寫
對 `.vue` 檔案：
- 不可整份覆蓋
- 不可先清空再重建
- 不可根據對話上下文重建整頁
- 不可用「我推測原本內容」方式補檔

只能做：
- 局部修改
- 精準替換
- 小範圍 patch

---

### 2. 禁止在空檔狀態下修復
如果目標 `.vue` 檔案：
- 0 bytes
- 缺少 `<template>`
- 缺少 `<script>` 或 `<script setup>`
- 缺少 `<style>` / `<style scoped>`

則：
- 不可直接重建
- 不可憑對話內容補完
- 必須先停止並回報
- 優先建議使用 git restore / backup restore

---

### 3. 先檢查，再修改
每次修改 `.vue` 檔前，必須先檢查：
- 檔案非空
- 存在 `<template>`
- 存在 `<script>` 或 `<script setup>`
- 存在 `<style>` 或 `<style scoped>`

若任一不成立：
- 停止修改
- 先回報問題
- 不可直接寫入

---

### 4. 一次只改一類事情
對高風險 Vue 頁面，不可同時做多種不同層級變更。

允許：
- 只改文字
- 只改單一 icon path
- 只改一個按鈕 class
- 只移除一個已精準定位的小區塊

禁止一次混做：
- 改文字 + 改 layout + 改結構 + 改樣式 + 改 icon
- 重構 + 視覺調整 同時進行
- 多頁面大改後才驗證

---

### 5. 結構修改前先做 Mapping Audit
若需求涉及以下任一項：
- 刪除某段 template
- 移動區塊
- 調整 card header / form 區塊 / CTA 區塊
- 修改多個相似區塊中的其中一個

必須先做：
- 讀取檔案
- 找出精準區塊
- 回報位置與前後文
- 不先修改

確認後才能進下一步。

---

### 6. 禁止把對話內容當磁碟真實來源
不可將：
- 使用者先前貼過的程式碼
- 對話中的檔案片段
- 模型自己的回憶內容

當成磁碟上真實檔案內容直接寫回。

必須以目前實體檔案內容為準。
若磁碟內容異常，先停止並回報，不可自行重建。

---

### 7. 只允許低風險直接修改
以下類型可以直接做局部修改：
- 單行文字替換
- 單一 SVG `<path d="...">` 替換
- 單一 class 名稱調整
- 單一按鈕文案修改
- 單一標題修改

以下類型不可直接做，必須先 audit：
- 刪整段 header
- 重新組 template
- 調整大區塊 hierarchy
- 拆 component
- 重構 script / reactive state
- 從空檔補整頁

---

### 8. 修改後必須自我驗證
每次修改 `.vue` 後，必須回報：
- 目標檔案是否非空
- `<template>` 是否仍存在
- `<script>` / `<script setup>` 是否仍存在
- `<style>` / `<style scoped>` 是否仍存在
- 是否只修改指定檔案
- 是否只改到指定區塊

---

### 9. 高風險頁面優先建議拆分
如果頁面同時包含：
- header
- form
- submit area
- 多個 icon
- 多個 card
- 多個重複區塊

則後續開發建議先拆分成較小 component，再繼續 UI 修改。

但拆分本身屬高風險任務，必須獨立執行，不可順手混做。

---

## 標準執行流程

### A. 純文字 / icon 小修改
1. 檢查檔案完整性
2. 局部修改
3. 回報修改點
4. 不做其他額外變更

### B. 結構修改
1. 先做 mapping audit
2. 等使用者確認
3. 只改一個精準區塊
4. 回報修改區塊與檔案完整性

### C. 空檔 / 檔案損壞
1. 停止
2. 回報目前檔案異常
3. 建議 restore
4. 禁止自行重建

---

## 回報格式（固定）
每次修改 Vue 檔後，必須輸出：

1. Files changed
2. Exact changes made
3. File integrity check
   - non-empty: YES/NO
   - template exists: YES/NO
   - script exists: YES/NO
   - style exists: YES/NO
4. Risk note
5. Whether next step is safe: YES/NO

---

## 禁止事項（不可違反）
- 不可整檔覆蓋 Vue 頁面
- 不可在空檔上補內容
- 不可用對話中的程式碼覆蓋磁碟檔案
- 不可未經 audit 就刪除 template 大區塊
- 不可同時做結構重組與樣式微調
- 不可自行假設使用者要重構整頁