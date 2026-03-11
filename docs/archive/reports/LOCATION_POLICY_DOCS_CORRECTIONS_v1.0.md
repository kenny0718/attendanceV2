# Location Policy Documentation Corrections Report

**Date**: 2026-03-09  
**Purpose**: Fix consistency issues in Location Policy documentation  
**Scope**: Documentation only (no code changes)

---

## Executive Summary

This report documents the required corrections to resolve conflicts and inconsistencies in the newly created Location Policy documentation (WP-11-13).

**Status**: ⚠️ Critical conflicts identified and resolved  
**Files Affected**: 4 documentation files  
**Key Decision**: GPS coordinates required when location policy is enabled

---

## 1. Major Conflict Resolved: PC without GPS vs Location Policy Enforcement

### The Problem

**Contradictory statements found**:
- ✅ "If allowed locations exist, user must be within at least one allowed radius"
- ✅ "Mobile must provide GPS, but PC does not need GPS"

**Why this is contradictory**:
- Backend cannot enforce geofence without GPS coordinates
- Cannot calculate distance without latitude/longitude
- Policy check requires `check_location_policy(company_id, lat, lng)`

### The Solution

**Final Rule** (to be applied consistently across all 4 docs):

| Scenario | Company Setup | Device | GPS Required | Behavior |
|----------|--------------|--------|--------------|----------|
| 1 | No allowed locations | Mobile | Recommended | Allow punch, record GPS if provided |
| 2 | No allowed locations | PC | Not required | Allow punch |
| 3 | **Has allowed locations** | Mobile | **REQUIRED** | Validate GPS, allow only if within radius |
| 4 | **Has allowed locations** | PC | **REQUIRED** | Validate GPS, allow only if within radius |

**Key Decision**:
- When location policy is enabled (has allowed locations), **ALL devices must provide GPS**
- PC devices that cannot provide GPS will be rejected for that punch flow
- Frontend must clearly inform users of this limitation

**Rationale**:
- Backend authoritative enforcement requires coordinates
- Cannot compromise security by allowing policy bypass
- Simpler rule: "policy enabled = GPS required"

**Backward Compatibility**:
- Phase 1 only implements BREAK_OUT (typically mobile)
- Future phases must evaluate PC GPS availability
- Consider "manual location selection" alternative for PC (Phase 2)

---

## 2. Status Downgrade: From "Production" to "Design Complete / Partially Implemented"

### Current Overstated Claims

**Found in docs**:
- ❌ "狀態: Production"
- ❌ "狀態: 已實作 (WP-11-13)"
- ❌ "文件狀態: ✅ 已實作並驗證"
- ❌ "狀態: ✅ 完成"

### Reality Check (from NEXT_WP_TICKET.md)

**Actually completed** ✅:
- Data model: `allowed_locations` table
- Backend service: `location_policy_service.py`
- GPS utils: `gps_utils.py`
- Admin API: `admin_location_api.py`
- Migration 008: Database schema
- Critical bug fix: repo.py location_id parameter (commit d8eb797)

**Partially implemented** ⚠️:
- BREAK_OUT API integration (code written, not tested)

**Not implemented** ❌:
- BREAK_IN integration
- Punch-in / Punch-out integration
- Frontend UI (map picker)
- RBAC permission control (admin API)
- End-to-end testing
- Environment setup (Python venv, PostgreSQL)

### Corrected Status

**All 4 docs should use**:
```
Status: Design Complete / Partially Implemented
Implementation Phase: ⚠️ Partial (BREAK_OUT only)
Testing Phase: ⏳ Pending environment setup
Deployment Phase: ⏳ Not started
```

---

## 3. HTTP Status Code Standardization

### Current Inconsistency

**Mixed usage found**:
- Validation errors: sometimes 400, sometimes 422
- Business rule violations: sometimes 400, sometimes 403
- No clear documented rule

### Standardized Mapping

| Status | Use Case | Example |
|--------|----------|---------|
| 200 | Success | Query success, update success |
| 201 | Created | POST create resource |
| 204 | Deleted (no content) | DELETE success |
| **400** | **Request error** (missing required field, format error) | GPS_REQUIRED_FOR_LOCATION_POLICY |
| 401 | Unauthorized (not logged in) | Invalid JWT token |
| **403** | **Forbidden** (permission denied, business rule rejection) | LOCATION_POLICY_VIOLATION, FORBIDDEN |
| 404 | Not found | Location not found |
| **422** | **Validation error** (schema validation) | VALIDATION_ERROR (latitude out of range) |
| 500 | Server error | Unexpected error |

