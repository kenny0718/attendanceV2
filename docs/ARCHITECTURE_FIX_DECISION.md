# Architecture Fix Decision（架構修正決策）

**審查日期：** 2026-03-04  
**審查者：** 架構團隊  
**提案來源：** SA_REALITY_GAP_REPORT.md  
**決策狀態：** ✅ APPROVED with modifications

---

## Executive Summary

**提案審查結果：** 部分接受，需調整優先順序與執行策略

**關鍵決策：**
1. ✅ Auth 轉換策略：接受，但調整順序
2. ⚠️ 回歸測試優先度：提升為 P0（不同意 P1）
3. ✅ Scope 驗證：接受，但需同步實作
4. ⚠️ API 文件：接受自動生成，但需補充
5. ⚠️ Migration Chain：不同意 clean rebuild，建議驗證優先

**修正後的執行順序：**
1. Migration Chain 驗證（P0，阻斷其他工作）
2. 回歸測試實作（P0，驗證核心邏輯）
3. Auth 轉換 + Scope 驗證（P0，安全性）
4. Feature Gate 套用（P1）
5. API 文件補充（P2）

---

## 1. Proposal Review

### 提案 1: Auth Transition

**原提案：**
```
Strategy: Batch migration from Header to JWT Actor
Modules: notifications → backup → audit → attendance
Compatibility: temporary Header support for internal APIs
```

**技術評估：**

#### ✅ 優點
1. 批次轉換降低風險（相比 Big Bang）
2. 保留 Header 作為 fallback 提供安全網
3. 模組順序合理（低風險到高風險）

#### ⚠️ 風險
1. **順序問題：** attendance 是核心業務，應該優先而非最後
2. **相容性成本：** 維護兩套機制增加複雜度
3. **測試成本：** 每個模組都需要更新測試
4. **時間窗口：** Header fallback 保留多久？

#### 💡 建議改進

**調整轉換順序：**
```
Batch 1: attendance（核心業務，優先驗證）
Batch 2: audit（管理功能，中等風險）
Batch 3: notifications（低風險）
Batch 4: backup（管理功能，低頻使用）
```

**理由：**
- attendance 是核心業務邏輯，越早轉換越早發現問題
- audit 需要記錄操作者，應該有 user_id
- notifications 和 backup 使用頻率低，可以最後轉換

**相容性策略：**
```
Week 1-2: 實作 Batch 1 (attendance)
  - 同時支援 Header + JWT
  - 測試兩種方式都能工作
  
Week 3: 實作 Batch 2-4
  - 逐步移除 Header 支援
  
Week 4: 完全移除 Header
  - 只保留 auth login endpoint 不需要 auth
```

**決策：** ✅ 接受，但調整順序與時程

---

### 提案 2: Attendance Regression Tests

**原提案：**
```
Priority: P1
Timing: after WP-11-04B
```

**技術評估：**

#### ❌ 不同意 P1 優先度

**理由：**
1. **SA v1.9 明確要求：** 8 個回歸測試是 P0
2. **核心業務邏輯：** 沒有測試無法驗證正確性
3. **Auth 轉換風險：** 轉換前應該先有測試保護
4. **Gate 5 完成標準：** 回歸測試是必要條件

**實際風險：**
- 如果先做 Auth 轉換，沒有測試保護，可能破壞業務邏輯
- 如果測試發現 bug，需要回頭修正，浪費時間
- 沒有測試，無法驗證 policy_engine.py (24KB) 是否正確

#### 💡 建議改進

**提升為 P0，調整時機：**
```
Timing: BEFORE Auth transition
Reason: 
1. 建立測試基線（確保現有邏輯正確）
2. 保護 Auth 轉換（防止破壞業務邏輯）
3. 符合 SA v1.9 要求
```

**執行策略：**
```
Phase 1: 實作 8 個測試（1 天）
  - 如果測試失敗 → 修正業務邏輯
  - 如果測試通過 → 建立保護基線
  
Phase 2: Auth 轉換（有測試保護）
  - 每次轉換後執行回歸測試
  - 確保業務邏輯不被破壞
```

**決策：** ⚠️ 不接受 P1，提升為 P0，調整時機

---

### 提案 3: Scope Validation

**原提案：**
```
Implement assert_company_scope() at API and repo layer
Feature Gates postponed
```

**技術評估：**

#### ✅ 優點
1. Scope checker 已實作（`scope.py`）
2. API 層驗證防止越權
3. Repo 層驗證提供雙重保護

