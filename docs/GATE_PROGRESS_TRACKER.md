
## WP-11-07 Phase 2 — API Integration (Mock → Real API)

**Status:** ✅ COMPLETED (Code Ready, Pending Manual Test)  
**Date:** 2026-03-05

**Deliverables:**
- ✅ 替換 Mock 數據為真實 API 呼叫
- ✅ 統一錯誤處理策略（409/404/403/5xx/網路錯誤）
- ✅ Tenant/Auth headers 自動注入
- ✅ Loading 狀態與錯誤提示 UI
- ✅ 測試文件：`docs/WP-11-07_UI_MVP_PHASE2_TEST_LOG.md`

**Key Changes:**
- ✅ `stores/attendance.js` - 移除所有 Mock，改用真實 API
- ✅ `api/attendance.js` - 簡化為 4 個核心方法
- ✅ `views/Home.vue` - 新增錯誤 Toast 提示
- ✅ 錯誤處理：自動刷新狀態，防止 UI 與後端不同步

**API Integration:**
- ✅ POST `/api/v1/attendance/punch-in` - 上班打卡
- ✅ POST `/api/v1/attendance/punch-out` - 下班打卡
- ✅ GET `/api/v1/attendance/current-status` - 獲取狀態
- ✅ GET `/api/v1/attendance/history` - 獲取記錄

**Error Handling:**
- ✅ 409 Conflict: 「已有打開的打卡記錄」+ 自動刷新
- ✅ 404 Not Found: 「找不到打開的打卡記錄」+ 自動刷新
- ✅ 403 Forbidden: 「無權限執行此操作」
- ✅ 5xx Server Error: 「伺服器暫時無法處理請求」
- ✅ Network Error: 「網絡連接失敗」

**Known Limitations:**
- ⚠️ 外出/返回功能暫不支援（後端無 endpoints）
- ⚠️ 需要 Node.js 環境才能執行測試

**Test Status:**
- ⏳ 待手動測試（需要 npm install + npm run dev）
- ⏳ 測試檢查清單見 `WP-11-07_UI_MVP_PHASE2_TEST_LOG.md`

**Next Phase:**
- ⏳ 手動執行完整測試流程
- ⏳ 更新測試結果到 TEST_LOG
- ⏳ Phase 3: 外出/返回功能（需後端支援）

---

**Document Version:** 8.0  
**Last Updated:** 2026-03-05  
**Gate 4 Status:** 🔒 CLOSED & FROZEN  
**Gate 5 Status:** 🚧 IN PROGRESS (Backend complete, UI MVP Phase 2 code ready)  
**Next Review:** Manual testing completion or Phase 3 planning
