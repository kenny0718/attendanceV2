# WP-11-13 Step 3A - 部署驗證報告

**票號**: WP-11-13 Step 3A  
**標題**: Frontend Integration for BREAK_OUT Location Policy - Deployment Validation  
**日期**: 2026-03-08  
**環境**: Test / Staging / Production

---

## 執行摘要

本文件提供 WP-11-13 Step 3A 的部署驗證清單和程序。

**目的**: 確保 Step 3A 可以安全部署到各個環境

---

## 部署前檢查清單

### 1. 程式碼準備 ✅

- [✅] Step 2 後端程式碼已合併
- [✅] Step 3A 前端程式碼已完成
- [✅] 所有檔案已提交到版本控制
- [✅] 程式碼審查已通過
- [ ] Pull Request 已建立並審核

---

### 2. 資料庫準備

- [ ] Migration 008 已準備
- [ ] Migration 在測試環境已驗證
- [ ] Rollback script 已準備（如需要）
- [ ] 資料庫備份已完成

**Migration 檔案**: `backend/alembic/versions/008_wp_11_13_create_allowed_locations.py`

**Migration 內容**:
- 建立 `allowed_locations` 表
- 在 `attendance_punches` 表新增 `location_id` 欄位
- 建立必要的索引和外鍵約束

---

### 3. 後端準備

- [✅] `location_policy_service.py` 已完成
- [✅] `admin_location_api.py` 已完成
- [✅] `api.py` BREAK_OUT endpoint 已更新
- [✅] `models.py` 已更新
- [ ] 後端測試已通過
- [ ] 後端 build 成功

---

### 4. 前端準備

- [✅] `Home.vue` 錯誤處理已更新
- [✅] `useLocation.js` composable 已存在
- [✅] `attendance.js` store 已存在
- [✅] `attendance.js` API 已存在
- [ ] 前端測試已通過
- [ ] 前端 build 成功
- [ ] 無 linting 錯誤

---

### 5. 文件準備 ✅

- [✅] 實作報告已完成
- [✅] QA 報告已完成
- [✅] 部署驗證文件已完成（本文件）
- [✅] NEXT_WP_TICKET.md 已更新

---

## 部署程序

### 階段 1: 測試環境部署

#### 1.1 資料庫 Migration

```bash
# 1. 備份資料庫
pg_dump attendance_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 執行 migration
cd backend
alembic upgrade head

# 3. 驗證 migration
alembic current
# 應該顯示: 008 (head)

# 4. 檢查表結構
psql attendance_db -c "\d allowed_locations"
psql attendance_db -c "\d attendance_punches"
```

**預期結果**:
- ✅ `allowed_locations` 表已建立
- ✅ `attendance_punches.location_id` 欄位已新增
- ✅ 索引和外鍵約束已建立

---

#### 1.2 後端部署

```bash
# 1. 拉取最新程式碼
git pull origin main

# 2. 安裝依賴（如有更新）
cd backend
pip install -r requirements.txt

# 3. 重啟後端服務
systemctl restart attendance-backend
# 或
supervisorctl restart attendance-backend

# 4. 檢查服務狀態
systemctl status attendance-backend
# 或
supervisorctl status attendance-backend

# 5. 檢查日誌
tail -f /var/log/attendance-backend/error.log
```

**預期結果**:
- ✅ 服務啟動成功
- ✅ 無錯誤日誌
- ✅ API 端點可訪問

---

#### 1.3 前端部署

```bash
# 1. 拉取最新程式碼
git pull origin main

# 2. 安裝依賴（如有更新）
cd frontend
npm install

# 3. Build
npm run build

# 4. 部署到 web server
cp -r dist/* /var/www/attendance-frontend/

# 5. 重啟 web server（如需要）
systemctl restart nginx
```

**預期結果**:
- ✅ Build 成功
- ✅ 無 linting 錯誤
- ✅ 前端可訪問

