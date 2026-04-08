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
| `SA/modules/attendance.md` | `docs_aligned` | 已補 baseline 結論、remediation blocks、approve/pending owner 獨立追蹤與 F6 最小 inventory 結論 |
| `SA/modules/attendance-capture.md` | `docs_aligned` | 已補 write-side 與驗證基線 |
| `SA/modules/attendance-reporting.md` | `docs_aligned` | 已補 P0 分流與 read-only 邊界 |
| `SA/modules/attendance-policy.md` | `docs_aligned` | 已回寫 F6 helper 修補、regression test、reporting smoke、live canonical write 與 repo-level 最小 inventory |
| `SA/modules/schedule.md` | `docs_aligned` | 已補 schedule baseline 與 contract |
| `SA/modules/auth.md` | `docs_aligned` | 已補 auth / scope 分工 |
| `SA/modules/tenants.md` | `docs_aligned` | 已補 tenants source of truth |
| `SA/modules/leave.md` | `docs_aligned` | 已補 leave 邊界與 approvals 說明 |
| `SA/modules/notifications.md` | `docs_aligned` | 已補 event consumer 定位 |
| `SA/modules/audit.md` | `docs_aligned` | 已補治理與高風險追溯責任 |
| `SA/modules/backup.md` | `docs_aligned` | 已補 consistency / FK closure 檢查 |
| `SA/modules/customer_service.md` | `docs_aligned` | 已補 assignment scope 定位 |
| `SA/modules/frontend.md` | `docs_aligned` | 已補非最終安全邊界定位 |

---

## 3. SA/architecture 文件完成度

| 文件 | 狀態 | 備註 |
|---|---|---|
| `SA/architecture/SYSTEM_SDD.md` | `docs_aligned` | 已補系統級 baseline 結論 |
| `SA/architecture/MODULE_BOUNDARY_MATRIX.md` | `docs_aligned` | 已補 attendance / reporting 補充 |
| `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md` | `docs_aligned` | 已補產品判斷與目前收斂方向 |

---

## 4. Remediation 追蹤

| 問題 ID | 標題 | 狀態 | 主要文件 | 下一步 |
|---|---|---|---|---|
| `R-LEGACY-ATTENDANCE-API` | legacy attendance API 相容層治理 | `docs_aligned` | `SA/modules/attendance.md` | 先做 deprecated / expansion-stop，後續再評估 tests migration 與退場條件 |
| `R-APPROVE-PENDING-OWNER-INVENTORY` | approve / pending owner 與重算責任盤點 | `docs_aligned` | `SA/modules/attendance.md` | 先確認 pending 是否存在正式語意，再判定 approve event-chain 是否只是 legacy compatibility path |
| `R-BOUNDARY-AND-LAYER-COUPLING` | `##9` 已知衝突與技術債治理 | `spec_defined` | `SA/modules/attendance.md` | 依子議題拆分 code 修正順序 |
| `R-F6-SCHEDULE-AWARE-CANONICAL-GUARD` | `##10` F6 嚴謹結論正式修正規格 | `tests_added` | `SA/modules/attendance-policy.md` | 已完成 dormant helper canonical guard、targeted regression、reporting smoke 與最小 repo-level inventory；approve/pending owner 另追 `R-APPROVE-PENDING-OWNER-INVENTORY` |

---

## 5. 目前建議的下一步

1. 對 `R-LEGACY-ATTENDANCE-API` 先做 deprecated / expansion-stop 治理，避免 legacy route 再擴張
2. 評估 `backend` tests 是否可由 fixture / repo seed 取代 `/api/attendance/mock-create` 依賴
3. 針對 `R-APPROVE-PENDING-OWNER-INVENTORY` 確認 `pending` 是否存在正式產品語意 / state owner
4. 針對 `approve` 的 `attendance.approved` event-chain，確認是否只是 legacy compatibility path，而非正式 attendance policy 重算 owner
5. 視需要把 `R-BOUNDARY-AND-LAYER-COUPLING` 再拆成更細的子票
6. 若未來新增新的 schedule-aware close path 或新的 session duration persistence path，需重新檢查 `R-F6-SCHEDULE-AWARE-CANONICAL-GUARD` 的 canonical write contract
7. 後續每次 AI 改 code，請同步在對應 remediation block 與本 tracker 更新狀態

---

## 6. 更新規則

- 若只改 SDD，狀態更新為 `spec_defined` 或 `docs_aligned`
- 若已改 code，狀態更新為 `code_updated`
- 若已補測試，再更新為 `tests_added`
- 文件、程式、測試都完成後，才更新為 `done`