**Key Distinctions**:
- **400**: Request itself is malformed (missing required field, wrong format)
- **422**: Request format is correct but data validation fails (latitude > 90, radius <= 0)
- **403**: Request is valid but business rule rejects it (not within allowed radius, no permission)

### Error Code Examples

**GPS Required (400)**:
```json
{
  "error_code": "GPS_REQUIRED_FOR_LOCATION_POLICY",
  "message": "公司已啟用地點限制，必須提供 GPS 座標才能打卡",
  "policy_enabled": true,
  "allowed_locations_count": 3
}
```

**Location Policy Violation (403)**:
```json
{
  "error_code": "LOCATION_POLICY_VIOLATION",
  "message": "不在允許的打卡範圍內。最近的地點：台北101工地（距離 350 公尺）",
  "nearest_location": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "台北101工地",
    "distance_meters": 350
  }
}
```

**Validation Error (422)**:
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "latitude",
      "message": "緯度必須在 -90 到 90 之間"
    },
    {
      "field": "radius_meters",
      "message": "半徑必須大於 0"
    }
  ]
}
```

---

## 4. Schema Type Verification: company_id

### Current Issue

**Docs assume**:
```sql
company_id VARCHAR(255) NOT NULL
```

**Problem**: Not verified against actual `tenants.id` type

### Corrected Approach

**Use safe wording**:
```sql
-- Tenant Isolation (type must match tenants.id exactly)
company_id VARCHAR(255) NOT NULL,  -- TODO: Verify type matches tenants.id
```

**Add note in docs**:
```
Note: company_id type (VARCHAR(255)) must match tenants.id type exactly.
If tenants.id uses a different type (e.g., UUID), this must be updated
before migration execution.
```

**Foreign Key Constraint**:
```sql
CONSTRAINT fk_allowed_locations_company 
    FOREIGN KEY (company_id) REFERENCES tenants(id) ON DELETE CASCADE
```
This will fail at migration time if types don't match, providing safety.

---

## 5. Current Scope Clarification

### Problem

Docs imply location policy applies to all punch flows, but reality is:

**Phase 1 (Current)**:
- ✅ BREAK_OUT only

**Not Yet Implemented**:
- ❌ BREAK_IN
- ❌ Punch-in
- ❌ Punch-out
- ❌ OUT checkpoints (deprecated)

### Required Addition to All Docs

**Add "Current Scope" section**:

```markdown
## Current Implementation Scope (Phase 1)

**Applies to**:
- BREAK_OUT flow only

**Does NOT apply to** (planned for Phase 2):
- BREAK_IN
- Punch-in
- Punch-out

**Rationale**:
- BREAK_OUT is the primary use case for geofencing (field workers)
- Allows validation of architecture before broader rollout
- Minimizes risk to core attendance flows
```

---

## 6. Terminology Standardization

### Inconsistencies Found

**Mixed terms for same concept**:
- "allowed location" vs "allowed_location" vs "AllowedLocation"
- "location policy" vs "Location Policy" vs "geofence policy"
- "GPS coordinates" vs "GPS 座標" vs "location coordinates"
- "radius meters" vs "radius_meters" vs "允許半徑"

### Standardized Terminology

| English Term | Chinese Term | Code/DB Name | Usage |
|--------------|--------------|--------------|-------|
| Allowed Location | 允許打卡地點 | `allowed_locations` | Table name |
| AllowedLocation | - | `AllowedLocation` | Model class |
| Location Policy | 地點政策 | `location_policy` | Feature name |
| Geofence | 地理圍欄 | - | Alternative term |
| GPS Coordinates | GPS 座標 | `latitude`, `longitude` | Data fields |
| Radius (meters) | 允許半徑（公尺） | `radius_meters` | Distance field |
| Location Violation | 地點違規 | `LOCATION_POLICY_VIOLATION` | Error code |
| Supported Device | 支援的裝置 | - | Device capability |

**Rule**: Use English terms in code/API, Chinese in user-facing messages

---

## 7. Specific File Corrections

### A) ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md

**Changes required**:

1. **Update header status**:
```markdown
**狀態**: Design Complete / Partially Implemented
```

2. **Add implementation status section** (after header):
```markdown
## 文件狀態

**設計階段**: ✅ Complete
**實作階段**: ⚠️ Partial (BREAK_OUT only)
**測試階段**: ⏳ Pending environment setup
**部署階段**: ⏳ Not started
```

3. **Add "Current Scope" section** (after 執行摘要):
```markdown
## 當前實作範圍 (Phase 1)

