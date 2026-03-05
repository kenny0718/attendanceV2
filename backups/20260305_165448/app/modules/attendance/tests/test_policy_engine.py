"""Tests for Attendance Policy Engine (WP-11-03)

Tests policy evaluation logic:
- Late detection
- Early leave detection
- Overtime detection
- Fallback behavior (no policy)
- Tenant isolation
"""

import pytest
from datetime import datetime, time, timezone, timedelta
from uuid import uuid4

from app.modules.attendance.models import AttendanceSession, AttendancePolicy
from app.modules.attendance.policy_engine import AttendancePolicyEngine, PolicyEvaluationResult


class TestPolicyEngineBasics:
    """Test basic policy engine functionality"""
    
    def test_evaluate_normal_attendance(self):
        """測試：正常出勤（不遲到、不早退、不加班）"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=540
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        assert result.is_late == False
        assert result.late_minutes == 0
        assert result.is_early_leave == False
        assert result.early_leave_minutes == 0
        assert result.is_overtime == False
        assert result.overtime_minutes == 0
        assert result.work_minutes == 540
        assert result.policy_name == "Standard Policy"
    
    def test_evaluate_late_attendance(self):
        """測試：遲到（超過 grace period）"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 20, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=520
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        assert result.is_late == True
        assert result.late_minutes == 5
        assert result.is_early_leave == False
        assert result.work_minutes == 520
    
    def test_evaluate_within_grace_period(self):
        """測試：在寬限時間內（不算遲到）"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 10, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=530
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        assert result.is_late == False
        assert result.late_minutes == 0
    
    def test_evaluate_early_leave(self):
        """測試：早退"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 17, 30, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=510
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        assert result.is_late == False
        assert result.is_early_leave == True
        assert result.early_leave_minutes == 30
        assert result.work_minutes == 510
    
    def test_evaluate_overtime(self):
        """測試：加班"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 19, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=600
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        assert result.is_late == False
        assert result.is_early_leave == False
        assert result.is_overtime == True
        assert result.overtime_minutes == 60
        assert result.work_minutes == 600
    
    def test_evaluate_late_and_overtime(self):
        """測試：遲到 + 加班"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 10, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 19, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=540
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        assert result.is_late == True
        assert result.late_minutes == 45
        assert result.is_overtime == False
        assert result.work_minutes == 540


class TestPolicyEngineFallback:
    """Test policy engine fallback behavior (no policy)"""
    
    def test_evaluate_without_policy(self):
        """測試：無政策時使用預設值"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 30, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 30, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy=None)
        
        assert result.is_late == True
        assert result.late_minutes == 30
        assert result.is_early_leave == False
        assert result.is_overtime == True
        assert result.overtime_minutes == 60
        assert result.work_minutes == 540
        assert result.policy_name == "Default Policy (No Policy Assigned)"
    
    def test_evaluate_overtime_without_policy(self):
        """測試：無政策時的加班判斷（使用 8 小時預設）"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy=None)
        
        assert result.is_overtime == True
        assert result.overtime_minutes == 60


