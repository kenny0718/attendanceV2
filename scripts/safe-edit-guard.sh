#!/bin/bash
# 在每次重要編輯前備份
FILE="$1"
if [ -z "$FILE" ]; then echo "Usage: $0 <file>"; exit 1; fi
BACKUP_DIR="/opt/attendance-system/backups/vue-guards"
mkdir -p "$BACKUP_DIR"
cp "$FILE" "$BACKUP_DIR/$(basename $FILE).$(date +%Y%m%d_%H%M%S).bak"
echo "Backed up to $BACKUP_DIR"