**✅ 已實作**:
- 資料模型: `allowed_locations` 表
- 後端服務: `location_policy_service.py`
- GPS 工具: `gps_utils.py`
- 管理端 API: `admin_location_api.py`
- Migration 008

**⚠️ 部分實作**:
- BREAK_OUT API 整合 (程式碼已寫，待測試)

**❌ 未實作**:
- BREAK_IN, Punch-in, Punch-out 整合
- 前端 UI (地圖選點器)
- RBAC 權限控制
- 完整測試
```

4. **Fix business rules conflict** (in 架構設計):
```markdown
### GPS 座標要求 ⭐ 關鍵規則

當公司設定了 allowed locations (location policy 啟用) 時:
- **必須提供 GPS 座標**，無論裝置類型
- 無法提供 GPS 的裝置/流程將被拒絕
- 理由: 後端無法在沒有座標的情況下執行 geofence 驗證

| 情境 | 公司設定 | 裝置 | GPS 要求 | 行為 |
|------|---------|------|---------|------|
| 1 | 無 allowed locations | Mobile | 建議 | 允許，記錄 GPS (如有) |
| 2 | 無 allowed locations | PC | 不需要 | 允許 |
| 3 | 有 allowed locations | Mobile | **必須** | 驗證 GPS，範圍內才允許 |
| 4 | 有 allowed locations | PC | **必須** | 驗證 GPS，範圍內才允許 |
```

5. **Standardize HTTP status codes** (in API 規格):
- Change "Response 400 (驗證錯誤)" to "Response 422 (驗證錯誤)"
- Add "Response 400 (GPS 必填但未提供)"
- Clarify 403 is for business rule violations

6. **Fix company_id type** (in 資料模型):
```sql
-- Tenant Isolation (type must match tenants.id exactly)
company_id VARCHAR(255) NOT NULL,  -- TODO: Verify type matches tenants.id
```

7. **Update footer status**:
```markdown
**文件狀態**: ⚠️ Design Complete / Partially Implemented
**最後更新**: 2026-03-09
**維護者**: Backend Team
**待辦事項**:
- 完成環境設定並執行測試
- 驗證 company_id 類型與 tenants.id 一致
- 實作 RBAC 權限控制
- 擴展到其他打卡流程 (Phase 2)
```

---

### B) API_DOCUMENTATION_v2.0.md

**Changes required**:

1. **Update header status**:
```markdown
**狀態**: Draft (Partially Implemented)
```

2. **Fix BREAK_OUT API GPS requirement** (in Request Body table):
```markdown
| gps | object | ⚠️ | GPS 資訊 (當公司啟用 location policy 時必填) |
```

3. **Add note about location policy**:
```markdown
**Note**: If company has enabled location policy (has allowed locations),
GPS is REQUIRED regardless of device type. Request will be rejected with
400 GPS_REQUIRED_FOR_LOCATION_POLICY if GPS is not provided.
```

4. **Standardize HTTP status table**:
```markdown
| 狀態碼 | 說明 | 用途 |
|--------|------|------|
| 400 | 請求錯誤 | 缺少必填欄位、格式錯誤 |
| 403 | 禁止存取 | 權限不足、業務規則拒絕 |
| 422 | 驗證錯誤 | Schema validation 失敗 |
```

5. **Update error code table**:
```markdown
| 錯誤碼 | HTTP | 說明 | 範例 |
|--------|------|------|------|
| GPS_REQUIRED_FOR_LOCATION_POLICY | 400 | Location policy 啟用時必須提供 GPS | 公司有 allowed locations 但未提供 GPS |
| LOCATION_POLICY_VIOLATION | 403 | 不在允許的打卡範圍內 | 員工在工地 500 公尺外打卡 |
| VALIDATION_ERROR | 422 | Schema 驗證錯誤 | 緯度超出範圍 |
```

6. **Add scope limitation note**:
```markdown
## Location Policy Scope (Phase 1)

**Currently applies to**:
- BREAK_OUT API only

**Not yet implemented**:
- BREAK_IN
- Punch-in / Punch-out

Future phases will extend location policy to other punch flows.
```

7. **Update footer**:
```markdown
**文件狀態**: ⚠️ Draft (Partially Implemented)
**最後更新**: 2026-03-09
**維護者**: Backend Team
```

---

### C) SA_MODULE_SPEC_v2.0.md

**Changes required**:

1. **Update header status**:
```markdown
Version: 2.0 Status: Design Complete (Location Policy Partially Implemented)
```

2. **Fix validation order note** (in section 8):
```markdown
API 必須依序驗證：

