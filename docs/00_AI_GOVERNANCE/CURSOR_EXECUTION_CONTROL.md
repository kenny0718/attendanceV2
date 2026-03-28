# Cursor Execution Control（強制）

本檔為所有修改的「最高優先規則」

---

# 1. 強制前置流程（不可跳過）

在任何修改前，必須先輸出：

1. Risk Level：

   * LOW
   * MEDIUM
   * HIGH

2. 是否需要停止 frontend dev server

3. 修改計畫（不可直接寫 code）

👉 未經使用者確認：
❌ 禁止寫檔

---

# 2. Risk Definition

## LOW

* 小範圍修改（幾行）
* 文案 / class / 小邏輯

## MEDIUM

* store / api / component 局部
* 多檔但小修改

## HIGH（關鍵）

* Vue 大頁（views）
* 大 store
* > 50 行修改
* 可能 whole-file rewrite

---

# 3. HIGH 修改強制流程

若為 HIGH：

1. 必須先提醒：
   👉「請先停止 frontend dev server（npm run dev）」

2. 未確認：
   ❌ 禁止修改

3. 修改完成後：

   * 必須提醒重新啟動

---

# 4. 寫檔安全（統一規則）

所有修改必須：

1. patch-style（禁止整檔）
2. tmp → rename
3. 驗證非 0 byte
4. 重新讀取確認

---

# 5. 0KB 防護

若發現：

* 檔案為 0 byte
* 結構缺失

👉 必須：

* 停止
* 回報
* 建議 git restore

❌ 禁止自行重建

---

# 6. Scope Control

* 僅修改指定檔案
* 不可擴散
* 不可順便重構
