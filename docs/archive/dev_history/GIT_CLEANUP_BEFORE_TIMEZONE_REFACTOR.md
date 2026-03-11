# Git Cleanup Before Timezone Refactor

**Date:** 2026-03-10  
**Purpose:** Classify all dirty/untracked files before starting timezone refactor  
**Baseline Tag:** `attendance-stable-before-timezone-refactor` (commit `3500958`)

---

## Current Git State Summary

- **Modified (tracked):** 18 files
- **Untracked:** ~80+ files
- **No root .gitignore** (only frontend has one, backend has none)

---

## Classification Table

### Group A — Must Keep and Commit (Real source changes)

| File | Reason |
|------|--------|
| `backend/app/main.py` | WP-11-13: registers `admin_location_router` |
| `backend/app/modules/attendance/api.py` | WP-11-13: location policy enforcement in `break_out` |
| `backend/app/modules/attendance/models.py` | WP-11-13: `AllowedLocation` model + `location_id` FK on punch |
| `backend/app/modules/attendance/schemas.py` | WP-11-13: `AllowedLocation*` schemas |
| `backend/app/modules/attendance/admin_location_api.py` | WP-11-13: new admin API for location management |
| `backend/app/modules/attendance/location_policy_service.py` | WP-11-13: location policy check service |
| `backend/alembic/versions/008_wp_11_13_create_allowed_locations.py` | WP-11-13: migration |
| `backend/alembic.ini` | Minor config change |
| `frontend/src/api/attendance.js` | Remove obsolete OUT checkpoint API calls |
| `frontend/src/utils/locationAdapter.js` | Documentation update on deprecation status |
| `frontend/src/components/Navbar.vue` | UI icon/style update |
| `frontend/src/components/attendance/` | New attendance sub-components (refactor) |
| `docs/GATE_PROGRESS_TRACKER.md` | Progress documentation |
| `docs/NEXT_WP_TICKET.md` | Next ticket documentation |
| `backend/app/modules/attendance/tests/test_break_out_enforcement.py` | WP-11-13 tests |
| `backend/app/modules/attendance/tests/test_location_policy.py` | WP-11-13 tests |
| `docs/API_DOCUMENTATION_v2.0.md` | API docs |
| `docs/ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md` | Location policy spec |
| `docs/WP-11-13_*.md` | WP-11-13 implementation docs |
| `docs/WP-11-12_*.md` | WP-11-12 historical docs |
| `docs/HOME_UI2_*.md` | UI refactor planning docs |
| `docs/HOME_UI_ADJUSTMENT_REPORT.md` | UI report |
| `docs/SA_MODULE_SPEC_v2.0.md` | Module spec |
| `scripts/` | Utility scripts |

### Group B — Should Be Ignored Going Forward (Runtime/Cache/Env)

