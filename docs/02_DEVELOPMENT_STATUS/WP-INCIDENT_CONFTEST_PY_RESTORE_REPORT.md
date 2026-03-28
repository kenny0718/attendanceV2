
# WP-INCIDENT: backend/app/conftest.py Restore Report

**日期：** 2026-03-28
**執行人：** Cursor AI Agent
**事故類型：** 0 bytes（第 7 次 0KB 事故記錄）
**狀態：** RESOLVED
**Commit：** 563ac2c

---

## 1. Summary

- backend/app/conftest.py 從 0 bytes 安全恢復至 4361 bytes
- pytest 動態測試基礎已恢復：21 tests collected（原為全部 ERROR）
- 3 個測試 FAILED（pre-existing bug：user_a.id.id AttributeError，非本輪 scope）
- 動態測試從 BLOCKED 進入 FAILED 狀態，基礎設施已可用

---

## 2. Files Changed

| 檔案 | 操作 | 說明 |
|------|------|------|
| backend/app/conftest.py | restore from 5aa994a | 從 0 bytes 恢復至 4361 bytes |
| backend/app/conftest.py.incident_20260328 | cp 保全副本 | 保留 0 bytes 事故現場 |
| docs/02_DEVELOPMENT_STATUS/WP-INCIDENT_CONFTEST_PY_RESTORE_REPORT.md | 新增（本檔）| 記錄恢復過程 |

---

## 3. Restore Source



各 commit 版本大小：

| Commit | Size | 說明 |
|--------|------|------|
| 19cf043（HEAD）| 0 bytes | 0KB 事故，不可用 |
| 5aa994a | 4361 bytes | 最近可用版本，選用此版本 |
| 6cf5ce3 | 4027 bytes | 可用 |
| c6c9c28 | 4021 bytes | 可用 |
| fd7c6a5 | 3275 bytes | 可用（較舊）|

**恢復策略：** git show 5aa994a:backend/app/conftest.py > /tmp/conftest_restore.py，確認 4361 bytes 後 cp 覆蓋
**incident 副本：** backend/app/conftest.py.incident_20260328（0 bytes，保留事故現場）

---

## 4. Integrity Verification



**結論：** 完整，非截斷，db fixture 存在

---

## 5. Pytest Baseline Validation

**collect 驗證：**


**動態執行（3 個代表性測試）：**

| 測試 | 結果 | 說明 |
|------|------|------|
| SES-11 naive datetime 422 | FAILED | pre-existing bug：user_a.id.id AttributeError |
| SES-12 company_admin cross-user | FAILED | 同上 |
| SES-06 tenant isolation | FAILED | 同上 |

**重要：** 3 個 FAILED 均為  AttributeError，
這是測試程式碼本身的既有 bug（UUID 物件無  屬性），
與 conftest 恢復無關，不在本輪修復 scope 內。

**動態測試狀態：** 從 BLOCKED（ERROR）進入 FAILED，基礎設施已恢復

---

## 6. Git Status / Commit



已 git add + commit：YES

---

## 7. Risks / Follow-up

| 風險 | 等級 | 建議 |
|------|------|------|
| user_a.id.id AttributeError（3 個測試）| Medium | 下一輪修復（test bug，非 production bug）|
| 0KB 再發風險（已第 7 次）| High | 需建立強制 pre-write verify 機制 |
| backend/app/conftest.py 0KB 來源不明 | Medium | 最後正常版本在 5aa994a（2026-03-12），中間某個操作清空，需追查 |

### 下一輪建議

1. 修復 test_reporting_sessions.py 中的  → （最小 patch）
2. 執行 SES-01 ~ SES-12 全套測試，確認動態驗證完整通過
3. 標記 S1-12D 為 PASS（動態確認後）

---

*恢復完成。conftest 從 0 bytes 安全救回，pytest 基礎設施已可用。*