#### ⚠️ 風險
1. **Feature Gate 延後：** 為什麼延後？基礎設施已完成
2. **實作成本：** 需要修改所有 API endpoints
3. **測試成本：** 需要測試 Scope 驗證邏輯

#### 💡 建議改進

**不要延後 Feature Gate：**
```
Reason:
1. Feature Gate 基礎設施已完成（feature_service.py）
2. 實作成本低（只需加一行 assert_feature_enabled）
3. 與 Scope 驗證同時實作，避免二次修改
```

**實作策略：**
```
在 Auth 轉換時同步加入：
1. Scope Validation
2. Tenant Isolation（repo 自動處理）
3. Feature Gate

範例：
@router.post("/api/attendance/punch-in")
def punch_in(actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)):
    # 1. Scope (已包含在 get_current_actor)
    # 2. Tenant Isolation (repo 自動處理)
    # 3. Feature Gate
    assert_feature_enabled(actor.company_id, "attendance.punch_in_out", db)
    
    return service.punch_in(...)
```

**決策：** ✅ 接受 Scope 驗證，但不延後 Feature Gate

---

### 提案 4: API Documentation

**原提案：**
```
Use FastAPI automatic OpenAPI generation
No manual docs yet
```

**技術評估：**

#### ✅ 優點
1. FastAPI 自動生成 OpenAPI/Swagger
2. 減少手動維護成本
3. 與程式碼同步

#### ⚠️ 風險
1. **SA v1.9 要求：** 每個模組有 `docs.md`
2. **自動生成限制：** 無法包含業務邏輯說明
3. **開發者體驗：** 需要啟動 server 才能看文件

#### 💡 建議改進

**混合策略：**
```
1. 使用 FastAPI 自動生成（基礎）
   - Endpoint 列表
   - Request/Response schema
   - 錯誤碼

2. 補充 docs.md（業務邏輯）
   - 業務流程說明
   - 使用範例
   - 常見問題
   - 與其他模組的互動
```

**範例 docs.md 結構：**
```markdown
# Attendance Module API Documentation

## Overview
打卡/出勤管理模組

## Business Logic
- Punch In/Out 流程
- Policy Engine 規則
- Session 管理

## API Endpoints
詳見 OpenAPI: http://localhost:8000/docs

## Examples
### Punch In
```bash
curl -X POST http://localhost:8000/api/attendance/punch-in \
  -H "Authorization: Bearer <token>"
```

## Integration
- 發布事件：attendance.approved
- 訂閱事件：無
```

**決策：** ✅ 接受自動生成，但需補充 docs.md

---

### 提案 5: Migration Chain

**原提案：**
```
Strategy: Clean rebuild instead of manual fixes
```

**技術評估：**

#### ❌ 不同意 Clean Rebuild

**理由：**
1. **風險過高：** 可能破壞現有 DB
2. **不必要：** 001b 已修正問題
3. **時間成本：** Clean rebuild 需要重新測試所有功能

**實際需求：**
- 只需要驗證 001b 能在 fresh DB 執行
- 不需要重建整個 migration chain

#### 💡 建議改進

**驗證優先策略：**
```
Phase 1: 驗證現有 DB 狀態（30 分鐘）
  - 檢查 alembic_version
  - 檢查 tables 是否存在
  - 確認 001 vs 001b 狀態

Phase 2: Fresh DB 測試（30 分鐘）
  - 建立全新測試 DB
  - 執行 alembic upgrade head
  - 驗證所有 tables 正確建立

Phase 3: 清理（如果需要）（30 分鐘）
  - 刪除 001 (舊版) 檔案
  - 更新文件
```

**不需要 Clean Rebuild 的原因：**
- 001b 已經是正確的 migration
- wp_11_04a 已指向 001b
- Migration chain 是線性的（無循環）

**決策：** ⚠️ 不接受 Clean Rebuild，改為驗證策略

---

## 2. Risk Assessment

### 2.1 提案風險矩陣

| 提案 | 原風險 | 修正後風險 | 風險降低措施 |
|------|--------|------------|--------------|
| Auth 轉換 | 🟡 中 | 🟢 低 | 調整順序，attendance 優先 |
| 回歸測試 | 🔴 高 | 🟢 低 | 提升為 P0，Auth 轉換前執行 |
| Scope 驗證 | 🟡 中 | 🟢 低 | 與 Auth 轉換同步，避免二次修改 |
| API 文件 | 🟢 低 | 🟢 低 | 補充 docs.md |
| Migration | 🔴 高 | 🟢 低 | 改為驗證，不做 rebuild |

---

### 2.2 新增風險

#### 風險 1: 回歸測試可能失敗

