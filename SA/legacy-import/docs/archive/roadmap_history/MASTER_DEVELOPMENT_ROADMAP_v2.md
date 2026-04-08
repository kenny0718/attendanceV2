# Master Development Roadmap v2

**系統名稱：** Attendance SaaS System  
**架構版本：** SA_MODULE_SPEC v1.9 (Platform-First Architecture)  
**文件版本：** 2.0  
**建立日期：** 2026-03-04  
**狀態：** ✅ APPROVED

---

## Document Authority

本文件為系統開發的**唯一權威路線圖**。

**整合來源：**
1. SA_MODULE_SPEC v1.9 - 架構規格
2. SA_REALITY_GAP_REPORT.md - 現況分析
3. REALITY_AUDIT_STATUS_INVENTORY.md - 實作盤點
4. ARCHITECTURE_FIX_DECISION.md - 修正決策
5. REALITY_AUDIT_NEXT_ACTIONS.md - 行動計畫

**v2 變更：**
- ✅ 移除週次時間線，改用 Work Package 流程
- ✅ 調整 Frontend 預估時間：8-10 週 → 3-4 週
- ✅ 將 Vehicles/Dispatch 移至 Phase 6: Extensions
- ✅ Frontend 啟動條件新增 Tenant Isolation 驗證

**變更控制：**
- 任何偏離本路線圖的開發需要架構審查
- 路線圖更新需要團隊共識
- 版本控制：每次重大變更產生新版本

---

## 1. Architecture Baseline

### 1.1 System Authority

**SA_MODULE_SPEC v1.9** 為系統架構的唯一權威規範。

**核心原則：**
- Platform-First Identity（使用者為全域身份）
- Same Database, Same Tables（A 架構）
- Tenant Isolation via company_id（租戶隔離）
- Feature Flags（功能分級）
- Scope → Tenant → Feature 驗證順序

**不可妥協的要求（P0）：**
1. 所有 Tenant Data 必須有 company_id
2. 所有查詢必須過濾 company_id
3. company_id 不得來自 request body
4. 8 個 Attendance 回歸測試必須通過
5. Backup/Restore 只操作單一 company
6. Tenant Isolation 驗證完成

---

### 1.2 Architecture Compliance

**當前符合度：** 75% (17/40 完全符合，11/40 部分符合)

**目標符合度：** > 95%

**達成條件：** Phase 1 完成後

---

## 2. Current System Status

### 2.1 Implemented Modules

| Module | 完成度 | 狀態 | 備註 |
|--------|--------|------|------|
| **tenants** | 100% | ✅ COMPLETE | Migration + CRUD + Entitlements |
| **auth** | 100% | ✅ COMPLETE | JWT + Platform-First v2 |
| **attendance** | 85% | 🚧 IN PROGRESS | 缺回歸測試 + Auth 轉換 |
| **notifications** | 80% | 🚧 IN PROGRESS | 缺 Auth 轉換 |
| **backup** | 100% | ✅ COMPLETE | Export/Restore 符合規範 |
| **audit** | 80% | 🚧 IN PROGRESS | 缺 Auth 轉換 |
| **customer_service** | 100% | ✅ COMPLETE | Scope + Assignments |

**總計：** 7/14 模組已實作（50%）

---

### 2.2 Missing Modules

| Module | 優先度 | 預計 Phase | 說明 |
|--------|--------|-----------|------|
| **locations** | P1 | Phase 2 | 打卡地點管理 |
| **approvals** | P1 | Phase 2 | 審批流程 |
| **leave** | P1 | Phase 2 | 請假管理 |
| **accrual** | P1 | Phase 2 | 假期額度 |
| **reporting** | P1 | Phase 2 | 報表模組 |
| **vehicles** | P2 | Phase 6 | 車輛管理（延後至擴充階段）|
| **dispatch** | P2 | Phase 6 | 派車管理（延後至擴充階段）|

**核心模組：** 5/12 未實作（Phase 2 目標）  
**擴充模組：** 2/14 未實作（Phase 6 目標）

---

