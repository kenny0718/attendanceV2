# 首頁備份檔案清理建議報告

**建立日期：** 2026-03-09  
**目的：** 識別可安全刪除、歸檔或必須保留的備份檔案

---

## 1. 必須永久保留 ✅

### 1.1 基準版本（正確的 2 時間版本）

| 檔案名稱 | 大小 | 狀態 | 原因 |
|---------|------|------|------|
| `Home.BASELINE_V1_2.vue` | 34K | 🔒 基準 | V1.2 正式基準版本 |
| `HomeCardUnified.vue.before_grouping_fix` | 34K | 🔒 源檔案 | 正確 2 時間版本的原始來源 |
| `HomeCardUnified.vue.before_width_fix` | 34K | 🔒 備用 | 次佳的 2 時間版本 |

**保留原因：**
- 這些是唯一正確的 2 時間版本
- 未來如果 Home.vue 損壞，必須從這些檔案恢復
- 作為 UI 基準的參考實作

**操作：** 無需操作，永久保留

---

## 2. 建議歸檔（錯誤的 4 時間版本）📦

### 2.1 可能有歷史參考價值的錯誤版本

| 檔案名稱 | 大小 | 版本類型 | 建議 |
|---------|------|---------|------|
| `HomeCardUnified.vue.current_backup` | 29K | 4 時間 | 歸檔 |
| `HomeCardUnified.vue.backup` | 29K | 4 時間 | 歸檔 |
| `Home.vue.emergency_backup` | 25K | 4 時間 | 歸檔 |
| `Home.vue.before_fix` | 25K | 4 時間 | 歸檔 |
| `Home.vue.before_out_checkpoint_removal` | 25K | 4 時間 | 歸檔 |

**歸檔原因：**
- 這些是錯誤的 4 時間版本，不應該用於恢復
- 但可能有歷史參考價值（了解過去的錯誤）
- 移出主目錄可避免誤用

**建議操作：**
```bash
# 創建歸檔目錄
mkdir -p /opt/attendance-system/frontend/src/views/archive/wrong_4time_versions

# 移動到歸檔
cd /opt/attendance-system/frontend/src/views
mv HomeCardUnified.vue.current_backup archive/wrong_4time_versions/
mv HomeCardUnified.vue.backup archive/wrong_4time_versions/
mv Home.vue.emergency_backup archive/wrong_4time_versions/
mv Home.vue.before_fix archive/wrong_4time_versions/
mv Home.vue.before_out_checkpoint_removal archive/wrong_4time_versions/
```

---

## 3. 可以安全刪除 🗑️

### 3.1 零位元組損壞檔案

| 檔案名稱 | 大小 | 原因 |
|---------|------|------|
| `Home.vue.broken_backup_20260309_220339` | 0 bytes | 損壞的空檔案 |
| `HomeV1.vue` | 0 bytes | 空檔案 |
| `HomeCardUnified.vue.before_fix` | 0 bytes | 空檔案 |

**刪除原因：**
- 0 bytes 檔案沒有任何內容
- 無法恢復或參考
- 佔用檔案系統空間

### 3.2 重複的 4 時間版本

| 檔案名稱 | 大小 | 原因 |
|---------|------|------|
| `Home.vue.backup.phase2b` | 23K | 與其他 4 時間版本重複 |
| `Home.vue.before_step3a` | 23K | 與其他 4 時間版本重複 |
| `Home.vue.after_ui_adjustment` | 16K | 過時的版本 |

**刪除原因：**
- 內容與其他備份重複
- 已有更完整的版本保留
- 命名模糊，容易混淆

**建議操作：**
```bash
cd /opt/attendance-system/frontend/src/views

# 刪除 0 bytes 檔案
rm -f Home.vue.broken_backup_20260309_220339
rm -f HomeV1.vue
rm -f HomeCardUnified.vue.before_fix

# 刪除重複的 4 時間版本
rm -f Home.vue.backup.phase2b
rm -f Home.vue.before_step3a
rm -f Home.vue.after_ui_adjustment
```

---

## 4. 檔案命名規範建議

### 4.1 推薦的命名格式

**基準版本：**
```
格式：Home.BASELINE_V{major}_{minor}.vue
範例：Home.BASELINE_V1_2.vue
```

**變更前備份：**
```
格式：Home.pre_change.YYYYMMDD_HHMM.vue
範例：Home.pre_change.20260309_2203.vue
```

**功能分支備份：**
```
格式：Home.{feature_name}.YYYYMMDD.vue
範例：Home.add_overtime.20260310.vue
```

**測試版本：**
```
格式：Home.test_{test_name}.YYYYMMDD.vue
範例：Home.test_mobile_ui.20260311.vue
```

### 4.2 禁止使用的模糊命名

❌ **避免使用：**
- `Home.backup.vue` - 太模糊，不知道是什麼時候的
- `Home.old.vue` - 不知道是哪個版本
- `Home.before_fix.vue` - 不知道修復了什麼
- `Home.current_backup.vue` - "current" 會過時
- `Home.temp.vue` - 容易被誤刪
- `HomeV1.vue` - 與版本控制混淆
- `Home.emergency_backup.vue` - 不知道緊急情況是什麼

### 4.3 命名規範的好處

✅ **清晰的命名可以：**
- 一眼看出檔案的用途
- 知道檔案的創建時間
- 避免誤用錯誤的版本
- 方便自動化清理腳本

---

## 5. 備份保留策略

### 5.1 基準版本
- **保留期限：** 永久
- **數量限制：** 每個主要版本至少保留一個
- **清理規則：** 永不刪除

