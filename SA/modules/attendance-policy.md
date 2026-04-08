# attendance-policy 子文件 SDD

**子域名稱**：`attendance.policy`  
**你可以把它理解成**：出勤模組裡的「規則與語意核心」  
**對應主文件**：`SA/modules/attendance.md`  
**主要程式位置**：
- `backend/app/modules/attendance/policy_engine.py`
- `backend/app/modules/attendance/policy_rules.py`
- `backend/app/modules/attendance/policy_missing_segment.py`
- `backend/app/modules/attendance/policy_schedule_support.py`
- `backend/app/modules/attendance/policy_schedule_models.py`
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/punch_close_domain.py`

---

## 1. 這份文件是給誰看的？

如果你要改的是下面這些功能，就先看這份：

- 遲到 / 早退 / 加班判定
- schedule-aware 評估
- work hour 計算
- missing segment 規則
- canonical semantic
- policy remediation 相關風險

白話說：

> 只要你要動的是「怎麼算、怎麼判斷、什麼欄位代表真正語意」，先看這份。

---

## 2. 這個子域是做什麼的？

`attendance.policy` 處理的是出勤規則本身。

它的工作包括：

- 根據 session 與 policy 算出遲到/早退/加班
- 根據 schedule 資訊做 schedule-aware 判定
- 處理 work hour 相關純計算
- 處理 missing segment 相關規則

這裡不是主要 DB 寫入層，但它會影響寫入時要寫什麼。

---

## 3. 主要功能拆解

### 3.1 Standard Policy Evaluation
用途：在一般情況下判斷是否遲到、早退、加班。

### 3.2 Schedule-aware Evaluation
用途：當 session 需要參考排班基準時，使用 normalized windows 做判定。

### 3.3 Work Hour Calculation
用途：計算工時、分鐘數、與其他衍生值。

### 3.4 Missing Segment
用途：處理缺段、異常或 dry-run 類規則。

### 3.5 Default Policy Fallback
用途：當沒有明確 policy 時，仍能用預設規則完成判定。

---

## 4. 主要檔案與白話用途

| 檔案 | 白話說明 | 你什麼時候會改到 |
|---|---|---|
| `policy_engine.py` | 政策 façade / orchestration engine | 改政策入口時 |
| `policy_rules.py` | 細部規則 | 改 late/early/overtime 規則時 |
| `policy_missing_segment.py` | 缺段規則 | 改 missing-segment 時 |
| `policy_schedule_support.py` | schedule-aware 支援 | 改 schedule 整合規則時 |
| `policy_schedule_models.py` | schedule-aware model | 改排班輸入模型時 |
| `work_hour_engine.py` | 工時純計算 | 改純計算時 |
| `punch_close_domain.py` | close-flow 的 policy adapter | 改 close flow 與 canonical guard 時 |

---

## 5. 不可破壞的正式語意契約

這一節非常重要，之後不要亂改。

### 5.1 canonical = gross
目前正式語意基線：

- `session.duration_minutes` = canonical persisted duration
- canonical = `gross`

### 5.2 break deduction = derived only
意思是：

- break deduction 可以計算
- 可以顯示
- 可以做額外資訊輸出
- **但不應寫回 canonical 欄位**

### 5.3 reporting = canonical consumer only
意思是：

- reporting 只能讀 canonical persisted duration
- 不應反過來改 policy semantic

---

## 6. 這個子域與 schedule 的關係

### schedule 提供
- 預期工作視窗
- normalized windows
- baseline

### policy 子域負責
- 用這些輸入做 attendance 判定

一句話：

> `schedule` 提供排班事實，`attendance.policy` 提供規則判斷。

---

## 7. 目前最重要的風險

### 7.1 命名語意混亂
目前存在多種相似名稱：
- `canonical_minutes`
- `work_minutes`
- `duration_minutes`
- `net_work_minutes`

這很容易讓人把 derived 值當 canonical 值。

### 7.2 schedule-aware canonical drift
`schedule-aware` 的 dormant helper 曾存在 F6 風險：
- `build_policy_evaluation_with_schedule_v2()` 曾把 derived `work_minutes` 寫入 `session.duration_minutes`

目前已完成修補：
- helper 已改為維持 `session.duration_minutes = gross_minutes`
- derived `work_minutes` 僅保留在 evaluation payload
- 已補 targeted regression test 防止回歸
- 已補 reporting smoke coverage，確認 canonical consumer 仍只讀 `duration_minutes`

目前判定：
- 主 `punch-out` live path 本來就不是走這條 helper
- 先前風險屬於 dormant path
- dormant path 的 canonical drift 寫入點已清除

### 7.3 policy_engine 過胖
`policy_engine.py` 目前承接了多個歷史層次：
- basic
- schedule-aware
- façade

這是高風險核心檔，不適合大改。

---

## 8. 與 remediation 的對應重點

這個子域最直接對應的風險票包括：

- `P6_F5_PUNCH_OUT_ORCHESTRATION_BOUNDARY_GUARD`
- `P6_F6_SCHEDULE_AWARE_CANONICAL_GUARD`
- `P6_F11_POLICY_ENGINE_EXPANSION_STOP_GUARD`
- `P6_F12_SCHEDULE_AWARE_TEST_COVERAGE_TICKET`

### 你應該怎麼理解它們

- `F5`：不要讓 close-flow owner 邊界越來越亂
- `F6`：不要讓 `work_minutes` 寫進 canonical 欄位
- `F11`：不要再讓 `policy_engine.py` 吸進更多責任
- `F12`：高風險 schedule-aware 路徑要補測試

---

## 9. F6 的嚴謹判斷

目前依實際程式判讀：

- `P6_F6` 的 dormant helper 風險已完成修補
- 主 `punch-out` live path 原本就不是走該 helper；目前 live path 由 `api/punch.py` 計算 `gross_minutes`，並經 `repo.close_session(..., duration_minutes=gross_minutes, ...)` 寫回 canonical duration
- 已有 targeted regression test 鎖住 `work_minutes` 不得再寫回 `duration_minutes`
- 已有 reporting smoke coverage 鎖住 canonical consumer 仍只讀 `duration_minutes`
- 已完成最小 repo-level inventory：`repo.py` 目前僅見 `AttendanceSessionRepository.close_session()` 寫入 `session.duration_minutes`，`attendance_punch_repo.py` 未見碰觸 canonical session duration
- `approve/pending` 後重算 owner 尚未盤出正式 attendance policy 重算路徑；此議題已獨立轉入 `R-APPROVE-PENDING-OWNER-INVENTORY`（見 `SA/modules/attendance.md` 與 `SA/SDD_PROGRESS_TRACKER.md`），不能再併入 `F6` 主 remediation 判定

所以現在若要判斷 F6 是否可進一步收斂，你要檢查五件事：

1. 程式中是否仍存在 `work_minutes -> duration_minutes` 寫入路徑
2. live punch-out canonical write 是否仍維持 `gross_minutes`
3. targeted tests 是否存在且通過
4. reporting canonical consumer smoke 是否存在且通過
5. remediation / tracker 文件是否已同步回寫

如果未來又新增新的 schedule-aware close path，或新增其他 session duration persistence path，仍必須重新檢查這五件事，不能因為這次修過就假定永久安全。

---

## 10. 之後你要改這裡時，先檢查這 6 件事

1. 你改的是 pure rule，還是 transaction write contract？
2. 你有沒有不小心碰到 canonical semantic？
3. derived 值有沒有被誤寫回 persistence？
4. 你有沒有把 schedule 主責任拉進 attendance？
5. 你有沒有讓 `policy_engine.py` 再變胖？
6. 改完後有沒有同步更新 `attendance.md` 或這份文件？

---

## 11. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `attendance.policy`（出勤規則子域）是規則判斷與語意保護層，不是任意 persistence owner
- `schedule`（排班）提供 baseline，`attendance.policy` 負責依 baseline 進行出勤規則判定
- `canonical = gross`、`break deduction = derived only`、`reporting = canonical consumer only` 是不可破壞的正式基線
- `P6_F6` 的 dormant schedule-aware helper 已完成 canonical guard 修補，且已補 targeted regression test
- reporting canonical consumer smoke 已補，確認 summary 聚合仍只使用 `duration_minutes`
- 主 `punch-out` live path 目前仍走 gross canonical write，不是由 schedule-aware helper 寫入
- 已完成最小 repo-level inventory，`repo.py` 未見第二條 canonical duration persistence path，`attendance_punch_repo.py` 未見越權碰觸 session duration
- `approve/pending` 後重算 owner 尚未盤出正式 attendance policy 重算路徑；此議題請改追 `R-APPROVE-PENDING-OWNER-INVENTORY`（見 `SA/modules/attendance.md` 與 `SA/SDD_PROGRESS_TRACKER.md`）
- 高風險路徑後續仍建議持續覆蓋：`approve pending` 後重算、schedule-aware canonical guard、缺卡 / 可能缺卡判定

---

## 12. Remediation SDD Blocks（供後續 AI / 人工依規格修正）

### R-F6-SCHEDULE-AWARE-CANONICAL-GUARD — ##10 F6 嚴謹結論正式修正規格

#### 1. 問題定義
schedule-aware dormant helper 曾存在將 derived `work_minutes` 寫入 `session.duration_minutes` 的風險。這會直接破壞 canonical semantic。

#### 2. 為什麼危險
- canonical semantic 被破壞
- reporting 可能讀到錯誤 canonical duration
- break deduction / summary / 後續 consumer 可能被污染
- 維護者可能誤以為改了欄位名就算完成修正

#### 3. 正式 owner
- 模組：`attendance`
- 子域：`attendance.policy`
- 核心檔案：`backend/app/modules/attendance/punch_close_domain.py`、`backend/app/modules/attendance/work_hour_engine.py`、`backend/app/modules/attendance/policy_engine.py`
- 關聯檔案：`backend/app/modules/attendance/api/punch.py`、`backend/app/modules/attendance/repo.py`、`backend/app/modules/attendance/attendance_punch_repo.py`
- 文件檔案：`SA/modules/attendance-policy.md`

#### 4. 非 owner
- `attendance.reporting` 不得重新定義 canonical
- `schedule` 不得決定最終 persisted duration
- `frontend` 不得假設 derived minutes 就是 canonical
- `approve/pending` owner 問題不得繼續混入 `F6` 主 remediation，應改追 `R-APPROVE-PENDING-OWNER-INVENTORY`

#### 5. 允許修改範圍
- close-flow policy adapter
- canonical write contract
- schedule-aware guard
- 對應 regression tests
- session duration persistence inventory
- 文件與 tracker 同步回寫

#### 6. 禁止修改範圍
- 不可用 reporting 邏輯補救 canonical
- 不可把 derived 欄位改名後繼續寫回 canonical
- 不可把修正責任丟給 frontend
- 不可只寫文件就宣告 F6 完成

#### 7. 完成條件
- dormant helper 的 canonical drift 寫入點已移除
- `session.duration_minutes` 僅允許維持 canonical gross semantic
- regression test 可防止 `work_minutes` 再次寫回 canonical
- reporting smoke 可確認 canonical consumer 未被污染
- live punch-out canonical write 已確認維持 `gross_minutes`
- 最小 repo-level inventory 已完成，未見第二條 `work_minutes -> session.duration_minutes` persistence path
- remediation / tracker 已同步回寫

#### 8. 驗證條件
- targeted regression test 通過
- reporting smoke 通過
- grep / code review 確認無新的 `work_minutes -> duration_minutes` 寫入
- 已確認 `api/punch.py -> service.py -> punch_close_domain.py -> repo.close_session()` 主線寫回值為 `gross_minutes`
- 文件結論與 tracker 狀態一致

#### 9. 跨模組影響
- `attendance.reporting`
- `schedule`
- `frontend`

#### 10. 文件回寫清單
- `SA/modules/attendance-policy.md`
- `SA/modules/attendance.md`
- `SA/SDD_PROGRESS_TRACKER.md`

#### Change Log
- Datetime: 2026-04-08 00:00:00 +08:00
- Status: tests-added-and-docs-aligned
- Summary: 已完成 dormant helper canonical guard 修補、targeted regression test、reporting smoke，並完成 `api/punch.py`、`service.py`、`punch_close_domain.py`、`policy_engine.py`、`work_hour_engine.py`、`repo.py`、`attendance_punch_repo.py` 最小 inventory
- Next: 若未來新增新的 schedule-aware close path 或新的 session duration persistence path，需重新檢查 canonical write contract；approve/pending owner 請改追 `R-APPROVE-PENDING-OWNER-INVENTORY`
