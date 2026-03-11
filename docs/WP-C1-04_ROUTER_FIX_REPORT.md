# WP-C1-04 Router Fix 報告

**日期：** 2026-03-11  
**執行路徑：** `/opt/attendance-system/backend`

---

## 問題描述

`app/modules/attendance/api.py` 檔案內容為空（0 bytes），導致：

```
ImportError: cannot import name 'router'
from app.modules.attendance.api
```

`app/main.py` 依賴以下 import：

```python
from app.modules.attendance.api import router as attendance_router, router_v1 as attendance_router_v1
```

---

## 根本原因

`backend/app/modules/attendance/api.py` 被清空（推測為 WP-C1-02 遷移過程中的意外操作）。  
git HEAD（commit `9576bfb`）仍保有完整的原始內容（642 行），兩個 router 符號均完整存在：

| 符號 | 定義位置 | Prefix |
|------|----------|--------|
| `router` | 第 43 行 | `/api/attendance` |
| `router_v1` | 第 46 行 | `/api/v1/attendance` |

---

## 修復方式

**選用 Option A（還原原始檔案）**，不修改 `main.py`。

執行指令：

```bash
cd /opt/attendance-system
git show HEAD:backend/app/modules/attendance/api.py > backend/app/modules/attendance/api.py
```

還原後行數：**642 行**

---

## 驗證結果

```
$ python -m py_compile backend/app/modules/attendance/api.py
attendance/api.py OK

$ python -m py_compile backend/app/main.py
main.py OK
```

兩個檔案語法檢查均通過，無任何錯誤。

---

## 確認匯出符號

```python
# app/modules/attendance/api.py 第 43-46 行
router = APIRouter(prefix="/api/attendance", tags=["attendance"])
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])
```

`main.py` 的 import 完全匹配，無需修改。

---

## 注意事項

`attendance/api.py` 仍使用舊版 Header 依賴（`get_current_company_id`、`get_current_user_id`），  
這是 **WP-C1-03 範圍外**的模組，本次修復僅還原檔案至 git HEAD 狀態，不修改任何 endpoint 邏輯。  
該模組的 JWT Actor 遷移需另開 WP ticket 處理。
