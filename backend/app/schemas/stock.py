"""
股票相关 Schema 模型

定义股票数据的请求和响应格式
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class StockBase(BaseModel):
    """股票基础模型"""

    ts_code: str = Field(..., description="股票代码（如：000001.SZ）")
    symbol: str = Field(..., description="股票代码（如：000001）")
    name: str = Field(..., description="股票名称")
    market: Optional[str] = Field(None, description="市场（SZ/SH/BJ）")
    industry: Optional[str] = Field(None, description="行业")
    list_date: Optional[date] = Field(None, description="上市日期")


class StockCreate(StockBase):
    """创建股票的请求模型"""

    pass


class StockUpdate(BaseModel):
    """更新股票的请求模型"""

    name: Optional[str] = None
    industry: Optional[str] = None
    is_active: Optional[bool] = None


class StockResponse(StockBase):
    """股票响应模型"""

    id: int = Field(..., description="股票ID")
    is_active: bool = Field(..., description="是否有效")
    market_name: Optional[str] = Field(None, description="市场中文名称")
    board: Optional[str] = Field(None, description="板块（主板/创业板/科创板等）")

    class Config:
        from_attributes = True


class StockListResponse(BaseModel):
    """股票列表响应模型（简化版）"""

    id: int
    ts_code: str
    symbol: str
    name: str
    market: Optional[str]
    market_name: Optional[str] = None
    board: Optional[str] = None

    class Config:
        from_attributes = True


class KlineDataBase(BaseModel):
    """K线数据基础模型"""

    trade_date: date = Field(..., description="交易日期")
    open: Optional[Decimal] = Field(None, description="开盘价")
    close: Optional[Decimal] = Field(None, description="收盘价")
    high: Optional[Decimal] = Field(None, description="最高价")
    low: Optional[Decimal] = Field(None, description="最低价")
    volume: Optional[int] = Field(None, description="成交量（手）")
    amount: Optional[Decimal] = Field(None, description="成交额（元）")


class KlineDataResponse(KlineDataBase):
    """K线数据响应模型"""

    id: int = Field(..., description="数据ID")
    ts_code: str = Field(..., description="股票代码")

    class Config:
        from_attributes = True


class KlineDataRequest(BaseModel):
    """K线数据查询请求"""

    start_date: Optional[str] = Field(None, description="起始日期（YYYY-MM-DD）")
    end_date: Optional[str] = Field(None, description="结束日期（YYYY-MM-DD）")
