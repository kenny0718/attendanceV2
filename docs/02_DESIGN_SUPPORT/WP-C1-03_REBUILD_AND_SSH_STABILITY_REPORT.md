# WP-C1-03 重建報告 + SSH 穩定性分析

**建立日期：** 2026-03-16  
**狀態：** 分析報告（不含程式碼修改）  
**基準點：** restore 至 `wp-11-08-leave-api-complete`（commit `4e9198b`）

---

## 1. Restore 後 Leave 模組狀態盤點

### 1.1 Leave 模組檔案

| 檔案 | 行數 | 狀態 |
|------|------|------|
| `backend/app/modules/leave/models.py` | 439 | 完整 |
| `backend/app/modules/leave/repo.py` | 487 | 完整 |
| `backend/app/modules/leave/service.py` | 467 | 完整 |
| `backend/app/modules/leave/api.py` | 243 | 完整 |
| `backend/app/modules/leave/schemas.py` | 231 | 完整 |
| `backend/app/modules/leave/__init__.py` | 0 | 存在 |
| `backend/alembic/versions/009_wp_11_08_create_leave_tables.py` | — | 完整 |

**總計：1,867 行 leave 核心程式碼完整保留。**

### 1.2 Leave API 端點（WP-11-08 已驗收）

| Endpoint | 狀態 |
|----------|------|
| `POST /api/v1/leave/requests` | 實作完成，manual test PASS |
| `GET /api/v1/leave/my-requests` | 實作完成，manual test PASS |
| `GET /api/v1/leave/pending` | 實作完成，manual test PASS |
| `POST /api/v1/leave/requests/{id}/approve` | 實作完成，manual test PASS |
| `POST /api/v1/leave/requests/{id}/reject` | 實作完成，manual test PASS |

### 1.3 已知限制（繼承自 WP-11-08）

- `approver_id` 欄位目前儲存為 `null`（manager chain 解析邏輯待後續補齊）
- 無自動化測試（無 `tests/` 目錄）
- cancel endpoint 未對外暴露（設計決策）

### 1.4 結論

Restore 至 `4e9198b` 後，**leave 模組本身完整無缺失**。  
今天遺失的是 **WP-C1-03** 的工作，不是 WP-11-08。

---

## 2. 今天遺失的 WP-C1-03 工作盤點

### 2.1 背景

`git log` 最新 commit 為 `4e9198b`（2026-03-15 WP-11-08 完成）。  
今天（2026-03-16）WP-C1-03 的工作**未 commit 即遺失**（SSH service 23:00:56 被 SIGTERM 重啟所致）。

### 2.2 現有程式碼掃描結果

> 重要發現：三個模組的 `api.py` JWT 遷移程式碼已存在於目前 HEAD。

| 模組 | `api.py` JWT 狀態 | 說明 |
|------|-------------------|------|
| `audit` | 已含 `get_actor_with_company` | 多個 endpoint 已遷移，含 WP-C1-03 標注 |
| `notifications` | 已含 `get_actor_with_company` | endpoint 已遷移 |
| `backup` | 已含 `get_actor_with_company` | endpoint 已遷移，含 WP-C1-03 標注 |

這表示 api.py 層的 JWT 遷移早在 WP-11-08 之前已完成並存在 repo 中。  
**今天遺失的是測試更新與文件結案工作。**

### 2.3 推斷遺失的具體工作

1. **三個模組的 `tests/conftest.py`**：JWT actor fixture 更新
2. **`test_audit_api.py` / notifications `test_api.py` / backup `test_api.py`**：改用 actor override
3. **WP-C1-03 結案文件**（docs/ 下找不到對應 .md）
4. **`NEXT_WP_TICKET.md` 更新**：標記 WP-C1-03 COMPLETE、WP-C1-04 NEXT

---

## 3. 重新規劃安全重建順序

### Phase A：快速驗收現有程式碼（估計 30 分鐘）

```bash
# A1. import smoke test
cd /opt/attendance-system/backend && source .venv/bin/activate
python -c "from app.modules.audit.api import router_v1; print('audit OK')"
python -c "from app.modules.notifications.api import router_v1; print('notifications OK')"
python -c "from app.modules.backup.api import router_v1; print('backup OK')"

# A2. 啟動確認：/docs 顯示三模組 endpoints
# A3. auth 行為驗證：無 JWT 應回 403
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/audit/logs
```

### Phase B：補測試（估計 60 分鐘）

```
B1. audit/tests/conftest.py + test_audit_api.py → JWT actor override
    pytest app/modules/audit/tests/ -v

B2. notifications/tests/conftest.py + test_api.py → JWT actor override
    pytest app/modules/notifications/tests/ -v

B3. backup/tests/conftest.py + test_api.py → JWT actor override
    （參考 test_api.py.bak）
    pytest app/modules/backup/tests/ -v
```

### Phase C：文件 + Commit（估計 15 分鐘）

