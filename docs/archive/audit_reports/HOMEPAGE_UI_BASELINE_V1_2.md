# 首頁 UI 基準規範 V1.2

**文件版本：** V1.2  
**建立日期：** 2026-03-09  
**最後更新：** 2026-03-09  
**狀態：** 🔒 已鎖定 - 這是正確的基準版本

---

## 📌 重要提示

**這是首頁的正確版本基準。任何對 `Home.vue` 的修改都必須遵守本文件的規範。**

違反本規範的修改將導致首頁 UI 退化到錯誤的舊版本。

---

## 1. 當前首頁真相來源

### 正確的源檔案
- **檔案：** `frontend/src/views/Home.vue`
- **源基準：** `HomeCardUnified.vue.before_grouping_fix`
- **版本：** V1.2（2 時間版本）
- **行數：** 1484 行
- **大小：** 34K
- **Git Commit：** `f1e3fb9` - "fix(frontend): restore homepage to correct 2-time v1.2 baseline"
- **恢復日期：** 2026-03-09 22:03

### 基準標記
在 `Home.vue` 第 6 行包含以下註解：
```vue
<!-- 今日狀態 - 簡化為只顯示上班/下班 -->
```

這個註解是正確版本的識別標記。

---

## 2. 首頁必須包含的內容 ✅

### 2.1 今日狀態區塊（只有 2 個時間欄位）

**正確的結構：**
```vue
<!-- 今日狀態 - 簡化為只顯示上班/下班 -->
<Card title="今日狀態" class="status-section">
  <div class="status-grid-simple">
    <StatusCard 
      label="上班時間" 
      :value="formattedTodayStatus.punch_in"
      :valueClass="todayStatus.punch_in ? 'active' : 'empty'"
    />
    <StatusCard 
      label="下班時間" 
      :value="formattedTodayStatus.punch_out"
      :valueClass="todayStatus.punch_out ? 'active' : 'empty'"
    />
  </div>
</Card>
```

**關鍵特徵：**
- ✅ 只有 2 個 `<StatusCard>` 組件
- ✅ 只顯示「上班時間」和「下班時間」
- ✅ 使用 `status-grid-simple` class（不是 `grid-cols-4`）
- ✅ 註解明確說明「簡化為只顯示上班/下班」

### 2.2 打卡操作區塊

**必須包含：**
- 上班打卡按鈕
- 下班打卡按鈕
- 使用 `function-card` 自訂樣式（不依賴 PunchButton 組件）

### 2.3 外出原因區塊

**必須包含：**
- 常用原因快速選擇
- 自訂原因管理
- 原因輸入欄
- 新增自訂原因功能

### 2.4 外出 / 返回打卡區塊

**必須包含：**
- 外出打卡按鈕
- 返回打卡按鈕
- 外出/返回記錄列表（可收合）
- 編輯外出原因對話框

### 2.5 最近打卡記錄區塊

**必須包含：**
- 最近打卡記錄列表
- 打卡類型顯示
- 遲到狀態標記

---

## 3. 首頁絕對禁止的內容 ❌

### 3.1 禁止的 4 時間佈局

**❌ 錯誤的結構（絕對不可出現）：**
```vue
<!-- 這是錯誤的舊版本 - 禁止使用 -->
<div class="status-grid grid grid-cols-2 md:grid-cols-4 gap-4">
  <StatusCard label="上班時間" />
  <StatusCard label="下班時間" />
  <StatusCard label="外出時間" />      <!-- ❌ 禁止 -->
  <StatusCard label="返回時間" />      <!-- ❌ 禁止 -->
</div>
```

### 3.2 禁止的 UI 元素

**絕對不可在「今日狀態」區塊中出現：**
- ❌ `label="外出時間"` 的 StatusCard
- ❌ `label="返回時間"` 的 StatusCard
- ❌ `formattedTodayStatus.break_out` 的顯示
- ❌ `formattedTodayStatus.break_in` 的顯示
- ❌ `grid-cols-4` 或 `md:grid-cols-4` 的 grid 設定
- ❌ 任何 4 欄位的時間摘要佈局

### 3.3 禁止的檔案來源

**以下檔案是錯誤的舊版本，絕對不可作為恢復源：**
- ❌ `HomeCardUnified.vue.current_backup` - 4 時間版本
- ❌ `HomeCardUnified.vue.backup` - 4 時間版本
- ❌ `Home.vue.emergency_backup` - 4 時間版本
- ❌ `Home.vue.before_fix` - 4 時間版本
- ❌ `Home.vue.before_out_checkpoint_removal` - 4 時間版本
- ❌ `Home.vue.backup.phase2b` - 4 時間版本
- ❌ `Home.vue.before_step3a` - 4 時間版本
- ❌ `Home.vue.after_ui_adjustment` - 4 時間版本

