"""
Schedule Module — API Router
==============================
WP-S1-01 Foundation: Router skeleton only.

This file defines the router prefix and tags for the schedule module.
NO endpoints are registered in this ticket.
NO router registration in main app is performed in this ticket.

Router is defined here so future tickets (WP-S1-03+) can add endpoints
without changing module structure.

Out of scope (this ticket):
  - Any working endpoint
  - Router registration in main app (app.include_router)
  - Request/response schemas beyond import declaration
  - Feature gate wiring
  - JWT actor wiring

Expected next step:
  WP-S1-03 — Basic Schedule API (CRUD for ShiftTemplate + ShiftAssignment)
"""

from fastapi import APIRouter

# ---------------------------------------------------------------------------
# Router definition
# Router is NOT registered in main app in this ticket (WP-S1-01).
# Registration happens in a future API ticket (WP-S1-03+).
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/schedule",
    tags=["schedule"],
)

# ---------------------------------------------------------------------------
# No endpoints defined in WP-S1-01.
# Placeholder comment so future tickets know where to add routes.
# ---------------------------------------------------------------------------

# TODO (WP-S1-03): Add GET /shift-templates
# TODO (WP-S1-03): Add POST /shift-templates
# TODO (WP-S1-03): Add GET /shift-assignments
# TODO (WP-S1-03): Add POST /shift-assignments