---

#### 1.4 煙霧測試（Smoke Test）

```bash
# 1. 檢查後端健康狀態
curl http://test-api.example.com/health

# 2. 檢查前端可訪問
curl http://test.example.com

# 3. 檢查 API 端點
curl -X GET http://test-api.example.com/v1/attendance/current-status \
  -H "Authorization: Bearer $TOKEN"
```

**預期結果**:
- ✅ 所有端點回應正常
- ✅ 無 500 錯誤

---

### 階段 2: Manual QA 執行

參考 `WP-11-13_STEP3A_QA_REPORT.md` 中的測試案例。

**必須執行的測試**:
1. [ ] Test Case 1: 無 Policy - 正常打卡
2. [ ] Test Case 2: 有 Policy + 在範圍內
3. [ ] Test Case 3: 有 Policy + 超出範圍
4. [ ] Test Case 4: GPS 權限被拒絕
5. [ ] Test Case 5: GPS 超時
6. [ ] Test Case 6: GPS 無法取得
7. [ ] Test Case 7: PC 裝置（無 GPS）
8. [ ] Test Case 8: 其他流程不受影響

---

### 階段 3: 問題修正（如需要）

如果 Manual QA 發現問題：

1. **記錄問題**
   - 問題描述
   - 重現步驟
   - 預期 vs 實際結果
   - 嚴重程度

2. **評估影響**
   - 是否為 blocker？
   - 是否影響其他功能？
   - 是否需要 rollback？

3. **修正問題**
   - 建立 hotfix branch
   - 修正程式碼
   - 重新測試
   - 合併並重新部署

4. **更新文件**
   - 記錄問題和修正
   - 更新 QA 報告

---

### 階段 4: Staging 環境部署

重複階段 1 的步驟，但部署到 Staging 環境。

**額外檢查**:
- [ ] 使用 production-like 資料
- [ ] 測試效能
- [ ] 測試負載
- [ ] 測試安全性

---

### 階段 5: Production 部署

#### 5.1 部署前最終檢查

- [ ] 所有測試已通過
- [ ] Staging 環境運行穩定
- [ ] 部署計劃已審核
- [ ] Rollback 計劃已準備
- [ ] 團隊已通知
- [ ] 使用者已通知（如需要）

---

#### 5.2 部署時間窗口

**建議時間**: 非營業時間或低流量時段

**預估時間**:
- Migration: 5-10 分鐘
- 後端部署: 5 分鐘
- 前端部署: 5 分鐘
- 驗證: 10 分鐘
- **總計**: 約 30 分鐘

---

#### 5.3 部署步驟

與階段 1 相同，但需要：

1. **更謹慎的驗證**
   - 每個步驟都要驗證
   - 檢查日誌
   - 監控系統指標

2. **即時監控**
   - 錯誤率
   - 回應時間
   - 使用者活動

3. **準備 Rollback**
   - 如果發現嚴重問題，立即 rollback

---

#### 5.4 部署後驗證

```bash
# 1. 檢查服務狀態
systemctl status attendance-backend
systemctl status nginx

# 2. 檢查日誌
tail -f /var/log/attendance-backend/error.log
tail -f /var/log/nginx/error.log

# 3. 執行煙霧測試
curl https://api.example.com/health
curl https://app.example.com

# 4. 測試關鍵流程
# - 登入
# - 上班打卡
# - 外出打卡
# - 返回打卡
# - 下班打卡
```

---

#### 5.5 監控指標

**前 24 小時需要監控**:
- 錯誤率
- API 回應時間
- 資料庫查詢效能
- 使用者回報問題

---

## Rollback 計劃

### 何時需要 Rollback？

- 嚴重 bug 影響核心功能
- 資料損壞
- 效能嚴重下降
- 安全性問題

---

### Rollback 步驟

#### 1. 前端 Rollback