### 3.4 禁止的混合版本模式

**不可出現以下情況：**
- ❌ 同時存在 Home.vue 和 HomeV1.vue 作為活躍路由
- ❌ 在「今日狀態」中顯示外出/返回時間摘要
- ❌ 將外出/返回時間提升到頂部摘要區塊
- ❌ 使用 PunchButton 組件（應使用 function-card 自訂樣式）

---

## 4. 未來編輯 Home.vue 的工作流程

### 4.1 編輯前準備（必須執行）

**步驟 1：創建時間戳備份**
```bash
cd /opt/attendance-system/frontend/src/views
cp Home.vue Home.pre_change.$(date +%Y%m%d_%H%M%S).vue
```

**步驟 2：閱讀本基準文件**
```bash
cat /opt/attendance-system/docs/HOMEPAGE_UI_BASELINE_V1_2.md
```

確認理解：
- ✅ 只能有 2 個時間欄位
- ✅ 不可重新引入 4 時間佈局
- ✅ 不可使用禁止的檔案作為參考

**步驟 3：記錄變更意圖**
在進行修改前，明確記錄：
- 為什麼要修改？
- 修改哪些部分？
- 是否會影響「今日狀態」區塊？

### 4.2 編輯中檢查（持續驗證）

**檢查清單：**
- [ ] 「今日狀態」區塊仍然只有 2 個 StatusCard
- [ ] 沒有新增「外出時間」或「返回時間」
- [ ] 沒有使用 `grid-cols-4` 或 `md:grid-cols-4`
- [ ] 註解 `<!-- 今日狀態 - 簡化為只顯示上班/下班 -->` 仍然存在
- [ ] 沒有從禁止的備份檔案複製程式碼

### 4.3 編輯後驗證（必須執行）

**步驟 1：執行前端建置**
```bash
cd /opt/attendance-system/frontend
npm run build
```

**預期結果：**
- ✅ 建置成功，無錯誤
- ✅ 無 linting 警告

**步驟 2：驗證時間欄位數量**
```bash
cd /opt/attendance-system/frontend/src/views
grep -c "label=\"上班時間\"\|label=\"下班時間\"" Home.vue
# 應該輸出：2

grep -c "label=\"外出時間\"\|label=\"返回時間\"" Home.vue
# 應該輸出：0
```

**步驟 3：驗證今日狀態區塊**
```bash
grep -A15 "今日狀態" Home.vue | head -20
```

**預期輸出：**
```vue
<!-- 今日狀態 - 簡化為只顯示上班/下班 -->
<Card title="今日狀態" class="status-section">
  <div class="status-grid-simple">
    <StatusCard label="上班時間" />
    <StatusCard label="下班時間" />
  </div>
</Card>
```

**步驟 4：檢查 grid 設定**
```bash
grep "grid-cols-4\|md:grid-cols-4" Home.vue
# 應該無輸出（或只在外出記錄等其他區塊）
```

### 4.4 提交前確認（必須執行）

**只有在以下所有條件都滿足時才可提交：**
- ✅ 前端建置成功
- ✅ 「今日狀態」只有 2 個時間欄位
- ✅ 無「外出時間」和「返回時間」
- ✅ 所有功能測試通過
- ✅ 備份檔案已創建

**提交命令：**
```bash
git add frontend/src/views/Home.vue
git commit -m "feat(frontend): [描述變更] - maintains 2-time baseline"
```

**提交訊息必須包含：**
- 變更的具體內容
- 確認維持 2 時間基準的聲明

### 4.5 緊急回滾程序

**如果發現錯誤引入了 4 時間佈局：**

```bash
# 立即回滾到最近的備份
cd /opt/attendance-system/frontend/src/views
cp Home.pre_change.YYYYMMDD_HHMM.vue Home.vue

# 或回滾到基準版本
cp HomeCardUnified.vue.before_grouping_fix Home.vue

# 重新建置
cd /opt/attendance-system/frontend
npm run build

# 驗證
grep -c "label=\"外出時間\"\|label=\"返回時間\"" src/views/Home.vue
# 必須輸出：0
```

---

## 5. 檔案命名規範

### 5.1 基準檔案命名

**格式：** `Home.BASELINE_V{major}_{minor}.vue`

**範例：**
- `Home.BASELINE_V1_2.vue` - V1.2 基準版本
- `Home.BASELINE_V1_3.vue` - V1.3 基準版本（未來）

### 5.2 變更前備份命名

**格式：** `Home.pre_change.YYYYMMDD_HHMM.vue`

**範例：**
- `Home.pre_change.20260309_2203.vue`
- `Home.pre_change.20260310_1430.vue`

### 5.3 功能分支備份命名

**格式：** `Home.{feature_name}.YYYYMMDD.vue`