**機率：** 中  
**影響：** 高  
**應變：**
- 如果測試失敗 → 修正業務邏輯（可能需要 1-2 天）
- 如果邏輯無法修正 → 調整測試規格（需要產品確認）
- 如果影響太大 → 記錄為 known issue，未來修正

**建議：** 預留 buffer time（+1 天）

---

#### 風險 2: Auth 轉換破壞現有功能

**機率：** 中  
**影響：** 高  
**應變：**
- 每個 batch 轉換後執行完整測試
- 保留 Header fallback 直到所有測試通過
- Git commit 每個 batch，方便 rollback

**建議：** 每個 batch 獨立驗證

---

#### 風險 3: Feature Gate 影響現有功能

**機率：** 低  
**影響：** 中  
**應變：**
- 預設所有 feature 為 enabled
- 逐步測試 disabled 情況
- 提供 bypass 機制（super_admin）

**建議：** 先實作，預設全開

---

## 3. Modified Priorities

### 3.1 原提案優先順序

```
1. Auth Transition (P0)
2. Attendance Regression Tests (P1)
3. Scope Validation (P0)
4. API Documentation (P2)
5. Migration Chain (P1)
```

---

### 3.2 修正後優先順序

```
P0（本週必須完成）：
1. Migration Chain 驗證（1 小時）← 阻斷其他工作
2. 回歸測試實作（1 天）← 建立保護基線
3. Auth 轉換 Batch 1: attendance（1 天）← 核心業務
4. Scope 驗證 + Feature Gate（包含在 Auth 轉換中）

P1（下週完成）：
5. Auth 轉換 Batch 2-4（1-2 天）
6. 測試 DB 重建（0.5 天）

P2（未來兩週）：
7. API 文件補充（0.5 天）
8. 文件同步更新（0.5 天）
```

---

### 3.3 優先順序調整理由

#### 為什麼 Migration 驗證是第一優先？
- **阻斷性：** 如果 migration 有問題，無法建立測試環境
- **時間短：** 只需 1 小時
- **風險低：** 只是驗證，不修改

#### 為什麼回歸測試提升為 P0？
- **SA v1.9 要求：** 明確定義為 P0
- **保護作用：** Auth 轉換前需要測試保護
- **驗證邏輯：** 確保 policy_engine 正確

#### 為什麼 attendance 優先轉換？
- **核心業務：** 越早轉換越早發現問題
- **測試覆蓋：** attendance 有最多測試
- **影響範圍：** 如果 attendance 有問題，其他模組也會有

#### 為什麼不延後 Feature Gate？
- **實作成本低：** 只需加一行程式碼
- **避免二次修改：** 與 Auth 轉換同步
- **基礎設施完成：** 不需要額外開發

---

## 4. Recommended Execution Order

### Week 1: 基礎驗證與測試

#### Day 1 (Monday)
**AM: Migration Chain 驗證**
- [ ] 檢查實際 DB 狀態
- [ ] Fresh DB 測試
- [ ] 清理 001 (如果需要)
- [ ] 更新文件

**PM: 回歸測試實作 (Part 1)**
- [ ] 實作 Test 1-4
- [ ] 執行測試
- [ ] 修正失敗（如果有）

**產出：**
- Migration chain 可在 fresh DB 執行
- 4/8 回歸測試通過

---

#### Day 2 (Tuesday)
**AM: 回歸測試實作 (Part 2)**
- [ ] 實作 Test 5-8
- [ ] 執行測試
- [ ] 修正失敗（如果有）

**PM: 回歸測試驗證**
- [ ] 執行完整測試套件
- [ ] 確認 8/8 通過
- [ ] 建立測試報告

**產出：**
- 8/8 回歸測試通過
- 測試基線建立

---

#### Day 3 (Wednesday)
**Auth 轉換 Batch 1: attendance**
- [ ] 修改 attendance/api.py 使用 get_current_actor
- [ ] 加入 Scope 驗證
- [ ] 加入 Feature Gate
- [ ] 更新測試使用 JWT
- [ ] 執行回歸測試（確保不破壞）

**產出：**
- attendance 模組使用 JWT
- 所有測試通過（包含回歸測試）

---

#### Day 4 (Thursday)
**Auth 轉換 Batch 2: audit**
- [ ] 修改 audit/api.py
- [ ] 加入 Scope + Feature Gate
- [ ] 更新測試
- [ ] 執行測試

**產出：**
- audit 模組使用 JWT

---

#### Day 5 (Friday)
**Auth 轉換 Batch 3-4: notifications + backup**
- [ ] 修改 notifications/api.py
- [ ] 修改 backup/api.py
- [ ] 更新測試
- [ ] 執行完整測試套件

