"""Tenant Isolation 測試

驗證 Tenant Isolation (P0) 規則：
- A 公司 context 無法存取 B 公司資料
- company_id 必須由後端注入，不信任 request body
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestTenantIsolation:
    """Tenant Isolation 測試（P0）"""
    
    def test_approve_requires_company_header(self):
        """測試：缺少 X-Company-ID header 應回 400"""
        response = client.post(
            "/api/attendance/test-record-123/approve",
            json={
                "employee_id": "emp-001",
                "approved_by": "manager-001"
            }
            # 故意不提供 X-Company-ID header
        )
        
        assert response.status_code == 400
        assert "X-Company-ID" in response.text or "Missing" in response.text
    
    def test_approve_with_company_a_context(self):
        """測試：使用 A 公司 context 核准考勤"""
        # 使用 A 公司 context
        headers = {"X-Company-ID": "company-A"}
        
        response = client.post(
            "/api/attendance/test-record-123/approve",
            headers=headers,
            json={
                "employee_id": "emp-A-001",
                "approved_by": "manager-A-001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        
        # 驗證 payload 中的 company_id 是後端注入的
        payload = data["payload"]
        assert payload["company_id"] == "company-A"
        assert payload["employee_id"] == "emp-A-001"
    
    def test_approve_with_company_b_context(self):
        """測試：使用 B 公司 context 核准考勤"""
        # 使用 B 公司 context
        headers = {"X-Company-ID": "company-B"}
        
        response = client.post(
            "/api/attendance/test-record-456/approve",
            headers=headers,
            json={
                "employee_id": "emp-B-001",
                "approved_by": "manager-B-001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        
        # 驗證 payload 中的 company_id 是後端注入的
        payload = data["payload"]
        assert payload["company_id"] == "company-B"
        assert payload["employee_id"] == "emp-B-001"
    
    def test_company_id_injected_by_backend_not_request_body(self):
        """測試：company_id 由後端注入，不信任 request body
        
        即使 request body 試圖傳入 company_id，也應該被忽略
        （因為 ApproveRequest 已不接受 company_id 欄位）
        """
        # 使用 A 公司 context
        headers = {"X-Company-ID": "company-A"}
        
        # 嘗試在 request body 中夾帶 company_id（應該被忽略或拒絕）
        response = client.post(
            "/api/attendance/test-record-789/approve",
            headers=headers,
            json={
                "company_id": "company-B",  # 嘗試偽造成 B 公司
                "employee_id": "emp-001",
                "approved_by": "manager-001"
            }
        )
        
        # 應該成功，但 company_id 必須是 header 中的 A，不是 body 中的 B
        if response.status_code == 200:
            data = response.json()
            payload = data["payload"]
            # 驗證：實際使用的是 header 的 company-A，不是 body 的 company-B
            assert payload["company_id"] == "company-A"
        else:
            # 或者直接拒絕（422 Unprocessable Entity，因為 schema 不接受 company_id）
            assert response.status_code == 422
    
    def test_mock_create_requires_company_header(self):
        """測試：mock-create 也需要 X-Company-ID header"""
        response = client.post("/api/attendance/mock-create")
        
        assert response.status_code == 400
        assert "X-Company-ID" in response.text or "Missing" in response.text
    
    def test_mock_create_with_company_context(self):
        """測試：使用公司 context 建立假考勤記錄"""
        headers = {"X-Company-ID": "company-A"}
        
        response = client.post(
            "/api/attendance/mock-create",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "attendance_record_id" in data
        assert len(data["attendance_record_id"]) > 0


class TestCrossCompanyIsolation:
    """跨公司隔離測試（P0）
    
    Phase 1: 由於沒有資料庫，無法測試「A 公司讀取 B 公司資料」
    Phase 2: 加入資料庫後，必須測試：
    - A 公司 context 查詢 B 公司的 attendance_record → 404 或空集合
    - A 公司 context 更新 B 公司的 attendance_record → 403 或 404
    - A 公司 context 刪除 B 公司的 attendance_record → 403 或 404
    """
    
    def test_phase2_cross_company_read_forbidden(self):
        """Phase 2 必做：A 公司無法讀取 B 公司資料"""
        pytest.skip("Phase 2: 需要資料庫支援")
    
    def test_phase2_cross_company_update_forbidden(self):
        """Phase 2 必做：A 公司無法更新 B 公司資料"""
        pytest.skip("Phase 2: 需要資料庫支援")
    
    def test_phase2_cross_company_delete_forbidden(self):
        """Phase 2 必做：A 公司無法刪除 B 公司資料"""
        pytest.skip("Phase 2: 需要資料庫支援")
