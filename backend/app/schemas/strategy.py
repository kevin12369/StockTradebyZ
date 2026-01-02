"""
策略相关 Schema 模型

定义选股策略的请求和响应格式
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class StrategyBase(BaseModel):
    """策略基础模型"""

    class_name: str = Field(..., description="策略类名")
    alias: str = Field(..., description="策略别名")
    description: Optional[str] = Field(None, description="策略描述")


class StrategyCreate(StrategyBase):
    """创建策略的请求模型"""

    config_json: str = Field(..., description="策略参数（JSON字符串）")
    sort_order: int = Field(0, description="排序")


class StrategyUpdate(BaseModel):
    """更新策略的请求模型"""

    alias: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config_json: Optional[str] = None
    sort_order: Optional[int] = None


class StrategyResponse(StrategyBase):
    """策略响应模型"""

    id: int = Field(..., description="策略ID")
    is_active: bool = Field(..., description="是否启用")
    config_json: str = Field(..., description="策略参数（JSON字符串）")
    sort_order: int = Field(..., description="排序")

    class Config:
        from_attributes = True


class StrategyExecuteRequest(BaseModel):
    """执行策略的请求模型"""

    strategy_ids: list[int] = Field(..., description="要执行的策略ID列表")
    trade_date: Optional[str] = Field(None, description="选股日期（YYYY-MM-DD），默认为当天")


class SelectionResultBase(BaseModel):
    """选股结果基础模型"""

    strategy_id: int = Field(..., description="策略ID")
    ts_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="选股日期")


class SelectionResultResponse(SelectionResultBase):
    """选股结果响应模型"""

    id: int = Field(..., description="结果ID")
    score: Optional[Decimal] = Field(None, description="评分")
    reason: Dict[str, Any] = Field(default_factory=dict, description="选股理由")

    class Config:
        from_attributes = True


class StrategyExecuteResponse(BaseModel):
    """策略执行响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    strategy_id: Optional[int] = Field(None, description="策略ID")
    strategy_alias: Optional[str] = Field(None, description="策略别名")
    trade_date: Optional[str] = Field(None, description="选股日期")
    total_stocks: Optional[int] = Field(None, description="总股票数")
    selected_count: Optional[int] = Field(None, description="选中的股票数")
    saved_count: Optional[int] = Field(None, description="保存的结果数")
    results: list[Dict[str, Any]] = Field(default_factory=list, description="选股结果列表")
