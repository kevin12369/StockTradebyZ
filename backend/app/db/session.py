"""
数据库会话管理
"""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# 创建数据目录
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)


# 创建数据库引擎
# SQLite 需要设置 check_same_thread=False
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False,  # 关闭SQL echo，避免SQL日志刷屏（通过logging系统控制）
    pool_pre_ping=True,  # 连接前检查连接有效性
    pool_recycle=3600,  # 1小时回收连接（本地项目可以设置更长）
)


# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入）

    Yields:
        Session: SQLAlchemy 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库

    创建所有表
    """
    from app.models.base import Base
    from app.models.stock import Stock
    from app.models.kline import KlineDaily
    from app.models.strategy import Strategy
    from app.models.backtest import SelectionResult, DataUpdateLog

    # 导入所有模型后创建表
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """删除所有表（危险操作，仅用于测试）"""
    from app.models.base import Base

    Base.metadata.drop_all(bind=engine)


__all__ = ["engine", "SessionLocal", "get_db", "init_db", "drop_db"]
