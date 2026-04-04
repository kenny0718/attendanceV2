# WP-S1-07B Template Edit UI — Completion Report

**票號：** WP-S1-07B  
**日期：** 2026-03-25  
**狀態：** ✅ COMPLETE（最小侵入 Template Edit）

---

## 1. Scope

本次僅實作：
1. Template Edit UI（`/schedule`）
2. 呼叫既有 `updateTemplate()`
3. 成功後 refresh template list
4. 最小必要 docs sync

未實作：Assignment Edit、modal 重構、component 拆分、backend 改動。

---

## 2. Files Changed

- `frontend/src/views/schedule/SchedulePage.vue`
- `backend/app/modules/schedule/docs.md`
- `docs/02_DEVELOPMENT_STATUS/WP-S1-07B_TEMPLATE_EDIT_UI_COMPLETION_REPORT.md`

---

## 3. UI Behavior Added

### Template 區塊新增 inline 編輯能力
- 每列新增 `編輯` 按鈕。
- 進入編輯後，同列欄位改為可輸入：
  - `name`
  - `start_time`
  - `end_time`
  - `break_minutes`
  - `is_overnight`
- 同時顯示 `儲存` / `取消`。
- 同一時間僅允許一列編輯（其他列的 `編輯` disabled）。

### 取消編輯
- 取消會清除編輯狀態並還原原值（重新從當前 row 初始化）。

### 儲存編輯
- 呼叫既有 `scheduleApi.updateTemplate(templateId, payload)`。
- payload 僅含：
  - `name`
  - `start_time`
  - `end_time`
  - `break_minutes`
  - `is_overnight`
- 不送 `is_active`。
- 成功後：
  - `fetchTemplates()` refresh list
  - 顯示成功訊息

---

## 4. Data / Format Notes

- `break_minutes` 使用 `v-model.number`，送出前強制 `Number(...)`。
- `time` 輸入採 `input[type=time]`，送出時轉為 `HH:mm:ss`（與 backend schema 相容）。

---

## 5. Validation Performed

### Static 檢查
- `SchedulePage.vue` 仍保留原本 create / activate / deactivate / assignment create / cancel 流程。
- 新增 edit 僅插入 Templates 表格區塊與 script 對應 state/method。
- 未修改 backend API / schema / service / repo。

### Scope 檢查
- 僅修改授權三個檔案。
- 未觸碰 router/auth/client.js。

---

## 6. Known Limitations

- 目前 edit 成功後採整表 refresh，不做局部 optimistic update。
- 未新增前端欄位級驗證規則（沿用 backend 驗證返回錯誤訊息）。
- Assignment Edit 仍不支援（符合本票 out-of-scope）。

---

## 7. Safety

- 寫檔採 tmp -> size check -> rename -> reread confirm。
- 無未授權檔案變更。
