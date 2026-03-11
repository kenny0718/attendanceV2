# Blocker Bug 驗證指南

**Bug ID**: BLOCKER-2026-03-08-001  
**修復 Commit**: ab529ef  
**驗證人員**: ___________  
**驗證日期**: ___________

---

## 快速驗證步驟

### 1. 部署修復

```bash
cd /opt/attendance-system/frontend
npm run build
# 或重啟開發伺服器
npm run dev
```

### 2. 清除快取

- 使用無痕模式，或
- 清除瀏覽器快取（Ctrl+Shift+Delete）

### 3. 執行驗證

1. 登入系統
2. 點擊「上班打卡」
3. **不要重新整理頁面**
4. 檢查以下項目：

| 檢查項目 | 預期結果 | 實際結果 | 狀態 |
|---------|---------|---------|------|
| 狀態文案 | 「已上班打卡」 | _______ | [ ] Pass [ ] Fail |
| 上班時間 | 顯示剛打卡的時間 | _______ | [ ] Pass [ ] Fail |
| 下班時間 | 顯示「-」或空白 | _______ | [ ] Pass [ ] Fail |
| 外出時間 | 顯示「-」或空白 | _______ | [ ] Pass [ ] Fail |
| 返回時間 | 顯示「-」或空白 | _______ | [ ] Pass [ ] Fail |
| 上班打卡按鈕 | Disabled | _______ | [ ] Pass [ ] Fail |
| 下班打卡按鈕 | Enabled | _______ | [ ] Pass [ ] Fail |
| 外出打卡按鈕 | Enabled | _______ | [ ] Pass [ ] Fail |
| 返回打卡按鈕 | Disabled | _______ | [ ] Pass [ ] Fail |

### 4. DevTools 檢查（選用）

打開 Console，執行：

```javascript
console.log(JSON.stringify(attendanceStore.todayStatus, null, 2))
```

預期輸出：

```json
{
  "punch_in": "2026-03-08T09:00:00Z",
  "punch_out": null,
  "break_out": null,
  "break_in": null,
  "is_punched_in": true,
  "is_on_break": false,
  "session_id": "xxx"
}
```

---

## 驗證結果

```
[ ] ✅ 驗證通過 - Bug 已修復
[ ] ❌ 驗證失敗 - Bug 仍存在
[ ] ⏸️ 無法驗證 - 環境問題

備註：
_________________________________
_________________________________
```

---

## 簽核

```
驗證人員: ___________
簽名: ___________
日期: ___________
```
