"""事件處理器測試"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.modules.notifications.repo import NotificationRepository
from app.modules.notifications.event_handlers import handle_attendance_approved

# 測試用資料庫（in-memory SQLite）
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立測試資料表
Base.metadata.create_all(bind=engine)


class TestEventHandlers:
    """事件處理器測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # 覆寫 SessionLocal（讓 event handler 使用測試 DB）
        import app.modules.notifications.event_handlers as handlers
        handlers.SessionLocal = TestingSessionLocal
    
    def test_handle_attendance_approved_success(self):
        """測試：成功處理 attendance.approved 事件"""
        payload = {
            "company_id": "company-test",
            "employee_id": "emp-001",
            "attendance_record_id": "record-001",
            "approved_at": "2026-01-14T10:00:00.000000Z",
            "approved_by": "manager-001"
        }
        
        # 處理事件
        handle_attendance_approved(payload)
        
        # 驗證：資料已寫入
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        notifications = repo.get_notifications("company-test")
        
        assert len(notifications) == 1
        assert notifications[0].company_id == "company-test"
        assert notifications[0].event_type == "attendance.approved"
        assert notifications[0].event_payload == payload
        
        db.close()
    
    def test_handle_attendance_approved_fail_fast_missing_company_id(self):
        """測試：Fail-fast - payload 缺少 company_id 應拋出錯誤"""
        payload = {
            "employee_id": "emp-001",
            "attendance_record_id": "record-001",
            "approved_at": "2026-01-14T10:00:00.000000Z"
            # 缺少 company_id
        }
        
        # 應該拋出 ValueError
        with pytest.raises(ValueError) as exc_info:
            handle_attendance_approved(payload)
        
        assert "company_id" in str(exc_info.value)
        
        # 驗證：資料未寫入
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        notifications = repo.get_all_notifications_for_company("any-company")
        assert len(notifications) == 0
        db.close()
    
    def test_handle_attendance_approved_fail_fast_empty_company_id(self):
        """測試：Fail-fast - payload 的 company_id 為空應拋出錯誤"""
        payload = {
            "company_id": "",  # 空字串
            "employee_id": "emp-001",
            "attendance_record_id": "record-001",
            "approved_at": "2026-01-14T10:00:00.000000Z"
        }
        
        # 應該拋出 ValueError
        with pytest.raises(ValueError) as exc_info:
            handle_attendance_approved(payload)
        
        assert "company_id" in str(exc_info.value)
    
    def test_handle_attendance_approved_fail_fast_whitespace_company_id(self):
        """測試：Fail-fast - payload 的 company_id 只有空白應拋出錯誤"""
        payload = {
            "company_id": "   ",  # 只有空白
            "employee_id": "emp-001",
            "attendance_record_id": "record-001",
            "approved_at": "2026-01-14T10:00:00.000000Z"
        }
        
        # 應該拋出 ValueError
        with pytest.raises(ValueError) as exc_info:
            handle_attendance_approved(payload)
        
        assert "company_id" in str(exc_info.value)
    
    def test_handle_attendance_approved_multiple_companies(self):
        """測試：處理多個公司的事件，正確隔離"""
        # 處理 A 公司事件
        payload_a = {
            "company_id": "company-A",
            "employee_id": "emp-A-001",
            "attendance_record_id": "record-A-001",
            "approved_at": "2026-01-14T10:00:00.000000Z"
        }
        handle_attendance_approved(payload_a)
        
        # 處理 B 公司事件
        payload_b = {
            "company_id": "company-B",
            "employee_id": "emp-B-001",
            "attendance_record_id": "record-B-001",
            "approved_at": "2026-01-14T11:00:00.000000Z"
        }
        handle_attendance_approved(payload_b)
        
        # 驗證：各公司資料正確隔離
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        notifications_a = repo.get_notifications("company-A")
        assert len(notifications_a) == 1
        assert notifications_a[0].company_id == "company-A"
        assert notifications_a[0].event_payload["employee_id"] == "emp-A-001"
        
        notifications_b = repo.get_notifications("company-B")
        assert len(notifications_b) == 1
        assert notifications_b[0].company_id == "company-B"
        assert notifications_b[0].event_payload["employee_id"] == "emp-B-001"
        
        db.close()
    
    def test_handle_attendance_approved_uses_payload_company_id_as_source_of_truth(self):
        """測試：使用 payload.company_id 作為 Source of Truth 寫入 DB"""
        payload = {
            "company_id": "company-from-payload",
            "employee_id": "emp-001",
            "attendance_record_id": "record-001",
            "approved_at": "2026-01-14T10:00:00.000000Z"
        }
        
        handle_attendance_approved(payload)
        
        # 驗證：DB 中的 company_id 與 payload 一致
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        notifications = repo.get_notifications("company-from-payload")
        
        assert len(notifications) == 1
        assert notifications[0].company_id == "company-from-payload"
        
        # 驗證：event_payload 也保留了原始 company_id（供稽核）
        assert notifications[0].event_payload["company_id"] == "company-from-payload"
        
        db.close()
