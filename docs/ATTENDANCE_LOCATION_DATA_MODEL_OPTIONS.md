# Attendance Location Data Model Options

**文件版本**: 1.0  
**建立日期**: 2026-03-08  
**狀態**: ✅ DRAFT  
**目的**: 比較定位政策資料模型的放置方案

---

## Executive Summary

需要在資料庫中儲存「定位政策」，包含：
- 是否需要定位
- 目標點座標
- 允許半徑
- 精度要求

**比較 3 種方案**:
1. 公司層級設定（`companies` 表擴充）
2. 打卡設定層級（`attendance_settings` 表擴充）
3. 獨立政策表（新增 `attendance_location_policies` 表）

**建議**: 方案 3（獨立政策表）- 最靈活，易擴充

---

## 方案 1: 公司層級設定

### 1.1 Schema

```sql
ALTER TABLE companies ADD COLUMN location_enforcement_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE companies ADD COLUMN default_target_latitude NUMERIC(10,8);
ALTER TABLE companies ADD COLUMN default_target_longitude NUMERIC(11,8);
ALTER TABLE companies ADD COLUMN default_allowed_radius_meters NUMERIC(8,2);
ALTER TABLE companies ADD COLUMN default_min_accuracy_meters NUMERIC(8,2);
ALTER TABLE companies ADD COLUMN location_label VARCHAR(255);
```

### 1.2 優點

- ✅ 簡單直接
- ✅ 不需要新表
- ✅ 適合「全公司統一政策」

### 1.3 缺點

- ❌ 無法區分「上班打卡」與「外出打卡」政策
- ❌ 無法支援多打卡點（總公司、分公司）
- ❌ 擴充性差

### 1.4 適用情境

- 小型公司（單一辦公室）
- 全公司統一政策
- 不需要區分打卡類型

---

## 方案 2: 打卡設定層級

### 2.1 Schema

假設已有 `attendance_settings` 表：

```sql
ALTER TABLE attendance_settings ADD COLUMN punch_in_location_required BOOLEAN DEFAULT FALSE;
ALTER TABLE attendance_settings ADD COLUMN punch_in_target_lat NUMERIC(10,8);
ALTER TABLE attendance_settings ADD COLUMN punch_in_target_lng NUMERIC(11,8);
ALTER TABLE attendance_settings ADD COLUMN punch_in_allowed_radius_m NUMERIC(8,2);

ALTER TABLE attendance_settings ADD COLUMN punch_out_location_required BOOLEAN DEFAULT FALSE;
ALTER TABLE attendance_settings ADD COLUMN punch_out_target_lat NUMERIC(10,8);
ALTER TABLE attendance_settings ADD COLUMN punch_out_target_lng NUMERIC(11,8);
ALTER TABLE attendance_settings ADD COLUMN punch_out_allowed_radius_m NUMERIC(8,2);

-- 外出打卡不限制（已有 out_checkpoints 表）
```

### 2.2 優點

- ✅ 可區分上班/下班打卡政策
- ✅ 與現有 attendance_settings 整合
- ✅ 中等複雜度

### 2.3 缺點

- ❌ 無法支援多打卡點
- ❌ 欄位過多（每種打卡類型 4-5 個欄位）
- ❌ 擴充困難（新增打卡類型需改 schema）

### 2.4 適用情境

- 中型公司
- 需要區分上下班政策
- 單一辦公室

---

## 方案 3: 獨立政策表（推薦）

### 3.1 Schema

```sql
CREATE TABLE attendance_location_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Tenant Isolation
    company_id VARCHAR(255) NOT NULL,
    
    -- 政策適用範圍
    punch_type VARCHAR(20) NOT NULL,  -- 'IN' | 'OUT' | 'BREAK_OUT' | 'BREAK_IN' | '*'
    work_site_id UUID,                -- 工作地點 ID（NULL = 全公司預設）
    
    -- 定位要求
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 目標點座標
    target_latitude NUMERIC(10,8),
    target_longitude NUMERIC(11,8),
    location_label VARCHAR(255),      -- 地點名稱（例如：總公司、台北分公司）
    
    -- 範圍限制
    allowed_radius_meters NUMERIC(8,2),
    min_accuracy_meters NUMERIC(8,2),
    
    -- 時間限制（可選）
    effective_from DATE,
    effective_until DATE,
    
    -- 優先順序（數字越小優先級越高）
    priority INTEGER DEFAULT 100,
    
    -- 啟用狀態
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- 審計欄位
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    
    -- 約束
    CONSTRAINT ck_punch_type CHECK (punch_type IN ('IN', 'OUT', 'BREAK_OUT', 'BREAK_IN', '*')),
    CONSTRAINT ck_radius CHECK (allowed_radius_meters IS NULL OR allowed_radius_meters > 0),
    CONSTRAINT ck_accuracy CHECK (min_accuracy_meters IS NULL OR min_accuracy_meters > 0),
    
    -- 外鍵
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_location_policies_company ON attendance_location_policies(company_id);
CREATE INDEX idx_location_policies_punch_type ON attendance_location_policies(punch_type);
CREATE INDEX idx_location_policies_active ON attendance_location_policies(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_location_policies_lookup ON attendance_location_policies(company_id, punch_type, is_active);
```

