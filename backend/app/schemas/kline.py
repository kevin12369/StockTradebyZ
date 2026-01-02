"""
K线数据 Schema 模型

定义 K线数据的请求和响应格式
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class KlineChartData(BaseModel):
    """K线图表数据格式"""

    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    close: float = Field(..., description="收盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    volume: int = Field(..., description="成交量")
    amount: Optional[float] = Field(None, description="成交额")


class IndicatorData(BaseModel):
    """技术指标数据"""

    name: str = Field(..., description="指标名称")
    data: list[float] = Field(..., description="指标值列表")
    color: Optional[str] = Field(None, description="线条颜色")
