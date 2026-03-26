# Cursor Rule — Frontend Safe Edit Rules (Vue Focus)

## 適用範圍
所有前端檔案，特別是：

- `frontend/src/views/**/*.vue`
- `frontend/src/components/**/*.vue`
- `frontend/src/api/**/*.js`
- `frontend/src/stores/**/*.js`

重點高風險：
- Vue SFC（template + script + style）
- API client（client.js）
- admin / dashboard 頁面

---

# 🔴 核心原則（最高優先）

## 1. 強制 Patch-Style（禁止整檔重寫）
所有檔案修改必須：

- 採「最小差異修改（patch-style edit）」
- 禁止整檔覆蓋（full rewrite）
- 禁止先清空再重建
- 禁止重新生成整個檔案內容

若任務需要大改：
- 必須拆成多步驟
- 每步保持可驗證狀態

---

## 2. 禁止在異常檔案上寫入
若檔案為：

- 0 byte
- 結構缺失（Vue 缺 template/script/style）
- 明顯被截斷

👉 必須：

- 停止
- 回報
- 建議 restore（git / backup）
- 禁止自行重建

---

## 3. 寫入安全機制（強制）
所有寫入必須：

1. 寫入 `.tmp`
2. 檢查檔案大小（不可 0 byte）
3. rename 覆蓋
4. 重新讀取確認內容存在

任一步失敗 → **立即停止**

---

## 4. 不可使用對話內容當真實來源
禁止：

- 用 ChatGPT / Cursor 對話中的程式碼覆蓋檔案
- 用「記憶中的版本」重建檔案

必須以 **磁碟實際內容為準**

---

# 🟡 Vue 專用安全規則

## 5. 修改前完整性檢查
每次修改 `.vue` 前必須確認：

- 檔案非空
- `<template>` 存在
- `<script>` 或 `<script setup>` 存在
- `<style>` 存在

否則：停止

---

## 6. 一次只改一類事情
允許：

- 文案
- 單一 class
- 單一 icon
- 單一小區塊

禁止：

- layout + style + logic 同時改
- 多頁修改
- 重構 + UI 同時做

---

## 7. 結構修改必須先 Audit
若涉及：

- 刪除 template 區塊
- 移動區塊
- 調整 card / form / CTA

必須：

1. 先讀檔
2. 定位區塊
3. 回報
4. 等確認

---

## 8. 僅允許低風險直接修改
可直接改：

- 文字
- class
- icon path

不可直接改：

- 大區塊 template
- reactive state
- component 結構

---

# 🟠 API / Core 檔案保護（新增）

## 9. 高風險檔案禁止整檔操作
以下檔案屬高風險：

- `frontend/src/api/client.js`
- auth / config / env 類檔案

規則：

- 禁止整檔重寫
- 修改前必須：
  - 檢查大小
  - 確認 export 結構
- 修改後必須：
  - 確認關鍵 export 存在（如 `export default apiClient`）

---

## 10. Import/Export 不可隨意改動
禁止：

- default ↔ named export 隨意切換
- 修改 API client export 結構

除非：

- 有明確 audit
- 且為單一目標修復

---

# 🧠 AI 行為限制（關鍵補強）

## 11. 禁止 fallback 重建策略
當 AI 無法理解檔案時：

❌ 不可：
- 重寫整個檔案
- 自行補全缺失內容

✅ 必須：
- 停止
- 回報「無法安全修改」

---

## 12. 強制最小影響原則
每次修改必須：

- 只動指定檔案
- 只動指定區塊
- 不影響其他 module

---

# 🧪 修改後驗證（強制）

每次修改後必須回報：

### File Integrity
- non-empty: YES/NO
- template exists: YES/NO
- script exists: YES/NO
- style exists: YES/NO

### Scope Check
- only target file modified: YES/NO
- only target block modified: YES/NO

### Additional Check（API 檔）
- export structure intact: YES/NO

---

# 🧭 標準流程

## A. 小修改
1. 檢查
2. patch
3. 驗證

## B. 結構修改
1. audit
2. 確認
3. 單區塊修改

## C. 檔案異常
1. 停止
2. 回報
3. restore

---

# 🚨 禁止事項

- 整檔覆蓋
- 空檔寫入
- 用對話內容覆蓋
- 未 audit 刪大區塊
- 多類型修改混做
- 自行重構