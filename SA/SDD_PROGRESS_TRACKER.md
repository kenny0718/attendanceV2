# SDD Progress Tracker

> 這份文件是 `SA` 正式文件與 remediation 狀態的總追蹤檔。  
> 用途不是取代各 SDD，而是幫你快速看到：哪些文件已完成、哪些 remediation 已定義、哪些還只有 spec、哪些後續要進 code 修正。

---

## 1. 狀態說明

- `pending`：尚未開始
- `in_progress`：進行中
- `spec_defined`：已完成 SDD / remediation 規格定義，程式尚未確認已修
- `docs_aligned`：文件已回寫對齊目前基線
- `code_updated`：已有程式修改
- `tests_added`：已補測試
- `done`：文件、程式、驗證皆完成
- `blocked`：卡住，需先解前置問題

---

## 2. SA/modules 文件完成度

| 文件 | 狀態 | 備註 |
|---|---|---|
| `SA/modules/README.md` | `docs_aligned` | 已補目前閱讀指引 |
| `SA/modules/attendance.md` | `docs_aligned` | 已升級為主模組 spec 入口，聚焦總覽、owner mapping、正式語意契約與 remediation 對應 |
| `SA/modules/attendance-capture.md` | `docs_aligned` | 已補 write-side 與驗證基線 |
| `SA/modules/attendance-reporting.md` | `docs_aligned` | 已正式 spec 化，補齊 read-only 邊界、P0 分流、Formalized Semantic Block 與驗證流程 |
| `SA/modules/attendance-policy.md` | `docs_aligned` | 已正式 spec 化，回寫 F6 helper 修補、regression test、reporting smoke、live canonical write 與 repo-level 最小 inventory |
| `SA/modules/schedule.md` | `docs_aligned` | 已補 schedule baseline 與 contract |
| `SA/modules/auth.md` | `docs_aligned` | 已補 auth / scope 分工，並對齊 `company_id` / `tax_id` 公司登入識別規則與 `tenants` 邊界 |
| `SA/modules/tenants.md` | `docs_aligned` | 已補 tenants source of truth，並定義 `company_id` 必填、`tax_id` 選填可登入、公司資料查詢採人工查核 / 半自動模式，且補上 backend schema / frontend 畫面對齊規劃 |
| `SA/modules/leave.md` | `docs_aligned` | 已補 leave 邊界與 approvals 說明 |
| `SA/modules/notifications.md` | `docs_aligned` | 已補 event consumer 定位 |
| `SA/modules/audit.md` | `docs_aligned` | 已補治理與高風險追溯責任 |
| `SA/modules/backup.md` | `docs_aligned` | 已補 consistency / FK closure 檢查 |
| `SA/modules/customer_service.md` | `docs_aligned` | 已補 assignment scope 定位 |
| `SA/modules/frontend.md` | `docs_aligned` | 已補非最終安全邊界定位，並補充 code-level inventory：目前未見 SSE / EventSource / streaming consume 現況 |
| `SA/modules/upstream-streaming.md` | `code_updated` | 已新增正式 upstream / streaming 模組 SDD，並完成第一版 backend / frontend skeleton 對齊；目前已新增 `system.status.v1` 與 `attendance.status.v1` demo event，前端可 consume attendance status 並同步首頁狀態 |

---

## 3. SA/architecture 文件完成度

| 文件 | 狀態 | 備註 |
|---|---|---|
| `SA/architecture/SYSTEM_SDD.md` | `docs_aligned` | 已補系統級 baseline、EventBus code inventory 與目前無 upstream owner 結論 |
| `SA/architecture/MODULE_BOUNDARY_MATRIX.md` | `docs_aligned` | 已補 streaming / upstream 預設邊界規則 |
| `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md` | `docs_aligned` | 已補產品判斷與目前收斂方向 |

---

## 4. Remediation 追蹤

