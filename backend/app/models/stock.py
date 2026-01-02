"""
股票基本信息模型
"""

from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Stock(Base, TimestampMixin):
    """股票基本信息表

    存储A股股票的基本信息
    """

    __tablename__ = "stocks"

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 股票标识
    ts_code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True, comment="股票代码（如：000001.SZ）"
    )
    symbol: Mapped[str] = mapped_column(String(6), nullable=False, index=True, comment="股票代码（如：000001）")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="股票名称")

    # 市场信息
    market: Mapped[Optional[str]] = mapped_column(String(10), comment="市场（SZ/SH）")
    industry: Mapped[Optional[str]] = mapped_column(String(50), comment="行业")
    list_date: Mapped[Optional[date]] = mapped_column(Date, comment="上市日期")

    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否有效"
    )

    @property
    def market_name(self) -> str:
        """获取中文名称的市场"""
        market_map = {
            "SZ": "深交所",
            "SH": "上交所",
            "BJ": "北交所",
        }
        return market_map.get(self.market, "未知") if self.market else "未知"

    @property
    def board(self) -> str:
        """获取板块信息（主板/创业板/科创板等）"""
        if not self.ts_code:
            return "未知"

        code = self.ts_code.split(".")[0]

        if self.market == "SH":
            if code.startswith("688"):
                return "科创板"
            else:
                return "沪主板"
        elif self.market == "SZ":
            if code.startswith("300"):
                return "创业板"
            elif code.startswith("000") or code.startswith("001"):
                return "深主板"
            else:
                return "深交所"
        elif self.market == "BJ":
            return "北交所"
        else:
            return "未知"

    def __repr__(self) -> str:
        return f"<Stock(id={self.id}, ts_code={self.ts_code}, name={self.name})>"
