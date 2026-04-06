# P2 F3 Blocker Report — Historical `app.main` / Upstream Availability Blocker Resolved

> **Document Type**: Blocker Report
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Ticket**: F3 — Align reporting entrypoints to the canonical Taipei boundary normalization owner
> **Purpose**: Record the historical blocker that previously prevented safe F3 baseline collection and validation, and document its audited resolution
> **Execution Mode**: Read-only investigation and documentation update only
> **Status**: Unblocked
> **Inputs**:
> - `backend/app/main.py`
> - `backend/app/modules/attendance/api/reporting.py`
> - `docs/attendance/remediation/02_fix/P2_F3_FIX_SPEC.md`
> - `systemctl status attendance-system --no-pager`
> - `journalctl -u attendance-system -n 120 --no-pager`
> - `ss -ltnp | grep 8000`
> - `curl -I http://127.0.0.1:8000/`
> - `tail -n 50 /var/log/nginx/error.log`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件的目的，是記錄 Phase 2 / F3 在正式進入實作前曾遇到的既有阻塞問題，並補充該阻塞已解除的可審計證據。

本文件整理：
- 歷史阻塞檔案
- 歷史阻塞原因
- 為何曾阻止 F3 baseline / validation
- blocker 已解除的系統層證據
- 目前可進入之下一階段判定

本文件**不包含**：
- 任何 code 修改
- 任何 diff
- 任何 F3 實作內容

---

# 1. Blocker File

歷史阻塞檔案為：
- `backend/app/main.py`

此檔案不是 F3 允許修改範圍，
但它是載入正式 FastAPI app 入口所必經的檔案。

---

# 2. Historical Blocker Reason

> 本節保留原始 `BLOCKED` 分析，作為歷史阻塞紀錄。以下內容描述的是**過去狀態**，不是目前狀態。

## 2.1 Immediate Failure Mode

在建立 F3 baseline 時，正式應用入口載入 `app.main` 曾立即失敗，錯誤為：

```text
IndentationError: unexpected indent
```

## 2.2 Confirmed Problem Location

歷史問題位置為 `backend/app/main.py` 中一行縮排異常的 router include：

```67:67:backend/app/main.py
    app.include_router(debug_event_router, prefix="/api")
```

該行當時在既有路由註冊區塊中出現額外縮排，造成：
- Python parser 在 import `app.main` 時即失敗
- FastAPI app 無法被正常建立

## 2.3 Nature of the Problem

此歷史問題屬於：
- 既有語法 / 縮排錯誤
- 與 F3 boundary owner 邏輯無關
- 在 F3 開始修改前就已存在

因此它是：
- **historical pre-existing blocker**
- 不是 F3 實作過程產生的新錯誤

---

# 3. Why This Previously Blocked F3 Baseline / Validation

> 本節保留原始阻塞分析，說明**過去為何無法安全進入 F3**。

F3 的安全執行流程要求：

1. 先建立 baseline（修改前）
   - `sessions`
   - `user-summary`
   - `company-summary`
2. 再做 boundary source 替換
3. 再做 after compare
4. 再做 consistency validation
   - reporting vs breaks
5. 再確認既有 tests 未失敗

但在歷史阻塞狀態下，`backend/app/main.py` 無法被 import，會直接造成以下問題：

## 3.1 Baseline Cannot Be Collected Safely

由於正式 app 入口無法建立：
- 無法透過正式 API entrypoints 安全取得 `sessions / user-summary / company-summary` baseline
- 任何嘗試建立 baseline 的腳本，都會先在 `app.main` import 階段失敗

因此：
- 無法取得可信的修改前參考值

## 3.2 After Validation Cannot Be Trusted

即使後續強行修改 `reporting.py`，
若 app 入口本身仍無法正常載入：
- after validation 無法可靠執行
- 無法判定結果差異到底來自 F3 boundary 修正，還是來自既有 app 入口錯誤

因此：
- 無法形成可審計的 before / after compare

## 3.3 Consistency Check Cannot Be Proven

F3 要求：
- reporting 與 breaks 在同一 Taipei business boundary 下結果一致

但若正式 app 入口不能啟動：
- reporting API 無法可靠呼叫
- breaks vs reporting consistency 無法在同一正式執行路徑上驗證

因此：
- 無法提供足夠證據證明 F3 成功

## 3.4 Stop Condition Logic

F3 本票的執行規則要求：
- baseline / after 必須可驗證
- 測試必須可執行
- 若差異不可解釋或驗證流程不成立，必須停止

