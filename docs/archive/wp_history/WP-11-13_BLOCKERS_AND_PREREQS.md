# WP-11-13 - 阻塞項目與前置條件

**日期**: 2026-03-08  
**狀態**: 已識別所有阻塞項目

---

## 阻塞項目清單

### 1. Python 依賴環境 ❌ BLOCKER

**問題**: 系統 Python 環境受保護，無法直接安裝套件

**錯誤訊息**:
```
error: externally-managed-environment
```

**影響範圍**:
- Backend 模組 import 測試
- Backend 服務啟動
- pytest 執行
- Alembic migration 執行

**解決方案**:
```bash
# 1. 建立 venv
cd backend
python3 -m venv venv

# 2. 啟動 venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 驗證安裝
python -c "import fastapi, sqlalchemy, pydantic; print('✅ 依賴已安裝')"
```

**預估時間**: 5 分鐘

---

### 2. PostgreSQL 資料庫 ❌ BLOCKER

**問題**: 無可用的 PostgreSQL 資料庫

**影響範圍**:
- Migration 執行
- Backend API 啟動
- 所有資料庫相關測試

**解決方案**:

**Option A: 使用 Docker**
```bash
# 啟動 PostgreSQL
docker run -d \
  --name attendance-postgres \
  -e POSTGRES_DB=attendance_db \
  -e POSTGRES_USER=attendance_user \
  -e POSTGRES_PASSWORD=attendance_pass \
  -p 5432:5432 \
  postgres:15

# 設定環境變數
export DATABASE_URL="postgresql://attendance_user:attendance_pass@localhost:5432/attendance_db"
```

**Option B: 本地安裝**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15

# 建立資料庫
sudo -u postgres createdb attendance_db
sudo -u postgres createuser attendance_user
sudo -u postgres psql -c "ALTER USER attendance_user WITH PASSWORD 'attendance_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;"

# 設定環境變數
export DATABASE_URL="postgresql://attendance_user:attendance_pass@localhost:5432/attendance_db"
```

**預估時間**: 10-30 分鐘（視方案而定）

---

### 3. Backend 服務啟動 ❌ BLOCKER

**問題**: 依賴於阻塞項目 1 和 2

**影響範圍**:
- API 端點測試
- Integration 測試
- 煙霧測試

**解決方案**:
```bash
# 前置條件: 已解決阻塞項目 1 和 2

# 1. 啟動 venv
cd backend
source venv/bin/activate

# 2. 設定環境變數
export DATABASE_URL="postgresql://..."

# 3. 執行 migration
alembic upgrade head

# 4. 啟動服務
uvicorn app.main:app --reload

# 5. 驗證
curl http://localhost:8000/health
```

**預估時間**: 5 分鐘（在前置條件完成後）

---

## 前置條件檢查清單

### Phase 1: 環境準備

- [ ] Python 3.11.x 已安裝
- [ ] Node.js 20.x 已安裝
- [ ] PostgreSQL 15.x 可用
- [ ] Git 已安裝

### Phase 2: Python 環境

- [ ] backend/venv 已建立
- [ ] venv 已啟動
- [ ] requirements.txt 依賴已安裝
- [ ] 可以 import fastapi, sqlalchemy, pydantic

### Phase 3: 資料庫

- [ ] PostgreSQL 服務運行中
- [ ] attendance_db 資料庫已建立
- [ ] 使用者權限已設定
- [ ] DATABASE_URL 環境變數已設定
- [ ] 可以連線到資料庫

### Phase 4: Migration

- [ ] Alembic 可用
- [ ] Migration 007 已執行（前置 migration）
- [ ] Migration 008 準備執行

### Phase 5: Backend 服務

- [ ] Backend 可以啟動
- [ ] /health 端點回應正常
- [ ] /v1/attendance/current-status 端點可訪問

### Phase 6: Frontend

- [ ] node_modules 已安裝
- [ ] npm run build 成功
- [ ] dist 目錄已產生

---

## 依賴關係圖

```
Phase 1: 環境準備
    ↓
Phase 2: Python 環境 ← 解決阻塞項目 1
    ↓
Phase 3: 資料庫 ← 解決阻塞項目 2
    ↓
Phase 4: Migration
    ↓
Phase 5: Backend 服務 ← 解決阻塞項目 3
    ↓
Phase 6: Frontend
    ↓
Manual QA 執行
```

---

## 快速啟動腳本

```bash
#!/bin/bash
# quick-start.sh - WP-11-13 快速啟動腳本

set -e

echo "=== WP-11-13 環境準備 ==="

# Phase 1: 檢查環境
echo "Phase 1: 檢查環境..."
python3 --version || { echo "❌ Python 3 未安裝"; exit 1; }
node --version || { echo "❌ Node.js 未安裝"; exit 1; }
psql --version || { echo "❌ PostgreSQL 未安裝"; exit 1; }

# Phase 2: Python 環境
echo "Phase 2: 建立 Python 環境..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# Phase 3: 資料庫（假設已運行）
echo "Phase 3: 檢查資料庫..."
export DATABASE_URL="${DATABASE_URL:-postgresql://attendance_user:attendance_pass@localhost:5432/attendance_db}"
psql $DATABASE_URL -c "SELECT 1" || { echo "❌ 資料庫連線失敗"; exit 1; }

# Phase 4: Migration
echo "Phase 4: 執行 Migration..."
alembic upgrade head

# Phase 5: 啟動 Backend（背景）
echo "Phase 5: 啟動 Backend..."
uvicorn app.main:app --reload &
BACKEND_PID=$!
sleep 3

# Phase 6: Frontend
echo "Phase 6: 準備 Frontend..."
cd ../frontend
npm run build

echo "✅ 環境準備完成"
echo "Backend PID: $BACKEND_PID"
echo "Backend URL: http://localhost:8000"
echo "Frontend: dist/ 目錄已準備"
```

---

## 故障排除

### 問題: venv 建立失敗

**症狀**: `python3 -m venv venv` 失敗

**可能原因**: python3-venv 套件未安裝

**解決方式**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# 然後重試
python3 -m venv venv
```

---

### 問題: PostgreSQL 連線失敗

**症狀**: `psql: could not connect to server`

**可能原因**: PostgreSQL 服務未啟動

**解決方式**:
```bash
# 檢查服務狀態
sudo systemctl status postgresql

# 啟動服務
sudo systemctl start postgresql

# 設定開機自動啟動
sudo systemctl enable postgresql
```

---

### 問題: Migration 失敗

**症狀**: `alembic upgrade head` 失敗

**可能原因**: 
1. 資料庫連線問題
2. 前置 migration 未執行
3. 表已存在

**解決方式**:
```bash
# 檢查當前 migration 版本
alembic current

# 檢查 migration 歷史
alembic history

# 如果需要，降級後重新升級
alembic downgrade -1
alembic upgrade head
```

---

## 總結

**Critical Blockers**: 3 個
- Python 依賴環境
- PostgreSQL 資料庫
- Backend 服務啟動

**預估總時間**: 20-40 分鐘（首次設定）

**建議順序**: 
1. 先解決 Python 環境（5 分鐘）
2. 再解決資料庫（10-30 分鐘）
3. 最後啟動服務（5 分鐘）

**完成後**: 可以執行 Backend Unit Tests 和 API Integration Tests

---

**建立日期**: 2026-03-08  
**狀態**: 已識別所有阻塞項目  
**下一步**: 依序解決阻塞項目