## 3. Execution Phases

### Phase Overview

| Phase | 名稱 | 依賴關係 | 狀態 |
|-------|------|----------|------|
| **Phase 1** | Architecture Alignment | - | 🎯 NEXT |
| **Phase 2** | Core Backend Completion | Phase 1 | ⏳ PLANNED |
| **Phase 3** | SaaS Infrastructure | Phase 2 | ⏳ PLANNED |
| **Phase 4** | Frontend | Phase 1, 2, 3 | ⏳ PLANNED |
| **Phase 5** | External Integration | Phase 2, 3 | ⏳ PLANNED |
| **Phase 6** | Extensions | Phase 2, 3 | ⏳ OPTIONAL |

**關鍵路徑：** Phase 1 → Phase 2 → Phase 3 → Phase 4  
**平行開發：** Phase 5, 6 可與 Phase 4 平行進行

---
## Phase 1 — Architecture Alignment

**目標：** 將現有系統對齊 SA v1.9 規範

**完成標準：**
- SA 符合度 > 95%
- 8 個回歸測試通過
- 所有模組使用 JWT
- Scope 驗證統一實作
- Feature Gate 套用到所有 API
- Tenant Isolation 驗證完成

**依賴關係：** 無（可立即開始）

---

### Phase 1 Work Packages

#### WP-11-04B: Migration Chain 驗證

**Goal:** 確保 migration chain 可在 fresh DB 執行

**Priority:** P0（阻斷其他工作）

**Definition of Done:**
- [ ] Fresh DB 可執行 `alembic upgrade head`
- [ ] 所有 14 個 tables 正確建立
- [ ] `alembic heads` 只顯示一個 head
- [ ] 001 (舊版) 已刪除或標記為 deprecated

**依賴關係：** 無  
**後續 WP：** WP-11-05

---

#### WP-11-05: Attendance 回歸測試實作

**Goal:** 實作並通過 8 個 Attendance 核心回歸測試

**Priority:** P0（建立測試基線）

**Tests Required:**
1. NO_MATCH 未填原因 → 拒絕
2. NO_MATCH 有原因 → PENDING
3. APPROVED → 推導正確
4. PENDING 不參與推導與日結
5. 21:00 日結缺卡正確
6. approve pending → 該日重算
7. customer_service 未指派公司 → 403
8. OTP 一次性 + 強制改密碼

**Definition of Done:**
- [ ] 8/8 測試實作完成
- [ ] 8/8 測試通過
- [ ] 測試報告已產出

**依賴關係：** WP-11-04B  
**後續 WP：** WP-11-06

---

#### WP-11-06: Auth 轉換 Batch 1 (attendance)

**Goal:** 將 attendance 模組轉換為 JWT + Actor

**Priority:** P0（核心業務）

**Definition of Done:**
- [ ] attendance/api.py 所有 endpoints 使用 JWT
- [ ] Scope 驗證已加入
- [ ] Feature Gate 已加入
- [ ] 所有測試通過（包含回歸測試）
- [ ] Header-based auth 已移除

**依賴關係：** WP-11-05  
**後續 WP：** WP-12

---

#### WP-12: Auth 轉換 Batch 2-4 (audit, notifications, backup)

**Goal:** 將剩餘 3 個模組轉換為 JWT + Actor

**Priority:** P0

**Batch 順序：**
1. audit - 管理功能，中等風險
2. notifications - 低風險
3. backup - 管理功能，低頻使用

**Definition of Done:**
- [ ] 3 個模組全部使用 JWT
- [ ] Scope 驗證已加入
- [ ] Feature Gate 已加入
- [ ] 所有測試通過
- [ ] Header-based auth 完全移除

**依賴關係：** WP-11-06  
**後續 WP：** WP-13

---

#### WP-13: Tenant Isolation 驗證測試

**Goal:** 實作並通過 Tenant Isolation 驗證測試

**Priority:** P0（Frontend 啟動條件）

**Tests Required:**
1. A company 無法讀取 B company
2. 錯誤 company_id 寫入被拒
3. 無 membership → 403
4. Restore 不污染其他 company
5. customer_service 只能存取已指派公司