| 問題 ID | 標題 | 狀態 | 主要文件 | 下一步 |
|---|---|---|---|---|
| `R-LEGACY-ATTENDANCE-API` | legacy attendance API 相容層治理 | `docs_aligned` | `SA/modules/attendance.md` | 先做 deprecated / expansion-stop，後續再評估 tests migration 與退場條件 |
| `R-APPROVE-PENDING-OWNER-INVENTORY` | approve / pending owner 與重算責任盤點 | `docs_aligned` | `SA/modules/attendance.md` | 先確認 pending 是否存在正式語意，再判定 approve event-chain 是否只是 legacy compatibility path |
| `R-BOUNDARY-AND-LAYER-COUPLING` | `##9` 已知衝突與技術債治理 | `spec_defined` | `SA/modules/attendance.md` | 依子議題拆分 code 修正順序 |
| `R-F6-SCHEDULE-AWARE-CANONICAL-GUARD` | `##10` F6 嚴謹結論正式修正規格 | `tests_added` | `SA/modules/attendance-policy.md` | 已完成 dormant helper canonical guard、targeted regression、reporting smoke 與最小 repo-level inventory；approve/pending owner 另追 `R-APPROVE-PENDING-OWNER-INVENTORY` |
| `R-C2-STREAMING-UPSTREAM-INVENTORY` | streaming / SSE / upstream owner 盤點 | `docs_aligned` | `SA/modules/frontend.md`, `SA/architecture/SYSTEM_SDD.md`, `SA/architecture/MODULE_BOUNDARY_MATRIX.md` | 已完成 frontend / backend 第一輪 code inventory：前端僅 `axios` request/response；後端僅 internal EventBus + notifications subscriber + debug JSON API；尚無對外 upstream client / SSE gateway 正式 owner |
| `R-C3-UPSTREAM-STREAMING-MODULE-SDD` | upstream / streaming 正式模組 SDD 建立 | `code_updated` | `SA/modules/upstream-streaming.md` | 已建立 `backend/app/core/streaming/` skeleton、註冊 authenticated SSE route、建立 `frontend/src/api/streaming.js`、`frontend/src/stores/streaming.js`，完成全域連線整合，並新增 `system.status.v1` 與 `attendance.status.v1` demo event；下一步是把 demo payload 收斂成正式 provider / consumer contract |

---

## 5. 目前建議的下一步

1. 對 `R-LEGACY-ATTENDANCE-API` 先做 deprecated / expansion-stop 治理，避免 legacy route 再擴張
2. 評估 `backend` tests 是否可由 fixture / repo seed 取代 `/api/attendance/mock-create` 依賴
3. 針對 `R-APPROVE-PENDING-OWNER-INVENTORY` 確認 `pending` 是否存在正式產品語意 / state owner
4. 針對 `approve` 的 `attendance.approved` event-chain，確認是否只是 legacy compatibility path，而非正式 attendance policy 重算 owner
5. 視需要把 `R-BOUNDARY-AND-LAYER-COUPLING` 再拆成更細的子票
6. 若未來新增新的 schedule-aware close path 或新的 session duration persistence path，需重新檢查 `R-F6-SCHEDULE-AWARE-CANONICAL-GUARD` 的 canonical write contract
7. 後續每次 AI 改 code，請同步在對應 remediation block 與本 tracker 更新狀態
8. 若要真正導入 `SSE` / streaming / upstream gateway，先補正式 owner、provider contract、consumer contract、retry / auth / observability 邊界，再進 code 實作
9. 若下一步要開始實作 upstream，優先從 `core` 或新的平台整合模組設計 transport owner，不要直接從 `attendance.service`、`auth.service`、`tenants.service` 內硬接第三方
10. 目前已完成 `system.status.v1` 與 `attendance.status.v1` demo event；下一步可直接把同樣路徑替換成單一真實 domain event contract

---

## 6. 更新規則

- 若只改 SDD，狀態更新為 `spec_defined` 或 `docs_aligned`
- 若已改 code，狀態更新為 `code_updated`
- 若已補測試，再更新為 `tests_added`
- 文件、程式、測試都完成後，才更新為 `done`
