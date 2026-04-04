Step 2 Final Acceptance Report
1. Summary

本次 Step 2 目標為：
收斂 policy_engine 的出勤判定邏輯，使其達到可預測、可測試、低風險的穩定狀態。

本階段已完成：

移除不可靠的推論型邏輯（missing_segment）
保留 deterministic 判定（late / early_leave）
明確界定 Step 2 能力邊界
完成測試語意與 business timezone 對齊
所有 policy_engine baseline 測試通過（24 passed, 0 failed）

👉 本階段重點為「穩定與收斂」，而非功能擴張。

2. Scope Accepted

本次驗收確認以下邏輯為正式行為（accepted behavior）：

出勤判定規則
late 判定
以「第一段 shift window 的 start」為基準
early_leave 判定
以「最後一段 shift window 的 end」為基準
不使用 segment / overlap 推論
evaluate_with_schedule_v2()
violation_flags = []
僅保留 deterministic 判定
不進行 missing_segment 推論
測試語意（重要）
baseline 測試統一採用：
Asia/Taipei business timezone
不再使用 UTC wall-clock 作為出勤語意

👉 原則：

UTC 用於儲存與傳輸，
business rule 一律依 company timezone 判定。

3. Explicitly Deferred

以下項目明確不屬於 Step 2，已延後：

missing_segment 判定

已停用，原因：

單一 session（punch_in ~ punch_out）
無法可靠推斷中間是否缺勤
缺乏以下 runtime 資訊：
segment-level punch artifacts
multi-session trace
session ↔ segment mapping
延後至 Step 3 / Runtime Hardening

後續需要：

session segmentation model
segment-level attendance evidence
break / multi-session 行為建模

👉 Step 2 不處理推論型缺勤。

4. Test Validation

測試結果：

24 passed, 0 failed

驗證內容包含：

normal attendance
late / within grace
early_leave
overtime
fallback（無 policy）
split shift 基本行為
tenant isolation
測試修正重點
baseline 測試改為 Asia/Taipei
消除原本 +480 分鐘偏移
未修改 engine 邏輯
5. Known Non-Blocking Items

目前存在但不阻斷驗收的項目：

Deprecation Warnings

包含：

Pydantic V1 → V2：
class Config
@validator
FastAPI：
@app.on_event

👉 性質：

非 runtime error
屬於 future compatibility issue
處理策略
本次 不處理
後續另立 migration / technical debt 票：
Pydantic V2 migration
FastAPI lifespan migration
6. Risk Assessment
當前風險：低

已消除：

❌ overlap-based 推論錯誤
❌ 時區語意不一致
❌ 測試不可預測性
已知限制（可接受）
無法判定中段缺勤（missing_segment）
無 multi-session 支援

👉 已明確 defer，非隱性風險。

7. Final Verdict

✅ Step 2 可結案（ACCEPTED）

理由：

核心邏輯已收斂為 deterministic 行為
測試已與 business timezone 完整對齊
所有 baseline 測試通過
高風險推論邏輯已移除並延後
無 blocking issue
最終一句話

Step 2 已達「穩定可預測版本」，可作為後續 Step 3（runtime hardening / segment model）的安全基線。