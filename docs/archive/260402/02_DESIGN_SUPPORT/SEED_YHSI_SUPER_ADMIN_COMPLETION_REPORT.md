# YHSI Super Admin Seed — Completion Report

- Date: 2026-03-25
- Status: Completed
- Scope: Create idempotent dev seed for fixed super_admin account (yhsi / yhsimis)
- Risk Level: Low (dev seed only, never runs in production)

---

## Summary

Created a new idempotent seed script `backend/scripts/dev/seed_yhsi_super_admin.py` that provisions a fixed super_admin account for YHSI. The script was successfully executed and verified.

---

## Files Changed

| File | Action | Reason |
|------|--------|--------|
| `backend/scripts/dev/seed_yhsi_super_admin.py` | Created | New seed script for YHSI super_admin |
| `docs/02_DEVELOPMENT_STATUS/SEED_YHSI_SUPER_ADMIN_COMPLETION_REPORT.md` | Created | This report |

**No production code was modified.** No auth flow, no router, no frontend, no JWT logic was touched.

---

## Seeded Fixed Account Details

| Field | Value |
|-------|-------|
| company_id | `yhsi` |
| company_name | `YHSI` |
| login_username | `yhsimis` |
| password | `Yh2028109!` |
| role_id | `super_admin` |
| user display_name | `YHSI MIS Admin` |
| user email | `null` (intentional per audit) |
| user UUID | `008d7786-21f2-4b75-8fd0-2e6648e197e4` |
| membership UUID | `2708f70c-48dd-4db4-86b8-cfb057e1c63f` |

**Login endpoint:** `POST /api/internal/auth/login`

```json
{
  "company_id": "yhsi",
  "login_username": "yhsimis",
  "password": "Yh2028109!"
}
```

---

## Seed Status on First Run

| Object | Status | Detail |
|--------|--------|--------|
| role: `super_admin` | **EXISTS / REUSED** | Already seeded by prior migration |
| tenant: `yhsi` | **CREATED** | New tenant |
| user: `YHSI MIS Admin` | **CREATED** | New user (email=null) |
| membership: `(yhsi, yhsimis)` | **CREATED** | New membership |
| password | **initialized** to `Yh2028109!` | Set only on first user creation |

---

## Idempotent Behavior

The script is safe to rerun at any time:

| Object | Lookup Key | If Exists |
|--------|-----------|----------|
| Role | `role.id == "super_admin"` | Skip |
| Tenant | `tenant.id == "yhsi"` | Skip |
| User + Membership | `membership.company_id="yhsi" AND login_username="yhsimis"` | Skip |
| Password | N/A | **Never overwritten** if user pre-exists |

**Safety guard:** If membership `(yhsi, yhsimis)` exists but `role_id != super_admin` → script aborts with `[ABORT]` error and rolls back. No silent data corruption.

**Second run output (verified):**
```
  [EXISTS ]  role: super_admin
  [EXISTS ]  tenant: yhsi (YHSI)
  [EXISTS ]  user: YHSI MIS Admin
  [EXISTS ]  membership: company=yhsi, login=yhsimis, role=super_admin
  [PASSWORD]  unchanged (user pre-existed)
  Seed completed successfully.
```

---

## Verification Performed

1. `python3 -m py_compile` — syntax OK
2. First run: all 4 objects created correctly, commit successful
3. Second run: all 4 objects detected as EXISTS, no duplicate creation, password unchanged
4. File size check: 7258 bytes (non-zero)

---

## How to Run

```bash
cd /opt/attendance-system/backend
source venv/bin/activate
python3 scripts/dev/seed_yhsi_super_admin.py
```

---

## Known Limitations / Assumptions

- **Dev only:** Script is in `scripts/dev/` and should never be run in production.
- **Password not rotatable via script:** If `yhsimis` account already exists, password is never overwritten. Manual DB update required if password needs changing.
- **email=null:** Per auth audit (A1-3 series), login does not require email. `User.email` is nullable and left null intentionally.
- **super_admin role pre-existed:** The `super_admin` role was already present in the DB from a prior seed. Script correctly detected and reused it.
- **No UI test performed:** Login via browser or curl was not tested in this ticket. The login endpoint contract is established by A1-3 audit.

---

## NEXT_WP_TICKET.md updated

NO (per task scope rules)