**範例：**
- `Home.add_overtime_feature.20260310.vue`
- `Home.ui_polish.20260311.vue`

### 5.4 禁止使用的模糊命名

**❌ 避免使用：**
- `Home.backup.vue` - 太模糊
- `Home.old.vue` - 不知道是哪個版本
- `Home.before_fix.vue` - 不知道修復了什麼
- `Home.current_backup.vue` - 不知道是什麼時候的
- `Home.temp.vue` - 容易被誤刪
- `HomeV1.vue` - 與版本控制混淆

---

## 6. 備份檔案保留建議

### 6.1 必須保留（作為基準參考）

**永久保留：**
- ✅ `HomeCardUnified.vue.before_grouping_fix` - **正確的 2 時間版本源**
- ✅ `HomeCardUnified.vue.before_width_fix` - 次佳的 2 時間版本

**保留原因：**
- 這是唯一正確的 2 時間版本
- 未來如果 Home.vue 損壞，可以從這裡恢復
- 作為 UI 基準的參考實作

**建議操作：**
```bash
# 創建基準副本
cd /opt/attendance-system/frontend/src/views
cp HomeCardUnified.vue.before_grouping_fix Home.BASELINE_V1_2.vue
```

### 6.2 可以歸檔（移到 archive 目錄）

**這些是錯誤的 4 時間版本，但可能有歷史參考價值：**
- 📦 `HomeCardUnified.vue.current_backup` - 4 時間版本
- 📦 `HomeCardUnified.vue.backup` - 4 時間版本
- 📦 `Home.vue.emergency_backup` - 4 時間版本
- 📦 `Home.vue.before_fix` - 4 時間版本
- 📦 `Home.vue.before_out_checkpoint_removal` - 4 時間版本

**建議操作：**
```bash
# 創建歸檔目錄
mkdir -p /opt/attendance-system/frontend/src/views/archive/wrong_4time_versions

# 移動錯誤版本到歸檔
cd /opt/attendance-system/frontend/src/views
mv HomeCardUnified.vue.current_backup archive/wrong_4time_versions/
mv HomeCardUnified.vue.backup archive/wrong_4time_versions/
mv Home.vue.emergency_backup archive/wrong_4time_versions/
mv Home.vue.before_fix archive/wrong_4time_versions/
mv Home.vue.before_out_checkpoint_removal archive/wrong_4time_versions/
```

### 6.3 可以安全刪除

**這些檔案沒有保留價值：**
- 🗑️ `Home.vue.broken_backup_20260309_220339` - 0 bytes 損壞檔案
- 🗑️ `HomeV1.vue` - 0 bytes 空檔案
- 🗑️ `HomeCardUnified.vue.before_fix` - 0 bytes 空檔案
- 🗑️ `Home.vue.backup.phase2b` - 重複的 4 時間版本
- 🗑️ `Home.vue.before_step3a` - 重複的 4 時間版本
- 🗑️ `Home.vue.after_ui_adjustment` - 過時的版本

**建議操作（驗證後執行）：**
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

### 6.4 備份保留時間表

**變更前備份（pre_change）：**
- 保留最近 30 天的備份
- 每月保留一個月初備份
- 每季保留一個季初備份

**功能分支備份：**
- 功能合併後保留 7 天
- 7 天後可以刪除

**基準版本：**
- 永久保留
- 每個主要版本至少保留一個基準

---

## 7. 驗證檢查清單

### 7.1 快速驗證（每次編輯後）

```bash
cd /opt/attendance-system/frontend/src/views

# 1. 檢查時間欄位數量
echo "=== 時間欄位檢查 ==="
echo -n "正確欄位數量: "
grep -c "label=\"上班時間\"\|label=\"下班時間\"" Home.vue
echo -n "錯誤欄位數量: "
grep -c "label=\"外出時間\"\|label=\"返回時間\"" Home.vue

# 2. 檢查基準註解
echo "=== 基準註解檢查 ==="
grep "簡化為只顯示上班/下班" Home.vue

# 3. 檢查 grid 設定
echo "=== Grid 設定檢查 ==="
grep -n "grid-cols-4" Home.vue | grep "今日狀態" -A5 -B5

# 4. 檢查檔案大小
echo "=== 檔案大小檢查 ==="
wc -l Home.vue
```

**預期輸出：**
```
=== 時間欄位檢查 ===
正確欄位數量: 2
錯誤欄位數量: 0
=== 基準註解檢查 ===
      <!-- 今日狀態 - 簡化為只顯示上班/下班 -->
=== Grid 設定檢查 ===
（無輸出或只在其他區塊）
=== 檔案大小檢查 ===
1484 Home.vue
```

### 7.2 完整驗證（提交前）

