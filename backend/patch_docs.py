#!/usr/bin/env python3
"""
S1-09B: Update docs.md - assignment list query contract sync.
Minimal local patch only, no full rewrite.
"""

path = 'app/modules/schedule/docs.md'
with open(path, 'r') as f:
    content = f.read()

assert len(content) > 1000, f'docs.md too short: {len(content)} bytes'
print(f'docs.md before patch: {content.count(chr(10))} lines')

# -----------------------------------------------------------------------
# Patch 1: Update the ShiftAssignment Endpoints table - list row
# -----------------------------------------------------------------------
OLD_LIST_ROW = '| GET | /api/v1/schedule/shift-assignments | 列出指派（?user_id / ?start_date / ?end_date / ?work_date）|'
NEW_LIST_ROW = '| GET | /api/v1/schedule/shift-assignments | 列出指派（?user_id / ?start_date / ?end_date / ?work_date / ?template_id / ?status）|'

assert OLD_LIST_ROW in content, 'ERROR: OLD_LIST_ROW not found'
content = content.replace(OLD_LIST_ROW, NEW_LIST_ROW, 1)
print('Patch 1 (list row in endpoint table): OK')

# -----------------------------------------------------------------------
# Patch 2: Update Request/Filter 規則 section
# -----------------------------------------------------------------------
OLD_FILTER_RULES = '''### Request/Filter 規則
- company_id 從 JWT actor 取得，不接受 payload 自填
- list assignments 支援：work_date（單日）/ user_id+date_range / date_range / 全公司
- status change 透過 PATCH update endpoint 處理（含 cancel 獨立端點）'''

NEW_FILTER_RULES = '''### Request/Filter 規則
- company_id 從 JWT actor 取得，不接受 payload 自填
- list assignments 支援：work_date（單日）/ user_id+date_range / date_range / 全公司
- status change 透過 PATCH update endpoint 處理（含 cancel 獨立端點）

### Assignment List Optional Filters（S1-09B）

**新增 optional query params：**

| 參數 | 型別 | 行為 |
|------|------|------|
| `template_id` | `UUID`（optional）| 精確匹配 `shift_template_id`，不帶則不過濾 |
| `status` | `string`（optional）| 精確匹配狀態值（`scheduled` / `confirmed` / `cancelled`）|

**work_date precedence 規則（維持既有，不變）：**
1. `work_date` 存在 → 單日優先，`template_id` / `status` 在此路徑疊加
2. `user_id` 存在（無 `work_date`）→ 必須同時提供 `start_date` + `end_date`，`template_id` / `status` 在此路徑疊加
3. 其他 → `list_by_company` 路徑，所有 optional filter 均生效

**company scope 保證：**
- repo 層第一條件固定 `WHERE company_id = actor.active_company_id`
- `template_id` / `status` 只在 company scope 內做 AND 疊加
- 任何 filter 不得稀釋 tenant isolation

**invalid status 驗證：**
- `status` query param 型別為 `AssignmentStatusSchema`（FastAPI enum）
- 傳入非法值（如 `invalid_xyz`）→ FastAPI 自動回 `422 Unprocessable Entity`
- 不需要應用層額外 guard'''

assert OLD_FILTER_RULES in content, 'ERROR: OLD_FILTER_RULES not found'
content = content.replace(OLD_FILTER_RULES, NEW_FILTER_RULES, 1)
print('Patch 2 (Request/Filter 規則 section): OK')

# -----------------------------------------------------------------------
# Patch 3: Update repo.py method descriptions for list methods
# -----------------------------------------------------------------------
OLD_REPO_LIST = '''- `list_by_user_date_range(company_id, user_id, start_date, end_date)` — 依使用者+日期範圍
- `list_by_company_date(company_id, work_date)` — 依公司+單日
- `list_by_company(company_id, start_date, end_date)` — 依公司+可選日期範圍'''

NEW_REPO_LIST = '''- `list_by_user_date_range(company_id, user_id, start_date, end_date, template_id?, status?)` — 依使用者+日期範圍（S1-09B: +template_id/status filter）
- `list_by_company_date(company_id, work_date, template_id?, status?)` — 依公司+單日（S1-09B: +template_id/status filter）
- `list_by_company(company_id, start_date?, end_date?, template_id?, status?)` — 依公司+可選日期範圍（S1-09B: +template_id/status filter）'''

assert OLD_REPO_LIST in content, 'ERROR: OLD_REPO_LIST not found'
content = content.replace(OLD_REPO_LIST, NEW_REPO_LIST, 1)
print('Patch 3 (repo.py method descriptions): OK')

# -----------------------------------------------------------------------
# Patch 4: Update service.py method descriptions for list methods
# -----------------------------------------------------------------------
OLD_SVC_LIST = '''- `list_assignments_for_user(company_id, user_id, start_date, end_date)` — 依使用者+日期
- `list_assignments_for_date(company_id, work_date)` — 依單日
- `list_assignments(company_id, start_date, end_date)` — 全公司+可選日期'''

NEW_SVC_LIST = '''- `list_assignments_for_user(company_id, user_id, start_date, end_date, template_id?, status?)` — 依使用者+日期（S1-09B: +filter）
- `list_assignments_for_date(company_id, work_date, template_id?, status?)` — 依單日（S1-09B: +filter）
- `list_assignments(company_id, start_date?, end_date?, template_id?, status?)` — 全公司+可選日期（S1-09B: +filter）'''

assert OLD_SVC_LIST in content, 'ERROR: OLD_SVC_LIST not found'
content = content.replace(OLD_SVC_LIST, NEW_SVC_LIST, 1)
print('Patch 4 (service.py method descriptions): OK')

# -----------------------------------------------------------------------
# Write back
# -----------------------------------------------------------------------
with open(path, 'w') as f:
    f.write(content)

final_lines = content.count('\n')
print(f'docs.md written OK, lines: {final_lines}')
assert len(content) > 1000, 'docs.md suspiciously short after write'
print('PATCH COMPLETE')
