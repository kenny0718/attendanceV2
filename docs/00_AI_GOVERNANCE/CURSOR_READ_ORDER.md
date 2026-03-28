# Cursor Read Order（強制）

在任何任務中，必須依序讀取：

1. CURSOR_EXECUTION_CONTROL.md ⭐（最高優先）
2. CURSOR_FRONTEND_SAFE_EDIT_RULES.md（前端任務）
3. CURSOR_BACKEND_SAFE_EDIT_RULES.md（後端任務）
4. AI_CONTEXT.md
5. 當前任務說明

---

# 🔴 Execution Gate（新增）

在讀取完成後，**必須先執行以下流程：**

1. 判斷 Risk Level（LOW / MEDIUM / HIGH）
2. 回報：
   - Risk Level
   - 是否需要停止 frontend dev server
   - 修改計畫

❌ 未經確認：
禁止寫檔

---

未完成上述流程：

❌ 禁止修改