**產出：**
- 所有模組使用 JWT
- Header 支援移除

---

### Week 2: 清理與文件

#### Day 1 (Monday)
**測試 DB 重建**
- [ ] 比對測試 DB 與 fresh DB schema
- [ ] 重建測試 DB（如果需要）
- [ ] 執行完整測試驗證

**產出：**
- 測試 DB 與 migration 一致

---

#### Day 2 (Tuesday)
**API 文件補充**
- [ ] 為 7 個模組建立 docs.md
- [ ] 記錄業務邏輯
- [ ] 補充使用範例

**產出：**
- 7 個 docs.md 完成

---

#### Day 3 (Wednesday)
**文件同步更新**
- [ ] 更新 STATUS_MATRIX.md
- [ ] 更新 GATE_PROGRESS_TRACKER.md
- [ ] 更新 DEVELOPMENT_ORDER.md

**產出：**
- 文件與實作一致

---

### Week 2: 驗收

#### Day 4-5 (Thursday-Friday)
**完整驗收**
- [ ] 執行所有測試
- [ ] 驗證 SA v1.9 符合度
- [ ] 產出 Gate 5 完成報告

**產出：**
- Gate 5 完成
- SA 符合度 > 90%

---

## 5. Success Criteria

### 5.1 技術指標

| 指標 | 目標 | 驗證方式 |
|------|------|----------|
| Migration chain | Fresh DB 可執行 | `alembic upgrade head` 成功 |
| 回歸測試 | 8/8 通過 | `pytest test_regression.py` 全綠 |
| Auth 統一 | 7/7 模組用 JWT | 檢查所有 api.py |
| Scope 驗證 | 7/7 模組實作 | 檢查所有 api.py |
| Feature Gate | 7/7 模組實作 | 檢查所有 api.py |
| 測試通過率 | 100% | `pytest -v` 全綠 |
| SA 符合度 | > 90% | 重新執行 GAP 分析 |

---

### 5.2 業務指標

| 指標 | 目標 | 驗證方式 |
|------|------|----------|
| 核心業務邏輯 | 不被破壞 | 回歸測試通過 |
| API 行為 | 一致 | 所有 API 用相同 auth |
| 安全性 | 提升 | Scope 驗證防止越權 |
| 功能分級 | 可用 | Feature Gate 實作 |

---

## 6. Rollback Plan

### 6.1 Migration 驗證失敗

**如果 fresh DB 無法執行：**
- [ ] 不繼續其他工作
- [ ] 修正 migration 問題
- [ ] 重新驗證

**預估時間：** +0.5 天

---

### 6.2 回歸測試失敗

**如果測試發現 bug：**
- [ ] 評估 bug 嚴重性
- [ ] 如果嚴重：修正業務邏輯（+1-2 天）
- [ ] 如果不嚴重：記錄為 known issue

**預估時間：** +1-2 天

---

### 6.3 Auth 轉換失敗

**如果轉換破壞功能：**
- [ ] Git revert 該 batch
- [ ] 保留 Header 支援
- [ ] 分析失敗原因
- [ ] 修正後重新轉換

**預估時間：** +0.5 天 per batch

---

## 7. Final Decision

### 7.1 接受的提案

✅ **Auth 轉換策略**（調整順序）
✅ **Scope 驗證**（不延後 Feature Gate）
✅ **API 文件**（補充 docs.md）

---

### 7.2 修正的提案

⚠️ **回歸測試優先度**（P1 → P0）
⚠️ **Migration 策略**（Clean Rebuild → 驗證）

---

### 7.3 執行時程

**總預估時間：** 10 天（2 週）

**關鍵里程碑：**
- Day 1: Migration 驗證完成
- Day 2: 回歸測試完成
- Day 5: Auth 轉換完成
- Day 10: Gate 5 完成

---

### 7.4 風險緩衝

**預留 buffer：** +2-3 天

**原因：**
- 回歸測試可能發現 bug
- Auth 轉換可能需要調整
- 測試更新可能需要時間

**實際時程：** 2-3 週

---

## 8. Approval

**技術審查：** ✅ APPROVED  
**架構審查：** ✅ APPROVED with modifications  
**產品審查：** ⏳ PENDING

**下一步：**
1. 產品確認回歸測試規格
2. 開始執行 Week 1 Day 1
3. 每日 standup 追蹤進度

---

**文件版本：** 1.0  
**決策日期：** 2026-03-04  
**生效日期：** 2026-03-05  
**審查者：** Claude Opus 4.6 (Cursor AI)
