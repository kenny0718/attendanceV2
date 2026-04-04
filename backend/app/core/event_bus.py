"""In-memory 同步事件匯流排"""

from typing import Callable, Dict, List, Any


def _is_valid_event_name(event_name: str) -> bool:
    parts = event_name.split(".")
    if len(parts) != 2:
        return False

    domain, action = parts
    if not domain or not action:
        return False


    return True


import logging

from app.core.config import is_testing, settings

logger = logging.getLogger(__name__)


class EventBus:
    """In-memory 同步事件匯流排
    
    事件命名規範：<module>.<action>（例如：test.event、attendance.approved）
    """
    
    def __init__(self):
        """初始化 EventBus"""
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, handler: Callable) -> None:
        """訂閱事件
        
        Args:
            event_name: 事件名稱（格式：<module>.<action>）
            handler: 事件處理函式，接收 payload: Dict[str, Any] 作為參數
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.debug(f"已訂閱事件: {event_name}")
    
    def emit(self, event_name: str, payload: Dict[str, Any]) -> None:
        """發出事件（同步執行所有訂閱者）
        
        Args:
            event_name: 事件名稱
            payload: 事件資料（字典格式）
        
        注意：一個訂閱者失敗不會影響其他訂閱者的執行
        """
        if not _is_valid_event_name(event_name):
            logger.warning(f"事件名稱不符合最小命名規範: {event_name}")

        if not settings.debug and not is_testing() and (event_name.startswith("demo.") or event_name.startswith("debug.")):
            logger.warning(f"已阻擋非 debug/testing 環境事件發出: {event_name}")
            return

        if event_name not in self._subscribers:
            logger.debug(f"事件 {event_name} 沒有訂閱者")
            return
        
        handlers = self._subscribers[event_name]
        logger.info(f"發出事件: {event_name}，訂閱者數量: {len(handlers)}")
        
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                logger.error(
                    f"事件處理器執行失敗: {event_name}, handler={handler.__name__}, error={e}",
                    exc_info=True
                )
    
    def get_subscribers(self, event_name: str) -> List[Callable]:
        """取得指定事件的所有訂閱者（用於測試/除錯）
        
        Args:
            event_name: 事件名稱
        
        Returns:
            訂閱者列表
        """
        return self._subscribers.get(event_name, []).copy()
    
    def list_events(self) -> List[str]:
        """列出所有已訂閱的事件名稱（用於測試/除錯）
        
        Returns:
            事件名稱列表
        """
        return list(self._subscribers.keys())


# 全域 EventBus 單例
_event_bus_instance: EventBus | None = None


def get_event_bus() -> EventBus:
    """取得全域 EventBus 單例
    
    Returns:
        EventBus 實例
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance
