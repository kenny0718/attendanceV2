
# CURSOR_DEVELOPMENT_RULES.md

> **Purpose**
> This document defines strict rules for AI-assisted development using Cursor.
> It prevents architecture drift, accidental core changes, and WP order violations.

**Status:** ACTIVE  
**Applies to:** Cursor / GPT / Claude AI sessions  
**Location:** docs/CURSOR_DEVELOPMENT_RULES.md

---

# 1. Mandatory Pre‑Read (Before Any Coding)

Before implementing any feature, Cursor **MUST read**:

1. docs/AI_CONTEXT.md
2. docs/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md
3. docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md
4. docs/NEXT_WP_TICKET.md

Failure to read these documents may result in incorrect architecture decisions.

---

# 2. Current Development Position Rule

Cursor must always confirm:

```
CURRENT WP
CURRENT PHASE
NEXT WP
```

These values must be taken from:

```
docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md
```

Cursor **must not assume the next task**.

---

# 3. Work Package (WP) Execution Rules

### 3.1 No WP Jumping

Cursor **must NOT start a future WP** before the current WP is complete.

Example:

```
CURRENT WP: WP‑11‑07
NEXT WP: WP‑11‑08
```

Cursor **cannot start WP‑11‑08** until WP‑11‑07 is marked COMPLETE.

---

### 3.2 One Feature WP at a Time

Only **one Feature WP** may be active simultaneously.

Infrastructure WPs (WP‑C1‑xx) may run in parallel but must not interfere with Feature WPs.

---

# 4. Architecture Layer Rules

Cursor must follow the strict architecture layering:

```
Frontend Page
   ↓
Store
   ↓
API Client
   ↓
Backend Router
   ↓
Service / Policy
   ↓
Repository
   ↓
Database
```

### Forbidden

```
Page → Database
Page → Repository
Store → Database
Router → Direct DB queries
```

---

# 5. Protected Core Areas

The following components are **protected core modules** and must not be modified without explicit WP authorization.

### Backend Core

```
backend/app/modules/attendance/service.py
backend/app/modules/attendance/models.py
backend/app/modules/attendance/policy_engine.py
```

### Frontend Core

```
frontend/src/stores/attendance.js
frontend/src/views/Home.vue
frontend/src/api/client.js
```

### Platform Core

```
backend/app/core/security/jwt.py
backend/app/core/tenant_context.py
backend/app/core/dependencies.py
```

### Special Rules

Protected core modules may only change if:

1. A dedicated WP authorizes it
2. Architecture impact is explained
3. Migration impact is evaluated

---

# 6. Reporting System Rules

The reporting module **already exists**.

Reporting backend:

```
/api/v1/attendance/sessions
/api/v1/attendance/reports/user-summary
/api/v1/attendance/reports/company-summary
```

Cursor must **NOT recreate these endpoints**.

Reporting UI pages already exist:

```
AttendanceSessionsPage.vue
CompanySummaryPage.vue
UserSummaryPage.vue
```

Allowed work:

```
UI polish
error state fixes
UX improvements
QA validation
```

Forbidden work:

```
rewriting reporting system
creating duplicate APIs
changing reporting data model
```

---

# 7. GPS Module Rules

Current GPS status:

```
FOUNDATION ONLY
```

Existing components:

```
useLocation.js
gps_utils.py
location_policy_service.py
```

This **does NOT mean GPS module is complete**.

Full GPS / Field Work implementation belongs to:

```
WP‑11‑10
```

Cursor must not expand GPS functionality before that WP.

---

# 8. Database Rules

### Migration Policy

Database schema changes must follow:

```
new migration file
never edit old migration
never delete migration
```

Migration chain is linear.

Current head:

```
008_wp_11_13
```

---

# 9. Tenant Isolation Rules

Every query must include:

```
WHERE company_id = ?
```

Cursor must ensure:

```
no cross‑tenant queries
no global queries
```

---

# 10. Development Flow Rule

All development must follow this sequence:

```
Spec
→ API Contract
→ Backend Implementation
→ Frontend Integration
→ Testing
→ Documentation
```

Skipping steps is forbidden.

---

# 11. Debugging Policy

When debugging:

1. Verify logs
2. Verify API response
3. Verify DB data
4. Verify frontend state

Cursor must not guess root causes without verification.

---

# 12. Code Modification Policy

Cursor should prefer:

```
small targeted changes
```

Avoid:

```
large refactors
rewriting modules
changing working logic
```

---

# 13. Documentation Rules

When a WP is completed:

Update:

```
docs/NEXT_WP_TICKET.md
docs/GATE_PROGRESS_TRACKER.md
docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md
```

Documentation must always reflect real repo status.

---

# 14. AI Session Handoff Rules

Every new Cursor session must start with:

1. Reading AI_CONTEXT.md
2. Confirming current WP
3. Confirming protected modules
4. Confirming architecture layers

Only after this may development begin.

---

# 15. Final Principle

Cursor must behave as a **disciplined developer**, not an autonomous architect.

Cursor must:

```
respect roadmap
respect architecture
respect protected modules
```

---

**END OF CURSOR_DEVELOPMENT_RULES.md**