**Definition of Done:**
- [ ] 5/5 測試實作完成
- [ ] 5/5 測試通過
- [ ] 測試報告已產出

**依賴關係：** WP-12  
**後續 WP：** WP-14

---

#### WP-14: 測試 DB 重建與驗證

**Goal:** 確保測試 DB schema 與 migration 一致

**Priority:** P1

**Definition of Done:**
- [ ] 測試 DB schema 與 migration 一致
- [ ] 所有測試通過
- [ ] conftest.py 使用正確的 DB setup

**依賴關係：** WP-13  
**後續 WP：** WP-15

---

#### WP-15: API 文件補充

**Goal:** 為每個模組建立 API 文件

**Priority:** P2

**Files Affected:**
- `backend/app/modules/*/docs.md` (7 個模組)

**Definition of Done:**
- [ ] 7 個 docs.md 完成
- [ ] 文件包含業務邏輯說明
- [ ] 文件包含使用範例
- [ ] 文件包含錯誤碼說明

**依賴關係：** WP-14  
**後續 WP：** Phase 2

---

### Phase 1 Summary

**完成後狀態：**
- SA 符合度：75% → 95%
- Auth 統一：2/7 → 7/7 模組使用 JWT
- Scope 驗證：2/7 → 7/7 模組實作
- Feature Gate：0/7 → 7/7 模組實作
- 回歸測試：0/8 → 8/8 通過
- Tenant Isolation 測試：0/5 → 5/5 通過
- API 文件：0/7 → 7/7 完成

**Gate 5 狀態：** ✅ COMPLETE

**可啟動：** Phase 2, Phase 4 (Frontend)

---

## Phase 2 — Core Backend Completion

**目標：** 實作剩餘的核心業務模組

**完成標準：**
- 5 個核心模組全部實作
- 所有模組符合 SA v1.9 規範
- 所有模組有完整測試
- 所有模組有 API 文件

**依賴關係：** Phase 1

---

### Phase 2 Work Packages

#### WP-16: Reporting 模組

**Goal:** 實作報表模組（只讀彙總）

**Priority:** P1

**Key Features:**
- 出勤報表（日/週/月）
- 請假統計
- 加班統計
- 異常報表
- 匯出功能（CSV/Excel）

**SA v1.9 Compliance:**
- ✅ 只讀模組（不修改資料）
- ✅ 使用 JWT + Actor
- ✅ Scope 驗證
- ✅ Feature Gate
- ✅ Tenant Isolation

**Definition of Done:**
- [ ] 模組結構完整
- [ ] 所有報表 API 實作
- [ ] 測試覆蓋率 > 80%
- [ ] API 文件完成

**依賴關係：** Phase 1  
**後續 WP：** WP-17

---

#### WP-17: Locations 模組

**Goal:** 實作地點管理模組

**Priority:** P1

**Key Features:**
- 地點 CRUD
- 地理圍欄驗證
- 地點群組管理

**Definition of Done:**
- [ ] Migration 完成
- [ ] CRUD API 完成
- [ ] 地理圍欄邏輯實作
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-16  
**後續 WP：** WP-18

---

#### WP-18: Approvals 模組

**Goal:** 實作審批流程模組

**Priority:** P1

**Key Features:**
- 多層級審批流程
- 審批歷史記錄
- 審批通知
- 審批統計

**Definition of Done:**
- [ ] Migration 完成
- [ ] 審批引擎實作
- [ ] 與 attendance 整合
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-17  
**後續 WP：** WP-19

---

#### WP-19: Leave 模組

**Goal:** 實作請假管理模組

**Priority:** P1

**Key Features:**
- 請假類型管理
- 請假申請/審批
- 請假額度檢查
- 請假統計

**Definition of Done:**
- [ ] Migration 完成
- [ ] CRUD API 完成
- [ ] 與 approvals 整合
- [ ] 與 accrual 整合
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-18  
**後續 WP：** WP-20

---

#### WP-20: Accrual 模組