```bash
# 1. 切換到上一個版本
cd frontend
git checkout <previous-commit>

# 2. Build
npm run build

# 3. 部署
cp -r dist/* /var/www/attendance-frontend/

# 4. 重啟 web server
systemctl restart nginx
```

---

#### 2. 後端 Rollback

```bash
# 1. 切換到上一個版本
cd backend
git checkout <previous-commit>

# 2. 重啟服務
systemctl restart attendance-backend

# 3. 檢查狀態
systemctl status attendance-backend
```

---

#### 3. 資料庫 Rollback

```bash
# 1. 執行 downgrade
cd backend
alembic downgrade -1

# 2. 驗證
alembic current
# 應該顯示: 007

# 3. 檢查表結構
psql attendance_db -c "\d attendance_punches"
# location_id 欄位應該被移除
```

**注意**: 如果已有資料寫入 `allowed_locations` 或 `location_id`，需要評估資料損失風險。

---

## 部署檢查清單

### 測試環境

- [ ] Migration 已執行
- [ ] 後端已部署
- [ ] 前端已部署
- [ ] 煙霧測試已通過
- [ ] Manual QA 已完成
- [ ] 所有測試案例已通過
- [ ] 無嚴重問題

---

### Staging 環境

- [ ] Migration 已執行
- [ ] 後端已部署
- [ ] 前端已部署
- [ ] 煙霧測試已通過
- [ ] 效能測試已通過
- [ ] 負載測試已通過
- [ ] 安全性檢查已通過

---

### Production 環境

- [ ] 部署計劃已審核
- [ ] Rollback 計劃已準備
- [ ] 團隊已通知
- [ ] 資料庫已備份
- [ ] Migration 已執行
- [ ] 後端已部署
- [ ] 前端已部署
- [ ] 煙霧測試已通過
- [ ] 關鍵流程已驗證
- [ ] 監控已設定
- [ ] 無嚴重錯誤

---

## 部署後任務

### 立即任務（部署後 1 小時）

- [ ] 檢查錯誤日誌
- [ ] 檢查系統指標
- [ ] 回應使用者問題（如有）

---

### 短期任務（部署後 24 小時）

- [ ] 持續監控系統
- [ ] 收集使用者回饋
- [ ] 記錄任何問題
- [ ] 評估是否需要 hotfix

---

### 中期任務（部署後 1 週）

- [ ] 分析使用數據
- [ ] 評估功能效果
- [ ] 決定下一步（Step 3B 或其他）
- [ ] 更新文件

---

## 已知限制

### 1. 前端 Precheck 未實作

**說明**: 前端沒有提前檢查 location policy，所有驗證都在後端。

**影響**: 使用者需要等待 API 回應才知道是否在範圍內。

**緩解**: 錯誤訊息已經很友善，且包含最近地點資訊。

---

### 2. Admin UI 未實作

**說明**: 目前沒有管理端 UI 來管理 allowed locations。

**影響**: 需要使用 API 或資料庫直接操作。

**緩解**: Admin API 已完整實作，可以使用 Postman 或 curl。

---

### 3. 其他打卡流程未整合

**說明**: 目前只有 BREAK_OUT 整合了 location policy。

**影響**: BREAK_IN, punch-in, punch-out 不受 location policy 限制。

**緩解**: 這是設計決策，未來可以擴充。

---

## 風險評估

### 高風險

**無**

---

### 中風險

**1. Migration 失敗**

**機率**: 低  
**影響**: 高  
**緩解**: 
- 在測試環境先驗證
- 準備 rollback script
- 資料庫備份

---

### 低風險

**1. GPS 權限問題**

**機率**: 中  
**影響**: 低  
**緩解**: 
- 錯誤訊息已經很清楚
- 使用者可以重試

**2. 前端錯誤處理不完整**

**機率**: 低  
**影響**: 低  
**緩解**: 
- 程式碼審查已通過
- 有 fallback 錯誤處理

---

## 成功指標

### 技術指標