在歷史阻塞狀態下：
- 驗證前提條件不成立
- 阻塞檔案又在本票禁止修改範圍內

因此當時合理結論為：
- **F3 必須在實作前停止**

---

# 4. Historical Suggested Resolution

> 本節保留原始建議，作為歷史處置脈絡紀錄。

## 4.1 Recommended Fix Path

建議先以**獨立小票**處理 `backend/app/main.py` 的既有縮排 / 語法錯誤。

原因：
- 該問題不是 F3 boundary owner 問題
- 也不是 reporting 專屬邏輯問題
- 應獨立為 app entry blocker 修復

## 4.2 Why It Should Be Separate

將其獨立處理的好處：
- 避免把 F3 boundary 修正與 unrelated app entry fix 混在同一票
- 保持 F3 execution report 可審計
- baseline / validation 的因果關係更乾淨

## 4.3 Minimal Unblock Requirement

要解除 F3 阻塞，至少必須先滿足：
- `backend/app/main.py` 可被正常 import
- 正式 FastAPI app 入口可建立
- baseline 腳本能順利呼叫 reporting 三個 entrypoints

只有在這之後，F3 才能安全進入：
- baseline
- `.tmp` implementation
- after compare
- consistency validation

---

# 5. Blocker Resolution

## 5.1 Historical 502 / Upstream Failure Evidence

系統層唯讀診斷已確認，先前 502 的直接證據來自 `nginx` error log：

```text
connect() failed (111: Connection refused) while connecting to upstream
upstream: "http://127.0.0.1:8000/api/internal/auth/login"
```

此證據表示：
- `nginx` 已嘗試連線至既定 upstream `127.0.0.1:8000`
- 當時 upstream 端口拒絕連線
- 問題屬於**當時 uvicorn / FastAPI service 未接受連線**

## 5.2 Root Cause Classification

根據 `nginx`、`systemd`、`uvicorn` 與本機 loopback 驗證結果，先前 502 應分類為：

- **暫時性 upstream 不可用**
- **非 nginx upstream 配置錯誤**

換言之：
- 問題發生時，`nginx` 的代理目標為 `127.0.0.1:8000`
- 真正失敗點是 upstream 端無法接受連線，而不是 upstream 設定本身錯誤

## 5.3 Current State Evidence

目前已完成系統層唯讀確認，證據如下：

1. `app.main` import 成功
   - 驗證方式：在正確 venv 下執行 `import app.main`
   - 結果：`IMPORT_OK`

2. `attendance-system` service 為 active
   - 驗證方式：`systemctl status attendance-system --no-pager`
   - 結果：`Active: active (running)`

3. `uvicorn` 正常 listen 於 `127.0.0.1:8000`
   - 驗證方式：`ss -ltnp | grep 8000`
   - 結果：`127.0.0.1:8000` 處於 `LISTEN`

4. 本機 curl 可取得有效回應
   - 驗證方式：`curl -I http://127.0.0.1:8000/`
   - 結果：`HTTP/1.1 405 Method Not Allowed`
   - 該結果代表請求已到達 `uvicorn`，屬有效 HTTP 回應，非 502 / 非 connection refused

5. `journalctl` 未見目前啟動阻塞
   - 驗證方式：`journalctl -u attendance-system -n 120 --no-pager`
   - 結果：可見近期正常 API 請求與正常 SQL 執行紀錄，未見當前 import crash / startup failure

## 5.4 Current Interpretation

綜合目前證據可判定：
- 先前 blocker 屬於**歷史性、暫時性 upstream 不可用事件**
- 目前已不存在 `main.py` / `app.main` 啟動阻塞
- 目前正式服務可接受連線，且 loopback 驗證可成功回應

因此，先前 blocker 已符合「已解除」條件。

---

# 6. Final Blocker Status

本次 Phase 2 / F3 目前可判定為：

- **Historical Blocker Status: BLOCKED (resolved)**
- **Current Execution Status: UNBLOCKED**

目前結論：
- 歷史上確實曾存在 blocker
- 該 blocker 曾使 F3 不得進入 baseline / validation
- 但經系統層唯讀診斷後，已確認 blocker 原因為當時 upstream connection refused
- 目前該條件已不存在

一句話總結：

**F3 曾因歷史性 upstream 不可用 / app entry 載入問題而阻塞，但該 blocker 已解除；目前不再被 `main.py` 或 app 啟動問題阻塞，可進入 baseline / validation 階段。**
