# A1-4 Header Reintroduction Guard — Completion Report

- Date: 2026-03-25
- Status: Completed
- Scope: Add log-only guard against reintroduction of retired legacy headers
- Risk Level: Minimal (log-only, no request blocking)

---

## Summary

Added a lightweight Starlette HTTP middleware to `backend/app/main.py` that logs a warning whenever a request contains the retired legacy headers `X-Company-ID` or `X-User-ID`. The middleware never blocks or modifies requests — it only surfaces accidental reintroduction via the application log.

---

## Files Changed

| File | Action | Detail |
|------|--------|--------|
| `backend/app/main.py` | Modified | Added `Request` import and `legacy_header_guard` middleware (~18 lines) |

---

## Guard Implementation

```python
@app.middleware("http")
async def legacy_header_guard(request: Request, call_next):
    """A1-4: Warn if retired legacy headers reappear in any request.

    X-Company-ID and X-User-ID were retired in A1-3.
    All production endpoints use JWT actor exclusively.
    This guard logs a warning to surface accidental reintroduction.
    """
    _RETIRED_HEADERS = ("x-company-id", "x-user-id")
    for header in _RETIRED_HEADERS:
        if header in request.headers:
            logger.warning(
                f"[A1-4] Legacy header detected: '{header}' — "
                "retired in A1-3, ignored by all production endpoints. "
                "Check for accidental reintroduction."
            )
    return await call_next(request)
```

### Design Decisions

- **Layer chosen**: `main.py` HTTP middleware — covers all endpoints, minimal code surface
- **No blocking**: `call_next(request)` always proceeds regardless of header presence
- **Header name check**: Starlette normalises header names to lowercase; checking `x-company-id` / `x-user-id` covers all case variants
- **Log prefix `[A1-4]`**: Makes guard warnings easily grep-able in production logs

---

## Validation Result

| Check | Result |
|-------|--------|
| `python3 -m py_compile app/main.py` | OK ✅ |
| Guard does not block requests | Confirmed (only `logger.warning` + `call_next`) ✅ |
| Existing auth flow unchanged | Confirmed ✅ |
| No business logic modified | Confirmed ✅ |

---

## Known Limitations

- Guard is log-only. If stricter enforcement is needed in the future, the middleware can be upgraded to return HTTP 400, but this is intentionally deferred.
- No automated test added for the guard (non-required per ticket scope).

---

## NEXT_WP_TICKET.md updated

NO (per task scope rules)