**Goal:** 實作假期額度管理模組

**Priority:** P1

**Key Features:**
- 額度累積規則
- 額度使用記錄
- 額度查詢
- 額度調整

**Definition of Done:**
- [ ] Migration 完成
- [ ] Ledger 實作
- [ ] 計算引擎實作
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-19  
**後續 WP：** Phase 3

---

### Phase 2 Summary

**完成後狀態：**
- 模組完成度：7/12 → 12/12 (100% 核心模組)
- 所有模組符合 SA v1.9
- 所有模組有完整測試
- 所有模組有 API 文件

**可啟動：** Phase 3, Phase 4 (如 Phase 1 已完成)

---

## Phase 3 — SaaS Infrastructure

**目標：** 強化 SaaS 基礎設施

**完成標準：**
- Tenant 管理完善
- Feature Tier 系統完整
- Backup/Restore 自動化

**依賴關係：** Phase 2

---

### Phase 3 Work Packages

#### WP-21: Tenant 管理強化

**Goal:** 強化 Tenant 管理功能

**Key Features:**
- Tenant 啟用/停用
- Tenant 配額限制（使用者數、儲存空間）
- Tenant 使用統計（API 呼叫、儲存使用）
- Tenant 設定管理

**Definition of Done:**
- [ ] 生命週期 API 完成
- [ ] 配額系統實作
- [ ] 統計 API 完成
- [ ] 測試覆蓋率 > 80%

**依賴關係：** Phase 2  
**後續 WP：** WP-22

---

#### WP-22: Feature Tier 系統

**Goal:** 實作功能分級系統

**Feature Tiers:**

**Free Tier:**
- attendance.punch_in_out
- attendance.basic_reports
- 最多 10 個使用者

**Pro Tier:**
- Free Tier +
- attendance.policy_engine
- attendance.split_shift
- leave.management
- 最多 100 個使用者

**Enterprise Tier:**
- Pro Tier +
- attendance.advanced_reports
- approvals.multi_level
- dispatch.management
- 無使用者限制

**Definition of Done:**
- [ ] Tier 定義完成
- [ ] Tier 管理 API 完成
- [ ] 升級/降級邏輯實作
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-21  
**後續 WP：** WP-23

---

#### WP-23: Backup/Restore 自動化

**Goal:** 實作自動化備份/還原

**Key Features:**
- 自動排程備份（每日/每週）
- 備份版本保留策略
- 備份完整性驗證
- 還原前預覽

**Definition of Done:**
- [ ] 排程系統實作
- [ ] 版本管理實作
- [ ] 驗證邏輯實作
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-22  
**後續 WP：** Phase 4, Phase 5

---

### Phase 3 Summary

**完成後狀態：**
- SaaS 基礎設施完整
- 可支援多租戶生產環境
- 可支援功能分級計費

**可啟動：** Phase 4 (如 Phase 1 已完成), Phase 5

---
## Phase 4 — Frontend

**目標：** 實作前端 UI

**完成標準：**
- Admin UI 完成
- Employee UI 完成
- Mobile responsive
- 所有 API 整合完成

**依賴關係：** Phase 1, Phase 2, Phase 3

---

### Frontend Start Criteria

**必須滿足以下條件才能開始 Frontend 開發：**

#### 技術條件
- [ ] Phase 1 完成（Architecture Alignment）
- [ ] Phase 2 完成（Core Backend Completion）
- [ ] Phase 3 完成（SaaS Infrastructure）
- [ ] 所有 API 有 OpenAPI 文件
- [ ] 所有 API 測試通過
- [ ] Backend 可穩定運行
- [ ] **Tenant Isolation 驗證完成**

#### API 穩定性
- [ ] API 合約凍結（不再變更 request/response schema）
- [ ] 錯誤碼統一且文件化
- [ ] API 效能測試通過

#### 開發環境
- [ ] Backend dev server 可穩定運行
- [ ] 測試資料可快速建立
- [ ] API mock server 可用（選擇性）

