"""
回测结果和数据更新日志模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, DECIMAL, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SelectionResult(Base):
    """选股结果表

    存储策略选股的结果
    """

    __tablename__ = "selection_results"

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 关联
    strategy_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="策略ID"
    )
    ts_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="股票代码")
    trade_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="选股日期"
    )

    # 结果
    score: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), comment="评分（可选）"
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, comment="选股理由（JSON）")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<SelectionResult(id={self.id}, strategy_id={self.strategy_id}, ts_code={self.ts_code})>"


class DataUpdateLog(Base, TimestampMixin):
    """数据更新日志表

    记录数据同步的操作日志
    """

    __tablename__ = "data_update_log"

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 更新信息
    data_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="数据类型（stock_list/kline/strategy）"
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, comment="起始日期")
    end_date: Mapped[Optional[date]] = mapped_column(Date, comment="结束日期")

    # 结果
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="状态（success/failed/partial）"
    )
    records_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="记录数"
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, comment="错误信息")

    def __repr__(self) -> str:
        return f"<DataUpdateLog(id={self.id}, data_type={self.data_type}, status={self.status})>"
