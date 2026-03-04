"""Customer Service data models

WP-11-04A: Support Company Assignments
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class SupportCompanyAssignment(Base):
    """Support Company Assignment model
    
    Design principles (WP-11-04A):
    - Links customer_service users to companies they can support
    - PRIMARY KEY (user_id, company_id)
    - Managed by super_admin only
    """
    
    __tablename__ = "support_company_assignments"
    
    # Composite primary key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
        comment="Customer service user ID (FK)"
    )
    company_id = Column(
        String(50),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        primary_key=True,
        comment="Company ID (FK)"
    )
    
    # Audit trail
    assigned_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Assignment timestamp (UTC)"
    )
    assigned_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="Assigned by user ID (FK, usually super_admin)"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_support_company_assignments_user_id', 'user_id'),
        Index('idx_support_company_assignments_company_id', 'company_id'),
    )
    
    def __repr__(self):
        return f"<SupportCompanyAssignment(user_id={self.user_id}, company_id={self.company_id})>"