1️⃣ Scope Validation
2️⃣ Tenant Isolation
3️⃣ Feature Gate
4️⃣ Location Policy (if enabled and flow supports it)

**Note**: Location Policy currently only applies to BREAK_OUT flow (Phase 1).
```

3. **Clarify Location Policy rules** (in section 11):
```markdown
## 11.2 Location Policy 驗證流程

**GPS 座標要求**:
- 當公司設定了 allowed locations (policy 啟用)
- 且打卡流程支援 location policy 驗證時
- **必須提供 GPS 座標**，無論裝置類型
- 無法提供 GPS 的請求將被拒絕 (400 GPS_REQUIRED_FOR_LOCATION_POLICY)

**Phase 1 範圍**:
- 僅適用於 BREAK_OUT 流程
- 其他流程 (BREAK_IN, punch-in, punch-out) 尚未整合
```

4. **Update error codes** (in section 16):
```markdown
400 + GPS_REQUIRED_FOR_LOCATION_POLICY → Location policy 啟用但未提供 GPS
403 + LOCATION_POLICY_VIOLATION → 不在允許打卡範圍內
422 + VALIDATION_ERROR → Schema 驗證錯誤
```

5. **Fix company_id type note** (in section 23):
```markdown
**Migration 008** (WP-11-13):
- 建立 allowed_locations 表
- company_id 類型必須與 tenants.id 一致 (待驗證)
- 擴充 attendance_punches.location_id
```

6. **Update footer**:
```markdown
**文件版本**: v2.0
**最後更新**: 2026-03-09
**更新原因**: 新增 WP-11-13 Location Policy / Geofence 功能
**實作狀態**: ⚠️ Design Complete / Partially Implemented (BREAK_OUT only)
```

---

### D) DOCUMENTATION_UPDATE_SUMMARY_v2.0.md

**Changes required**:

1. **Update status claims**:
```markdown
**狀態**: ⚠️ Design Complete / Partially Implemented
```

2. **Add "Known Decisions Finalized in This Revision" section**:
```markdown
## 🔑 本次修訂確定的關鍵決策

### 1. GPS 座標要求規則

**決策**: 當 location policy 啟用時，所有裝置都必須提供 GPS

**理由**:
- 後端無法在沒有座標的情況下執行 geofence 驗證
- 簡化規則：policy 啟用 = GPS 必須
- 避免安全漏洞

**影響**:
- PC 裝置如無法提供 GPS，該打卡流程將不支援 location policy
- 前端需明確告知使用者此限制
- Phase 2 可考慮「手動選擇地點」替代方案

### 2. HTTP 狀態碼標準化

**決策**:
- 400: 請求錯誤 (缺少必填欄位)
- 403: 業務規則拒絕 (不在範圍內、無權限)
- 422: Schema 驗證錯誤 (緯度超出範圍)

### 3. 實作範圍限制

**決策**: Phase 1 僅實作 BREAK_OUT

**理由**:
- BREAK_OUT 是主要使用場景 (外勤人員)
- 降低風險，不影響核心打卡流程
- 驗證架構正確性後再擴展

### 4. 狀態標示誠實化

**決策**: 使用 "Design Complete / Partially Implemented"

**理由**:
- 程式碼已寫但未完整測試
- 環境尚未設定 (Python venv, PostgreSQL)
- RBAC 權限控制未實作
- 避免誇大完成度
```

3. **Update 文件對照表**:
```markdown
| 文件名稱 | 版本 | 狀態 | 說明 |
|---------|------|------|------|
| SA_MODULE_SPEC_v2.0.md | v2.0 | ⚠️ Design Complete | 含 Location Policy 規範 |
| ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md | v1.0 | ⚠️ Partial Impl | Location Policy 詳細規格 |
| API_DOCUMENTATION_v2.0.md | v2.0 | ⚠️ Draft | API 文件 (含 Location API) |
```

4. **Update 開發者需知**:
```markdown
### 3. 驗證順序（重要）

```
1️⃣ Scope Validation (JWT)
2️⃣ Tenant Isolation (company_id)
3️⃣ Feature Gate (可選)
4️⃣ Location Policy Check (if enabled and flow supports it) ⭐ Phase 1: BREAK_OUT only
```

### 4. GPS 座標要求 ⭐ 新增

**關鍵規則**:
- 當公司啟用 location policy (有 allowed locations)
- **所有裝置都必須提供 GPS**，無論 Mobile 或 PC
- 無法提供 GPS 的請求將被拒絕 (400 GPS_REQUIRED_FOR_LOCATION_POLICY)
```

5. **Add 待辦事項 section**:
```markdown
## ⏳ 待辦事項

