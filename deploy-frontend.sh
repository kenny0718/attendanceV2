#!/bin/bash
# deploy-frontend.sh
# 前端部署腳本：build + verify + reload nginx
# 用法：/opt/attendance-system/deploy-frontend.sh

set -e

FRONTEND_DIR="/opt/attendance-system/frontend"
DIST_ASSETS="$FRONTEND_DIR/dist/assets"

echo "========================================"
echo " Frontend Deploy Script"
echo "========================================"

# Step 1 — 切換到 frontend 目錄
echo "[1/4] Entering frontend directory..."
cd "$FRONTEND_DIR"

# Step 2 — 執行前端 build
echo "[2/4] Building frontend..."
npm run build

# Step 3 — 驗證 bundle 包含關鍵字
echo "[3/4] Verifying bundle..."
TZ_CHECK=$(grep -rl "Asia/Taipei" "$DIST_ASSETS"/*.js 2>/dev/null || true)
if [ -n "$TZ_CHECK" ]; then
    echo "  [OK] Asia/Taipei found in bundle: $TZ_CHECK"
else
    echo "  [WARN] Asia/Taipei NOT found in any bundle — timezone plugin may be missing"
fi

# Step 4 — reload nginx
echo "[4/4] Reloading nginx..."
nginx -t && systemctl reload nginx
echo "  [OK] nginx reloaded"

# Step 5 — 完成訊息
echo
echo "========================================"
echo " Deploy complete."
echo " Hard-refresh browser (Ctrl+Shift+R)"
echo " to load new assets."
echo "========================================"
