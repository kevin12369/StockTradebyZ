"""
任务管理 API 路由

提供任务的提交、状态查询、取消等接口
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.dependencies import get_db
from app.schemas.task import TaskListResponse, TaskResponse, TaskSubmitRequest
from app.services.task_queue import task_queue, TaskInfo

router = APIRouter()


@router.post("/submit", response_model=TaskResponse)
async def submit_task(
    request: TaskSubmitRequest,
    db: Session = Depends(get_db),
):
    """提交异步任务到队列

    支持的任务类型：
    - sync_stock_list: 同步股票列表
    - sync_kline: 同步单只股票K线
    - batch_sync_kline: 批量同步K线

    Args:
        request: 任务提交请求
        db: 数据库会话

    Returns:
        TaskResponse: 任务信息
    """
    from app.services.akshare_service import akshare_service

    # 根据任务类型创建执行器
    async def executor(task: TaskInfo, rate_limiter):
        """任务执行器"""
        if request.task_type == "sync_stock_list":
            # 同步股票列表
            result = akshare_service.sync_stock_list_to_db(db)
            task.result = result
            task.message = f"成功同步 {result.get('total', 0)} 只股票，新增 {result.get('new', 0)} 只"

        elif request.task_type == "sync_kline":
            # 同步单只股票K线
            ts_code = request.params.get("ts_code")
            if not ts_code:
                raise ValueError("缺少 ts_code 参数")

            # 等待速率限制器
            await rate_limiter.acquire()

            force_full_sync = request.params.get("force_full_sync", False)
            result = akshare_service.sync_stock_kline_to_db(
                db, ts_code, force_full_sync=force_full_sync
            )
            task.result = result
            task.message = result.get("message", "同步完成")

        elif request.task_type == "batch_sync_kline":
            # 批量同步K线（异步版本，使用速率限制器）
            limit = request.params.get("limit")
            force_full_sync = request.params.get("force_full_sync", False)
            only_active = request.params.get("only_active", True)

            result = await akshare_service.async_batch_sync_kline_to_db(
                db,
                task_info=task,
                rate_limiter=rate_limiter,
                limit=limit,
                force_full_sync=force_full_sync,
                only_active=only_active,
            )
            task.result = result
            task.message = result.get("message", "批量同步完成")

        else:
            raise ValueError(f"不支持的任务类型: {request.task_type}")

    # 提交任务到队列
    task_id = await task_queue.submit(
        task_type=request.task_type,
        params=request.params,
        executor=executor,
    )

    # 获取任务信息
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=500, detail="任务创建失败")

    logger.info(f"任务已提交: {request.task_type} - {task_id}")
    return TaskResponse(**task.to_dict())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        TaskResponse: 任务信息
    """
    task = task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskResponse(**task.to_dict())


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: str = None,
    limit: int = 50,
):
    """获取任务列表

    Args:
        status: 过滤状态（可选）
        limit: 返回数量限制

    Returns:
        TaskListResponse: 任务列表
    """
    all_tasks = task_queue.get_all_tasks()

    # 状态过滤
    if status:
        all_tasks = [t for t in all_tasks if t.status.value == status]

    # 限制数量（按创建时间倒序）
    all_tasks.sort(key=lambda t: t.created_at or t.created_at, reverse=True)
    all_tasks = all_tasks[:limit]

    return TaskListResponse(
        tasks=[TaskResponse(**t.to_dict()) for t in all_tasks],
        total=len(all_tasks),
    )


@router.delete("/{task_id}", response_model=TaskResponse)
async def cancel_task(task_id: str):
    """取消任务

    只能取消状态为 pending 的任务

    Args:
        task_id: 任务ID

    Returns:
        TaskResponse: 取消后的任务信息
    """
    success = task_queue.cancel_task(task_id)

    if not success:
        task = task_queue.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        else:
            raise HTTPException(
                status_code=400, detail=f"无法取消状态为 {task.status.value} 的任务"
            )

    task = task_queue.get_task(task_id)
    return TaskResponse(**task.to_dict())
