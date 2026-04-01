#!/usr/bin/env python3
"""
S1-09B patch: add template_id + status optional filters to ShiftAssignmentRepo list methods.
"""

path = 'app/modules/schedule/repo.py'
with open(path, 'r') as f:
    content = f.read()

assert len(content) > 100, f'File too short: {len(content)} bytes'
print(f'Original lines: {content.count(chr(10))}')

# -----------------------------------------------------------------------
# 1. list_by_user_date_range
# -----------------------------------------------------------------------
OLD1 = (
    "    def list_by_user_date_range(\n"
    "        self,\n"
    "        company_id: str,\n"
    "        user_id: UUID,\n"
    "        start_date: date,\n"
    "        end_date: date,\n"
    "    ) -> List[ShiftAssignment]:\n"
    '        """List all ShiftAssignments for a user within a date range.\n'
    "\n"
    "        Tenant Isolation: enforces company_id in WHERE clause.\n"
    '        """\n'
    "        return (\n"
    "            self.db.query(ShiftAssignment)\n"
    "            .filter(\n"
    "                and_(\n"
    "                    ShiftAssignment.company_id == company_id,\n"
    "                    ShiftAssignment.user_id == user_id,\n"
    "                    ShiftAssignment.work_date >= start_date,\n"
    "                    ShiftAssignment.work_date <= end_date,\n"
    "                )\n"
    "            )\n"
    "            .order_by(ShiftAssignment.work_date.asc())\n"
    "            .all()\n"
    "        )"
)

NEW1 = (
    "    def list_by_user_date_range(\n"
    "        self,\n"
    "        company_id: str,\n"
    "        user_id: UUID,\n"
    "        start_date: date,\n"
    "        end_date: date,\n"
    "        template_id: Optional[UUID] = None,\n"
    "        status: Optional[str] = None,\n"
    "    ) -> List[ShiftAssignment]:\n"
    '        """List all ShiftAssignments for a user within a date range.\n'
    "\n"
    "        Tenant Isolation: enforces company_id in WHERE clause.\n"
    "        Optional filters: template_id, status (S1-09B).\n"
    '        """\n'
    "        q = (\n"
    "            self.db.query(ShiftAssignment)\n"
    "            .filter(\n"
    "                and_(\n"
    "                    ShiftAssignment.company_id == company_id,\n"
    "                    ShiftAssignment.user_id == user_id,\n"
    "                    ShiftAssignment.work_date >= start_date,\n"
    "                    ShiftAssignment.work_date <= end_date,\n"
    "                )\n"
    "            )\n"
    "        )\n"
    "        if template_id is not None:\n"
    "            q = q.filter(ShiftAssignment.shift_template_id == template_id)\n"
    "        if status is not None:\n"
    "            q = q.filter(ShiftAssignment.status == status)\n"
    "        return q.order_by(ShiftAssignment.work_date.asc()).all()"
)

assert OLD1 in content, 'ERROR: OLD1 not found'
content = content.replace(OLD1, NEW1, 1)
print('Patch 1 (list_by_user_date_range): OK')

# -----------------------------------------------------------------------
# 2. list_by_company_date
# -----------------------------------------------------------------------
OLD2 = (
    "    def list_by_company_date(\n"
    "        self,\n"
    "        company_id: str,\n"
    "        work_date: date,\n"
    "    ) -> List[ShiftAssignment]:\n"
    '        """List all ShiftAssignments for a company on a specific date.\n'
    "\n"
    "        Tenant Isolation: enforces company_id in WHERE clause.\n"
    '        """\n'
    "        return (\n"
    "            self.db.query(ShiftAssignment)\n"
    "            .filter(\n"
    "                and_(\n"
    "                    ShiftAssignment.company_id == company_id,\n"
    "                    ShiftAssignment.work_date == work_date,\n"
    "                )\n"
    "            )\n"
    "            .order_by(ShiftAssignment.user_id.asc())\n"
    "            .all()\n"
    "        )"
)

