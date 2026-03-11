#!/bin/bash
# 首頁基準驗證腳本
# 用途：驗證 Home.vue 是否符合 V1.2 基準規範

cd /opt/attendance-system/frontend/src/views

echo "=== 首頁基準驗證 V1.2 ==="
echo ""

# 1. 檢查時間欄位數量
echo "1. 時間欄位檢查："
correct_count=$(grep -c "label=\"上班時間\"\|label=\"下班時間\"" Home.vue)
wrong_count=$(grep -c "label=\"外出時間\"\|label=\"返回時間\"" Home.vue)

echo "   正確欄位數量: $correct_count (預期: 2)"
echo "   錯誤欄位數量: $wrong_count (預期: 0)"

if [ "$correct_count" -eq 2 ] && [ "$wrong_count" -eq 0 ]; then
    echo "   ✓ 通過"
else
    echo "   ✗ 失敗"
    exit 1
fi

# 2. 檢查基準註解
echo ""
echo "2. 基準註解檢查："
if grep -q "簡化為只顯示上班/下班" Home.vue; then
    echo "   ✓ 通過"
else
    echo "   ✗ 失敗：缺少基準註解"
    exit 1
fi

# 3. 檢查檔案大小
echo ""
echo "3. 檔案大小檢查："
line_count=$(wc -l < Home.vue)
echo "   行數: $line_count (預期: ~1484)"

if [ "$line_count" -gt 1400 ] && [ "$line_count" -lt 1600 ]; then
    echo "   ✓ 通過"
else
    echo "   ⚠ 警告：行數異常"
fi

# 4. 檢查基準檔案存在
echo ""
echo "4. 基準檔案檢查："
if [ -f "Home.BASELINE_V1_2.vue" ]; then
    echo "   ✓ Home.BASELINE_V1_2.vue 存在"
else
    echo "   ✗ 失敗：基準檔案不存在"
    exit 1
fi

# 5. 檢查 grid 設定
echo ""
echo "5. Grid 設定檢查："
if grep -A5 "今日狀態" Home.vue | grep -q "grid-cols-4"; then
    echo "   ✗ 失敗：今日狀態使用 grid-cols-4"
    exit 1
else
    echo "   ✓ 通過"
fi

# 6. 檢查 status-grid-simple
echo ""
echo "6. 樣式類別檢查："
if grep -q "status-grid-simple" Home.vue; then
    echo "   ✓ 通過：使用 status-grid-simple"
else
    echo "   ⚠ 警告：未找到 status-grid-simple"
fi

echo ""
echo "=== 驗證完成 ==="
echo ""
echo "✓ Home.vue 符合 V1.2 基準規範"
