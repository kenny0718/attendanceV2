# 前端部署流程

## 生產環境部署

本系統現在只使用**生產版本前端**，所有前端變更必須透過重新建置來套用。

### 部署步驟

1. 進入前端目錄：
```bash
cd /opt/attendance-system/frontend
```

2. 建置生產版本：
```bash
npm run build
```

3. Nginx 會自動提供更新後的檔案（無需重啟）

### 驗證

- 前端：http://your-server/
- API：http://your-server/api/

### 重要提醒

- ❌ 不要使用 `npm run dev`（開發伺服器已停用）
- ✅ 所有變更都必須透過 `npm run build` 建置
- ✅ Nginx 只提供 `/opt/attendance-system/frontend/dist` 的靜態檔案

