"""
Feature Keys 定義
集中管理所有 feature flags 的 key，避免散落 hardcode

WP-11-04A: Company Entitlements + Feature Flags
"""
from typing import Set


class FeatureKeys:
    """所有可用的 feature keys"""
    
    # Attendance 模組相關功能
    ATTENDANCE_SHIFT_TEMPLATES = "attendance.shift_templates"
    ATTENDANCE_SPLIT_SHIFT = "attendance.split_shift"
    ATTENDANCE_SHIFT_OVERRIDES = "attendance.shift_overrides"
    
    # 未來可擴充其他模組的 feature keys
    # LEAVE_CUSTOM_TYPES = "leave.custom_types"
    # PAYROLL_ADVANCED = "payroll.advanced"
    
    @classmethod
    def all_keys(cls) -> Set[str]:
        """回傳所有定義的 feature keys"""
        return {
            cls.ATTENDANCE_SHIFT_TEMPLATES,
            cls.ATTENDANCE_SPLIT_SHIFT,
            cls.ATTENDANCE_SHIFT_OVERRIDES,
        }
    
    @classmethod
    def is_valid(cls, key: str) -> bool:
        """驗證 feature key 是否有效"""
        return key in cls.all_keys()
    
    @classmethod
    def validate(cls, key: str) -> None:
        """驗證 feature key，無效則拋出異常"""
        if not cls.is_valid(key):
            raise ValueError(
                f"Unknown feature key: {key}. "
                f"Valid keys: {', '.join(sorted(cls.all_keys()))}"
            )


# Plan 預設配置（不寫死在邏輯中，方便調整）
PLAN_DEFAULTS = {
    "Basic": {
        FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES: False,
        FeatureKeys.ATTENDANCE_SPLIT_SHIFT: False,
        FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES: False,
    },
    "Pro": {
        FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES: True,
        FeatureKeys.ATTENDANCE_SPLIT_SHIFT: True,
        FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES: True,
    },
}
