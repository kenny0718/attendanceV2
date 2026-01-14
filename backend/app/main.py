"""FastAPI 應用入口"""

import logging
from typing import Dict, Any
from fastapi import FastAPI

from app.core.event_bus import get_event_bus
from app.core.config import settings
from app.modules.attendance.api import router as attendance_router

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# 註冊路由
app.include_router(attendance_router)


@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化 EventBus 並註冊 demo 訂閱者"""
    event_bus = get_event_bus()
    
    # 註冊 demo 訂閱者
    def demo_handler(payload: Dict[str, Any]) -> None:
        """Demo 事件處理器"""
        logger.info(f"[Demo Handler] 收到事件 test.event，payload: {payload}")
    
    def attendance_approved_handler(payload: Dict[str, Any]) -> None:
        """Attendance 核准事件處理器（Demo）"""
        logger.info(f"[Attendance Approved Handler] 收到事件 attendance.approved")
        logger.info(f"  - company_id: {payload.get('company_id')}")
        logger.info(f"  - employee_id: {payload.get('employee_id')}")
        logger.info(f"  - attendance_record_id: {payload.get('attendance_record_id')}")
        logger.info(f"  - approved_at: {payload.get('approved_at')}")
        logger.info(f"  - approved_by: {payload.get('approved_by', 'N/A')}")
    
    event_bus.subscribe("test.event", demo_handler)
    event_bus.subscribe("attendance.approved", attendance_approved_handler)
    logger.info("EventBus 已初始化，demo 訂閱者已註冊")


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/test/event")
async def get_event_status():
    """取得當前事件訂閱狀態（用於測試/除錯）"""
    event_bus = get_event_bus()
    events = event_bus.list_events()
    
    result = {}
    for event_name in events:
        subscribers = event_bus.get_subscribers(event_name)
        result[event_name] = {
            "subscriber_count": len(subscribers),
            "subscribers": [handler.__name__ for handler in subscribers]
        }
    
    return {
        "status": "ok",
        "events": result
    }


@app.post("/api/test/event")
async def emit_test_event(payload: Dict[str, Any] | None = None):
    """發出 test.event 事件（用於測試）
    
    Body (可選):
        {
            "message": "測試訊息",
            "data": {...}
        }
    """
    event_bus = get_event_bus()
    
    # 如果沒有提供 payload，使用預設值
    if payload is None:
        payload = {"message": "Hello from test event!"}
    
    # 發出事件
    event_bus.emit("test.event", payload)
    
    return {
        "status": "ok",
        "message": "事件已發出",
        "event_name": "test.event",
        "payload": payload
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
