#!/usr/bin/env python3
"""
PostgreSQL 連接測試腳本
"""
import sys
import os

# 添加 backend 目錄到 Python 路徑
sys.path.insert(0, '/opt/attendance-system/backend')

from sqlalchemy import create_engine, text
from app.core.config import settings

def test_postgres_connection():
    """測試 PostgreSQL 連接"""
    
    print("=" * 60)
    print("PostgreSQL 連接測試")
    print("=" * 60)
    print(f"資料庫 URL: {settings.database_url.replace('Raxcxtjq260!', '***')}")
    print("-" * 60)
    
    try:
        # 嘗試連接
        print("正在連接到 PostgreSQL...")
        engine = create_engine(settings.database_url, echo=False)
        
        with engine.connect() as conn:
            print("✓ 連接成功！")
            print("\n執行測試查詢...")
            
            # 查詢 PostgreSQL 版本
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL 版本: {version[:80]}...")
            
            # 查詢當前資料庫
            result = conn.execute(text("SELECT current_database();"))
            current_db = result.fetchone()[0]
            print(f"✓ 當前資料庫: {current_db}")
            
            # 查詢當前使用者
            result = conn.execute(text("SELECT current_user;"))
            current_user = result.fetchone()[0]
            print(f"✓ 當前使用者: {current_user}")
            
            # 列出所有資料庫
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"))
            databases = result.fetchall()
            print(f"\n可用的資料庫:")
            for db in databases:
                print(f"  - {db[0]}")
            
            # 檢查 attendance_db 是否存在
            db_exists = any(db[0] == 'attendance_db' for db in databases)
            if db_exists:
                print(f"\n✓ attendance_db 資料庫存在")
            else:
                print(f"\n⚠ attendance_db 資料庫不存在，需要創建")
        
        print("\n" + "=" * 60)
        print("✓ 測試完成！所有連接測試通過。")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 連接失敗！")
        print(f"錯誤類型: {type(e).__name__}")
        print(f"錯誤訊息: {e}")
        print("\n可能的原因:")
        print("  1. PostgreSQL 服務未啟動")
        print("  2. 密碼不正確")
        print("  3. 主機或連接埠設定錯誤")
        print("  4. 使用者權限不足")
        print("  5. pg_hba.conf 配置問題")
        print("  6. 資料庫不存在")
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)

