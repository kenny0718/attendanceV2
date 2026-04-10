from typing import Optional

from fastapi import Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_actor
from app.core.scope import Actor


def get_stream_actor(
    access_token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Actor:
    auth_header = authorization
    if not auth_header and access_token:
        auth_header = f"Bearer {access_token}"

    return get_current_actor(authorization=auth_header, db=db)
