from app.core.config import settings, is_testing
from app.modules.demo_event_subscribers import register_demo_event_subscribers
from app.modules.notifications.event_handlers import register_event_handlers


def register_demo_startup_handlers(event_bus):
    if settings.debug or is_testing():
        register_demo_event_subscribers(event_bus)


def register_production_startup_handlers():
    register_event_handlers()
