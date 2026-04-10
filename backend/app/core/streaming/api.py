import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor

from .auth import get_stream_actor
from .service import streaming_service

router = APIRouter(prefix="/api/v1/streaming", tags=["streaming"])


@router.get("/events")
async def stream_events(
    actor: Actor = Depends(get_stream_actor),
    db: Session = Depends(get_db),
):
    async def event_generator():
        system_status = streaming_service.build_system_status_event(actor)
        yield streaming_service.encode_sse(system_status)

        attendance_status = streaming_service.build_attendance_status_event(actor, db)
        yield streaming_service.encode_sse(attendance_status)

        heartbeat = streaming_service.build_heartbeat_event(actor)
        yield streaming_service.encode_sse(heartbeat)

        keepalive_count = 0
        while keepalive_count < 2:
            await asyncio.sleep(15)
            keepalive = streaming_service.build_heartbeat_event(actor)
            yield streaming_service.encode_sse(keepalive)
            keepalive_count += 1

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