#### 文件完整性
- [ ] 所有 API 有使用範例
- [ ] 所有業務流程有文件
- [ ] UI/UX 設計稿完成

---

### Phase 4 Work Packages

#### WP-24: Frontend 架構建立

**Goal:** 建立 Frontend 專案架構

**Recommended Stack:**
- Framework: React + TypeScript
- State Management: Redux Toolkit / Zustand
- UI Library: Material-UI / Ant Design
- API Client: Axios + React Query
- Routing: React Router
- Form: React Hook Form + Zod

**Definition of Done:**
- [ ] 專案建立完成
- [ ] 開發環境可運行
- [ ] API client 整合完成
- [ ] 基礎元件庫建立

**依賴關係：** Phase 1, 2, 3  
**後續 WP：** WP-25

---

#### WP-25: Admin UI - 核心管理介面

**Goal:** 實作 Admin 核心管理介面

**Scope:**
- ✅ Tenant 管理（列表/建立/編輯/啟用停用/配額）
- ✅ 使用者管理（列表/建立/編輯/角色指派）
- ✅ Feature Flags 管理
- ✅ Entitlements 設定
- ✅ Tier 管理

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] UI 測試通過

**依賴關係：** WP-24  
**後續 WP：** WP-26

---

#### WP-26: Employee UI - 核心功能介面

**Goal:** 實作員工核心功能介面

**Scope:**
- ✅ 打卡功能（Punch In/Out/當前狀態/歷史/地理位置驗證）
- ✅ 請假功能（申請/歷史/額度查詢/審批狀態）
- ✅ 報表功能（個人出勤/請假統計/加班統計/匯出）

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] 地理位置功能正常
- [ ] Mobile responsive
- [ ] 匯出功能正常

**依賴關係：** WP-25  
**後續 WP：** Phase 5

---

### Phase 4 Summary

**完成後狀態：**
- Admin UI 完整
- Employee UI 完整
- Mobile responsive
- 可進行 UAT

**預估時間：** 3-4 週（相較 v1 的 8-10 週大幅縮短）

---

## Phase 5 — External Integration

**目標：** 實作外部系統整合

**完成標準：**
- 裝置整合完成
- 薪資匯出完成
- Webhook 系統完成

**依賴關係：** Phase 2, Phase 3

---

### Phase 5 Work Packages

#### WP-27: 裝置整合

**Goal:** 整合打卡裝置

**Scope:**
- ✅ 裝置 API 設計
- ✅ 裝置註冊/配對
- ✅ 裝置資料同步
- ✅ 裝置管理介面

**Definition of Done:**
- [ ] 裝置 API 完成
- [ ] 配對流程實作
- [ ] 同步邏輯實作
- [ ] 測試覆蓋率 > 80%

**依賴關係：** Phase 2, 3  
**後續 WP：** WP-28

---

#### WP-28: 薪資匯出

**Goal:** 實作薪資系統匯出

**Scope:**
- ✅ 薪資資料彙總
- ✅ 匯出格式定義
- ✅ 匯出 API
- ✅ 匯出排程

**Definition of Done:**
- [ ] 匯出 API 完成
- [ ] 格式支援（CSV/Excel）
- [ ] 排程系統實作
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-27  
**後續 WP：** WP-29

---

#### WP-29: Webhook 系統

**Goal:** 實作 Webhook 通知系統

**Key Events:**
- attendance.punch_in
- attendance.punch_out
- leave.approved
- leave.rejected

**Definition of Done:**
- [ ] Webhook 管理 API 完成
- [ ] 發送邏輯實作
- [ ] 重試機制實作
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-28  
**後續 WP：** Production

---

### Phase 5 Summary

**完成後狀態：**
- 可整合外部裝置
- 可匯出薪資資料
- 可接收 Webhook 通知

---

## Phase 6 — Extensions (Optional)

**目標：** 實作擴充功能模組

**完成標準：**
- Vehicles 模組完成
- Dispatch 模組完成

**依賴關係：** Phase 2, Phase 3

**優先度：** P2（可延後）

---

### Phase 6 Work Packages

