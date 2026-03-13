"""Attendance 資料模型

WP-11-05A: Synced with migration 001b_create_attendance_domain_v2_fixed.py
WP-11-05B: Updated status comment to include new approval workflow states

Phase 4: 定義 AttendanceRecord SQLAlchemy model (DEPRECATED)
WP-11-01: 定義 AttendancePolicy, AttendanceSession, AttendancePunch models
"""

from datetime import datetime
from app.core.config import get_utc_now
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, Time, Index, CheckConstraint, ForeignKeyConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import text

from app.core.database import Base


# ============================================
# WP-11-01: New Models (Synced with migration 001b)
# ============================================

class AttendancePolicy(Base):
    """考勤政策模型
    
    WP-11-05A: Synced with migration 001b
    
    設計原則：
    1. 主鍵使用 UUID
    2. 必須包含 company_id (Tenant Isolation)
    3. 支援 is_default (每公司只能有一個預設政策)
    """
    
    __tablename__ = "attendance_policies"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), comment='Policy ID (PK)')
    
    # Tenant Isolation
    company_id = Column(String(255), nullable=False, comment='公司 ID')
    
    # Policy fields
    name = Column(String(255), nullable=False, comment='政策名稱')
    description = Column(Text, nullable=True, comment='政策說明')
    work_start_time = Column(Time, nullable=False, comment='標準上班時間')
    work_end_time = Column(Time, nullable=False, comment='標準下班時間')
    grace_period_minutes = Column(Integer, nullable=False, server_default='0', comment='遲到寬限時間 (分鐘)')
    overtime_threshold_minutes = Column(Integer, nullable=True, comment='加班認定門檻 (分鐘)')
    is_active = Column(Boolean, nullable=False, server_default='true', comment='是否啟用')
    is_default = Column(Boolean, nullable=False, server_default='false', comment='是否為預設政策')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='建立時間 (UTC)')
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='更新時間 (UTC)')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_policies_company_id', 'company_id'),
        Index('idx_policies_company_active', 'company_id', 'is_active'),
        Index('idx_policies_company_default', 'company_id', 'is_default', postgresql_where=text("is_default = true")),
        Index('uq_policies_company_default', 'company_id', unique=True, postgresql_where=text("is_default = true")),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    def __repr__(self):
        return f"<AttendancePolicy(id={self.id}, company_id={self.company_id}, name={self.name})>"


class AttendanceSession(Base):
    """出勤 Session 模型
    
    WP-11-05A: Synced with migration 001b
    WP-11-05B: Updated status comment to include approval workflow states
    
    設計原則：
    1. 主鍵使用 UUID
    2. 必須包含 company_id (Tenant Isolation)
    3. Business invariant: 一個 user 只能有一個 open session (unique constraint)
    4. Cross-midnight: work_date = punch_in_time.date()
    """
    
    __tablename__ = "attendance_sessions"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), comment='Session ID (PK)')
    
    # Tenant Isolation
    company_id = Column(String(255), nullable=False, comment='公司 ID (tenant isolation)')
    user_id = Column(PGUUID(as_uuid=True), nullable=False, comment='員工 ID (global user)')
    
    # Session fields
    punch_in_time = Column(DateTime(timezone=True), nullable=False, comment='打卡上班時間 (UTC+8)')
    punch_out_time = Column(DateTime(timezone=True), nullable=True, comment='打卡下班時間 (UTC+8, NULL = open session)')
    status = Column(String(20), nullable=False, server_default='open', comment='Session 狀態 (open/closed)。擴充狀態須先執行 migration 更新 CHECK constraint ck_sessions_status')
    duration_minutes = Column(Integer, nullable=True, comment='工作時長 (分鐘, computed on close)')
    policy_id = Column(PGUUID(as_uuid=True), nullable=True, comment='適用的考勤政策')
    notes = Column(Text, nullable=True, comment='備註')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='建立時間 (UTC)')
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='更新時間 (UTC)')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_sessions_company_id', 'company_id'),
        Index('idx_sessions_user_id', 'user_id'),
        Index('idx_sessions_company_user', 'company_id', 'user_id'),
        Index('idx_sessions_company_punch_in', 'company_id', 'punch_in_time'),
        Index('idx_sessions_status_open', 'status', postgresql_where=text("status = 'open'")),
        Index('uq_sessions_company_user_open', 'company_id', 'user_id', unique=True, postgresql_where=text("status = 'open'")),
        CheckConstraint("status IN ('open', 'closed')", name='ck_sessions_status'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['policy_id'], ['attendance_policies.id'], ondelete='SET NULL'),
    )
    
    def __repr__(self):
        return f"<AttendanceSession(id={self.id}, company_id={self.company_id}, user_id={self.user_id}, status={self.status})>"


