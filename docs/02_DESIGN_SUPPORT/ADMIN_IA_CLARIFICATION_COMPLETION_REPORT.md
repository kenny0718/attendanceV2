# Admin IA Clarification — Completion Report

- Date: 2026-03-25
- Status: Completed
- Scope: Clarify Companies vs Onboarding separation; remove duplicate create-company entry point
- Risk Level: Low (UI text and dead code removal only; no backend, no auth, no router changes)

---

## Summary

Removed the duplicate "建立新公司" panel from `AdminCompaniesView.vue` and redirected all create-company intent to `/admin/onboarding`. Updated card descriptions and added a clear "前往新公司開通" CTA. AdminOnboardingView is now the sole create-company entry point.

---

## Overlap Issue Found

| Location | Issue |
|----------|-------|
| `Admin.vue` card desc | 「查看所有公司、快速建立新公司」— implied Companies page also creates companies |
| `AdminCompaniesView.vue` | Full "建立新公司" panel with form (company ID, name, timezone, submit button) — direct duplicate of Onboarding |
| `AdminCompaniesView.vue` empty state | Told users to "使用下方 Onboarding 建立第一間公司" while the create form was on the same page — self-contradictory |

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/views/Admin.vue` | Card desc: 「查看所有公司、快速建立新公司」→「查看與管理已建立的公司」|
| `frontend/src/views/admin/AdminCompaniesView.vue` | Removed `panel-form` section (建立新公司 form); removed dead code (`form`, `fieldErrors`, `createLoading`, `createError`, `createSuccess`, `handleCreate`, `validateForm`, `resetAlerts`, `isSuperAdmin` computed); added "前往新公司開通" CTA in panel header and empty state; added CSS for CTA button |
| `frontend/src/views/admin/AdminOnboardingView.vue` | Added description line: 「建立新租戶的唯一入口，含初始管理員帳號與 Membership。」|

**Not modified:** router, stores, backend, any other page.

---

## CTA Adjustment Made

- Removed: "建立新公司" form panel in AdminCompaniesView
- Added: `<router-link to="/admin/onboarding" class="btn-goto-onboarding">前往新公司開通</router-link>` in two places:
  1. Panel list header (always visible)
  2. Empty state (when no companies exist)
- Single consistent CTA text: **「前往新公司開通」**

---

## Verification Result

| Check | Result |
|-------|--------|
| `Admin.vue` desc no longer implies create-company | ✅ 「查看與管理已建立的公司」|
| `AdminCompaniesView` has no create-company form | ✅ `panel-form` fully removed |
| `AdminCompaniesView` dead code removed | ✅ `handleCreate`, `createLoading`, `isSuperAdmin`, `computed` import all removed |
| CTA text consistent (single variant) | ✅ 「前往新公司開通」x2 only |
| `AdminOnboardingView` positioning strengthened | ✅ desc line added |
| No role-based display affected | ✅ `v-if="isSuperAdmin"` on Onboarding card in Admin.vue unchanged |
| No router / store / backend modified | ✅ Confirmed |

---

## Scope Control Note

Only 3 frontend Vue files were modified, all within the stated scope:
- Text/desc changes only in `Admin.vue` and `AdminOnboardingView.vue`
- Dead code + duplicate panel removal in `AdminCompaniesView.vue`
- No refactoring of list/query/member logic in `AdminCompaniesView.vue`
- No router, store, backend, auth, or unrelated page was touched

---

## NEXT_WP_TICKET.md updated

NO (per task scope rules)
