#!/usr/bin/env python3
"""驗證 Audit Log 功能

此腳本展示如何查詢和使用 audit log。
"""

import sys
sys.path.insert(0, '/opt/attendance-system/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.modules.audit.models import AuditLog

# 連接測試資料庫
DATABASE_URL = "postgresql+psycopg2://attendance_user:test123@127.0.0.1:5432/attendance_test_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 60)
print("Phase 6C - Backup Audit Log 驗證")
print("=" * 60)

# 查詢所有 audit logs
all_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()

print(f"\n📊 最近 10 筆 Audit Logs：")
print("-" * 60)

if not all_logs:
    print("⚠️  目前沒有 audit log 記錄")
    print("💡 請先執行測試：pytest app/modules/audit/tests/test_audit_backup.py")
else:
    for log in all_logs:
        status_icon = "✅" if log.status == "success" else "❌"
        print(f"\n{status_icon} {log.action} - {log.status}")
        print(f"   公司: {log.company_id}")
        print(f"   執行者: {log.actor}")
        print(f"   時間: {log.created_at}")
        if log.meta:
            print(f"   Meta: {log.meta}")
        if log.error:
            print(f"   錯誤: {log.error[:100]}...")

# 統計
print("\n" + "=" * 60)
print("📈 統計資訊：")
print("-" * 60)

total = db.query(AuditLog).count()
success = db.query(AuditLog).filter(AuditLog.status == "success").count()
fail = db.query(AuditLog).filter(AuditLog.status == "fail").count()
export = db.query(AuditLog).filter(AuditLog.action == "backup.export").count()
restore = db.query(AuditLog).filter(AuditLog.action == "backup.restore").count()

print(f"總筆數: {total}")
print(f"成功: {success} ({success/total*100:.1f}%)" if total > 0 else "成功: 0")
print(f"失敗: {fail} ({fail/total*100:.1f}%)" if total > 0 else "失敗: 0")
print(f"匯出操作: {export}")
print(f"還原操作: {restore}")

print("\n" + "=" * 60)
print("✅ Phase 6C 功能驗證完成！")
print("=" * 60)

db.close()
