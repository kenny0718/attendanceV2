import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.scope import Actor
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.schemas import SessionResponse

from .schemas import StreamEventEnvelope


class StreamingService:
    def build_heartbeat_event(self, actor: Actor) -> StreamEventEnvelope:
        return StreamEventEnvelope(
            event="system.heartbeat.v1",
            id=str(uuid4()),
            data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "company_id": actor.active_company_id,
                "user_id": str(actor.user_id),
                "role": actor.role.value,
            },
        )

    def build_system_status_event(self, actor: Actor) -> StreamEventEnvelope:
        return StreamEventEnvelope(
            event="system.status.v1",
            id=str(uuid4()),
            data={
                "status": "ok",
                "app_name": settings.app_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "company_id": actor.active_company_id,
                "user_id": str(actor.user_id),
                "role": actor.role.value,
                "stream_scope": "authenticated_demo",
            },
        )

    def build_attendance_status_event(self, actor: Actor, db: Session) -> StreamEventEnvelope:
        repo = get_attendance_session_repository(db)
        user_uuid = UUID(str(actor.user_id))
        session = repo.get_open_session(actor.active_company_id, user_uuid)

        if session:
            elapsed = datetime.now(timezone.utc) - session.punch_in_time
            elapsed_minutes = int(elapsed.total_seconds() / 60)
            last_break_punch = repo.get_last_break_punch(session.id)
            is_on_break = bool(last_break_punch and last_break_punch.punch_type == 'break_start')

            session_response = SessionResponse(
                session_id=session.id,
                user_id=session.user_id,
                company_id=session.company_id,
                punch_in_time=session.punch_in_time,
                punch_out_time=session.punch_out_time,
                duration_minutes=session.duration_minutes,
                status=session.status,
            )

            payload = {
                "has_open_session": True,
                "session": session_response.model_dump(mode="json"),
                "elapsed_minutes": elapsed_minutes,
                "is_on_break": is_on_break,
                "company_id": actor.active_company_id,
                "user_id": str(actor.user_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            payload = {
                "has_open_session": False,
                "session": None,
                "elapsed_minutes": None,
                "is_on_break": False,
                "company_id": actor.active_company_id,
                "user_id": str(actor.user_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return StreamEventEnvelope(
            event="attendance.status.v1",
            id=str(uuid4()),
            data=payload,
        )

    def encode_sse(self, envelope: StreamEventEnvelope) -> str:
        return "\n".join([
            f"id: {envelope.id}",
            f"event: {envelope.event}",
            f"data: {json.dumps(envelope.data, ensure_ascii=False)}",
            "",
            "",
        ])


streaming_service = StreamingService()
