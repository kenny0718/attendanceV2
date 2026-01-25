# Attendance V2

出勤管理系統後端 API

## 環境需求

- Python 3.11.x
- PostgreSQL 15.x（Phase 0 尚未使用）
- Virtualenv (venv)

## 專案結構

```
attendanceV2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 應用入口
│   │   ├── core/
│   │   │   ├── event_bus.py     # EventBus 核心實作
│   │   │   └── config.py        # 應用設定
│   │   └── modules/              # 業務模組（Phase 0 為空）
│   └── requirements.txt         # Python 依賴
├── docs/                         # 專案文件
└── README.md
```

## Phase 0：最小可運行後端骨架

目前實作內容：

- ✅ FastAPI 應用框架
- ✅ In-memory 同步 EventBus
- ✅ 事件測試端點 (`/api/test/event`)

## 快速開始

### 1. 建立虛擬環境

```bash
cd backend
python -m venv venv
```

### 2. 啟動虛擬環境

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 啟動應用

```bash
# 從 backend 目錄執行
uvicorn app.main:app --reload
```

或

```bash
# 從專案根目錄執行
cd backend
uvicorn app.main:app --reload
```

### 5. 測試

- 健康檢查：`http://localhost:8000/health`
- 查看事件狀態：`http://localhost:8000/api/test/event` (GET)
- 發出測試事件：`http://localhost:8000/api/test/event` (POST)

## EventBus 使用方式

### 訂閱事件

```python
from app.core.event_bus import get_event_bus

event_bus = get_event_bus()

def my_handler(payload: Dict[str, Any]):
    print(f"收到事件，資料: {payload}")

event_bus.subscribe("test.event", my_handler)
```

### 發出事件

```python
from app.core.event_bus import get_event_bus

event_bus = get_event_bus()
event_bus.emit("test.event", {"message": "Hello"})
```

### 事件命名規範

格式：`<module>.<action>`

範例：
- `test.event`
- `attendance.approved`
- `leave.submitted`

## 開發規範

請參考 `docs/SA_MODULE_SPEC.md` 和 `docs/Cursor任務模板.txt`

## License

（待補充）
