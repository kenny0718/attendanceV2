# POLICY_ENGINE_FREEZE

> **Document Type**: Freeze Enforcement Specification  
> **Scope**: `backend/app/modules/attendance/policy_engine.py`  
> **Status**: ACTIVE FREEZE  
> **Execution Mode**: Task precondition / change gate  
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件定義 `policy_engine.py` 的 freeze 規則，作為未來所有 policy 相關 Cursor 任務、實作任務、PR 審查與治理判定的強制前置限制。

本文件的目的為：

- 防止 `policy_engine.py` 再次膨脹
- 防止 pure rule 被重新回塞至 façade
- 防止 schedule-aware support / normalization glue 再次累積於 façade 檔案
- 防止 `policy_engine.py` 再次承擔 missing segment、API、repo、reporting、UI shaping 等非 façade 責任
- 將 `policy_engine.py` 固定為 **orchestration façade**，而非規則倉庫或邏輯集中點

本文件是對 `POLICY_ENGINE_GOVERNANCE.md` 的**凍結補充規則**。治理文件定義邊界；本文件定義「現在開始不可再退回去」的 freeze enforcement。

---

# 1. Freeze Status

## 1.1 Formal Freeze Declaration

自本文件生效起，`backend/app/modules/attendance/policy_engine.py` 進入：

- **ACTIVE FREEZE STATUS**

此 freeze status 的含義為：

- `policy_engine.py` 已完成三刀收斂
- `policy_engine.py` 的核心定位已明確固定
- 未來不得再將已外移責任回塞至 `policy_engine.py`
- 未來不得以「改動方便」為理由，將新責任直接堆回 façade

## 1.2 Freeze Objective

freeze 的正式目標如下：

1. 防止 pure rule 回塞
2. 防止 schedule glue 再擴張
3. 防止 façade 重新膨脹
4. 防止 `policy_engine.py` 從 orchestration façade 退化回 mixed-responsibility engine

## 1.3 Frozen Positioning

`policy_engine.py` 的正式定位固定為：

- **policy evaluation orchestration façade**
- **最小接線層**
- **最小 fallback 協調層**
- **最小 result assembly 協調層**

`policy_engine.py` 的正式定位**不是**：

- pure rule module
- schedule rule module
- schedule support module
- missing segment module
- API / repo coordination module
- UI / response shaping module

---

# 2. Allowed Changes

未來若任務需要修改 `policy_engine.py`，只允許以下類型。

## 2.1 Allowed

### A. Façade orchestration 的極小接線

允許：

- 將既有 façade 接到已存在的外部模組
- 更新外部 pure/support module 的呼叫點
- 調整 façade 對外部 module 的最小接線順序

限制：

- 不得改 public façade signature
- 不得引入新責任類型
- 不得擴張為新的 branch tree

### B. 已拆出模組的呼叫更新

允許：

- `policy_rules.py` 函式呼叫更新
- `policy_schedule_support.py` 函式呼叫更新
- `policy_missing_segment.py` 協調點的最小更新

限制：

- 只允許 façade 接線變更
- 不允許把外部邏輯搬回 engine

### C. 極小 fallback 修正

允許：

- 維持既有 façade contract 所必需的 fallback 微調
- 修正明確的 fallback 接線錯誤

限制：

- 不得新增 fallback 體系
- 不得新增 compatibility tree
- 不得把 fallback 擴寫成新規則中心

### D. 極小 result assembly 修正（需 justification）

允許：

- 僅為維持既有 façade output contract 所需的極小欄位接線修正
- 不涉及新 output shaping policy 的最小 assembly 修改

限制：

- 必須提供 justification
- 不得把 result assembly 擴成 normalization / compatibility / presentation layer

---

# 3. Forbidden Changes

以下內容**禁止修改到 `policy_engine.py`**。

## 3.1 Pure Rule Backfill — Forbidden

禁止：

- 新 pure late rule 回塞 `policy_engine.py`
- 新 pure early leave rule 回塞 `policy_engine.py`
- 新 pure overtime rule 回塞 `policy_engine.py`
- 新 tolerance / grace / threshold 純計算回塞 `policy_engine.py`
- 任意可單元測試的 deterministic pure rule 回塞 `policy_engine.py`