- ✅ 部署成功率 100%
- ✅ 錯誤率 < 1%
- ✅ API 回應時間 < 500ms
- ✅ 無嚴重 bug

---

### 業務指標

- ✅ 使用者可以正常打卡
- ✅ Location policy 正確執行
- ✅ 錯誤訊息清楚友善
- ✅ 無使用者投訴

---

## 聯絡資訊

### 部署團隊

- **後端負責人**: [Name]
- **前端負責人**: [Name]
- **DBA**: [Name]
- **DevOps**: [Name]

---

### 緊急聯絡

- **On-call**: [Phone]
- **Slack Channel**: #attendance-system
- **Email**: team@example.com

---

## 附錄

### A. 測試資料準備

```sql
-- 建立測試公司
INSERT INTO companies (id, name) VALUES ('test-company-1', 'Test Company');

-- 建立測試使用者
INSERT INTO users (id, company_id, email, name) 
VALUES ('test-user-1', 'test-company-1', 'test@example.com', 'Test User');

-- 建立測試 allowed location
INSERT INTO allowed_locations (
  id, company_id, name, latitude, longitude, radius_meters, is_active
) VALUES (
  gen_random_uuid(),
  'test-company-1',
  '台北101工地',
  25.0330,
  121.5654,
  100,
  true
);
```

---

### B. 常用命令

```bash
# 檢查 migration 狀態
alembic current

# 執行 migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# 檢查服務狀態
systemctl status attendance-backend

# 重啟服務
systemctl restart attendance-backend

# 查看日誌
tail -f /var/log/attendance-backend/error.log

# 測試 API
curl -X POST http://localhost:8000/v1/attendance/break-out \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes":"測試","location":{"latitude":25.0330,"longitude":121.5654}}'
```

---

### C. 故障排除

#### 問題 1: Migration 失敗

**症狀**: `alembic upgrade head` 失敗

**可能原因**:
- 資料庫連線問題
- 權限不足
- 表已存在

**解決方式**:
1. 檢查資料庫連線
2. 檢查使用者權限
3. 檢查 alembic_version 表
4. 手動執行 SQL（如需要）

---

#### 問題 2: 後端服務無法啟動

**症狀**: `systemctl start attendance-backend` 失敗

**可能原因**:
- 程式碼錯誤
- 依賴缺失
- 設定檔錯誤

**解決方式**:
1. 檢查錯誤日誌
2. 檢查依賴是否安裝
3. 檢查設定檔
4. 手動執行看錯誤訊息

---

#### 問題 3: 前端 build 失敗

**症狀**: `npm run build` 失敗

**可能原因**:
- 語法錯誤
- 依賴缺失
- 記憶體不足

**解決方式**:
1. 檢查錯誤訊息
2. 執行 `npm install`
3. 檢查 Node.js 版本
4. 增加記憶體限制

---

#### 問題 4: GPS 無法取得

**症狀**: 使用者回報無法外出打卡

**可能原因**:
- 瀏覽器不支援
- 權限被拒絕
- HTTPS 未啟用

**解決方式**:
1. 確認使用 HTTPS
2. 檢查瀏覽器支援
3. 引導使用者允許權限
4. 檢查錯誤訊息是否清楚

---

## 結論

### 部署準備狀態

**程式碼**: ✅ 準備完成  
**文件**: ✅ 準備完成  
**測試計劃**: ✅ 準備完成  
**Rollback 計劃**: ✅ 準備完成

**建議**: 可以開始部署到測試環境

---

### 下一步

1. 執行測試環境部署
2. 執行 Manual QA
3. 修正問題（如有）
4. 部署到 Staging
5. 部署到 Production
6. 監控與收集回饋
7. 決定下一步（Step 3B 或其他）

---

**建立日期**: 2026-03-08  
**版本**: 1.0  
**狀態**: ✅ 準備完成  
**下一步**: 測試環境部署
