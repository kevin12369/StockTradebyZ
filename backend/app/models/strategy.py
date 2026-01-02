"""
选股策略配置模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Strategy(Base, TimestampMixin):
    """选股策略配置表

    存储选股策略的配置信息
    """

    __tablename__ = "strategies"

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 策略标识
    class_name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="策略类名"
    )
    alias: Mapped[str] = mapped_column(String(50), nullable=False, comment="策略别名")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="策略描述")

    # 配置
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )
    config_json: Mapped[str] = mapped_column(Text, nullable=False, comment="策略参数（JSON）")

    # 排序
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序"
    )

    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, class_name={self.class_name}, alias={self.alias})>"
