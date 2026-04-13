"""Phase 1 快速測試腳本

此腳本會：
1. 建立假考勤記錄
2. 核准該考勤記錄
3. 測試 Tenant Isolation
4. 顯示結果
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
        headers = {"X-Company-ID": "company-123"}
        response = requests.post(
            f"{BASE_URL}/api/attendance/mock-create",
            headers=headers
        )
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
        headers = {
            "X-Company-ID": "company-123",
            "X-User-ID": "user-001"
        }
        payload = {
            "employee_id": "emp-456",
            "approved_by": "approver-789"
        }
        response = requests.post(
            f"{BASE_URL}/api/attendance/{attendance_record_id}/approve",
            headers=headers,
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
    
    # 驗證 company_id 是後端注入的
    if payload_data.get("company_id") == "company-123":
        print(f"✓ company_id 正確（由後端注入）")
    else:
        print(f"✗ company_id 錯誤")
    
    # 步驟 3: 測試 Tenant Isolation
    print("\n[步驟 3] 測試 Tenant Isolation（P0）...")
    
    # 測試 3.1: 缺少 X-Company-ID header
    print("\n  [3.1] 測試缺少 X-Company-ID header...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/attendance/test-001/approve",
            json={"employee_id": "emp-001"}
        )
        if response.status_code == 400:
            print("  ✓ 正確拒絕（400 Bad Request）")
        else:
            print(f"  ✗ 應該回 400，實際回 {response.status_code}")
    except Exception as e:
        print(f"  ✗ 測試失敗: {e}")
    
    # 測試 3.2: A 公司 context
    print("\n  [3.2] 測試 A 公司 context...")
    try:
        headers = {"X-Company-ID": "company-A"}
        response = requests.post(
            f"{BASE_URL}/api/attendance/test-002/approve",
            headers=headers,
            json={"employee_id": "emp-A-001"}
        )
        if response.status_code == 200:
            data = response.json()
            if data["payload"]["company_id"] == "company-A":
                print("  ✓ company_id 正確注入為 company-A")
            else:
                print(f"  ✗ company_id 應為 company-A，實際為 {data['payload']['company_id']}")
        else:
            print(f"  ✗ 應該成功（200），實際回 {response.status_code}")
    except Exception as e:
        print(f"  ✗ 測試失敗: {e}")
    
    # 測試 3.3: B 公司 context
    print("\n  [3.3] 測試 B 公司 context...")
    try:
        headers = {"X-Company-ID": "company-B"}
        response = requests.post(
            f"{BASE_URL}/api/attendance/test-003/approve",
            headers=headers,
            json={"employee_id": "emp-B-001"}
        )
        if response.status_code == 200:
            data = response.json()
            if data["payload"]["company_id"] == "company-B":
                print("  ✓ company_id 正確注入為 company-B")
            else:
                print(f"  ✗ company_id 應為 company-B，實際為 {data['payload']['company_id']}")
        else:
            print(f"  ✗ 應該成功（200），實際回 {response.status_code}")
    except Exception as e:
        print(f"  ✗ 測試失敗: {e}")
    
    # 測試 3.4: 嘗試在 body 偽造 company_id
    print("\n  [3.4] 測試在 body 偽造 company_id...")
    try:
        headers = {"X-Company-ID": "company-A"}
        response = requests.post(
            f"{BASE_URL}/api/attendance/test-004/approve",
            headers=headers,
            json={
                "company_id": "company-B",  # 嘗試偽造
                "employee_id": "emp-001"
            }
        )
        if response.status_code == 422:
            print("  ✓ 正確拒絕（422 Unprocessable Entity）")
        elif response.status_code == 200:
            data = response.json()
            if data["payload"]["company_id"] == "company-A":
                print("  ✓ 忽略 body 的 company_id，使用 header 的值")
            else:
                print(f"  ✗ 安全漏洞！使用了 body 的 company_id")
        else:
            print(f"  ? 未預期的狀態碼: {response.status_code}")
    except Exception as e:
        print(f"  ✗ 測試失敗: {e}")
    
    print("\n" + "=" * 60)
    print("Phase 1 測試完成")
    print("=" * 60)
    print("\n請檢查終端機 log，應該看到：")
    print("  - 'INFO:app.modules.attendance.service:準備發出事件 attendance.approved'")
    print("  - 'INFO:app.core.event_bus:發出事件: attendance.approved'")
    print("  - 'INFO:app.main:[Attendance Approved Handler] 收到事件 attendance.approved'")
    print("  - 各個 payload 欄位的詳細資訊")
    print("\n執行完整測試套件：")
    print("  pytest backend/app/modules/attendance/tests/ -v")


if __name__ == "__main__":
    test_phase1()
