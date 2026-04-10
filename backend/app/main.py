"""FastAPI 應用入口"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request

from app.core.event_bus import get_event_bus
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.streaming import router as streaming_router
# from app.core.database import init_db  # Deprecated: Use alembic upgrade head instead
from app.modules.attendance.api import router as attendance_router, router_v1 as attendance_router_v1
from app.modules.router_wiring import register_demo_routers
from app.modules.attendance.admin_location_api import router as admin_location_router  # WP-11-13
from app.modules.notifications.api import router as notifications_router
from app.modules.backup.api import router as backup_router
from app.modules.audit.api import router as audit_router
from app.modules.auth.api import router as auth_router
from app.modules.tenants.api import router as tenants_router
from app.modules.customer_service.api import router as customer_service_router
from app.modules.leave.api import router_v1 as leave_router_v1  # WP-11-08
from app.modules.schedule.api import router as schedule_router  # WP-S1-04B
from app.modules.startup_wiring import register_demo_startup_handlers, register_production_startup_handlers
from app.modules.debug_event_api import router as debug_event_router

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

# 註冊統一錯誤處理
register_exception_handlers(app)

# A1-4: Legacy header reintroduction guard (log-only, never block)
@app.middleware("http")
async def legacy_header_guard(request: Request, call_next):
    """A1-4: Warn if retired legacy headers reappear in any request.

    X-Company-ID and X-User-ID were retired in A1-3.
    All production endpoints use JWT actor exclusively.
    This guard logs a warning to surface accidental reintroduction.
    """
    _RETIRED_HEADERS = ("x-company-id", "x-user-id")
    for header in _RETIRED_HEADERS:
        if header in request.headers:
            logger.warning(
                f"[A1-4] Legacy header detected: '{header}' — "
                "retired in A1-3, ignored by all production endpoints. "
                "Check for accidental reintroduction."
            )
    return await call_next(request)

# 註冊路由
app.include_router(attendance_router)
app.include_router(attendance_router_v1)
register_demo_routers(app)  # WP-C1-06
app.include_router(admin_location_router)  # WP-11-13
app.include_router(notifications_router)
app.include_router(backup_router)
app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(customer_service_router)
app.include_router(leave_router_v1)  # WP-11-08
app.include_router(schedule_router)  # WP-S1-04B
app.include_router(debug_event_router, prefix="/api")
app.include_router(streaming_router)


@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化資料庫與 EventBus"""
    logger.info("應用啟動 - 確保已執行 alembic upgrade head")

    # 初始化 EventBus
    event_bus = get_event_bus()

    # 註冊 demo 訂閱者
    register_demo_startup_handlers(event_bus)

    # 註冊 notifications 事件處理器
    register_production_startup_handlers()

    logger.info("EventBus 已初始化，所有訂閱者已註冊")


@app.get("/")
async def root():
    """API 根路徑 - 歡迎頁面"""
    return {
        "message": "Welcome to Attendance System API",
        "version": "2.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1"
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok", "service": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