class TestPolicyEngineEdgeCases:
    """Test edge cases and error handling"""
    
    def test_evaluate_open_session_raises_error(self):
        """測試：評估 open session 會拋出錯誤"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=None,
            status='open',
            duration_minutes=None
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        with pytest.raises(ValueError, match="Cannot evaluate open session"):
            engine.evaluate(session, policy)
    
    def test_evaluate_no_overtime_threshold(self):
        """測試：政策無加班門檻時不判斷加班"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 20, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=660
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="No Overtime Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=None
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        assert result.is_overtime == False
        assert result.overtime_minutes == 0
        assert result.work_minutes == 660
    
    def test_result_to_dict(self):
        """測試：PolicyEvaluationResult.to_dict() 轉換"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=540
        )
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate(session, policy)
        
        result_dict = result.to_dict()
        
        assert "session_id" in result_dict
        assert "policy" in result_dict
        assert "timing" in result_dict
        assert "evaluation" in result_dict
        assert result_dict["policy"]["policy_name"] == "Standard Policy"
        assert result_dict["evaluation"]["is_late"] == False
        assert result_dict["timing"]["work_minutes"] == 540


class TestPolicyEngineTenantIsolation:
    """Test tenant isolation in policy evaluation"""
    
    def test_different_companies_different_policies(self):
        """測試：不同公司使用不同政策"""
        session_a = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 20, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=520
        )
        
        policy_a = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Strict Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=10,
            overtime_threshold_minutes=540
        )
        
        session_b = AttendanceSession(
            id=uuid4(),
            company_id="company-b",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 20, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=520
        )
        
        policy_b = AttendancePolicy(
            id=uuid4(),
            company_id="company-b",
            name="Lenient Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=30,
            overtime_threshold_minutes=540
        )
        
        engine = AttendancePolicyEngine()
        result_a = engine.evaluate(session_a, policy_a)
        result_b = engine.evaluate(session_b, policy_b)
        
        assert result_a.is_late == True
        assert result_a.late_minutes == 10
        
        assert result_b.is_late == False
        assert result_b.late_minutes == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================
# WP-11-03S: Split Shift Tests
# ============================================

class TestSplitShiftBasics:
    """Test split shift basic functionality"""
    
    def test_split_shift_normal_attendance(self):
        """測試：分段工時正常出勤（08:00-14:00 + 16:00-18:00）"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Session: 08:00 - 18:00 (full day including break)
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 8, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=600  # Total 10 hours
        )
        
        # Split shift: 08:00-14:00 (6h) + 16:00-18:00 (2h) = 8h work
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Split Shift Policy",
            work_start_time=time(8, 0),  # Not used in split shift
            work_end_time=time(18, 0),   # Not used in split shift
            grace_period_minutes=15,
            overtime_threshold_minutes=480
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate_with_schedule(session, schedule, policy)
        
        # Should count 6h + 2h = 8h = 480 minutes (not 10h)
        assert result.work_minutes == 480
        assert result.is_late == False
        assert result.is_early_leave == False
        assert result.is_overtime == False
    
    def test_split_shift_late_first_window(self):
        """測試：第一段遲到"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Punch in at 08:20 (late by 20 min, grace is 15)
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 8, 20, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=580
        )
        
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Split Shift Policy",
            work_start_time=time(8, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=480
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate_with_schedule(session, schedule, policy)
        
        assert result.is_late == True
        assert result.late_minutes == 5  # 20 - 15 grace
        # Work time: (14:00-08:20)=340min + (18:00-16:00)=120min = 460min
        assert result.work_minutes == 460
    
    def test_split_shift_early_leave_last_window(self):
        """測試：最後一段早退"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Punch out at 17:30 (30 min early)
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 8, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 17, 30, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=570
        )
        
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Split Shift Policy",
            work_start_time=time(8, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=480
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate_with_schedule(session, schedule, policy)
        
        assert result.is_early_leave == True
        assert result.early_leave_minutes == 30
        # Work time: 6h + 1.5h = 450min
        assert result.work_minutes == 450
    
    def test_split_shift_punch_only_first_window(self):
        """測試：只在第一段工作"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Punch in 08:00, out 13:00 (only first window)
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 8, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 13, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=300
        )
        
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Split Shift Policy",
            work_start_time=time(8, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=480
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate_with_schedule(session, schedule, policy)
        
        # Only first window: 5 hours = 300 min
        assert result.work_minutes == 300
        assert result.is_early_leave == True  # Left before last window end
    
    def test_split_shift_punch_only_second_window(self):
        """測試：只在第二段工作"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Punch in 16:00, out 18:00 (only second window)
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 16, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=120
        )
        
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Split Shift Policy",
            work_start_time=time(8, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=480
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate_with_schedule(session, schedule, policy)
        
        # Only second window: 2 hours = 120 min
        assert result.work_minutes == 120
        assert result.is_late == True  # Started after first window start
    
    def test_split_shift_punch_during_break(self):
        """測試：打卡時間在間段（不計工時）"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Punch in 14:30, out 15:30 (during break 14:00-16:00)
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 14, 30, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 15, 30, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=60
        )
        
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Split Shift Policy",
            work_start_time=time(8, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=480
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate_with_schedule(session, schedule, policy)
        
        # No overlap with any window: 0 minutes
        assert result.work_minutes == 0
    
    def test_split_shift_cross_window_boundary(self):
        """測試：跨 window 邊界（只計重疊部分）"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Punch in 13:00, out 17:00 (crosses first window end and second window start)
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 13, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 17, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=240
        )
        
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Split Shift Policy",
            work_start_time=time(8, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=480
        )
        
        engine = AttendancePolicyEngine()
        result = engine.evaluate_with_schedule(session, schedule, policy)
        
        # First window: 13:00-14:00 = 60min
        # Break: 14:00-16:00 = not counted
        # Second window: 16:00-17:00 = 60min
        # Total: 120min
        assert result.work_minutes == 120


