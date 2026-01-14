# Phase 1 測試指南

## 啟動應用

```bash
cd backend
uvicorn app.main:app --reload
```

## 測試步驟

### 1. 建立假考勤記錄

```bash
curl -X POST http://localhost:8000/api/attendance/mock-create
```

**預期回應：**
```json
{
  "attendance_record_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. 核准考勤記錄

使用上一步回傳的 `attendance_record_id`：

```bash
curl -X POST http://localhost:8000/api/attendance/550e8400-e29b-41d4-a716-446655440000/approve \
  -H "Content-Type: application/json" \
  -d "{\"company_id\": \"company-123\", \"employee_id\": \"emp-456\", \"approved_by\": \"manager-789\"}"
```

**預期回應：**
```json
{
  "ok": true,
  "payload": {
    "company_id": "company-123",
    "employee_id": "emp-456",
    "attendance_record_id": "550e8400-e29b-41d4-a716-446655440000",
    "approved_at": "2026-01-14T10:30:00.000000Z",
    "approved_by": "manager-789"
  }
}
```

### 3. 檢查 Log

在終端機中應該看到類似以下的 log：

```
INFO:app.modules.attendance.service:準備發出事件 attendance.approved，payload: {...}
INFO:app.core.event_bus:發出事件: attendance.approved，訂閱者數量: 1
INFO:app.main:[Attendance Approved Handler] 收到事件 attendance.approved
INFO:app.main:  - company_id: company-123
INFO:app.main:  - employee_id: emp-456
INFO:app.main:  - attendance_record_id: 550e8400-e29b-41d4-a716-446655440000
INFO:app.main:  - approved_at: 2026-01-14T10:30:00.000000Z
INFO:app.main:  - approved_by: manager-789
INFO:app.modules.attendance.service:事件 attendance.approved 已發出
```

## 使用 FastAPI Swagger UI 測試

1. 開啟瀏覽器訪問：http://localhost:8000/docs
2. 找到 `attendance` 標籤下的端點
3. 先執行 `POST /api/attendance/mock-create`
4. 複製回傳的 `attendance_record_id`
5. 執行 `POST /api/attendance/{attendance_record_id}/approve`，填入：
   - Path parameter: `attendance_record_id`
   - Request body:
     ```json
     {
       "company_id": "company-123",
       "employee_id": "emp-456",
       "approved_by": "manager-789"
     }
     ```

## 驗證清單

- [ ] API 可以成功建立假考勤記錄
- [ ] API 可以成功核准考勤記錄
- [ ] 回應包含正確的 payload 結構
- [ ] Log 顯示事件已發出
- [ ] Log 顯示訂閱者收到事件
- [ ] Payload 包含所有必填欄位（company_id, employee_id, attendance_record_id, approved_at）
- [ ] Payload 包含選填欄位（approved_by）

## PowerShell 測試指令

如果使用 PowerShell，請使用以下指令：

```powershell
# 1. 建立假考勤記錄
Invoke-RestMethod -Uri "http://localhost:8000/api/attendance/mock-create" -Method Post

# 2. 核准考勤記錄（替換 {id} 為實際的 ID）
$body = @{
    company_id = "company-123"
    employee_id = "emp-456"
    approved_by = "manager-789"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/attendance/{id}/approve" -Method Post -Body $body -ContentType "application/json"
```
