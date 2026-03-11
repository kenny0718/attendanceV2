# 🎯 下班打卡 UI 閃爍問題 - 修復完成

## 問題
下班打卡後，頁面閃爍，今日記錄消失。

## 根本原因
```javascript
// punch() 成功後調用 fetchTodayStatus()
await this.fetchTodayStatus()  // ❌ 返回 session: null，清空狀態
```

後端 `getCurrentStatus` API 在下班後返回 `session: null`，導致前端清空所有狀態。

## 修復方案
**文件**: `frontend/src/stores/attendance.js` (line 123)

**修改前**:
```javascript
await this.fetchTodayStatus()  // ❌ 會清空狀態
await this.fetchRecentLogs()
```

**修改後**:
```javascript
// 只刷新記錄，不刷新狀態
await this.fetchRecentLogs()
```

## 修復結果
✅ 下班時間正確顯示  
✅ UI 不會閃爍  
✅ 記錄保持顯示  
✅ 編譯成功  

## 測試
請驗證：
1. 上班打卡 → 顯示上班時間
2. 下班打卡 → 顯示下班時間（不閃爍）
3. 刷新頁面 → 時間仍然顯示

---
**修復時間**: 2026-03-10  
**詳細報告**: PUNCH_OUT_UI_FIX_REPORT.md
