"""Phase 1 快速測試腳本

此腳本會：
1. 建立假考勤記錄
2. 核准該考勤記錄
3. 顯示結果
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_phase1():
    """測試 Phase 1 功能"""
    print("=" * 60)
    print("Phase 1 測試開始")
    print("=" * 60)
    
    # 步驟 1: 建立假考勤記錄
    print("\n[步驟 1] 建立假考勤記錄...")
    try:
        response = requests.post(f"{BASE_URL}/api/attendance/mock-create")
        response.raise_for_status()
        data = response.json()
        attendance_record_id = data["attendance_record_id"]
        print(f"✓ 成功建立考勤記錄")
        print(f"  attendance_record_id: {attendance_record_id}")
    except Exception as e:
        print(f"✗ 失敗: {e}")
        return
    
    # 步驟 2: 核准考勤記錄
    print("\n[步驟 2] 核准考勤記錄...")
    try:
        payload = {
            "company_id": "company-123",
            "employee_id": "emp-456",
            "approved_by": "manager-789"
        }
        response = requests.post(
            f"{BASE_URL}/api/attendance/{attendance_record_id}/approve",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ 成功核准考勤記錄")
        print(f"  回應: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"✗ 失敗: {e}")
        return
    
    # 驗證結果
    print("\n[驗證] 檢查回應內容...")
    if data.get("ok") == True:
        print("✓ ok 欄位正確")
    else:
        print("✗ ok 欄位錯誤")
    
    payload_data = data.get("payload", {})
    required_fields = ["company_id", "employee_id", "attendance_record_id", "approved_at"]
    
    for field in required_fields:
        if field in payload_data:
            print(f"✓ payload 包含必填欄位: {field}")
        else:
            print(f"✗ payload 缺少必填欄位: {field}")
    
    if "approved_by" in payload_data:
        print(f"✓ payload 包含選填欄位: approved_by")
    
    print("\n" + "=" * 60)
    print("Phase 1 測試完成")
    print("=" * 60)
    print("\n請檢查終端機 log，應該看到：")
    print("  - 'INFO:app.modules.attendance.service:準備發出事件 attendance.approved'")
    print("  - 'INFO:app.core.event_bus:發出事件: attendance.approved'")
    print("  - 'INFO:app.main:[Attendance Approved Handler] 收到事件 attendance.approved'")
    print("  - 各個 payload 欄位的詳細資訊")


if __name__ == "__main__":
    test_phase1()
