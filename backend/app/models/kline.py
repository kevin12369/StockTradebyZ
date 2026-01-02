"""
K线数据模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, DECIMAL, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KlineDaily(Base):
    """日线K线数据表

    存储股票的日线OHLCV数据
    """

    __tablename__ = "kline_daily"

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 股票标识
    ts_code: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="股票代码"
    )
    trade_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )

    # OHLCV 数据
    open: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="开盘价")
    close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="收盘价")
    high: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="最高价")
    low: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="最低价")
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, comment="成交量（手）")
    amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(20, 2), comment="成交额（元）"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="创建时间"
    )

    # 唯一约束
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uix_kline_daily_code_date"),
    )

    def __repr__(self) -> str:
        return f"<KlineDaily(id={self.id}, ts_code={self.ts_code}, trade_date={self.trade_date})>"
