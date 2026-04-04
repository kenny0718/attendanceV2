from typing import Dict, Any

from fastapi import APIRouter

from app.core.event_bus import get_event_bus

router = APIRouter()


@router.get("/test/event")
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


@router.post("/test/event")
async def emit_test_event(payload: Dict[str, Any] | None = None):
    """發出 demo.test_event 事件（用於測試）

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
    event_bus.emit("demo.test_event", payload)

    return {
        "status": "ok",
        "message": "事件已發出",
        "event_name": "demo.test_event",
        "payload": payload
    }


@router.get("/debug/events")
async def get_registered_events():
    """取得 EventBus registry（用於測試/除錯）"""
    event_bus = get_event_bus()
    return {
        "events": event_bus.list_registered_events()
    }
