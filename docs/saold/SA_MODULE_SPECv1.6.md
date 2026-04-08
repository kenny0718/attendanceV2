# CURSOR_MODULE_RULES.md
# Cursor 重寫規範 v1.6（必讀必遵守）

## 0. 最高原則（違反即視為錯誤）
- 「每個功能獨立」是第一目標：改一個功能不能影響其他功能
- 禁止把多個功能混在同一個 service 或同一個巨大檔案
- 禁止為了修 bug 同時改動多個模組（除非是 core 共用介面）

---

## 1. 強制專案結構

每個模組必須存在下列檔案（缺一不可）：
- api.py
- service.py
- repo.py
- models.py
- docs.md
- tests/

路徑：
`backend/app/modules/<module_name>/...`

模組清單（v1.6）：
- tenants
- auth
- locations
- attendance
- approvals
- notifications
- vehicles
- dispatch
- leave
- accrual
- reporting

---

## 2. 禁止事項（最常造成「改A壞B」）
- 模組 A 直接 import 模組 B 的 service / repo / models（禁止）
- 模組 A 直接寫入模組 B 的資料表（禁止）
- 在前端為了修手機版，修改桌機 CSS（禁止）
- 在多個 HTML 頁面複製貼上同一段 JS（禁止：要抽到 js/modules）
- reporting 不得做任何「計算規則」或「狀態變更」（只讀彙總）

---

## 3. 允許的跨模組互動方式（只能二選一）

### A) EventBus（優先）
- 模組發出事件，其他模組訂閱處理
- notifications 必須只靠事件運作
- accrual 必須透過訂閱 `leave.approved` 來扣帳

### B) Public Interface（少量）
- 若必須同步取得資訊，只能呼叫對方公開的 interface
- 不得呼叫對方內部 repo/service

---

## 4. attendance 核心不可破壞（P0 絕對不能被派車/請假影響）
- attendance 的推導邏輯唯一入口：
  - `modules/attendance/derivation.py`
- `PENDING_APPROVAL` 不參與推導、不參與日結計算
- 出勤成立必須有 `APPROVED IN`
- 派車 / 請假 / 額度不得改動 attendance 推導與日結語意

---

## 5. customer_service 權限硬規則
- customer_service 只能操作被指派公司（support_company_assignments）
- 產生 pairing code / 重置密碼 / 撤銷裝置等動作必須寫 audit log
- customer_service 不得直接信任裝置，只能產配對碼讓客戶端完成配對

---

## 6. Trusted Device / Site Pairing 規則（內勤無 GPS 主方案）
- Pairing code 僅用於裝置綁定，不可作為每日打卡依據
- Pairing code：
  - short-lived（建議 10 分鐘）
  - one-time
  - scope = company_id + site_id
- 配對成功後，該裝置打卡視為 SITE_MATCH（是否 APPROVED 由公司策略決定）

---

## 6.1 SSID Evidence 規則（補齊）
- wifi_ssid 為 Location Evidence（輔助證據），不得作為出勤成立的唯一依據（預設）
- wifi_ssid 為前端回報資料，可能為 null，不得假設一定存在
- 僅 SSID 命中、無 GPS 且非 Trusted Device：
  - 預設進入 `PENDING_APPROVAL`
- 公司可設定放寬（如 Level 0：SSID 命中即可 APPROVED），但必須：
  - 有 audit log
  - 不得繞過 attendance 推導規則

---

## 7. 請假 / 額度 / 統計（必須拆開）
- leave：只管流程
- accrual：只管 ledger
- reporting：只讀彙總，不做任何規則

---

## 8. 派車等級（只做 Level 0 / 1）
- default = 1
- 未完成 `APPROVED IN` → 禁止開始用車
- AutoClose（預設 23:59）→ `dispatch.autoclosed`

---

## 9. UI / CSS 改版規則
- 桌機 CSS 不動
- 手機只允許 `@media (max-width: 768px)` 排版調整
- 禁止改配色 / HTML 結構

---

## 10. 必跑回歸測試（打卡核心 8 條）
1) NO_MATCH 未填原因 → 拒絕
2) NO_MATCH 有原因 → PENDING
3) APPROVED → 模式 B 推導正確
4) PENDING 不參與推導與日結
5) 21:00 日結缺卡 / 可能缺卡正確
6) approve pending → 該日重算
7) customer_service 未指派公司 → 403
8) OTP / Reset token 一次性 + 強制改密碼

---

## Proxy / WAF / Cloudflare Rules
- Attendance validity MUST NOT rely on client IP
- Real IP 僅供 audit/security
- 信任 header 僅限 WAF/Nginx
- Header order：
  CF-Connecting-IP > X-Forwarded-For > X-Real-IP > remote_addr
- 所有 `/api/*` 錯誤回應必須是 JSON

---

## API Error Response Rule（必遵守）

```json
{
  "error": "Human readable short message",
  "code": "MACHINE_READABLE_CODE",
  "request_id": "<uuid or trace id>",
  "hint": "Optional hint message"
}
