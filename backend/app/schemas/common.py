"""
通用 Schema 模块

定义 API 响应的通用格式
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """通用 API 响应格式

    Args:
        code: 状态码（200=成功）
        message: 响应消息
        data: 响应数据
    """

    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")


class PageResponse(BaseModel, Generic[T]):
    """分页响应格式

    Args:
        total: 总记录数
        page: 当前页码
        page_size: 每页数量
        items: 数据列表
    """

    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: List[T] = Field(default_factory=list, description="数据列表")


class IdResponse(BaseModel):
    """ID 响应格式（用于创建/更新操作）"""

    id: int = Field(..., description="记录ID")


class MessageResponse(BaseModel):
    """简单消息响应"""

    message: str = Field(..., description="响应消息")