#### WP-30: Vehicles 模組

**Goal:** 實作車輛管理模組

**Priority:** P2

**Scope:**
- ✅ 建立 vehicles 模組
- ✅ 實作車輛 CRUD
- ⛔ 不實作派車邏輯（WP-31）

**Definition of Done:**
- [ ] Migration 完成
- [ ] CRUD API 完成
- [ ] 測試覆蓋率 > 80%

**依賴關係：** Phase 2, 3  
**後續 WP：** WP-31

---

#### WP-31: Dispatch 模組

**Goal:** 實作派車管理模組

**Priority:** P2

**Key Features:**
- 派車申請/審批
- 車輛使用記錄
- 派車統計

**Definition of Done:**
- [ ] Migration 完成
- [ ] 派車邏輯實作
- [ ] 與 attendance 整合
- [ ] 測試覆蓋率 > 80%

**依賴關係：** WP-30  
**後續 WP：** -

---

### Phase 6 Summary

**完成後狀態：**
- 模組完成度：12/14 → 14/14 (100%)
- 系統功能完整

**備註：** 此階段為選擇性，可依業務需求決定是否實作

---

## 4. Production Readiness Checklist

### 4.1 功能完整性

- [ ] Phase 1-3 完成（必須）
- [ ] Phase 4 完成（必須）
- [ ] Phase 5 完成（必須）
- [ ] Phase 6 完成（選擇性）
- [ ] 所有核心模組實作
- [ ] 所有 API 測試通過
- [ ] 所有回歸測試通過

---

### 4.2 效能指標

- [ ] API 回應時間 < 200ms (P95)
- [ ] 資料庫查詢優化
- [ ] 索引建立完整
- [ ] 快取策略實作

---

### 4.3 安全性

- [ ] JWT 驗證完整
- [ ] Scope 驗證統一
- [ ] Feature Gate 實作
- [ ] SQL Injection 防護
- [ ] XSS 防護
- [ ] CSRF 防護
- [ ] Rate Limiting

---

### 4.4 可靠性

- [ ] 錯誤處理完整
- [ ] 日誌記錄完整
- [ ] 監控系統建立
- [ ] 告警機制建立
- [ ] Backup 自動化
- [ ] Disaster Recovery 計畫

---

### 4.5 可維護性

- [ ] 程式碼文件完整
- [ ] API 文件完整
- [ ] 部署文件完整
- [ ] 運維手冊完整
- [ ] 測試覆蓋率 > 80%

---

### 4.6 合規性

- [ ] SA v1.9 符合度 > 95%
- [ ] Tenant Isolation 驗證
- [ ] 資料隱私保護
- [ ] Audit Log 完整

---

## 5. Risk Management

### 5.1 技術風險

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| 回歸測試失敗 | 中 | 高 | 預留 buffer time，準備修正計畫 |
| Auth 轉換破壞功能 | 中 | 高 | 批次轉換，保留 fallback |
| Migration 失敗 | 低 | 高 | 先驗證，再執行 |
| 效能問題 | 中 | 中 | 效能測試，優化查詢 |
| 整合問題 | 中 | 中 | 早期整合測試 |
| Tenant Isolation 漏洞 | 低 | 高 | 完整測試驗證 |

---

### 5.2 時程風險

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| Phase 1 延誤 | 中 | 高 | 預留 buffer，調整優先順序 |
| Phase 2 延誤 | 中 | 中 | 分批交付，降低風險 |
| 資源不足 | 低 | 高 | 提前規劃，外部支援 |
| Frontend 低估 | 中 | 中 | 簡化 UI，聚焦核心功能 |

---

## 6. Success Metrics

### 6.1 開發指標

| 指標 | 目標 | 測量方式 |
|------|------|----------|
| SA 符合度 | > 95% | GAP 分析 |
| 測試覆蓋率 | > 80% | pytest --cov |
| API 文件完整度 | 100% | 人工檢查 |
| 程式碼品質 | A 級 | SonarQube |

---

### 6.2 效能指標

