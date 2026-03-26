# WP-S1-08 Assignment Create Contract Alignment Fix Report

## Summary
本票完成 Shift Assignment create contract 與 tenant scope 對齊：
- create request 不再要求 `company_id`
- service create 不再依賴 / 比對 `payload.company_id`
- `company_id` 來源統一由 JWT actor scope (`actor.active_company_id`) 決定

## Scope
- 調整 `ShiftAssignmentCreate` schema（不繼承 base，移除 company_id）
- 調整 `create_shift_assignment()` service（移除 payload.company_id guard）
- 最小調整 assignment 相關測試 payload（移除 company_id）
- 文件同步

## Contract Before / After

### Before
- Request body required: `company_id`, `user_id`, `shift_template_id`, `work_date`, ...
- Service checked `payload.company_id != actor_company_id` then 403

### After
- Request body required: `user_id`, `shift_template_id`, `work_date`, ...
- Service no longer reads `payload.company_id`
- DB write still uses `company_id=actor_company_id`

## Tenant Isolation
- Tenant boundary remains server-side only
- Client payload no longer carries company scope responsibility

## Regression Notes
- `ShiftAssignmentRead` still includes `company_id`
- Assignment list/get/update/cancel flows unchanged
- Template flows unchanged