### 5.2 變更前備份（pre_change）
- **保留期限：** 30 天
- **數量限制：** 最近 30 個
- **清理規則：** 
  - 保留最近 30 天的所有備份
  - 每月保留一個月初備份（永久）
  - 每季保留一個季初備份（永久）

### 5.3 功能分支備份
- **保留期限：** 7 天（功能合併後）
- **數量限制：** 無限制（在保留期內）
- **清理規則：** 功能合併後 7 天自動刪除

### 5.4 測試版本
- **保留期限：** 3 天
- **數量限制：** 最近 10 個
- **清理規則：** 測試完成後 3 天自動刪除

### 5.5 歸檔版本
- **保留期限：** 90 天
- **數量限制：** 無限制
- **清理規則：** 90 天後可以刪除

---

## 6. 自動化清理腳本建議

### 6.1 清理腳本範例

```bash
#!/bin/bash
# cleanup_home_backups.sh
# 自動清理過期的首頁備份檔案

VIEWS_DIR="/opt/attendance-system/frontend/src/views"
ARCHIVE_DIR="$VIEWS_DIR/archive"
CURRENT_DATE=$(date +%s)

# 清理 pre_change 備份（保留 30 天）
find "$VIEWS_DIR" -name "Home.pre_change.*.vue" -type f -mtime +30 -delete

# 清理測試版本（保留 3 天）
find "$VIEWS_DIR" -name "Home.test_*.vue" -type f -mtime +3 -delete

# 清理歸檔（保留 90 天）
find "$ARCHIVE_DIR" -type f -mtime +90 -delete

echo "清理完成"
```

### 6.2 定期執行

```bash
# 添加到 crontab（每天凌晨 2 點執行）
0 2 * * * /opt/attendance-system/scripts/cleanup_home_backups.sh
```

---

## 7. 執行清理的安全檢查清單

### 7.1 清理前檢查

- [ ] 確認 `Home.BASELINE_V1_2.vue` 存在且完整
- [ ] 確認 `HomeCardUnified.vue.before_grouping_fix` 存在且完整
- [ ] 確認當前 `Home.vue` 是正確的 2 時間版本
- [ ] 確認前端建置成功
- [ ] 創建完整的系統備份

### 7.2 清理步驟

**步驟 1：創建歸檔目錄**
```bash
mkdir -p /opt/attendance-system/frontend/src/views/archive/wrong_4time_versions
```

**步驟 2：移動錯誤版本到歸檔**
```bash
cd /opt/attendance-system/frontend/src/views
mv HomeCardUnified.vue.current_backup archive/wrong_4time_versions/
mv HomeCardUnified.vue.backup archive/wrong_4time_versions/
mv Home.vue.emergency_backup archive/wrong_4time_versions/
mv Home.vue.before_fix archive/wrong_4time_versions/
mv Home.vue.before_out_checkpoint_removal archive/wrong_4time_versions/
```

**步驟 3：刪除無用檔案**
```bash
rm -f Home.vue.broken_backup_20260309_220339
rm -f HomeV1.vue
rm -f HomeCardUnified.vue.before_fix
rm -f Home.vue.backup.phase2b
rm -f Home.vue.before_step3a
rm -f Home.vue.after_ui_adjustment
```

**步驟 4：驗證清理結果**
```bash
# 檢查必須保留的檔案仍然存在
ls -lh Home.BASELINE_V1_2.vue
ls -lh HomeCardUnified.vue.before_grouping_fix
ls -lh Home.vue

# 檢查錯誤版本已移除
ls -lh Home*.vue | grep -E "emergency|before_fix|backup.phase"
# 應該無輸出
```

**步驟 5：測試恢復流程**
```bash
# 測試從基準恢復
cp Home.vue Home.vue.test_backup
cp Home.BASELINE_V1_2.vue Home.vue
npm run build
# 如果成功，恢復原檔案
mv Home.vue.test_backup Home.vue
```

### 7.3 清理後驗證

- [ ] 基準檔案完整
- [ ] 當前 Home.vue 正常運作
- [ ] 前端建置成功
- [ ] 錯誤版本已移除或歸檔
- [ ] Git 狀態正常

---

## 8. 清理時間表建議

### 立即執行（今天）
1. ✅ 創建 `Home.BASELINE_V1_2.vue`（已完成）
2. 🔄 刪除 0 bytes 檔案
3. 🔄 創建歸檔目錄

### 本週內執行
1. 移動錯誤的 4 時間版本到歸檔
2. 刪除重複的備份檔案
3. 驗證清理結果

### 本月內執行
1. 建立自動化清理腳本
2. 設定定期清理任務
3. 建立備份監控機制

---

## 9. 總結

### 9.1 檔案統計

| 類別 | 數量 | 總大小 | 建議操作 |
|------|------|--------|---------|
| 必須保留 | 3 | 102K | 永久保留 |
| 建議歸檔 | 5 | 127K | 移到 archive |
| 可以刪除 | 6 | 46K | 安全刪除 |

### 9.2 預期效果

**清理後：**
- 主目錄只保留 4 個檔案（Home.vue + 3 個基準）
- 錯誤版本移到歸檔，避免誤用
- 無用檔案刪除，釋放空間
- 檔案結構清晰，易於維護

### 9.3 風險評估

**風險等級：** 🟢 低風險

**原因：**
- 所有重要檔案都有保留
- 錯誤版本只是歸檔，不是刪除
- 可以隨時從基準恢復
- 有完整的驗證流程

---

**建議執行時間：** 非高峰時段  
**預計執行時間：** 15 分鐘  
**需要停機：** 否

**最後更新：** 2026-03-09