## 3.2 Schedule-Specific Pure Logic Backfill — Forbidden

禁止：

- 新 split-shift pure calculation 回塞
- 新 schedule window overlap / normalization 演算法回塞
- 新 expected start / end 推導純邏輯回塞
- 新 first / last window 選取純邏輯回塞
- 新 default window fallback support 回塞

## 3.3 Missing Segment Backfill — Forbidden

禁止：

- missing segment 規則回塞 `policy_engine.py`
- expected / actual / exception segment 細節進入 engine
- dry-run / trace / evidence sufficiency 規則進入 engine

## 3.4 API / Repo / Reporting Coupling — Forbidden

禁止：

- 讓 `policy_engine.py` 直接知道 API request / response 細節
- 讓 `policy_engine.py` 直接知道 repo query 細節
- 讓 `policy_engine.py` 承擔 reporting 相關責任
- 讓 `policy_engine.py` 成為跨模組資料整合中心

## 3.5 UI / Response Shaping Expansion — Forbidden

禁止：

- UI-friendly formatting 邏輯進入 engine
- response shaping policy 進入 engine
- presentation-specific 欄位裝飾邏輯進入 engine

## 3.6 Convenience-Based Backfill — Forbidden

禁止：

- 因為「改這裡最快」就把新功能塞進 façade
- 因為「上下文都在這裡」就把新責任留在 façade
- 因為「只是幾行」就忽略責任歸屬

正式規則：

- **方便性不是允許修改 `policy_engine.py` 的理由**

---

# 4. Mandatory Check Before Any Change

未來任何任務若要修改 `policy_engine.py`，必須先回答以下問題。

## 4.1 Mandatory Questions

1. **這次改動為什麼不能放 `policy_rules.py`？**
2. **這次改動為什麼不能放 `policy_missing_segment.py`？**
3. **這次改動為什麼不能放 `policy_schedule_support.py` 或其他 support/rule module？**
4. **這次改動是否只屬 façade 接線？**

## 4.2 Required Standard

只有在以下條件同時成立時，才可進入 `policy_engine.py`：

- 已完成責任歸屬判定
- 已排除外部 rule/support module 落點
- 可明確證明該修改只屬 façade 接線、極小 fallback 或極小 result assembly

若無法明確回答上述問題，則：

- **不得修改 `policy_engine.py`**

---

# 5. Hard Stop Conditions

未來任務若出現以下任一情況，必須立即停止，不得繼續修改 `policy_engine.py`。

## 5.1 Hard Stop List

### A. 想新增 pure rule 到 `policy_engine.py`

一旦任務內容是：

- 新增 pure rule
- 補 pure rule 分支
- 直接在 engine 裡寫 deterministic calculation

則必須：

- **STOP**

### B. 想新增 schedule branch 細節到 `policy_engine.py`

一旦任務內容是：

- 新增 schedule mode 細節
- 新增 schedule-specific branch tree
- 新增 normalized windows 演算法細節

則必須：

- **STOP**

### C. 想讓 engine 直接知道 API / repo 細節

一旦任務內容涉及：

- request model
- response model
- repo query
- DB lookup
- reporting data flow

則必須：

- **STOP**

### D. `policy_engine.py` 行數再次超過 500 且無治理票

一旦 `policy_engine.py` 再次超過：

- **500 行**

且未先建立治理票 / 拆分票，則必須：

- **STOP**

### E. 無法說明外移理由

若任務說明或 PR 說明無法回答：

- 為什麼不能放外部模組
- 為什麼這次只屬 façade glue

則必須：

- **STOP**

---

# 6. Future Workflow

未來新增任何 policy 功能時，必須遵守下列順序。

## 6.1 Mandatory Workflow Order

1. **先判定責任歸屬**
2. **先改外部 module**
3. **最後才回到 `policy_engine.py` 做最小 façade 接線**
4. **若不是 façade glue，禁止動 `policy_engine.py`**

## 6.2 Allocation Priority

未來新增責任時，優先判定落點如下：

### A. `policy_rules.py`

放置：

- pure rule
- deterministic calculation
- late / early / overtime / work-minute 純邏輯

