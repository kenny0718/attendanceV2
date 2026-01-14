"""Attendance Repository（資料存取層）

Phase 1: 空架構（不使用資料庫）
Phase 2: 將實作資料庫 CRUD 操作
"""

import logging

logger = logging.getLogger(__name__)


class AttendanceRepository:
    """考勤資料存取層
    
    Phase 1: 空實作
    Phase 2 將實作：
    - create_attendance_record(company_id, ...)
    - get_attendance_record(company_id, record_id)
    - update_attendance_status(company_id, record_id, status)
    - 所有查詢必須強制 company_id 篩選
    """
    
    def __init__(self):
        """初始化 Repository"""
        pass


# 全域 Repository 實例
_repo_instance: AttendanceRepository | None = None


def get_attendance_repository() -> AttendanceRepository:
    """取得 AttendanceRepository 單例
    
    Returns:
        AttendanceRepository 實例
    """
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = AttendanceRepository()
    return _repo_instance
