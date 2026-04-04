# WP-S1-07C Create Contract Alignment Fix Report

**日期:** 2026-03-25  
**範圍:** Schedule Template create contract alignment（非功能擴張）

## 問題
- `POST /api/v1/schedule/shift-templates` 出現 `422 body.company_id required`
- 與既有 JWT actor tenant scope 設計不一致

## 根因
- `ShiftTemplateCreate` 沿用 base schema，誤要求 `company_id`
- `service.create_shift_template()` 仍比對 `payload.company_id`

## 修正
1. `ShiftTemplateCreate` 不再要求 `company_id`
2. create service 移除 `payload.company_id` 比對
3. create 寫入仍以 API 傳入 `company_id`（來源 `actor.active_company_id`）為準

## 驗證
- create template（no company_id）PASS
- template edit（PATCH）PASS
- template activate/deactivate PASS

## 邊界與風險
- tenant isolation 模型不變（actor scope）
- 未擴修 assignment create contract（同型問題已記錄）