class AttendancePunch(Base):
    """打卡事件模型
    
    WP-11-05A: Synced with migration 001b
    
    設計原則：
    1. 主鍵使用 UUID
    2. 必須包含 company_id (denormalized for isolation)
    3. 記錄每次打卡的詳細資訊 (IP, GPS, device)
    """
    
    __tablename__ = "attendance_punches"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), comment='Punch ID (PK)')
    
    # Foreign keys
    session_id = Column(PGUUID(as_uuid=True), nullable=False, comment='所屬 session')
    company_id = Column(String(255), nullable=False, comment='公司 ID (denormalized for isolation)')
    user_id = Column(PGUUID(as_uuid=True), nullable=False, comment='員工 ID (denormalized for queries)')
    
    # Punch fields
    punch_type = Column(String(20), nullable=False, comment='打卡類型 (in/out/break_start/break_end)')
    punch_time = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='打卡時間 (UTC)')
    
    # Context fields
    ip_address = Column(String(45), nullable=True, comment='IP 地址 (IPv4/IPv6)')
    user_agent = Column(Text, nullable=True, comment='User Agent (device info)')
    location_lat = Column(Numeric(10, 8), nullable=True, comment='緯度')
    location_lng = Column(Numeric(11, 8), nullable=True, comment='經度')
    device_id = Column(String(255), nullable=True, comment='裝置 ID (mobile app)')
    photo_url = Column(Text, nullable=True, comment='打卡照片 URL')
    notes = Column(Text, nullable=True, comment='備註')
    
    # WP-11-13: Location Policy
    location_id = Column(PGUUID(as_uuid=True), nullable=True, comment='WP-11-13: 匹配的允許地點 ID')
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='建立時間 (UTC)')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_punches_session_id', 'session_id'),
        Index('idx_punches_company_id', 'company_id'),
        Index('idx_punches_user_id', 'user_id'),
        Index('idx_punches_company_time', 'company_id', 'punch_time'),
        Index('idx_punches_type', 'punch_type'),
        CheckConstraint("punch_type IN ('in', 'out', 'break_start', 'break_end')", name='ck_punches_type'),
        ForeignKeyConstraint(['session_id'], ['attendance_sessions.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['location_id'], ['allowed_locations.id'], ondelete='SET NULL'),  # WP-11-13
    )
    
    def __repr__(self):
        return f"<AttendancePunch(id={self.id}, session_id={self.session_id}, punch_type={self.punch_type})>"



class AttendanceOutCheckpoint(Base):
    """外出打卡點模型 (WP-11-10)
    
    設計原則：
    1. OUT checkpoint = standalone event (no RETURN/BREAK_IN)
    2. Multiple OUT checkpoints allowed per session
    3. Mobile device MUST provide GPS
    4. PC device MAY provide GPS (optional)
    5. device_type MUST be recorded (mobile|pc)
    
    Reporting Semantics:
    - OUT checkpoints are displayed as event list
    - NOT calculated as time intervals
    - NOT subtracted from work duration
    """
    
    __tablename__ = "attendance_out_checkpoints"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), comment='Checkpoint ID (PK)')
    
    # Tenant Isolation (MANDATORY per SA v1.9)
    company_id = Column(String(255), nullable=False, comment='公司 ID (tenant isolation)')
    
    # User & Session
    user_id = Column(PGUUID(as_uuid=True), nullable=False, comment='員工 ID (global user)')
    session_id = Column(PGUUID(as_uuid=True), nullable=True, comment='所屬 session (nullable: allow checkpoints without open session)')
    
    # Timestamp (server-set, NOT from client)
    punch_time = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='打卡時間 (UTC, server-set)')
    
    # Device Info (MANDATORY)
    device_type = Column(String(20), nullable=False, comment='裝置類型 (mobile|pc)')
    
    # GPS Data (MANDATORY for mobile, OPTIONAL for pc)
    gps_lat = Column(Numeric(10, 8), nullable=True, comment='緯度 (required for mobile)')
    gps_lng = Column(Numeric(11, 8), nullable=True, comment='經度 (required for mobile)')
    gps_accuracy_m = Column(Numeric(8, 2), nullable=True, comment='GPS 精度 (公尺)')
    gps_captured_at = Column(DateTime(timezone=True), nullable=True, comment='GPS 擷取時間 (client-side timestamp)')
    gps_provider = Column(String(20), nullable=True, comment='GPS 提供者 (gps|network|fused)')
    
    # Client Context (optional, for debugging)
    client_timezone = Column(String(50), nullable=True, comment='客戶端時區')
    client_user_agent = Column(Text, nullable=True, comment='User Agent')
    ip_address = Column(String(45), nullable=True, comment='IP 地址 (IPv4/IPv6)')
    
    # Notes
    notes = Column(Text, nullable=True, comment='備註')
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'), comment='建立時間 (UTC)')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_checkpoints_company_id', 'company_id'),
        Index('idx_checkpoints_user_id', 'user_id'),
        Index('idx_checkpoints_company_user_time', 'company_id', 'user_id', 'punch_time', postgresql_ops={'punch_time': 'DESC'}),
        Index('idx_checkpoints_session_id', 'session_id', postgresql_where=text('session_id IS NOT NULL')),
        Index('idx_checkpoints_gps', 'gps_lat', 'gps_lng', postgresql_where=text('gps_lat IS NOT NULL')),
        CheckConstraint("device_type IN ('mobile', 'pc')", name='ck_checkpoints_device_type'),
        CheckConstraint("gps_provider IN ('gps', 'network', 'fused') OR gps_provider IS NULL", name='ck_checkpoints_gps_provider'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['session_id'], ['attendance_sessions.id'], ondelete='SET NULL'),
    )
    
    def __repr__(self):
        return f"<AttendanceOutCheckpoint(id={self.id}, company_id={self.company_id}, user_id={self.user_id}, device_type={self.device_type})>"


