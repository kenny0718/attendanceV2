"""
考勤打卡 API 路由
"""
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.modules.attendance.schemas import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceStatusResponse,
    AttendanceLogResponse,
)
from app.modules.attendance.service import AttendanceService
from app.modules.users.models import User

router = APIRouter(prefix="/attendance", tags=["考勤打卡"])


@router.post("/punch", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def punch(
    attendance_data: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    打卡
    
    支援的打卡類型：
    - IN: 上班打卡
    - OUT: 下班打卡
    - BREAK_OUT: 外出打卡
    - BREAK_IN: 返回打卡
    """
    service = AttendanceService(db)
    
    try:
        attendance = service.create_attendance(
            user_id=current_user.id,
            attendance_type=attendance_data.attendance_type,
            latitude=attendance_data.latitude,
            longitude=attendance_data.longitude,
            reason=attendance_data.reason,
        )
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/status", response_model=AttendanceStatusResponse)
async def get_today_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    獲取今日打卡狀態
    
    返回今日的上班、下班、外出、返回時間
    """
    service = AttendanceService(db)
    status_data = service.get_today_status(current_user.id)
    return status_data


@router.get("/logs", response_model=List[AttendanceLogResponse])
async def get_attendance_logs(
    start_date: Optional[date] = Query(None, description="開始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    limit: int = Query(10, ge=1, le=100, description="返回數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    獲取打卡記錄
    
    可選參數：
    - start_date: 開始日期
    - end_date: 結束日期
    - limit: 返回數量（預設 10，最多 100）
    - offset: 偏移量（用於分頁）
    """
    service = AttendanceService(db)
    logs = service.get_attendance_logs(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return logs


@router.get("/report")
async def get_attendance_report(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    獲取月度考勤報表
    
    包含：
    - 出勤天數
    - 遲到次數
    - 早退次數
    - 缺勤天數
    - 加班時數
    """
    service = AttendanceService(db)
    report = service.get_monthly_report(
        user_id=current_user.id,
        year=year,
        month=month,
    )
    return report


@router.post("/missed-punch")
async def request_missed_punch(
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    補打卡申請
    
    需要提供：
    - date: 補打卡日期
    - attendance_type: 打卡類型
    - time: 打卡時間
    - reason: 補打卡原因
    """
    service = AttendanceService(db)
    
    try:
        request = service.create_missed_punch_request(
            user_id=current_user.id,
            date=request_data.get("date"),
            attendance_type=request_data.get("attendance_type"),
            time=request_data.get("time"),
            reason=request_data.get("reason"),
        )
        return {"success": True, "data": request}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/missed-punch")
async def get_missed_punch_requests(
    status: Optional[str] = Query(None, description="狀態篩選"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    獲取補打卡申請列表
    
    可選參數：
    - status: 狀態篩選（pending/approved/rejected）
    """
    service = AttendanceService(db)
    requests = service.get_missed_punch_requests(
        user_id=current_user.id,
        status=status,
    )
    return {"success": True, "data": requests}


@router.put("/missed-punch/{request_id}")
async def approve_missed_punch(
    request_id: int,
    action_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    審核補打卡申請（管理員）
    
    需要提供：
    - action: approve 或 reject
    - comment: 審核意見（可選）
    """
    # TODO: 檢查權限（只有管理員可以審核）
    
    service = AttendanceService(db)
    
    try:
        result = service.approve_missed_punch_request(
            request_id=request_id,
            approver_id=current_user.id,
            action=action_data.get("action"),
            comment=action_data.get("comment"),
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
