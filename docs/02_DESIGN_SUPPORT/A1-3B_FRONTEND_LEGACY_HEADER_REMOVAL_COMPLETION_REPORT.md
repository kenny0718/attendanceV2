# A1-3B Frontend Legacy Header Removal — Completion Report

- Date: 2026-03-25
- Status: Completed
- Scope: Remove `X-Company-ID` / `X-User-ID` global injection from frontend API client
- Risk Level: Low

---

## Summary

Successfully removed the legacy `X-Company-ID` and `X-User-ID` header injection from the frontend shared API client (`frontend/src/api/client.js`). The injection was located in the global Axios request interceptor and was the sole injection point across the entire frontend codebase. No other files required modification.

The file had been zeroed out (0 byte, `e69de29`) in the working tree prior to this task. Content was restored from git HEAD and the legacy block was removed cleanly before writing back.

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/api/client.js` | Removed legacy header injection block (13 lines removed) |

---

## Header Injection Before / After

### Before (git HEAD — lines 22–35)

```javascript
// 添加 tenant headers (從 localStorage 取得)
const company = localStorage.getItem('company')
const user = localStorage.getItem('user')

if (company) {
  const companyData = JSON.parse(company)
  config.headers['X-Company-ID'] = companyData.id
}

if (user) {
  const userData = JSON.parse(user)
  config.headers['X-User-ID'] = userData.id
}
```

### After

```javascript
// (removed — no replacement needed)
```

### Preserved (unchanged)

```javascript
const token = localStorage.getItem('token')
if (token) {
  config.headers.Authorization = `Bearer ${token}`
}
return config
```

---

## Validation Result

| Check | Result |
|-------|--------|
| `grep X-Company-ID client.js` | NOT FOUND ✅ |
| `grep X-User-ID client.js` | NOT FOUND ✅ |
| `grep Authorization client.js` | FOUND (line 20) ✅ |
| `grep return config client.js` | FOUND (line 23) ✅ |
| `grep interceptors client.js` | FOUND (lines 15, 31) ✅ |
| `node --check client.js` | EXIT 0 — syntax OK ✅ |
| Other frontend files injecting these headers | NONE (grep confirmed) ✅ |

---

## Known Limitations

- `localStorage.getItem('company')` and `localStorage.getItem('user')` are still written during login (in `stores/auth.js`). These values remain in localStorage for auth state purposes but are no longer injected as headers. This is intentional and correct — the data is used by the store, not the HTTP layer.
- No browser-level smoke test was executed (environment constraint). Validation was static only.
- `stores/auth.js` was not modified (not in scope, not needed).

---

## Non-Scope Files Touched

NONE. Only `frontend/src/api/client.js` was modified.

---

## NEXT_WP_TICKET.md updated

NO (per task scope rules)

---

## Next Step

A1-3c — Retire `tenant_context.py` legacy header dependencies (backend/test layer cleanup)
