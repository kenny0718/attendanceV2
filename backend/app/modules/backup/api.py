"""Backup API

備份模組的 API 端點（佔位符）。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/")
def backup_placeholder():
    """備份 API 佔位符"""
    return {"status": "ok", "message": "Backup API placeholder"}
