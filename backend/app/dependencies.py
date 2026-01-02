"""
依赖注入模块
提供 FastAPI 路由的依赖项
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal


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


__all__ = ["get_db", "get_settings"]
