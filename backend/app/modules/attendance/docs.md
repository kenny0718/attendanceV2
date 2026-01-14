# Attendance 模組文件

## 概述

Attendance 模組負責處理考勤相關的業務邏輯，包括考勤記錄的建立、核准等功能。

## Phase 1 實作範圍

Phase 1 為最小可行實作，目標是建立事件驅動架構的基礎。

### 功能

1. **Mock 建立考勤記錄**：產生假的考勤記錄 ID（用於測試）
2. **核准考勤記錄**：觸發考勤核准流程，發出 `attendance.approved` 事件

### API 端點

#### 1. POST /api/attendance/mock-create

建立假的考勤記錄（用於測試）。

**回應範例：**
```json
{
  "attendance_record_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 2. POST /api/attendance/{attendance_record_id}/approve

核准指定的考勤記錄。

**路徑參數：**
- `attendance_record_id`: 考勤記錄 ID

**請求 Body：**
```json
{
  "company_id": "company-123",
  "employee_id": "emp-456",
  "approved_by": "manager-789"
}
```

**欄位說明：**
- `company_id` (必填): 公司 ID，用於多租戶隔離
- `employee_id` (必填): 員工 ID
- `approved_by` (選填): 核准人 ID，建議提供以便未來稽核

**回應範例：**
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

## 事件定義

### attendance.approved

當考勤記錄被核准時發出此事件。

**Payload 規格：**

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `company_id` | string | 是 | 公司 ID（多租戶隔離用） |
| `employee_id` | string | 是 | 員工 ID |
| `attendance_record_id` | string | 是 | 考勤記錄 ID |
| `approved_at` | string | 是 | 核准時間（ISO8601 格式，UTC） |
| `approved_by` | string | 否 | 核准人 ID（建議提供） |

**Payload 範例：**
```json
{
  "company_id": "company-123",
  "employee_id": "emp-456",
  "attendance_record_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_at": "2026-01-14T10:30:00.000000Z",
  "approved_by": "manager-789"
}
```

## 架構說明

### 檔案結構

```
backend/app/modules/attendance/
├── __init__.py       # 模組初始化
├── api.py            # API 路由定義
├── service.py        # 業務邏輯層
└── docs.md           # 模組文件（本檔案）
```

### 設計原則

1. **最小實作**：Phase 1 不包含資料庫操作，專注於事件驅動架構
2. **事件驅動**：使用 EventBus 發出事件，解耦模組間的依賴
3. **多租戶支援**：所有 payload 都包含 `company_id`，為未來的多租戶隔離做準備
4. **可測試性**：提供 mock 端點方便測試

## 測試流程

1. 啟動應用：`uvicorn app.main:app --reload`
2. 建立假考勤記錄：
   ```bash
   curl -X POST http://localhost:8000/api/attendance/mock-create
   ```
3. 核准考勤記錄（使用上一步回傳的 ID）：
   ```bash
   curl -X POST http://localhost:8000/api/attendance/{attendance_record_id}/approve \
     -H "Content-Type: application/json" \
     -d '{
       "company_id": "company-123",
       "employee_id": "emp-456",
       "approved_by": "manager-789"
     }'
   ```
4. 檢查 log 確認事件已發出

## 未來擴展

Phase 1 之後的擴展方向：

- 加入資料庫層（models, repository）
- 實作真實的工時計算邏輯
- 加入權限驗證
- 加入更多考勤相關的事件（如：`attendance.created`, `attendance.rejected`）
- 實作事件訂閱者（如：工時計算模組、通知模組）
