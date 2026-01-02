"""
任务相关的 Pydantic Schema
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskSubmitRequest(BaseModel):
    """任务提交请求"""
    task_type: str = Field(..., description="任务类型：sync_stock_list/sync_kline/batch_sync_kline")
    params: Dict[str, Any] = Field(default_factory=dict, description="任务参数")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    status: str = Field(..., description="任务状态：pending/running/success/failed/cancelled")
    progress: float = Field(default=0.0, description="任务进度（0-100）")
    message: str = Field(default="", description="任务消息")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    started_at: Optional[str] = Field(default=None, description="开始时间")
    completed_at: Optional[str] = Field(default=None, description="完成时间")


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: list[TaskResponse] = Field(default_factory=list, description="任务列表")
    total: int = Field(default=0, description="总任务数")
