#!/bin/bash
# 自動備份重要文件

BACKUP_DIR="/opt/attendance-system/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 創建備份目錄
mkdir -p "$BACKUP_DIR"

# 備份所有 Python 文件
echo "開始備份..."
find /opt/attendance-system/backend -name "*.py" -type f ! -size 0 | while read file; do
    relative_path="${file#/opt/attendance-system/backend/}"
    backup_path="$BACKUP_DIR/$TIMESTAMP/$relative_path"
    mkdir -p "$(dirname "$backup_path")"
    cp "$file" "$backup_path"
done

echo "備份完成: $BACKUP_DIR/$TIMESTAMP"

# 只保留最近 10 次備份
cd "$BACKUP_DIR"
ls -t | tail -n +11 | xargs -r rm -rf

echo "清理完成，保留最近 10 次備份"