```bash
cd /opt/attendance-system/frontend

# 1. 前端建置
npm run build

# 2. 執行快速驗證
cd src/views
bash /opt/attendance-system/scripts/verify_homepage_baseline.sh

# 3. 視覺檢查
# 啟動開發伺服器，手動檢查首頁
npm run dev
```

---

## 8. 常見錯誤和解決方案

### 8.1 錯誤：意外引入 4 時間佈局

**症狀：**
- 「今日狀態」顯示 4 個時間欄位
- 出現「外出時間」和「返回時間」

**原因：**
- 從錯誤的備份檔案複製程式碼
- 使用了 `current_backup` 或其他 4 時間版本

**解決方案：**
```bash
# 立即回滾到基準版本
cd /opt/attendance-system/frontend/src/views
cp Home.BASELINE_V1_2.vue Home.vue

# 或從正確的源恢復
cp HomeCardUnified.vue.before_grouping_fix Home.vue

# 重新建置
cd /opt/attendance-system/frontend
npm run build
```

### 8.2 錯誤：使用了 PunchButton 組件

**症狀：**
- 打卡按鈕使用 `<PunchButton>` 組件
- 導入了 `import PunchButton from '@/components/PunchButton.vue'`

**原因：**
- 從舊版本 Home.vue 複製程式碼

**解決方案：**
- 使用 `function-card` 自訂樣式
- 參考 `HomeCardUnified.vue.before_grouping_fix` 的實作

### 8.3 錯誤：grid 設定錯誤

**症狀：**
- 「今日狀態」使用 `grid-cols-4` 或 `md:grid-cols-4`

**原因：**
- 複製了錯誤的 grid 設定

**解決方案：**
```vue
<!-- 錯誤 -->
<div class="status-grid grid grid-cols-2 md:grid-cols-4 gap-4">

<!-- 正確 -->
<div class="status-grid-simple">
```

---

## 9. 聯絡和支援

### 9.1 如果不確定是否符合基準

**在進行任何可能影響「今日狀態」區塊的修改前：**
1. 重新閱讀本文件
2. 檢查 `HomeCardUnified.vue.before_grouping_fix` 的實作
3. 創建備份
4. 在測試環境中驗證

### 9.2 基準文件更新

**本文件只能在以下情況下更新：**
- 產品需求明確要求改變首頁時間欄位顯示邏輯
- 經過完整的設計評審和批准
- 更新後必須創建新的基準版本（如 V1.3）

**更新流程：**
1. 創建新的基準文件（如 `HOMEPAGE_UI_BASELINE_V1_3.md`）
2. 保留舊版本文件作為歷史記錄
3. 更新 Git commit 引用
4. 通知所有開發人員

---

## 10. 附錄

### 10.1 正確版本的完整特徵

**檔案特徵：**
- 檔案大小：約 34K
- 行數：1484 行
- 包含註解：`<!-- 今日狀態 - 簡化為只顯示上班/下班 -->`
- 使用 `status-grid-simple` class
- 使用 `function-card` 自訂樣式
- 不依賴 PunchButton 組件

**UI 特徵：**
- 「今日狀態」只有 2 個卡片
- 使用 section-title 分組
- 外出/返回功能在專屬區塊
- 可收合的外出記錄列表
- 編輯外出原因對話框

### 10.2 錯誤版本的識別特徵

**檔案特徵：**
- 包含 `grid-cols-4` 或 `md:grid-cols-4` 在「今日狀態」區塊
- 包含 `label="外出時間"` 或 `label="返回時間"`
- 使用 PunchButton 組件
- 檔案大小約 25K（738 行）或 29K（973 行）

**UI 特徵：**
- 「今日狀態」有 4 個卡片
- 顯示外出時間和返回時間摘要
- 使用傳統按鈕樣式

### 10.3 版本歷史

| 版本 | 日期 | 描述 | Git Commit |
|------|------|------|------------|
| V1.2 | 2026-03-09 | 正確的 2 時間版本基準 | f1e3fb9 |
| V1.1 | 2026-03-08 | 錯誤的 4 時間混合版本 | （已廢棄） |
| V1.0 | 2026-03-05 | 初始版本 | （已廢棄） |

---

## 📋 快速參考

### 編輯前
```bash
cp Home.vue Home.pre_change.$(date +%Y%m%d_%H%M%S).vue
cat docs/HOMEPAGE_UI_BASELINE_V1_2.md
```

### 編輯後
```bash
npm run build
grep -c "label=\"外出時間\"\|label=\"返回時間\"" src/views/Home.vue  # 必須是 0
```

### 緊急回滾
```bash
cp HomeCardUnified.vue.before_grouping_fix Home.vue
npm run build
```

---

**🔒 本文件受版本控制保護。任何修改都必須經過審查和批准。**

**最後更新：** 2026-03-09  
**維護者：** 開發團隊  
**狀態：** 🟢 活躍
