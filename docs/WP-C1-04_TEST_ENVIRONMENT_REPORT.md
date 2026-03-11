# WP-C1-04 測試環境報告

**產出日期：** 2026-03-11  
**執行路徑：** `/opt/attendance-system/backend`  
**目的：** 說明目前 pytest 無法直接透過系統指令執行的原因，並提供正確的執行方式。

---

## A. Python 執行環境狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| `python` 指令 | ❌ 不可用 | 系統未設定 `python` symlink |
| `python3` 指令 | ✅ 可用 | `/usr/bin/python3` → Python 3.11.2 |
| `pip3` 指令 | ✅ 可用 | `/usr/bin/pip3`，但受 PEP 668 保護，無法系統安裝 |
| 系統 `pytest` | ❌ 不可用 | 未安裝於系統層 |
| venv `pytest` | ✅ 可用 | `/opt/attendance-system/backend/venv/bin/pytest 9.0.2` |

**根本原因：**

此伺服器為 Debian 系統，套用 PEP 668「externally-managed-environment」保護。執行 `pip3 install pytest` 會直接失敗：

```
error: externally-managed-environment
× This environment is externally managed
```

因此所有 Python 套件必須透過專案內建的 **venv** 環境安裝與執行。

---

## B. 專案依賴管理方式

**使用方式：** `requirements.txt` + 手動 venv

| 檔案 | 存在 | 說明 |
|------|------|------|
| `backend/requirements.txt` | ✅ | 主要依賴定義檔 |
| `pyproject.toml` | ❌ | 不存在 |
| `poetry.lock` | ❌ | 不存在 |
| `Pipfile` / `Pipfile.lock` | ❌ | 不存在 |
| `Makefile` | ❌ | 不存在 |
| `backend/venv/` | ✅ | 已建立，含所有套件 |

`backend/requirements.txt` 內容：

```
# FastAPI 與相關依賴
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# 資料庫（同步 SQLAlchemy + PostgreSQL）
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# 測試
pytest>=7.4.0
httpx>=0.25.0
```

---

## C. 測試框架確認

**框架：pytest**

依據：
- `requirements.txt` 明確列出 `pytest>=7.4.0`
- `backend/conftest.py` 使用 `@pytest.fixture` 模式
- `backend/tests/test_migration_smoke.py` 使用 `import pytest` 及 `def test_*()` 命名慣例
- venv 內已安裝 `pytest 9.0.2`

**測試檔案分布：**

```
backend/
├── conftest.py                          # Global fixtures（tenant 設定）
├── test_db_connection.py                # DB 連線測試（根目錄）
├── test_phase1.py                       # Phase 1 功能測試（根目錄）
└── tests/
    └── test_migration_smoke.py          # Alembic migration smoke test
```

---

## D. 正確的測試執行指令

### 前置條件

必須從 `backend/` 目錄執行，並使用 venv 內的 pytest：

```bash
cd /opt/attendance-system/backend
```

### 執行全部測試

```bash
/opt/attendance-system/backend/venv/bin/pytest
```

### 執行特定測試目錄

```bash
# 只跑 tests/ 子目錄
/opt/attendance-system/backend/venv/bin/pytest tests/

# 只跑根目錄測試檔
/opt/attendance-system/backend/venv/bin/pytest test_db_connection.py test_phase1.py

# 只跑 migration smoke test
/opt/attendance-system/backend/venv/bin/pytest tests/test_migration_smoke.py -v
```

### 使用 venv 啟動後執行（更簡潔）

```bash
source /opt/attendance-system/backend/venv/bin/activate
cd /opt/attendance-system/backend
pytest
```

### 搭配環境變數（migration smoke test 需要）

`test_migration_smoke.py` 會自行設定 `DATABASE_URL`，不需要額外傳入。但若需覆蓋：

```bash
DATABASE_URL=postgresql+psycopg2://postgres:PASSWORD@127.0.0.1:5432/attendance \
  /opt/attendance-system/backend/venv/bin/pytest tests/ -v
```

---

## E. 已安裝套件清單（venv 內）

以下為 `requirements.txt` 宣告套件的實際安裝版本：

| 套件 | 需求版本 | 已安裝版本 | 狀態 |
|------|----------|------------|------|
| `fastapi` | >=0.104.0 | 0.135.1 | ✅ |
| `uvicorn` | >=0.24.0 | 0.41.0 | ✅ |
| `pydantic` | >=2.5.0 | 2.12.5 | ✅ |
| `pydantic-settings` | >=2.1.0 | 2.13.1 | ✅ |
| `sqlalchemy` | >=2.0.0 | 2.0.48 | ✅ |
| `psycopg2-binary` | >=2.9.0 | 2.9.11 | ✅ |
| `pytest` | >=7.4.0 | 9.0.2 | ✅ |
| `httpx` | >=0.25.0 | 0.28.1 | ✅ |

**缺少的依賴：無。** 所有宣告套件均已安裝於 venv。

---

## F. 建議修復方式

### 現況總結

| 問題 | 說明 |
|------|------|
| `python` 指令不存在 | Debian 預設只有 `python3`；venv 內已建立 `python → python3` symlink |
| 系統層無法安裝套件 | PEP 668 保護，屬正常 Debian 行為 |
| `pytest` 不在 `$PATH` | 系統 PATH 未包含 venv；需明確使用完整路徑或 activate |

### 建議（不需修改任何程式碼）

**方案 1（推薦）：每次執行前 activate venv**

```bash
source /opt/attendance-system/backend/venv/bin/activate
cd /opt/attendance-system/backend
pytest -v
```

退出 venv：
```bash
deactivate
```

**方案 2：直接使用完整路徑（不需 activate，適合 CI/腳本）**

```bash
/opt/attendance-system/backend/venv/bin/pytest \
  /opt/attendance-system/backend \
  -v --tb=short
```

**方案 3：若需重建 venv（venv 損毀時）**

```bash
python3 -m venv /opt/attendance-system/backend/venv
/opt/attendance-system/backend/venv/bin/pip install -r /opt/attendance-system/backend/requirements.txt
```

### WP-C1-04 測試修復範圍說明

根據 WP-C1-03 遷移結果，以下測試預期會失敗（因仍使用 `X-Company-ID` Header）：

- 任何對 `notifications`、`backup`、`audit` 模組使用 `headers={"X-Company-ID": ...}` 的測試

WP-C1-04 任務為將這些測試更新為 JWT Bearer Token 驗證方式，**不在本報告範圍內修改**。

---

*報告產出：WP-C1-03 執行後，WP-C1-04 前置環境確認步驟*
