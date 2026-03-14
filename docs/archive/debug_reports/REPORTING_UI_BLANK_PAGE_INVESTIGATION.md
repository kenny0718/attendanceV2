# REPORTING_UI_BLANK_PAGE_INVESTIGATION

**調查日期：** 2026-03-14
**症狀：** 瀏覽 `http://192.168.88.164/attendance/reports/sessions` 整頁空白，DOM 只有 `<div id="app"></div>`

---

## 1. 目前 Serving 模式

| 項目 | 實際狀態 |
|------|----------|
| Serving 方式 | **Nginx 靜態 dist**（非 Vite dev server） |
| Nginx root | `/opt/attendance-system/frontend/dist` |
| SPA fallback | `try_files $uri $uri/ /index.html` — 設定正確 |
| API proxy | `/api/` → `http://127.0.0.1:8000` |
| Nginx 狀態 | active (running)，自 2026-03-05 起持續運行 |
| dist/index.html | 存在，HTTP 200 |
| JS bundle | `/assets/index-B3l4BhXx.js` HTTP 200 |
| CSS bundle | `/assets/index-d7zKy1Hf.css` HTTP 200 |

---

## 2. 根本原因：dist 為舊版 build，不含 Reporting UI

### 關鍵證據

| 檔案 | 最後修改時間 |
|------|-------------|
| `dist/assets/index-B3l4BhXx.js`（目前 bundle） | **2026-03-11 16:53** |
| `src/stores/reporting.js` | 2026-03-14 10:22 |
| `src/views/reports/AttendanceSessionsPage.vue` | 2026-03-13 22:38 |
| `src/views/reports/CompanySummaryPage.vue` | 2026-03-13 22:38 |
| `src/views/reports/UserSummaryPage.vue` | 2026-03-13 22:38 |
| `src/components/StatusBadge.vue` | 2026-03-13（新增）|
| `src/components/MonthPicker.vue` | 2026-03-13（新增）|

**結論：dist bundle 建立於 3月11日，Reporting UI 原始碼建立於 3月13日。dist 從未重新 build。**

### 字串搜尋確認

```
strings /opt/attendance-system/frontend/dist/assets/index-B3l4BhXx.js \
  | grep -E 'reports/sessions|company-summary|user-summary|AttendanceSessions'
```

**輸出：空（0 筆）**

舊 bundle 完全不含任何 reporting route、reporting store、reporting 元件的程式碼。

### dist 內容確認

```
dist/assets/
  Home-BrTzvsAY.css
  Home-DCN6nNUX.js
  index-B3l4BhXx.js
  index-d7zKy1Hf.css
  Login-BJ2Vlwea.js
  Login-hZZlHQDw.css
```

只有 Home 和 Login 的 chunk，**沒有任何 reporting 相關 chunk**。

---

## 3. 根本原因候選（按可能性排序）

### [CONFIRMED] #1 — dist 未重新 build，Reporting UI 程式碼從未打包

**可能性：100%（已確認）**

- Nginx 伺服 `/opt/attendance-system/frontend/dist`
- dist 建立於 2026-03-11，Reporting UI 原始碼建立於 2026-03-13
- bundle 內無任何 reporting 相關字串
- 瀏覽器訪問 `/attendance/reports/sessions` 時，Nginx `try_files` 正確回傳 `index.html`
- 但 `index.html` 載入的 JS bundle 中不含該路由的元件，Vue Router 找不到對應元件
- Vue Router 在無對應 route 時不渲染任何內容（`<router-view>` 空白）
- 結果：`#app` 內只有空的 `<router-view>`，頁面空白

### [NOT CONFIRMED] #2 — Home.vue build error 造成 build 失敗

**可能性：高（需驗證）**

已知 `Home.vue` 末尾被截斷（第 299 行 `return '✓ ` 不完整），`vite build` 會拋出：

```
[vite:vue] src/views/Home.vue (215:1): Element is missing end tag
```

這可能是無法重新 build 的直接原因。若嘗試 `npm run build`，build 會因 `Home.vue` syntax error 而失敗，無法產生新的 dist。

### [ELIMINATED] #3 — Nginx SPA fallback 設定錯誤

**可能性：0%（已排除）**

`try_files $uri $uri/ /index.html` 設定正確，訪問 `/attendance/reports/sessions` 會正確回傳 `index.html`（HTTP 200 確認）。

