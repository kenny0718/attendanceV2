# SA_MODULE_SPEC v2.1 Upgrade Note

**建立日期：** 2026-03-12  
**升級者：** AI session (Cursor)  
**狀態：** ACTIVE

---

## 1. 為什麼需要 v2.1

v2.0 完整定義了 Platform-first Identity 架構、Tenant Isolation、Location Policy（WP-11-13）等核心規則，但缺少出勤計算引擎的正式架構規範。

在 WP-C1-08 ~ WP-C1-11 的執行過程中，發現以下問題均源自缺乏明確規範：

- `duration_minutes` 在跨午夜情境下回傳 0（根本原因：naive datetime 混用）
- Out Checkpoint 與 break_duration 的邊界不清晰
- 報表層是否可自行計算工時，團隊沒有共同參照
- 前端計算與後端 session 欄位可能不一致，無規範禁止

v2.1 的目的是補全這些缺口，提供穩定的規範來源給後續所有工時計算、跨午夜處理、報表一致性工作。

---

## 2. v2.0 缺少什麼

| 缺失項目 | 影響 |
|---------|------|
| Attendance Engine 分層定義 | 工時計算邏輯散落在 API handler，無明確歸屬 |
| Work Hour canonical terms | raw_duration / work_duration / paid_hours 未正式定義 |
| Cross-midnight 計算規則 | 各實作者自行處理，易出錯（datetime.utcnow() 誤用） |
| Session Ownership Date 規則 | 跨午夜 session 歸哪天不明確 |
| Report Consistency Rule | 報表層是否可重新計算無禁止規範 |
| Timezone 使用規則 | UTC / Asia/Taipei 混用無明確邊界定義 |

---

## 3. v2.1 新增了什麼

新增 Section 25–32，統稱「Attendance Calculation Architecture」：

| Section | 內容 |
|---------|------|
| 25 | Architecture Overview — v2.1 的目的與適用範圍 |
| 26 | Engine Layering — Punch / Session / Policy / Work Hour / Report 五層定義 |
| 27 | Responsibility Boundaries — 明確列出四類禁止行為 |
| 28 | Work Hour Calculation Rules — canonical terms 定義與計算公式 |
| 29 | Cross-Midnight Rule — duration 計算、ownership date、月報歸屬 |
| 30 | Report Consistency Rule — 報表層只讀 canonical 欄位，禁止獨立計算 |
| 31 | Timezone Rule — 儲存 UTC / 業務 Asia/Taipei / API contract |
| 32 | Future Extensibility — 班表、彈性工時、分段班次、假日規則預留 |

v2.0 所有內容（Section 1–24）完整保留，無刪除。

---

## 4. 哪些文件從 v2.0 更新為 v2.1

以下文件為**當前治理文件**，參照版本已更新：

| 文件 | 原參照 | 更新後 |
|------|--------|--------|
| `docs/AI_CONTEXT.md` | SA_MODULE_SPEC_v1.9.md（多處） | SA_MODULE_SPEC_v2.1.md |
| `docs/ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md` | SA_MODULE_SPEC_v1.9.md（7處） | SA_MODULE_SPEC_v2.1.md |
| `docs/ACCEPTANCE_PLAN.md` | SA_MODULE_SPEC_v2.0.md | SA_MODULE_SPEC_v2.1.md |
| `docs/DEVELOPMENT_EXECUTION_PLAN.md` | SA_MODULE_SPEC_v2.0.md | SA_MODULE_SPEC_v2.1.md |
| `docs/MODULE_STATUS_MATRIX.md` | SA_MODULE_SPEC v2.0（3處） | SA_MODULE_SPEC v2.1 |
| `docs/API_DOCUMENTATION_v2.0.md` | SA_MODULE_SPEC_v2.0.md | SA_MODULE_SPEC_v2.1.md |

---

## 5. v2.0 參照應保持不變的文件

以下文件為**歷史記錄**，v2.0 參照刻意保留：

| 文件 | 保留原因 |
|------|----------|
| `docs/DOCS_STATE_AUDIT_REPORT.md` | 歷史審計報告，記錄 v2.0 當時的狀態 |
| `docs/DOCS_SAFE_ARCHIVE_SCAN.md` | 歷史掃描記錄 |
| `docs/SA_REALITY_GAP_REPORT.md` | v1.9 時代的 gap report，歷史文件 |
| `docs/MASTER_DEVELOPMENT_ROADMAP_v2.md` | 歷史 roadmap，以 v1.9 為基準撰寫 |
| `docs/SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md` | 歷史系統藍圖 |
| `docs/WORKSTREAM_STATUS_LEDGER.md` | WP 執行記錄，記錄當時使用的版本 |
| 所有 `WP-C1-*_*.md` 完成報告 | 執行時間點的歷史記錄 |
| 所有 `WP-11-*_*.md` 報告 | 歷史 WP 記錄 |

**規則**：若文件描述「在 v2.0 規範下完成了某工作」，v2.0 參照必須保留，不應改為 v2.1。

---

## 6. SA_MODULE_SPEC_v2.0.md 的處理

原始 `SA_MODULE_SPEC_v2.0.md` 保留在 `docs/` 目錄，作為歷史版本參照。  
新的 canonical spec 為 `docs/SA_MODULE_SPEC_v2.1.md`。

未來若需要升級至 v2.2，請依同樣模式：
1. 以 v2.1 為基礎建立 v2.2
2. 在 Version History section 新增記錄
3. 更新當前治理文件的參照
4. 建立對應的 upgrade note

---

## 7. 新規則的 diff 摘要

```
+ Section 26: 五層架構定義
  + Punch Layer     — 只記錄原始打卡事件
  + Session Engine  — 組合 session，計算 raw_duration
  + Policy Engine   — 評估合規性（遲到/加班/違規）
  + Work Hour Engine — canonical 工時計算唯一來源
  + Report Layer    — 只讀 canonical 欄位

+ Section 27: 四項明確禁止
  + 禁止 API handler inline 計算工時
  + 禁止前後端各自計算，結果可不同
  + 禁止 Report Layer 重新推導工時
  + 禁止 Report Layer 與 Session 欄位合法不同

+ Section 28: Canonical terms
  + raw_duration = punch_out_time - punch_in_time
  + work_duration = raw_duration - break_duration
  + Out Checkpoint 不等於 break_duration（除非 Policy 明確定義）
  + Missing punch → INCOMPLETE/INVALID，不得靜默填入

+ Section 29: Cross-midnight
  + raw_duration 跨午夜仍必須為正數
  + 禁止使用 datetime.utcnow()（naive datetime）
  + session ownership date = Asia/Taipei punch_in_time 日期
  + 月報歸屬 = punch_in_time 所在月份

+ Section 30: Report Consistency
  + 報表讀取 session.duration_minutes，不重新計算
  + 前端不得用 JS 重算工時

+ Section 31: Timezone
  + 儲存 UTC-aware datetime
  + 業務邊界 Asia/Taipei
  + datetime.utcnow() 明確禁止
  + API 要求 ISO 8601 with timezone offset

+ Section 32: Future extensibility
  + 預留 shift templates / flex time / split shifts /
    holiday rules / adjustment workflows
```

---

**文件版本：** v1.0  
**最後更新：** 2026-03-12  
**更新原因：** SA_MODULE_SPEC v2.0 → v2.1 升級
