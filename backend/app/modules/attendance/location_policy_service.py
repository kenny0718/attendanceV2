"""Attendance Location Policy Service (WP-11-13)

提供 location policy 評估功能，判斷打卡位置是否符合公司設定的允許地點。

設計原則：
1. 後端 authoritative enforcement（前端 precheck 只是 UX-friendly）
2. 無 allowed locations → 允許任何地點
3. 有 allowed locations → 必須在任一地點範圍內
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.modules.attendance.models import AllowedLocation
from app.modules.attendance.gps_utils import calculate_distance


@dataclass
class PolicyCheckResult:
    """Policy check result"""
    allowed: bool
    reason: str
    matched_location: Optional[Dict] = None
    nearest_location: Optional[Dict] = None


class AttendanceLocationPolicyService:
    """Location Policy 評估服務
    
    責任：
    1. 讀取公司啟用中的 allowed locations
    2. 檢查 GPS 是否命中任一允許地點
    3. 回傳 allow/deny + matched location + violation reason
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_allowed_locations(self, company_id: str) -> List[AllowedLocation]:
        """取得公司啟用中的 allowed locations
        
        Args:
            company_id: 公司 ID
        
        Returns:
            啟用中的 allowed locations 列表
        """
        return self.db.query(AllowedLocation).filter(
            AllowedLocation.company_id == company_id,
            AllowedLocation.is_active == True
        ).all()
    
    def check_location_policy(
        self,
        company_id: str,
        latitude: float,
        longitude: float
    ) -> PolicyCheckResult:
        """檢查 location policy
        
        邏輯：
        1. 取得公司的所有啟用中的 allowed locations
        2. 如果沒有任何 allowed locations → 允許任何地點打卡
        3. 如果有 allowed locations：
           a. 計算與每個地點的距離
           b. 檢查是否有任一地點在半徑內
           c. 如果有 → 允許打卡，返回匹配的地點
           d. 如果沒有 → 拒絕打卡，返回最近的地點
        
        Args:
            company_id: 公司 ID
            latitude: 打卡位置緯度
            longitude: 打卡位置經度
        
        Returns:
            PolicyCheckResult
        """
        # Step 1: 取得啟用中的 allowed locations
        locations = self.get_active_allowed_locations(company_id)
        
        # Step 2: 如果沒有設定任何地點 → 允許任何地點
        if not locations:
            return PolicyCheckResult(
                allowed=True,
                reason="公司允許任何地點打卡"
            )
        
        # Step 3: 計算距離並檢查
        matched_location = None
        nearest_location = None
        min_distance = float('inf')
        
        for location in locations:
            # 計算距離
            distance = calculate_distance(
                (latitude, longitude),
                (float(location.latitude), float(location.longitude))
            )
            
            # 更新最近地點
            if distance < min_distance:
                min_distance = distance
                nearest_location = location
            
            # 檢查是否在半徑內
            if distance <= location.radius_meters:
                matched_location = location
                break  # 找到第一個匹配的就可以
        
        # Step 4: 返回結果
        if matched_location:
            return PolicyCheckResult(
                allowed=True,
                reason=f"在允許的打卡範圍內：{matched_location.name}",
                matched_location={
                    "id": str(matched_location.id),
                    "name": matched_location.name,
                    "distance_meters": int(calculate_distance(
                        (latitude, longitude),
                        (float(matched_location.latitude), float(matched_location.longitude))
                    ))
                }
            )
        else:
            return PolicyCheckResult(
                allowed=False,
                reason=f"不在允許的打卡範圍內。最近的地點：{nearest_location.name}（距離 {int(min_distance)} 公尺）",
                nearest_location={
                    "id": str(nearest_location.id),
                    "name": nearest_location.name,
                    "distance_meters": int(min_distance)
                }
            )


def get_location_policy_service(db: Session) -> AttendanceLocationPolicyService:
    """Get location policy service instance
    
    Args:
        db: Database session
    
    Returns:
        AttendanceLocationPolicyService instance
    """
    return AttendanceLocationPolicyService(db)
