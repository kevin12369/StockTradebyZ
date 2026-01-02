"""
任务管理 API

提供任务查询、取消、暂停、恢复等功能
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.common import ApiResponse
from app.services.improved_task_queue import improved_task_queue, TaskInfo


router = APIRouter(prefix="/tasks", tags=["任务管理"])


# ========== 响应模型 ==========

class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[dict]
    total: int
    running: int
    pending: int


# ========== API 端点 ==========

@router.get(
    "",
    response_model=ApiResponse[TaskListResponse],
    summary="获取所有任务",
    description="获取所有任务的状态和进度信息",
)
async def get_all_tasks(
    limit: int = 50,
    status: Optional[str] = None,
) -> ApiResponse[TaskListResponse]:
    """获取所有任务

    Args:
        limit: 返回数量限制
        status: 状态筛选（pending/running/success/failed/cancelled）

    Returns:
        任务列表
    """
    all_tasks = improved_task_queue.get_all_tasks()

    # 状态筛选
    if status:
        all_tasks = [t for t in all_tasks if t.status.value == status]

    # 按创建时间倒序
    all_tasks.sort(key=lambda t: t.created_at, reverse=True)

    # 限制数量
    tasks = all_tasks[:limit]

    # 统计
    running_count = sum(1 for t in all_tasks if t.status.value == "running")
    pending_count = sum(1 for t in all_tasks if t.status.value == "pending")

    return ApiResponse[TaskListResponse](
        code=200,
        message=f"找到 {len(tasks)} 个任务",
        data=TaskListResponse(
            tasks=[t.to_dict() for t in tasks],
            total=len(all_tasks),
            running=running_count,
            pending=pending_count,
        ),
    )


@router.get(
    "/{task_id}",
    response_model=ApiResponse[dict],
    summary="获取任务详情",
    description="获取指定任务的详细信息",
)
async def get_task(task_id: str) -> ApiResponse[dict]:
    """获取任务详情

    Args:
        task_id: 任务ID

    Returns:
        任务详情
    """
    task = improved_task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return ApiResponse[dict](
        code=200,
        message="获取任务成功",
        data=task.to_dict(),
    )


@router.post(
    "/{task_id}/cancel",
    response_model=ApiResponse[dict],
    summary="取消任务",
    description="取消指定的任务（只能取消未开始或正在执行的任务）",
)
async def cancel_task(task_id: str) -> ApiResponse[dict]:
    """取消任务

    Args:
        task_id: 任务ID

    Returns:
        取消结果
    """
    task = improved_task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status.value in ["success", "failed", "cancelled"]:
        return ApiResponse[dict](
            code=400,
            message=f"任务已{task.status.value}，无法取消",
            data=task.to_dict(),
        )

    success = improved_task_queue.cancel_task(task_id)

    if success:
        return ApiResponse[dict](
            code=200,
            message="任务取消成功",
            data=task.to_dict(),
        )
    else:
        return ApiResponse[dict](
            code=400,
            message="任务无法取消",
            data=task.to_dict(),
        )


@router.post(
    "/{task_id}/pause",
    response_model=ApiResponse[dict],
    summary="暂停任务",
    description="暂停正在执行的任务",
)
async def pause_task(task_id: str) -> ApiResponse[dict]:
    """暂停任务

    Args:
        task_id: 任务ID

    Returns:
        暂停结果
    """
    task = improved_task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status.value != "running":
        return ApiResponse[dict](
            code=400,
            message="只能暂停正在执行的任务",
            data=task.to_dict(),
        )

    success = improved_task_queue.pause_task(task_id)

    if success:
        return ApiResponse[dict](
            code=200,
            message="任务暂停成功",
            data=task.to_dict(),
        )
    else:
        return ApiResponse[dict](
            code=400,
            message="任务无法暂停",
            data=task.to_dict(),
        )


@router.post(
    "/{task_id}/resume",
    response_model=ApiResponse[dict],
    summary="恢复任务",
    description="恢复已暂停的任务",
)
async def resume_task(task_id: str) -> ApiResponse[dict]:
    """恢复任务

    Args:
        task_id: 任务ID

    Returns:
        恢复结果
    """
    task = improved_task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status.value != "paused":
        return ApiResponse[dict](
            code=400,
            message="只能恢复已暂停的任务",
            data=task.to_dict(),
        )

    success = improved_task_queue.resume_task(task_id)

    if success:
        return ApiResponse[dict](
            code=200,
            message="任务恢复成功",
            data=task.to_dict(),
        )
    else:
        return ApiResponse[dict](
            code=400,
            message="任务无法恢复",
            data=task.to_dict(),
        )


@router.delete(
    "/{task_id}",
    response_model=ApiResponse[dict],
    summary="删除任务",
    description="从任务列表中删除指定的任务记录",
)
async def delete_task(task_id: str) -> ApiResponse[dict]:
    """删除任务记录

    注意：这只删除记录，不会取消正在执行的任务

    Args:
        task_id: 任务ID

    Returns:
        删除结果
    """
    task = improved_task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 不能删除正在执行的任务
    if task.status.value == "running":
        return ApiResponse[dict](
            code=400,
            message="无法删除正在执行的任务",
            data=None,
        )

    # 删除任务记录
    del improved_task_queue.tasks[task_id]

    return ApiResponse[dict](
        code=200,
        message="任务记录已删除",
        data={"task_id": task_id},
    )
