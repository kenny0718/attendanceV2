"""Tenants data model

WP-11-04A: Added CompanyEntitlement for feature flags
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Tenant(Base):
    """Tenant (Company) model
    
    Design principles:
    - id is the company_id (VARCHAR 50) as PK
    - name is the company display name
    - is_active flag for soft delete / deactivation
    - timezone for company-specific time handling
    - created_at / updated_at for audit trail
    """
    
    __tablename__ = "tenants"
    
    # Primary key (company_id)
    id = Column(String(50), primary_key=True, comment="Company ID (tenant identifier)")
    
    # Company information
    name = Column(String(255), nullable=False, comment="Company name")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    timezone = Column(String(50), nullable=False, default="UTC", comment="Company timezone")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Created timestamp (UTC)")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Updated timestamp (UTC)")
    
    # Index for fast active tenant queries
    __table_args__ = (
        Index('idx_tenants_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, is_active={self.is_active})>"


class CompanyEntitlement(Base):
    """Company Entitlement (Feature Flag) model
    
    Design principles (WP-11-04A):
    - Company-level feature flags
    - feature_key: fixed string identifier (e.g., "attendance.shift_templates")
    - enabled: boolean flag
    - UNIQUE(company_id, feature_key)
    - updated_by_user_id: audit trail (who changed it)
    """
    
    __tablename__ = "company_entitlements"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, comment="Entitlement ID (PK)")
    
    # Relationships
    company_id = Column(
        String(50),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=False,
        comment="Company ID (FK)"
    )
    
    # Feature flag
    feature_key = Column(String(100), nullable=False, comment="Feature key (e.g., attendance.shift_templates)")
    enabled = Column(Boolean, nullable=False, default=False, comment="Is feature enabled")
    
    # Audit trail
    updated_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="Last updated by user ID (FK)"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last updated timestamp (UTC)"
    )
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('company_id', 'feature_key', name='uq_company_entitlements_company_feature'),
        Index('idx_company_entitlements_company_id', 'company_id'),
        Index('idx_company_entitlements_feature_key', 'feature_key'),
    )
    
    def __repr__(self):
        return f"<CompanyEntitlement(company_id={self.company_id}, feature_key={self.feature_key}, enabled={self.enabled})>"
