"""
双模式数据同步 API

提供两种同步模式的 API 端点：
1. 初始化模式：慢速全量同步 + GitHub 备份
2. 日常模式：快速增量同步
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.sync_config import SyncMode
from app.dependencies import get_db
from app.core.config import settings
from app.services.sync_manager import get_sync_manager
from app.services.task_queue import task_queue
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/sync", tags=["数据同步"])


# ========== 请求/响应模型 ==========

class QuickSyncRequest(BaseModel):
    """快速同步请求"""
    mode: str = "daily"  # daily/init


class TimeEstimateResponse(BaseModel):
    """时间估算响应"""
    total_seconds: float
    hours: int
    minutes: int
    seconds: int
    formatted: str
    stock_count: int
    mode: str


# ========== API 端点 ==========

@router.post(
    "/quick",
    response_model=ApiResponse[dict],
    summary="快速同步（推荐）",
    description="根据模式自动选择最佳同步策略：日常模式=快速增量，初始化模式=慢速全量+备份",
)
async def quick_sync(
    mode: str = Query("daily", description="同步模式：daily(日常) 或 init(初始化)"),
    limit: Optional[int] = Query(None, description="限制同步数量（用于测试）"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """快速同步（推荐使用）

    ## 两种模式：

    ### 1. 日常模式 (mode=daily) - 默认
    - **速率**：每1秒1个请求
    - **数据**：只获取最近3天数据（增量）
    - **时间**：5000只股票 ≈ 1.5小时
    - **用途**：每日定时更新

    ### 2. 初始化模式 (mode=init)
    - **速率**：每10秒1个请求（超保守）
    - **数据**：全量历史数据（近3年）
    - **时间**：5000只股票 ≈ 14小时
    - **备份**：自动备份到 GitHub Release
    - **用途**：首次部署、历史数据补全

    ## 示例：
    - 日常更新：`POST /api/v1/sync/quick?mode=daily`
    - 首次初始化：`POST /api/v1/sync/quick?mode=init`
    - 测试模式：`POST /api/v1/sync/quick?mode=daily&limit=10`
    """
    try:
        # 验证模式
        try:
            sync_mode = SyncMode(mode)
        except ValueError:
            return ApiResponse[dict](
                code=400,
                message=f"无效的同步模式: {mode}，支持: daily, init",
                data=None,
            )

        # 创建任务执行器
        async def executor(task, rate_limiter):
            sync_manager = get_sync_manager(settings.DATABASE_URL)
            result = await sync_manager.sync_all(
                mode=sync_mode,
                limit=limit,
                task_info=task,
            )
            task.result = result
            task.message = result.get("message", "同步完成")

        # 提交任务到队列
        task_id = await task_queue.submit(
            task_type=f"quick_sync_{mode}",
            params={
                "mode": mode,
                "limit": limit,
            },
            executor=executor,
        )

        mode_names = {
            SyncMode.DAILY: "日常模式（快速增量）",
            SyncMode.INIT: "初始化模式（慢速全量+备份）",
        }

        return ApiResponse[dict](
            code=200,
            message=f"{mode_names.get(sync_mode, mode)}同步任务已提交",
            data={
                "task_id": task_id,
                "mode": mode,
                "mode_description": mode_names.get(sync_mode, mode),
                "status": "pending",
                "message": "任务已加入队列，等待执行",
            },
        )

    except Exception as e:
        return ApiResponse[dict](
            code=500,
            message=f"提交同步任务失败: {str(e)}",
            data=None,
        )


@router.post(
    "/daily",
    response_model=ApiResponse[dict],
    summary="日常快速同步",
    description="日常模式：每1秒1个请求，只更新最新3天数据，适合每日定时任务",
)
async def daily_sync(
    limit: Optional[int] = Query(None, description="限制同步数量"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """日常快速同步

    - **速率**：每1秒1个请求（快速）
    - **数据**：只获取最近3天数据（增量）
    - **时间**：5000只股票 ≈ 1.5小时
    - **推荐**：每日定时执行（如凌晨2点）
    """
    try:
        sync_manager = get_sync_manager(settings.DATABASE_URL)
        result = await sync_manager.quick_sync_today()

        return ApiResponse[dict](
            code=200 if result["success"] else 500,
            message=result.get("message", "日常同步完成"),
            data=result,
        )

    except Exception as e:
        return ApiResponse[dict](
            code=500,
            message=f"日常同步失败: {str(e)}",
            data=None,
        )


@router.post(
    "/init",
    response_model=ApiResponse[dict],
    summary="初始化全量同步",
    description="初始化模式：每10秒1个请求，全量历史数据+自动备份，适合首次部署",
)
async def init_sync(
    limit: Optional[int] = Query(None, description="限制同步数量（用于测试）"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """初始化全量同步

    - **速率**：每10秒1个请求（超保守，避免服务器压力）
    - **数据**：全量历史数据（近3年）
    - **时间**：5000只股票 ≈ 14小时
    - **备份**：完成后自动备份到 GitHub Release
    - **推荐**：首次部署时执行一次
    """
    try:
        sync_manager = get_sync_manager(settings.DATABASE_URL)
        result = await sync_manager.full_sync_with_backup(limit=limit)

        return ApiResponse[dict](
            code=200 if result["success"] else 500,
            message=result.get("message", "初始化同步完成"),
            data=result,
        )

    except Exception as e:
        return ApiResponse[dict](
            code=500,
            message=f"初始化同步失败: {str(e)}",
            data=None,
        )


@router.get(
    "/estimate",
    response_model=ApiResponse[TimeEstimateResponse],
    summary="估算同步时间",
    description="根据股票数量和同步模式，估算所需时间",
)
async def estimate_sync_time(
    stock_count: int = Query(..., description="股票数量", example=5000),
    mode: str = Query("daily", description="同步模式：daily 或 init"),
    db: Session = Depends(get_db),
) -> ApiResponse[TimeEstimateResponse]:
    """估算同步时间

    ## 示例：
    - 日常模式 5000 只：`GET /api/v1/sync/estimate?stock_count=5000&mode=daily`
    - 初始化模式 5000 只：`GET /api/v1/sync/estimate?stock_count=5000&mode=init`
    """
    try:
        sync_mode = SyncMode(mode)
        sync_manager = get_sync_manager(settings.DATABASE_URL)
        estimate = sync_manager.estimate_sync_time(stock_count, sync_mode)

        return ApiResponse[TimeEstimateResponse](
            code=200,
            message="时间估算完成",
            data=TimeEstimateResponse(**estimate),
        )

    except ValueError:
        return ApiResponse[TimeEstimateResponse](
            code=400,
            message=f"无效的同步模式: {mode}",
            data=None,
        )
    except Exception as e:
        return ApiResponse[TimeEstimateResponse](
            code=500,
            message=f"估算失败: {str(e)}",
            data=None,
        )


@router.post(
    "/backup",
    response_model=ApiResponse[dict],
    summary="手动备份到 GitHub",
    description="手动触发数据库备份到 GitHub Release",
)
async def manual_backup(
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """手动备份数据库到 GitHub Release

    需要配置环境变量：
    - GITHUB_TOKEN: GitHub 个人访问令牌
    - GITHUB_REPO: GitHub 仓库（格式：username/repo）

    备份文件格式：stocktrade_YYYYMMDD_HHMMSS.sql.gz
    """
    try:
        from app.services.github_backup_service import github_backup_service

        result = await github_backup_service.backup_to_github(settings.DATABASE_URL)

        return ApiResponse[dict](
            code=200 if result["success"] else 500,
            message=result.get("message", "备份完成"),
            data=result,
        )

    except Exception as e:
        return ApiResponse[dict](
            code=500,
            message=f"备份失败: {str(e)}",
            data=None,
        )


@router.get(
    "/backups",
    response_model=ApiResponse[list],
    summary="列出备份",
    description="列出 GitHub 上的数据库备份",
)
async def list_backups(
    limit: int = Query(10, description="返回数量"),
) -> ApiResponse[list]:
    """列出最近的 GitHub 备份

    Returns:
        备份列表，包含标签、名称、创建时间、下载链接等
    """
    try:
        from app.services.github_backup_service import github_backup_service

        backups = await github_backup_service.list_backups(limit=limit)

        return ApiResponse[list](
            code=200,
            message=f"找到 {len(backups)} 个备份",
            data=backups,
        )

    except Exception as e:
        return ApiResponse[list](
            code=500,
            message=f"获取备份列表失败: {str(e)}",
            data=[],
        )