# ============================================
# Phase 4: Old Model (DEPRECATED)
# ============================================

class AttendanceRecord(Base):
    """考勤記錄模型 (DEPRECATED)
    
    ⚠️ DEPRECATED: This is the old model from Phase 4.
    New code should use AttendanceSession instead.
    Kept for backward compatibility only.
    
    設計原則（SA_MODULE_SPEC v1.7 第 18 條）：
    1. 主鍵使用 UUID（避免單一租戶還原時 ID 衝突）
    2. 必須包含 company_id（Tenant Isolation P0）
    3. 為 company_id 建立索引（支援高效匯出與查詢）
    """
    
    __tablename__ = "attendance_records"
    
    # 主鍵（UUID）
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, comment="考勤記錄 ID（UUID）")
    
    # Tenant Isolation 必要欄位
    company_id = Column(String(255), nullable=False, index=True, comment="公司 ID（Tenant Isolation）")
    
    # 業務欄位
    employee_id = Column(String(255), nullable=False, comment="員工 ID")
    approved_by = Column(String(255), nullable=True, comment="核准人 ID")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="核准時間（UTC）")
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_utc_now, comment="建立時間（UTC）")
    
    # 索引（支援單一租戶全量抽取與高效查詢）
    __table_args__ = (
        Index('idx_attendance_company_id', 'company_id'),
        Index('idx_attendance_company_created', 'company_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AttendanceRecord(id={self.id}, company_id={self.company_id}, employee_id={self.employee_id})>"


# ============================================
# WP-11-13: Location Policy Models
# ============================================

class AllowedLocation(Base):
    """允許打卡地點模型 (WP-11-13)
    
    設計原則：
    1. 支援多筆地點（不要做死成只能一筆）
    2. Tenant isolation (company_id)
    3. 支援啟用/停用
    4. 預留擴充欄位
    """
    
    __tablename__ = "allowed_locations"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, 
                server_default=text('gen_random_uuid()'),
                comment='Location ID (PK)')
    
    # Tenant Isolation
    company_id = Column(String(255), nullable=False, 
                       comment='公司 ID (Tenant Isolation)')
    
    # 基本資訊
    name = Column(String(255), nullable=False, 
                 comment='地點名稱，例如：台北101工地')
    description = Column(Text, nullable=True, 
                        comment='地點描述')
    
    # 地點類型（預留擴充）
    location_type = Column(String(50), nullable=False, 
                          server_default='office',
                          comment='地點類型: office, construction_site, customer_site, temporary_site')
    
    # 位置資訊
    latitude = Column(Numeric(10, 7), nullable=False, 
                     comment='緯度 (Decimal for precision)')
    longitude = Column(Numeric(10, 7), nullable=False, 
                      comment='經度 (Decimal for precision)')
    radius_meters = Column(Integer, nullable=False, 
                          comment='允許半徑（公尺）')
    
    # 狀態
    is_active = Column(Boolean, nullable=False, 
                      server_default='true',
                      comment='是否啟用')
    
    # 審計欄位
    created_at = Column(DateTime(timezone=True), nullable=False, 
                       server_default=text('CURRENT_TIMESTAMP'),
                       comment='建立時間')
    updated_at = Column(DateTime(timezone=True), nullable=False, 
                       server_default=text('CURRENT_TIMESTAMP'),
                       comment='更新時間')
    created_by = Column(String(255), nullable=True, 
                       comment='建立者 user_id')
    updated_by = Column(String(255), nullable=True, 
                       comment='更新者 user_id')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_allowed_locations_company', 'company_id'),
        Index('idx_allowed_locations_active', 'company_id', 'is_active'),
        CheckConstraint('radius_meters > 0', name='chk_allowed_locations_radius_positive'),
        CheckConstraint('latitude >= -90 AND latitude <= 90', name='chk_allowed_locations_latitude_range'),
        CheckConstraint('longitude >= -180 AND longitude <= 180', name='chk_allowed_locations_longitude_range'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    def __repr__(self):
        return f"<AllowedLocation(id={self.id}, company_id={self.company_id}, name={self.name})>"