NEW2 = (
    "    def list_by_company_date(\n"
    "        self,\n"
    "        company_id: str,\n"
    "        work_date: date,\n"
    "        template_id: Optional[UUID] = None,\n"
    "        status: Optional[str] = None,\n"
    "    ) -> List[ShiftAssignment]:\n"
    '        """List all ShiftAssignments for a company on a specific date.\n'
    "\n"
    "        Tenant Isolation: enforces company_id in WHERE clause.\n"
    "        Optional filters: template_id, status (S1-09B).\n"
    '        """\n'
    "        q = (\n"
    "            self.db.query(ShiftAssignment)\n"
    "            .filter(\n"
    "                and_(\n"
    "                    ShiftAssignment.company_id == company_id,\n"
    "                    ShiftAssignment.work_date == work_date,\n"
    "                )\n"
    "            )\n"
    "        )\n"
    "        if template_id is not None:\n"
    "            q = q.filter(ShiftAssignment.shift_template_id == template_id)\n"
    "        if status is not None:\n"
    "            q = q.filter(ShiftAssignment.status == status)\n"
    "        return q.order_by(ShiftAssignment.user_id.asc()).all()"
)

assert OLD2 in content, 'ERROR: OLD2 not found'
content = content.replace(OLD2, NEW2, 1)
print('Patch 2 (list_by_company_date): OK')

# -----------------------------------------------------------------------
# 3. list_by_company (ShiftAssignment version)
# -----------------------------------------------------------------------
OLD3 = (
    "    def list_by_company(\n"
    "        self,\n"
    "        company_id: str,\n"
    "        start_date: Optional[date] = None,\n"
    "        end_date: Optional[date] = None,\n"
    "    ) -> List[ShiftAssignment]:\n"
    '        """List all ShiftAssignments for a company, optionally filtered by date range.\n'
    "\n"
    "        Tenant Isolation: enforces company_id in WHERE clause.\n"
    '        """\n'
    "        q = self.db.query(ShiftAssignment).filter(\n"
    "            ShiftAssignment.company_id == company_id\n"
    "        )\n"
    "        if start_date is not None:\n"
    "            q = q.filter(ShiftAssignment.work_date >= start_date)\n"
    "        if end_date is not None:\n"
    "            q = q.filter(ShiftAssignment.work_date <= end_date)\n"
    "        return q.order_by(\n"
    "            ShiftAssignment.work_date.asc(),\n"
    "            ShiftAssignment.user_id.asc(),\n"
    "        ).all()"
)

NEW3 = (
    "    def list_by_company(\n"
    "        self,\n"
    "        company_id: str,\n"
    "        start_date: Optional[date] = None,\n"
    "        end_date: Optional[date] = None,\n"
    "        template_id: Optional[UUID] = None,\n"
    "        status: Optional[str] = None,\n"
    "    ) -> List[ShiftAssignment]:\n"
    '        """List all ShiftAssignments for a company, optionally filtered by date range.\n'
    "\n"
    "        Tenant Isolation: enforces company_id in WHERE clause.\n"
    "        Optional filters: template_id, status (S1-09B).\n"
    '        """\n'
    "        q = self.db.query(ShiftAssignment).filter(\n"
    "            ShiftAssignment.company_id == company_id\n"
    "        )\n"
    "        if start_date is not None:\n"
    "            q = q.filter(ShiftAssignment.work_date >= start_date)\n"
    "        if end_date is not None:\n"
    "            q = q.filter(ShiftAssignment.work_date <= end_date)\n"
    "        if template_id is not None:\n"
    "            q = q.filter(ShiftAssignment.shift_template_id == template_id)\n"
    "        if status is not None:\n"
    "            q = q.filter(ShiftAssignment.status == status)\n"
    "        return q.order_by(\n"
    "            ShiftAssignment.work_date.asc(),\n"
    "            ShiftAssignment.user_id.asc(),\n"
    "        ).all()"
)

assert OLD3 in content, 'ERROR: OLD3 not found'
content = content.replace(OLD3, NEW3, 1)
print('Patch 3 (list_by_company): OK')

# -----------------------------------------------------------------------
# Write back
# -----------------------------------------------------------------------
with open(path, 'w') as f:
    f.write(content)

final_lines = content.count('\n')
print(f'repo.py written OK, lines: {final_lines}')

count = content.count('template_id: Optional[UUID] = None')
print(f'template_id Optional params: {count} occurrences (expected 3)')
assert count == 3, f'Expected 3, got {count}'
print('PATCH COMPLETE: all 3 methods verified')
