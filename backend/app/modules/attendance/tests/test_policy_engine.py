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
from types import SimpleNamespace
from uuid import uuid4

from app.modules.attendance.models import AttendanceSession, AttendancePolicy
from app.modules.attendance.policy_engine import AttendancePolicyEngine, PolicyEvaluationResult
from app.modules.attendance.punch_close_domain import build_policy_evaluation_with_schedule_v2


class TestPolicyEngineBasics:
    """Test basic policy engine functionality"""
    
    def test_evaluate_normal_attendance(self):
        """測試：正常出勤（不遲到、不早退、不加班）"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 10, 0, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 1, 20, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 10, 0, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 1, 10, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 10, 0, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 9, 30, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 11, 0, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 2, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 11, 0, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 1, 30, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 10, 30, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 10, 0, 0, tzinfo=timezone.utc),
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
            punch_in_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            punch_out_time=None,
            status='open',
            duration_minutes=None
        )
        
        engine = AttendancePolicyEngine()
        
        with pytest.raises(ValueError) as exc:
            engine.evaluate(session, policy=None)
        
        assert "Cannot evaluate open session" in str(exc.value)
    
    def test_evaluate_zero_duration_session(self):
        """測試：零時長 session"""
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            status='closed',
            duration_minutes=0
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
        
        assert result.work_minutes == 0
        assert result.is_late == False
        assert result.is_early_leave == True
        assert result.early_leave_minutes == 540
        assert result.is_overtime == False


class TestPolicyEngineResult:
    """Test PolicyEvaluationResult class"""
    
    def test_to_dict(self):
        """測試：PolicyEvaluationResult.to_dict()"""
        result = PolicyEvaluationResult(
            session_id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            policy_id=uuid4(),
            policy_name="Standard Policy",
            punch_in_time=datetime(2026, 3, 4, 1, 0, 0, tzinfo=timezone.utc),
            punch_out_time=datetime(2026, 3, 4, 10, 0, 0, tzinfo=timezone.utc),
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            is_late=False,
            late_minutes=0,
            is_early_leave=False,
            early_leave_minutes=0,
            is_overtime=False,
            overtime_minutes=0,
            work_minutes=540,
            grace_period_minutes=15,
            overtime_threshold_minutes=540,
        )
        
        data = result.to_dict()
        
        assert data['company_id'] == "company-a"
        assert data['policy']['policy_name'] == "Standard Policy"
        assert data['evaluation']['is_late'] == False
        assert data['evaluation']['late_minutes'] == 0
        assert data['evaluation']['is_early_leave'] == False
        assert data['evaluation']['is_overtime'] == False
        assert data['timing']['work_minutes'] == 540


class TestPolicyEvaluationWithScheduleV2:
    def test_build_policy_evaluation_uses_schedule_window(self):
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 1, 20, tzinfo=timezone.utc),
            punch_out_time=None,
            status='open',
            duration_minutes=None,
        )
        policy = AttendancePolicy(
            id=uuid4(),
            company_id="company-a",
            name="policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=10,
            overtime_threshold_minutes=480,
        )
        repo = SimpleNamespace(get_user_policy=lambda company_id, user_id: policy)

        result = build_policy_evaluation_with_schedule_v2(
            session=session,
            repo=repo,
            company_id="company-a",
            user_id=session.user_id,
            punch_out_time=datetime(2026, 3, 4, 10, 10, tzinfo=timezone.utc),
            gross_minutes=530,
            work_minutes=530,
            normalized_windows=[
                (datetime(2026, 3, 4, 1, 0, tzinfo=timezone.utc), datetime(2026, 3, 4, 10, 0, tzinfo=timezone.utc))
            ],
        )

        evaluation = result.evaluation
        assert evaluation.is_late is True
        assert evaluation.late_minutes == 10
        assert evaluation.is_early_leave is False
        assert evaluation.early_leave_minutes == 0
        assert evaluation.is_overtime is True
        assert evaluation.overtime_minutes == 50
        assert evaluation.work_minutes == 530
        assert result.policy_id == policy.id

    def test_build_policy_evaluation_without_windows_requires_windows(self):
        session = AttendanceSession(
            id=uuid4(),
            company_id="company-a",
            user_id=uuid4(),
            punch_in_time=datetime(2026, 3, 4, 1, 0, tzinfo=timezone.utc),
            punch_out_time=None,
            status='open',
            duration_minutes=None,
        )
        repo = SimpleNamespace(get_user_policy=lambda company_id, user_id: None)

        with pytest.raises(ValueError) as exc:
            build_policy_evaluation_with_schedule_v2(
                session=session,
                repo=repo,
                company_id="company-a",
                user_id=session.user_id,
                punch_out_time=datetime(2026, 3, 4, 9, 0, tzinfo=timezone.utc),
                gross_minutes=480,
                work_minutes=480,
                normalized_windows=[],
            )

        assert "normalized_windows must not be empty" in str(exc.value)
