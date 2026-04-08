# Cursor Read Order（強制）

> **[GOVERNANCE OVERRIDE]** `STOP_GATES.md` has the highest priority across all governance rules. If any conflict exists between this document and `STOP_GATES.md`, **STOP_GATES.md takes precedence**.

在任何任務中，必須依序讀取：

CURSOR_EXECUTION_CONTROL.md ⭐（最高優先，次於 STOP_GATES.md）
CURSOR_FRONTEND_SAFE_EDIT_RULES.md（前端任務）
CURSOR_BACKEND_SAFE_EDIT_RULES.md（後端任務）
AI_CONTEXT.md
當前任務說明

未完成上述讀取：

❌ 禁止修改
