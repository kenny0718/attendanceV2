import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def demo_handler(payload: Dict[str, Any]) -> None:
    """Demo 事件處理器"""
    logger.info(f"[Demo Handler] 收到事件 demo.test_event，payload: {payload}")


def attendance_approved_demo_handler(payload: Dict[str, Any]) -> None:
    """Attendance 核准事件處理器（Demo，用於 log）"""
    logger.info(f"[Demo Handler] 收到事件 attendance.approved")
    logger.info(f"  - company_id: {payload.get('company_id')}")
    logger.info(f"  - employee_id: {payload.get('employee_id')}")
    logger.info(f"  - attendance_record_id: {payload.get('attendance_record_id')}")
    logger.info(f"  - approved_at: {payload.get('approved_at')}")
    logger.info(f"  - approved_by: {payload.get('approved_by', 'N/A')}")


def register_demo_event_subscribers(event_bus) -> None:
    event_bus.subscribe("demo.test_event", demo_handler)
    event_bus.subscribe("attendance.approved", attendance_approved_demo_handler)
