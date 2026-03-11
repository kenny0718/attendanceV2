# Git Tag 建立指令 - WP-11-11.5

**日期**: 2026-03-08  
**Milestone**: Code Cleanup Complete

---

## 快速執行

```bash
cd /opt/attendance-system

# 1. 確認當前狀態
git status

# 2. 確認所有變更已提交
git log --oneline -5

# 3. 建立 annotated tag（推薦）
git tag -a milestone/wp-11-11.5-code-cleanup-complete -m "WP-11-11.5: GPS Legacy Cleanup - Code Complete

程式碼重構完成：
- 移除舊 GPS 方法（detectDeviceType, getGPSLocation）
- 建立 locationAdapter 臨時過渡層
- 重構 attendance.js 使用 adapter
- 重構 Home.vue 使用 adapter
- 刪除備份檔案（3 個）

檔案變更：
- 新增: locationAdapter.js, utils/README.md
- 修改: attendance.js (469→402行), Home.vue (566行)
- 刪除: Home.vue.{backup,before_fix,tmp}

文件建立：
- ATTENDANCE_GPS_LEGACY_INVENTORY.md
- ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md
- ATTENDANCE_GPS_LEGACY_CLEANUP_REPORT.md
- WP-11-11.5_COMPLETION_REPORT.md
- GPS_LEGACY_CLEANUP_SUMMARY.md

驗證完成：
✓ 語法檢查通過
✓ 舊方法引用已清除
✓ 新 import 正確

待執行：
⏸ 手動 QA 驗證
⏸ 測試環境部署驗證

狀態: Code Complete (Manual QA Pending)
類型: Checkpoint / Milestone (NOT Release)"

# 4. 驗證 tag 已建立
git tag -l "milestone/*"

# 5. 查看 tag 詳細資訊
git show milestone/wp-11-11.5-code-cleanup-complete

# 6. 記錄 commit hash
git rev-parse HEAD > docs/MILESTONE_WP-11-11.5_COMMIT.txt
echo "Commit hash saved to docs/MILESTONE_WP-11-11.5_COMMIT.txt"

# 7. 推送 tag 到遠端（可選，根據團隊政策決定）
# git push origin milestone/wp-11-11.5-code-cleanup-complete

echo "✅ Milestone tag created successfully"
```

---

## 驗證命令

```bash
# 列出所有 milestone tags
git tag -l "milestone/*"

# 查看 tag 訊息
git tag -n99 milestone/wp-11-11.5-code-cleanup-complete

# 查看 tag 指向的 commit
git rev-list -n 1 milestone/wp-11-11.5-code-cleanup-complete

# 查看此 tag 的檔案清單
git ls-tree -r --name-only milestone/wp-11-11.5-code-cleanup-complete

# 查看與當前 HEAD 的差異
git diff milestone/wp-11-11.5-code-cleanup-complete HEAD
```

---

## 還原命令（如需要）

```bash
# 查看 milestone 的程式碼（唯讀）
git checkout milestone/wp-11-11.5-code-cleanup-complete

# 回到原分支
git checkout master  # 或 main

# 基於 milestone 建立新分支
git checkout -b restore/from-cleanup-complete milestone/wp-11-11.5-code-cleanup-complete

# 還原特定檔案
git checkout milestone/wp-11-11.5-code-cleanup-complete -- frontend/src/utils/locationAdapter.js
```

---

## Tag 命名規範

### 格式

```
<type>/<ticket>-<description>
```

### 類型

- `milestone/` - Checkpoint / Milestone（程式碼完成點）
- `release/` - Release（QA 通過，可部署）
- `hotfix/` - Hotfix（緊急修復）
- `backup/` - Backup（備份點）

### 範例

```
milestone/wp-11-11.5-code-cleanup-complete  ✅ 本次使用
milestone/wp-11-11.5-qa-passed              ⏳ QA 通過後建立
release/v1.2.0-wp-11-11.5                   ⏳ 正式發布時建立
```

---

## 注意事項

### ⚠️ 重要提醒

1. **這不是 Release Tag**
   - 僅標記程式碼完成
   - 未經 QA 驗證
   - 不應部署到生產環境

2. **這是 Checkpoint**
   - 可作為開發基礎
   - 可作為回滾點
   - 可作為參考點

3. **後續需要**
   - 執行手動 QA
   - 通過後建立 `milestone/wp-11-11.5-qa-passed`
   - 正式發布時建立 `release/` tag

### ✅ 適合使用場景

- WP-11-12 開發的起點
- 問題回滾的還原點
- 程式碼對比的參考點

---

## 下一步

1. **立即**: 執行上述命令建立 tag
2. **本週**: 執行手動 QA
3. **QA 通過後**: 建立 `milestone/wp-11-11.5-qa-passed` tag
4. **開始 WP-11-12**: 基於此 milestone 開發 useLocation

---

**建立日期**: 2026-03-08  
**參考文件**: [MILESTONE_WP-11-11.5_CODE_CLEANUP_COMPLETE.md](./MILESTONE_WP-11-11.5_CODE_CLEANUP_COMPLETE.md)