### 環境設定
- [ ] 建立 Python venv 並安裝依賴
- [ ] 啟動 PostgreSQL 資料庫
- [ ] 執行 Migration 008
- [ ] 驗證 company_id 類型與 tenants.id 一致

### 測試
- [ ] Backend Unit Tests
- [ ] API Integration Tests
- [ ] Manual QA (8 test cases)

### 實作
- [ ] RBAC 權限控制 (管理端 API)
- [ ] 前端 UI (地圖選點器)
- [ ] 擴展到其他打卡流程 (Phase 2)
```

---

## 8. Remaining Open Questions

These require product/business decisions:

### Q1: PC Device GPS Availability

**Question**: How should we handle PC devices that cannot provide GPS when location policy is enabled?

**Options**:
1. **Reject the punch** (current decision)
   - Pros: Consistent rule, secure
   - Cons: May block legitimate use cases

2. **Allow manual location selection**
   - Pros: Supports PC users
   - Cons: Less secure, requires UI development

3. **Disable location policy for PC devices**
   - Pros: Simple
   - Cons: Security hole, inconsistent

**Recommendation**: Keep current decision for Phase 1, evaluate manual selection for Phase 2

### Q2: RBAC Permission Model

**Question**: Who can manage allowed locations?

**Options**:
1. Company admin only
2. HR manager role
3. Custom "location manager" role

**Current Status**: TODO in code, not implemented

### Q3: Location Policy Feature Flag

**Question**: Should location policy be a paid feature?

**Consideration**:
- Feature flag: `attendance.location_policy`
- May require entitlement check
- Not currently implemented

---

## 9. Summary of Changes

### Files to Update

1. ✅ `ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md` - 7 changes
2. ✅ `API_DOCUMENTATION_v2.0.md` - 7 changes
3. ✅ `SA_MODULE_SPEC_v2.0.md` - 6 changes
4. ✅ `DOCUMENTATION_UPDATE_SUMMARY_v2.0.md` - 5 changes

### Key Conflicts Resolved

1. ✅ **PC without GPS vs Location Policy**: GPS required when policy enabled
2. ✅ **Status overstated**: Changed to "Design Complete / Partially Implemented"
3. ✅ **HTTP status inconsistency**: Standardized 400/403/422 usage
4. ✅ **company_id type**: Added verification note
5. ✅ **Scope unclear**: Clarified Phase 1 = BREAK_OUT only

### Final Decision: PC / GPS Behavior

**When location policy is DISABLED** (no allowed locations):
- Mobile: GPS recommended but not required
- PC: GPS not required

**When location policy is ENABLED** (has allowed locations):
- Mobile: GPS **REQUIRED**
- PC: GPS **REQUIRED**
- Rationale: Backend cannot enforce geofence without coordinates

### Final HTTP Status Mapping

- **400**: Request error (missing required field, format error)
- **403**: Business rule rejection (not within radius, no permission)
- **422**: Schema validation error (latitude out of range, radius <= 0)

---

## 10. Implementation Checklist

**Before claiming "Production Ready"**:

- [ ] Complete environment setup (Python venv, PostgreSQL)
- [ ] Execute Migration 008 successfully
- [ ] Verify company_id type matches tenants.id
- [ ] Run backend unit tests (all pass)
- [ ] Run API integration tests (all pass)
- [ ] Execute manual QA (8 test cases, all pass)
- [ ] Implement RBAC permission control
- [ ] Deploy to staging environment
- [ ] Conduct user acceptance testing
- [ ] Update all 4 docs to "Production" status

**Current Reality**:
- ✅ Code written
- ✅ Critical bug fixed (commit d8eb797)
- ⏳ Environment setup pending
- ⏳ Testing pending
- ❌ RBAC not implemented
- ❌ Frontend UI not implemented

---

## Conclusion

**Documentation Status**: ⚠️ Corrected to reflect reality

**Key Takeaway**: Location policy is well-designed but only partially implemented. Documentation now accurately reflects this state and provides clear rules for GPS requirements.

**Next Steps**:
1. Apply corrections to all 4 documentation files
2. Complete environment setup
3. Execute comprehensive testing
4. Implement remaining features (RBAC, other punch flows)
5. Update docs to "Production" only after full verification

---

**Report Date**: 2026-03-09  
**Author**: Documentation Review Team  
**Status**: ✅ Review Complete, Corrections Documented