class TestSplitShiftEdgeCases:
    """Test split shift edge cases"""
    
    def test_work_window_validation_invalid_times(self):
        """測試：WorkWindow 驗證（start >= end 應拋錯）"""
        from app.modules.attendance.policy_engine import WorkWindow
        
        with pytest.raises(ValueError, match="Invalid WorkWindow"):
            WorkWindow(start_time=time(14, 0), end_time=time(8, 0))
    
    def test_work_schedule_overlapping_windows(self):
        """測試：WorkSchedule 驗證（重疊 windows 應拋錯）"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        with pytest.raises(ValueError, match="Overlapping windows"):
            WorkSchedule.create_split_shift([
                WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
                WorkWindow(start_time=time(13, 0), end_time=time(18, 0))  # Overlaps!
            ])
    
    def test_work_schedule_auto_sort_windows(self):
        """測試：WorkSchedule 自動排序 windows"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Provide windows in wrong order
        schedule = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0)),
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0))
        ])
        
        # Should be auto-sorted
        assert schedule.windows[0].start_time == time(8, 0)
        assert schedule.windows[1].start_time == time(16, 0)
    
    def test_split_shift_backward_compatibility(self):
        """測試：向後相容（WorkSchedule.from_policy）"""
        from app.modules.attendance.policy_engine import WorkSchedule
        
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="Standard Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=15,
            overtime_threshold_minutes=540
        )
        
        # Convert policy to schedule
        schedule = WorkSchedule.from_policy(policy)
        
        assert schedule.mode == 'standard'
        assert len(schedule.windows) == 1
        assert schedule.windows[0].start_time == time(9, 0)
        assert schedule.windows[0].end_time == time(18, 0)


class TestSplitShiftTenantIsolation:
    """Test tenant isolation with split shift"""
    
    def test_different_companies_different_split_schedules(self):
        """測試：不同公司使用不同分段工時"""
        from app.modules.attendance.policy_engine import WorkWindow, WorkSchedule
        
        # Company A: 08:00-14:00 + 16:00-18:00
        session_a = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 8, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 18, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=600
        )
        
        schedule_a = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(8, 0), end_time=time(14, 0)),
            WorkWindow(start_time=time(16, 0), end_time=time(18, 0))
        ])
        
        # Company B: 09:00-13:00 + 14:00-17:00
        session_b = AttendanceSession(
            id=uuid4(),
            company_id="company-b",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 9, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 17, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=480
        )
        
        schedule_b = WorkSchedule.create_split_shift([
            WorkWindow(start_time=time(9, 0), end_time=time(13, 0)),
            WorkWindow(start_time=time(14, 0), end_time=time(17, 0))
        ])
        
        engine = AttendancePolicyEngine()
        result_a = engine.evaluate_with_schedule(session_a, schedule_a, None)
        result_b = engine.evaluate_with_schedule(session_b, schedule_b, None)
        
        # Company A: 6h + 2h = 480min
        assert result_a.work_minutes == 480
        assert result_a.company_id == "company-a"
        
        # Company B: 4h + 3h = 420min
        assert result_b.work_minutes == 420
        assert result_b.company_id == "company-b"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
