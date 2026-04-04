from app.modules.attendance.feature_gate_demo import router as attendance_gate_demo_router


def register_demo_routers(app):
    if settings.debug or is_testing():
        app.include_router(attendance_gate_demo_router)