### 3.2 優點

- ✅ 最靈活（支援多打卡點、多政策）
- ✅ 易擴充（新增打卡類型不需改 schema）
- ✅ 支援優先順序（例如：特定地點 > 全公司預設）
- ✅ 支援時間範圍（例如：疫情期間放寬限制）
- ✅ 符合 SA v1.9 規範（獨立模組）

### 3.3 缺點

- ❌ 需要新表（migration）
- ❌ 查詢稍複雜（需要 JOIN 或多次查詢）

### 3.4 適用情境

- 大型公司（多辦公室）
- 需要靈活政策
- 未來可能擴充功能

---

## 方案比較表

| 特性 | 方案 1（公司層級） | 方案 2（設定層級） | 方案 3（獨立表）|
|------|-------------------|-------------------|----------------|
| 實作複雜度 | 🟢 低 | 🟡 中 | 🟡 中 |
| 查詢效能 | 🟢 高 | 🟢 高 | 🟡 中 |
| 靈活性 | 🔴 低 | 🟡 中 | 🟢 高 |
| 擴充性 | 🔴 低 | 🟡 中 | 🟢 高 |
| 多打卡點支援 | ❌ | ❌ | ✅ |
| 區分打卡類型 | ❌ | ✅ | ✅ |
| 時間範圍支援 | ❌ | ❌ | ✅ |
| 優先順序支援 | ❌ | ❌ | ✅ |
| Migration 需求 | ALTER | ALTER | CREATE |

---

## 建議方案: 方案 3（獨立政策表）

### 理由

1. **符合未來需求** - 支援多辦公室、多政策
2. **易於擴充** - 新增打卡類型不需改 schema
3. **符合 SA v1.9** - 獨立模組設計
4. **向後相容** - 不影響現有表結構

### 實作階段

**Phase 1（本輪不做）**: 設計 schema，不實作

**Phase 2（未來）**: 實作 migration + service layer

**Phase 3（未來）**: 實作管理後台 UI

---

## 查詢範例

### 取得打卡政策

```python
def get_location_policy(
    db: Session,
    company_id: str,
    punch_type: str,
    work_site_id: Optional[UUID] = None
) -> Optional[LocationPolicy]:
    """取得定位政策（優先順序：特定地點 > 全公司預設）"""
    
    query = (
        db.query(AttendanceLocationPolicy)
        .filter(
            AttendanceLocationPolicy.company_id == company_id,
            AttendanceLocationPolicy.is_active == True,
            or_(
                AttendanceLocationPolicy.punch_type == punch_type,
                AttendanceLocationPolicy.punch_type == '*'
            )
        )
    )
    
    # 若有指定工作地點，優先查詢
    if work_site_id:
        query = query.filter(
            or_(
                AttendanceLocationPolicy.work_site_id == work_site_id,
                AttendanceLocationPolicy.work_site_id == None
            )
        )
    else:
        query = query.filter(AttendanceLocationPolicy.work_site_id == None)
    
    # 按優先順序排序
    policy = query.order_by(AttendanceLocationPolicy.priority.asc()).first()
    
    return policy
```

---

## Migration 範例

```python
"""add attendance location policies table

Revision ID: 00X_location_policies
Revises: 007_wp_11_10
Create Date: 2026-03-XX
"""

def upgrade():
    op.create_table(
        'attendance_location_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('company_id', sa.String(255), nullable=False),
        sa.Column('punch_type', sa.String(20), nullable=False),
        sa.Column('work_site_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('target_latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('target_longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('location_label', sa.String(255), nullable=True),
        sa.Column('allowed_radius_meters', sa.Numeric(8, 2), nullable=True),
        sa.Column('min_accuracy_meters', sa.Numeric(8, 2), nullable=True),
        sa.Column('effective_from', sa.Date(), nullable=True),
        sa.Column('effective_until', sa.Date(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("punch_type IN ('IN', 'OUT', 'BREAK_OUT', 'BREAK_IN', '*')", name='ck_punch_type'),
        sa.CheckConstraint('allowed_radius_meters IS NULL OR allowed_radius_meters > 0', name='ck_radius'),
        sa.CheckConstraint('min_accuracy_meters IS NULL OR min_accuracy_meters > 0', name='ck_accuracy')
    )
    
    op.create_index('idx_location_policies_company', 'attendance_location_policies', ['company_id'])
    op.create_index('idx_location_policies_punch_type', 'attendance_location_policies', ['punch_type'])
    op.create_index('idx_location_policies_lookup', 'attendance_location_policies', ['company_id', 'punch_type', 'is_active'])

def downgrade():
    op.drop_table('attendance_location_policies')
```

---

## Definition of Done

- [ ] Schema 設計完成
- [ ] Migration 腳本準備好（未執行）
- [ ] Service layer 設計完成
- [ ] 查詢邏輯設計完成
- [ ] 團隊 review 通過

---

**文件狀態**: ✅ DRAFT  
**建議方案**: 方案 3（獨立政策表）  
**實作時機**: Phase 2（未來）

---

**END OF OPTIONS**