```bash
# C1. 更新 NEXT_WP_TICKET.md（WP-C1-03 COMPLETE，WP-C1-04 NEXT）
# C2. 更新 CURRENT_SYSTEM_STATE.md
# C3. commit + push
git add -A
git commit -m "WP-C1-03: JWT migration audit/notifications/backup COMPLETE"
git push
```

### Phase D：進入 WP-C1-04（下一 Session）

```
D1. 8 個回歸測試（真實 PostgreSQL DB）
D2. 每個測試通過後立即 commit
```

### 安全原則

- 每完成一個子任務 → 立即 `git add -A && git commit`
- 每 30 分鐘或換 Phase 前 → `git push`
- 開始新 Session 前確認 `git status` 乾淨
- SSH 斷線後重連 → 先執行 `git status` 確認工作區

---

## 4. Cursor SSH / Remote Shell 斷線根因分析

### 4.1 已確認根本原因

**主因：`pam_systemd / systemd-logind` 在 Proxmox LXC 中無法正常啟動**

每次 SSH 登入後 PAM 等待 **25 秒**才降級繼續（log 中每次登入均出現）：

```
pam_systemd(sshd:session): Failed to create session:
Failed to activate service 'org.freedesktop.login1':
timed out (service_start_timeout=25000ms)
```

**2026-03-16 23:00:56：SSH service 遭 SIGTERM 強制重啟**

```
sshd[217]: Received signal 15; terminating.
# 殘留：node(x4) / bash(x2) / sftp-server / sshd(x4) / sleep(x1)
```

此次重啟直接造成所有 Cursor SSH session 同時斷線，WP-C1-03 工作全部遺失。

### 4.2 次要因素

| 因素 | 影響 |
|------|------|
| SSH keepalive 全部停用 | 空閒連線靜默斷開，無通知 |
| 無 Swap（0B）| OOM 時 node 程序被靜默終止 |
| LXC cgroup（`0::/init.scope`）| systemd namespace 不完整，logind 無法啟動 |
| Cursor node 子程序累積 | 舊 session 程序在 SSH 重啟時全部終止 |
| ACPI GPE _L24 錯誤 | Proxmox host 硬體問題，與 SSH 斷線無直接關係 |

### 4.3 今日已完成修復（2026-03-16）

| 項目 | 修改位置 | 修改內容 | 狀態 |
|------|----------|----------|------|
| pam_systemd 停用 | `/etc/pam.d/common-session` 第24行 | `#session optional pam_systemd.so` | 完成 |
| TCPKeepAlive | `/etc/ssh/sshd_config` | `TCPKeepAlive yes` | 完成 |
| ClientAliveInterval | `/etc/ssh/sshd_config` | `ClientAliveInterval 60` | 完成 |
| ClientAliveCountMax | `/etc/ssh/sshd_config` | `ClientAliveCountMax 10` | 完成 |
| SSH service 重啟 | — | `systemctl restart ssh` | 完成 |

**修復後驗證：** 最新 log 中 pam_systemd timeout 錯誤已消失。  
**效果：** 空閒連線最多 10 分鐘（60s × 10）才斷，登入不再卡頓 25 秒。

### 4.4 仍存在的風險

- **無 Swap**：記憶體壓力時 node 程序仍可能被 OOM 靜默終止
- **Cursor 子程序累積**：建議偶爾執行 `pkill -f 'cursor-server'` 清理殘留

---

## 5. 建議後續工作流程

### 5.1 每次 Coding Session 標準 SOP

```
【開始前】
1. 確認 SSH 穩定（terminal 回應 < 1 秒）
2. cd /opt/attendance-system
3. git status            ← 必須為 clean
4. git log --oneline -3  ← 確認目前位置

【工作中】
5. 每完成一個子任務 → git add -A && git commit
6. 每 30 分鐘 → git push（無論完成與否）
7. SSH 感覺卡頓 → 立即 git add -A && git commit 搶救現場

【結束前】
8. git status 確認乾淨
9. git push
10. 更新 NEXT_WP_TICKET.md 標記進度
```

### 5.2 WP-C1-03 重建優先順序

```
本次 Session 目標：Phase A + Phase B + Phase C
  ↓
下次 Session：Phase D（WP-C1-04 回歸測試）
```

### 5.3 後續 WP 完整路徑

```
WP-C1-03（audit/notifications/backup JWT 遷移）← 重建中
  ↓
WP-C1-04（8 個回歸測試，真實 DB）
  ↓
WP-C1-05（Tenant Isolation 真實 DB 測試）
  ↓
WP-C1-06（Feature Gate 套用至所有核心 API）
  ↓
[Phase 1 Complete — Gate 5 宣告完成]
```

---

*本報告由 AI 依據 2026-03-16 實際系統掃描結果建立。*  
*不含任何程式碼修改，僅為分析與規劃文件。*