| 指標 | 目標 | 測量方式 |
|------|------|----------|
| API 回應時間 (P95) | < 200ms | APM 工具 |
| 資料庫查詢時間 (P95) | < 50ms | DB 監控 |
| 並發使用者 | > 1000 | 壓力測試 |

---

### 6.3 業務指標

| 指標 | 目標 | 測量方式 |
|------|------|----------|
| 系統可用性 | > 99.9% | 監控系統 |
| 錯誤率 | < 0.1% | 日誌分析 |
| 使用者滿意度 | > 4.5/5 | 問卷調查 |

---

## 7. Work Package Flow

### 7.1 Critical Path

```
WP-11-04B (Migration 驗證)
    ↓
WP-11-05 (回歸測試)
    ↓
WP-11-06 (Auth 轉換 Batch 1)
    ↓
WP-12 (Auth 轉換 Batch 2-4)
    ↓
WP-13 (Tenant Isolation 驗證)
    ↓
WP-14 (測試 DB 重建)
    ↓
WP-15 (API 文件)
    ↓
[Phase 1 Complete] ✅
    ↓
WP-16 (Reporting) → WP-17 (Locations) → WP-18 (Approvals) → WP-19 (Leave) → WP-20 (Accrual)
    ↓
[Phase 2 Complete] ✅
    ↓
WP-21 (Tenant 管理) → WP-22 (Feature Tier) → WP-23 (Backup 自動化)
    ↓
[Phase 3 Complete] ✅
    ↓
WP-24 (Frontend 架構) → WP-25 (Admin UI) → WP-26 (Employee UI)
    ↓
[Phase 4 Complete] ✅
    ↓
WP-27 (裝置整合) → WP-28 (薪資匯出) → WP-29 (Webhook)
    ↓
[Phase 5 Complete] ✅
    ↓
Production Ready 🚀
```

---

### 7.2 Parallel Tracks

**Phase 4 (Frontend) 可與 Phase 5 (External Integration) 平行開發**

條件：Phase 1, 2, 3 完成

```
Phase 1-3 Complete
    ↓
    ├─→ Phase 4 (Frontend)
    │       ↓
    │   [3-4 週]
    │
    └─→ Phase 5 (External Integration)
            ↓
        [可平行進行]
```

**Phase 6 (Extensions) 可獨立進行**

條件：Phase 2, 3 完成

---

### 7.3 Milestones

| Milestone | 驗收標準 | 可啟動階段 |
|-----------|---------|-----------|
| **M1: Gate 5 完成** | Phase 1 完成，SA 符合度 > 95% | Phase 2, Phase 4 |
| **M2: Backend 完成** | Phase 2 完成，所有核心模組實作 | Phase 3, Phase 4 |
| **M3: SaaS 就緒** | Phase 3 完成，可支援多租戶 | Phase 4, Phase 5 |
| **M4: Frontend 完成** | Phase 4 完成，可進行 UAT | UAT |
| **M5: 生產就緒** | Phase 5 完成，通過所有檢查 | Production |

---

## 8. Approval & Sign-off

**路線圖狀態：** ✅ APPROVED

**核准者：**
- 架構師：_________________
- 技術負責人：_________________
- 產品負責人：_________________
- 專案經理：_________________

**核准日期：** 2026-03-04

**下一次審查：** Phase 1 完成後

---

## 9. Document Control

**文件版本：** 2.0  
**建立日期：** 2026-03-04  
**最後更新：** 2026-03-04  
**維護者：** 架構團隊

**變更歷史：**
- v1.0 (2026-03-04): 初版建立
- v2.0 (2026-03-04): 架構審查後精煉版
  - 移除週次時間線
  - Frontend 時間調整為 3-4 週
  - Vehicles/Dispatch 移至 Phase 6
  - 新增 Tenant Isolation 驗證要求

**相關文件：**
- SA_MODULE_SPEC v1.9
- SA_REALITY_GAP_REPORT.md
- ARCHITECTURE_FIX_DECISION.md
- GATE_PROGRESS_TRACKER.md

---

**END OF ROADMAP v2**