| File/Pattern | Reason |
|-------------|--------|
| `backend.log` | Runtime log |
| `backend/backend.log` | Runtime log |
| `backend/backend.pid` | Runtime PID file |
| `backend/.env` | Local env secrets (should never be in Git) |
| `frontend/.env.development` | Local env config (already in frontend .gitignore as `*.local` but this doesn't match) |
| `backend/**/__pycache__/` | Python bytecode cache |
| `backend/**/*.pyc` | Python bytecode |
| `backend/alembic/versions/__pycache__/` | Alembic bytecode |

### Group C — Backup/Temporary Files (Should NOT enter Git)

| File | Reason |
|------|--------|
| `backend/app/modules/attendance/api.py.backup_20260309_201338` | Timestamped backup |
| `backend/app/modules/attendance/models.py.bak` | Backup |
| `backend/app/modules/attendance/repo.py.backup` | Backup |
| `docs/SA_MODULE_SPEC_v2.0.md.backup` | Backup |
| `frontend/src/stores/attendance.js.backup.phase2b` | Backup |
| `frontend/src/stores/attendance.js.backup_1773104203` | Backup |
| `frontend/src/stores/attendance.js.backup_before_fix` | Backup |
| `frontend/src/stores/attendance.js.bak` | Backup |
| `frontend/src/stores/attendance.js.before_out_checkpoint_removal` | Before-state backup |
| `frontend/src/stores/attendance.js.before_session_fix` | Before-state backup |
| `frontend/src/api/attendance.js.before_out_checkpoint_removal` | Before-state backup |
| `frontend/src/views/Home.vue.after_ui_adjustment` | Before/after backup |
| `frontend/src/views/Home.vue.backup.phase2b` | Backup |
| `frontend/src/views/Home.vue.backup_before_merge` | Backup |
| `frontend/src/views/Home.vue.backup_before_outing_refactor` | Backup |
| `frontend/src/views/Home.vue.backup_before_punch_icons` | Backup |
| `frontend/src/views/Home.vue.backup_before_refactor` | Backup |
| `frontend/src/views/Home.vue.backup_icons` | Backup |
| `frontend/src/views/Home.vue.before_fix` | Backup |
| `frontend/src/views/Home.vue.before_out_checkpoint_removal` | Backup |
| `frontend/src/views/Home.vue.before_step3a` | Backup |
| `frontend/src/views/Home.vue.broken_backup_20260309_220339` | Broken backup |
| `frontend/src/views/Home.vue.emergency_backup` | Emergency backup |
| `frontend/src/stores/attendance_debug.js` | Debug copy |
| `frontend/src/views/HomeV1.vue` | Empty legacy file (0 bytes) |
| `docs/WP-11-13_STEP3A_COMPLETION.txt` | Plain text completion note |
| `docs/WP-11-13_STEP3A_QA_COMPLETION.txt` | Plain text QA note |

### Group D — Manual Review Before Decision

| File | Concern |
|------|---------|
| `ALL_ICONS_UPDATE.md` (root) | Root-level report, may be AI-generated clutter |
| `ATTENDANCE_COMPONENT_REFACTOR.md` (root) | Root-level report |
| `BREAK_MANAGEMENT_MERGE.md` (root) | Root-level report |
| `BUNDLE_VERIFICATION_REPORT.md` (root) | Root-level report |
| `COMPLETE_ICONS_UPDATE.md` (root) | Root-level report |
| `DEPLOYMENT.md` (root) | Could be real deployment doc, review needed |
| `FINAL_ICONS_UPDATE.md` (root) | Root-level report |
| `FIX_SUMMARY.md` (root) | Root-level report |
| `FRONTEND_DIAGNOSTIC_REPORT.md` (root) | Root-level report |
| `ICON_UPDATE.md` (root) | Root-level report |
| `LIVE_DELIVERY_VERIFICATION_REPORT.md` (root) | Root-level report |
| `PUNCH_OUT_UI_FIX_REPORT.md` (root) | Root-level report |
| `SESSION_BASED_DISPLAY_FIX.md` (root) | Root-level report |
| `SESSION_FIX_SUMMARY.md` (root) | Root-level report |
| `docs/DOCS_CORRECTION_COMPLETION_REPORT.md` | May be clutter |
| `docs/DOCUMENTATION_UPDATE_SUMMARY_v2.0.md` | May be clutter |
| `docs/HOMEPAGE_PROTECTION_BASELINE_COMPLETION_REPORT.md` | Baseline report |
| `docs/HOME_UI2_ROLLOUT_CONTROL_PLAN.md` | Future plan, review |
| `docs/LOCATION_POLICY_DOCS_CORRECTIONS_v1.0.md` | Docs corrections |
| `docs/OUT_CHECKPOINT_REMOVAL_*.md` | Historical, review |

---

## .gitignore Recommendations

### Root `.gitignore` (create new)

```gitignore
# Python cache
**/__pycache__/
**/*.pyc
**/*.pyo

# Logs
*.log
backend.log
backend/backend.log

# PID files
*.pid
backend/backend.pid

# Environment files (secrets)
backend/.env

# Backup files (should never be committed)
**/*.bak
**/*.backup
**/*.backup_*
**/*.before_*
**/*.emergency_backup
**/*.broken_backup*
**/*_debug.js

# Temporary/timestamped backups
**/Home.vue.after_ui_adjustment
**/HomeV1.vue
```

### `frontend/.gitignore` (add to existing)

```gitignore
# Add to existing file
.env.development
.env.local
```

---

## Manual Review List

The 14 root-level `.md` files (`ALL_ICONS_UPDATE.md`, `FIX_SUMMARY.md`, etc.) appear to be AI-generated session reports accidentally placed at root instead of `docs/`. Recommend:
- Move to `docs/archive/` if historically valuable
- Or delete if content is already summarized in canonical docs

`DEPLOYMENT.md` at root — review if this is a real deployment guide or session artifact.

---

## Next Clean-Up Commit Proposal

Files to stage for next commit (Group A untracked files):
```bash
git add \
  backend/app/main.py \
  backend/app/modules/attendance/api.py \
  backend/app/modules/attendance/models.py \
  backend/app/modules/attendance/schemas.py \
  backend/app/modules/attendance/admin_location_api.py \
  backend/app/modules/attendance/location_policy_service.py \
  backend/alembic/versions/008_wp_11_13_create_allowed_locations.py \
  backend/alembic.ini \
  frontend/src/api/attendance.js \
  frontend/src/utils/locationAdapter.js \
  frontend/src/components/Navbar.vue \
  'frontend/src/components/attendance/' \
  docs/GATE_PROGRESS_TRACKER.md \
  docs/NEXT_WP_TICKET.md \
  docs/WP-11-12_PHASE2B_*.md \
  docs/WP-11-13_*.md \
  docs/HOME_UI2_*.md \
  docs/API_DOCUMENTATION_v2.0.md \
  docs/ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md \
  docs/SA_MODULE_SPEC_v2.0.md \
  scripts/
```

Recommended commit message:
```
chore: git cleanup - commit WP-11-12/13 changes before timezone refactor

- WP-11-13: location policy models, schemas, admin API, service
- WP-11-13: break_out location enforcement in API
- WP-11-13: migration 008 for allowed_locations table
- Remove OUT checkpoint API from frontend
- Add .gitignore for runtime/cache/backup patterns
```