### [ELIMINATED] #4 — JS/CSS assets 無法載入

**可能性：0%（已排除）**

`/assets/index-B3l4BhXx.js` HTTP 200，`/assets/index-d7zKy1Hf.css` HTTP 200，assets 正常載入。

### [ELIMINATED] #5 — app bootstrap / Vue mount 失敗

**可能性：0%（已排除）**

`/`（Home 頁）可正常顯示，表示 Vue app 可以正常 mount。問題只發生在 reporting routes，確認是 router 找不到元件，非 app bootstrap 失敗。

### [ELIMINATED] #6 — Reporting UI 元件程式碼錯誤

**可能性：0%（此情境下不相關）**

Reporting UI 元件根本未被打包進 dist，因此不可能是元件程式碼造成空白。元件程式碼是否正確與目前症狀無關。

---

## 4. 問題分類

| 問題類型 | 是否為根本原因 |
|---------|---------------|
| **app bootstrap issue** | 否 — Vue app 在 Home 頁正常運作 |
| **router issue** | 部分 — Router 無法找到 reporting 元件，因元件未被打包 |
| **nginx/proxy issue** | 否 — SPA fallback 設定正確，HTTP 200 |
| **reporting page issue** | 否 — 元件未被打包，無法評估 |
| **build/deployment issue** | **是 — 根本原因：dist 從未重新 build** |

---

## 5. 完整問題鏈

```
1. Reporting UI 原始碼建立於 2026-03-13（新增 9 個檔案，修改 2 個）
2. 開發者從未執行 npm run build
   └─ 原因可能是：Home.vue 截斷問題導致 vite build 失敗
3. Nginx 繼續伺服舊 dist（2026-03-11 版本）
4. 瀏覽器請求 /attendance/reports/sessions
5. Nginx try_files 正確回傳 index.html（HTTP 200）
6. index.html 載入舊 bundle（index-B3l4BhXx.js）
7. 舊 bundle 中 Vue Router 沒有 /attendance/reports/* 路由定義
8. router-view 不渲染任何元件
9. 頁面空白，#app 只有空的 router-view
```

---

## 6. 需要修改的檔案

**（僅列出，不做修改）**

### 必須修復（阻礙 build）

| 檔案 | 問題 | 需要的修改 |
|------|------|------------|
| `frontend/src/views/Home.vue` | 檔案末尾被截斷，缺少完整的 `</script>` 和 `</template>` 結尾 | 補全缺失的結尾標籤 |

### 修復後執行

```bash
cd /opt/attendance-system/frontend
npm run build
# 確認 dist/assets/ 出現 AttendanceSessionsPage / reporting 相關 chunk
# 重新載入 Nginx（通常不需要，nginx 直接讀取新檔案）
```

---

## 7. 最小修復路徑

**Step 1（必要）：修復 Home.vue 截斷問題**

`Home.vue` 在第 299 行截斷於 `return '\u2713 `（不完整字串），缺少：
- `getStatusLabel` function 的剩餘內容
- `onMounted` / 其他 lifecycle hooks
- `</script>` 結尾

**需要補全 Home.vue 的缺失程式碼，或從 backup 還原。**

確認 backup 存在：
- `frontend/src/views/Home.vue.backup_before_3card`
- `frontend/src/views/Home.vue.backup_before_singlecol`
- `frontend/src/views/Home.vue.backup.phase2b`

**Step 2（必要）：重新執行 build**

```bash
cd /opt/attendance-system/frontend && npm run build
```

Build 成功後 dist 會包含所有 reporting 路由的 chunk，頁面即可正常顯示。

**Step 3（驗證）：確認 reporting chunk 存在**

```bash
ls /opt/attendance-system/frontend/dist/assets/ | grep -i report
```

---

## 8. 結論摘要

| 問題 | 答案 |
|------|------|
| 最可能的 broken 原因 | dist 未重新 build，舊 bundle 不含 Reporting UI |
| #app 為何空白 | 舊 bundle 的 Vue Router 無 reporting routes，router-view 不渲染 |
| Reporting UI 元件是否為原因 | 否，元件本身未被打包，無法評估 |
| 最小修復路徑 | 1) 修復 Home.vue 截斷 2) 重新 build 3) Nginx 自動讀取新 dist |

**等待確認後再進行修復。**

---

*Investigation completed — 2026-03-14*
