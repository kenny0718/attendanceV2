"""Tenants data model"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index

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
