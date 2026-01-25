"""資料庫連線管理（同步 SQLAlchemy）"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# 建立 Engine（同步）
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Session:
    """取得資料庫 Session（FastAPI Dependency）
    
    使用方式：
        @app.get("/api/example")
        def example(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化資料庫（建立所有資料表）
    
    注意：生產環境應使用 Alembic migration
    """
    logger.info("初始化資料庫...")
    Base.metadata.create_all(bind=engine)
    logger.info("資料庫初始化完成")
