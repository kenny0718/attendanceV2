
---

## 9. 修正記錄（Post-closeout Fix）

**發現時間：** 2026-03-17（結案驗證階段）  
**問題：** `test_audit_retention.py` 原始檔案為空（0 bytes），pytest 從 `__pycache__` 執行舊版 `.pyc`，導致 `test_get_retention_default` 讀到 PostgreSQL 中的髒資料（retention_days=180 而非預設 365）。  
**根本原因：** 舊版測試中 `test_get_retention_default` 未請求 `test_db` fixture，未觸發 get_db override，因此連到真實 PostgreSQL 並讀取前次測試遺留資料。  
**修正內容：**
- 重建 `test_audit_retention.py`（從 0 bytes 還原為完整測試）
- `test_get_retention_default` 加入 `test_db` 參數，確保使用 SQLite 隔離環境
- 清除 `__pycache__` 中的舊版 `.pyc`

**最終驗證結果：**
- audit：**27/27 PASS**
- notifications：**26/26 PASS**
- backup：**25/25 PASS**
- **合計：78/78 PASS** ✅