### B. `policy_schedule_support.py`

放置：

- schedule-aware normalization glue
- business-date normalization support
- normalized windows fallback support
- expected window bounds support

### C. `policy_missing_segment.py`

放置：

- missing segment logic
- dry-run / trace / evidence sufficiency 決策

### D. 其他單一責任 module（若必要）

只有在既有外部 module 均不適合時，才可新增新的單一責任模組。

正式規則：

- 不得先改 `policy_engine.py` 再事後把邏輯外移
- 必須先決定外部 module，再做 façade 接線

---

# 7. Enforcement Rules for Cursor

本節為可直接提供給 Cursor 的固定前置規則。

## 7.1 Required Pre-Instruction

在任何 policy 相關任務中，必須先讀：

- `docs/attendance/architecture/POLICY_ENGINE_FREEZE.md`
- `docs/attendance/architecture/POLICY_ENGINE_GOVERNANCE.md`

並且在**未完成責任歸屬判定前，禁止修改 `policy_engine.py`**。

## 7.2 Fixed Cursor Prompt Snippet

可直接使用以下固定前置語句：

> 在任何 policy 相關任務中，先讀 `POLICY_ENGINE_FREEZE.md`。未完成責任歸屬判定前，禁止修改 `policy_engine.py`。若該修改可落於 `policy_rules.py`、`policy_missing_segment.py`、`policy_schedule_support.py` 或其他單一責任 module，則必須優先外移，不得回塞 façade。

## 7.3 Cursor Forbidden Behavior

Cursor 不得：

- 看到 engine 有上下文就直接加邏輯
- 把 pure rule 先暫放 engine 再說
- 把 schedule support 先塞進 engine 再說
- 把 missing segment 先接進 engine 再說
- 因為改動小而跳過責任歸屬判定

---

# 8. Review Gate

未來任何 PR / 任務若涉及 `policy_engine.py`，必須符合以下審查規則。

## 8.1 Review Questions

審查者必須確認：

1. 此修改是否真的只屬 façade orchestration 接線？
2. 是否已先判定 `policy_rules.py` 落點？
3. 是否已先判定 `policy_schedule_support.py` 落點？
4. 是否已先判定 `policy_missing_segment.py` 落點？
5. 是否有任何 pure logic 被錯誤塞回 engine？
6. 是否有任何 API / repo / reporting / UI 責任被錯誤帶入 engine？

## 8.2 Rejection Rule

若答案顯示：

- 修改不是 façade glue
- 可放外部 module 卻未外移
- 有 pure rule / support logic 回塞
- 無法說明外移理由

則應：

- **Reject / Stop**

---

# 9. Final Freeze Conclusion

`policy_engine.py` 現在已完成三刀收斂，其正式狀態為：

- **Freeze**
- **Façade only**
- **No responsibility backfill allowed**

最終凍結結論如下：

1. `policy_engine.py` 已固定為 orchestration façade
2. 只允許極小 façade 接線、極小 fallback 修正、極小 result assembly 修正
3. 所有 pure rule、schedule support、missing segment、API / repo / reporting / UI 邏輯，禁止回塞
4. 未來任何 task 若無法先完成責任歸屬判定，禁止修改 `policy_engine.py`
5. 若 `policy_engine.py` 再次膨脹或重新混入非 façade 責任，視為違反 freeze 規則

---

# 10. Enforcement Summary

## Allowed

- 極小 façade orchestration 接線
- 已拆模組呼叫更新
- 極小 fallback 修正
- 極小 result assembly 修正（需 justification）

## Forbidden

- pure rule 回塞
- schedule-specific pure logic 回塞
- missing segment 回塞
- API / repo / reporting 耦合回塞
- UI / response shaping 回塞
- 方便性導向的 façade 擴張

## Mandatory

- 先做責任歸屬判定
- 先回答四個 mandatory check 問題
- 先改外部 module
- 最後才做 façade 最小接線

## Hard Stop

- 想新增 pure rule 到 engine
- 想新增 schedule branch 細節到 engine
- 想讓 engine 直接知道 API / repo 細節
- `policy_engine.py` 超過 500 行且無治理票
- 無法說明外移理由
