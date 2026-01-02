"""
双模式数据同步管理器

支持两种同步模式：
1. 初始化模式：慢速全量同步 + GitHub 备份
2. 日常模式：快速增量同步
"""

import asyncio
from datetime import date, datetime
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.core.sync_config import SyncConfig, get_sync_config, SyncMode
from app.services.akshare_service import akshare_service
from app.services.github_backup_service import github_backup_service
from app.services.task_queue import RateLimiter, TaskInfo


class SyncManager:
    """数据同步管理器

    根据不同的同步模式，使用不同的速率和策略
    """

    def __init__(self, db_url: str):
        """初始化同步管理器

        Args:
            db_url: 数据库连接 URL
        """
        self.db_url = db_url

    async def sync_stock_list(
        self,
        mode: SyncMode = SyncMode.DAILY,
    ) -> dict:
        """同步股票列表

        Args:
            mode: 同步模式

        Returns:
            dict: 同步结果
        """
        config = get_sync_config(mode)
        logger.info(f"开始同步股票列表 - 模式: {config.description}")

        # 股票列表同步不需要速率限制（单次请求）
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            result = akshare_service.sync_stock_list_to_db(db)
            return result
        finally:
            db.close()

    async def sync_kline_data(
        self,
        db: Session,
        mode: SyncMode = SyncMode.DAILY,
        limit: Optional[int] = None,
        task_info: Optional[TaskInfo] = None,
    ) -> dict:
        """同步K线数据

        Args:
            db: 数据库会话
            mode: 同步模式
            limit: 限制同步数量（None=全部）
            task_info: 任务信息（用于进度更新）

        Returns:
            dict: 同步结果
        """
        config = get_sync_config(mode)
        logger.info(f"开始同步K线数据 - 模式: {config.description}")

        # 创建对应模式的速率限制器
        rate_limiter = RateLimiter(
            requests_per_second=config.rate_limit,
            burst_size=config.burst_size,
        )

        # 计算获取天数
        days_to_fetch = config.days_to_fetch

        # 执行同步
        result = await akshare_service.async_batch_sync_kline_to_db(
            db=db,
            task_info=task_info or TaskInfo(
                task_id="manual",
                task_type="manual_sync",
                params={},
                status=None,
            ),
            rate_limiter=rate_limiter,
            limit=limit,
            force_full_sync=config.force_full_sync,
            only_active=True,
        )

        # 如果是初始化模式，同步完成后备份到 GitHub
        if mode == SyncMode.INIT and config.enable_github_backup:
            logger.info("初始化模式同步完成，开始备份到 GitHub...")
            backup_result = await github_backup_service.backup_to_github(self.db_url)
            result["github_backup"] = backup_result

        return result

    async def sync_all(
        self,
        mode: SyncMode = SyncMode.DAILY,
        limit: Optional[int] = None,
        task_info: Optional[TaskInfo] = None,
    ) -> dict:
        """同步所有数据（股票列表 + K线）

        Args:
            mode: 同步模式
            limit: K线同步数量限制
            task_info: 任务信息

        Returns:
            dict: 同步结果
        """
        config = get_sync_config(mode)
        logger.info(f"开始全量数据同步 - 模式: {config.description}")

        if task_info:
            task_info.message = "正在同步股票列表..."

        # 1. 同步股票列表
        stock_list_result = await self.sync_stock_list(mode)

        if not stock_list_result["success"]:
            return {
                "success": False,
                "message": f"股票列表同步失败: {stock_list_result['message']}",
            }

        # 2. 同步K线数据
        if task_info:
            task_info.message = "正在同步K线数据..."

        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            kline_result = await self.sync_kline_data(
                db=db,
                mode=mode,
                limit=limit,
                task_info=task_info,
            )

            # 合并结果
            result = {
                "success": kline_result["success"],
                "message": f"股票列表: {stock_list_result['message']}, K线: {kline_result.get('message', '')}",
                "stock_list": stock_list_result,
                "kline": kline_result,
            }

            return result
        finally:
            db.close()

    async def quick_sync_today(self) -> dict:
        """快速同步今日数据

        日常模式的快捷方式，只更新今日数据

        Returns:
            dict: 同步结果
        """
        logger.info("执行快速今日数据同步...")

        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            # 使用日常模式，不限制数量
            result = await self.sync_kline_data(
                db=db,
                mode=SyncMode.DAILY,
                limit=None,
            )
            return result
        finally:
            db.close()

    async def full_sync_with_backup(self, limit: Optional[int] = None) -> dict:
        """全量同步并备份

        初始化模式的快捷方式，全量同步所有数据并备份到 GitHub

        Args:
            limit: 限制同步数量（用于测试）

        Returns:
            dict: 同步结果
        """
        logger.info("执行全量数据同步并备份...")

        result = await self.sync_all(
            mode=SyncMode.INIT,
            limit=limit,
        )

        return result

    def estimate_sync_time(
        self,
        stock_count: int,
        mode: SyncMode = SyncMode.DAILY,
    ) -> dict:
        """估算同步时间

        Args:
            stock_count: 股票数量
            mode: 同步模式

        Returns:
            dict: 时间估算（秒）
        """
        config = get_sync_config(mode)

        # 每只股票的平均处理时间（包括请求时间）
        # 初始化模式：10秒/股票（包括速率限制）
        # 日常模式：1秒/股票（包括速率限制）
        time_per_stock = 1.0 / config.rate_limit

        total_seconds = stock_count * time_per_stock
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        return {
            "total_seconds": total_seconds,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "formatted": f"{hours}小时{minutes}分{seconds}秒",
            "stock_count": stock_count,
            "mode": mode.value,
        }


# 全局实例（延迟初始化）
_sync_manager: Optional[SyncManager] = None


def get_sync_manager(db_url: str) -> SyncManager:
    """获取同步管理器单例

    Args:
        db_url: 数据库连接 URL

    Returns:
        SyncManager: 同步管理器实例
    """
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager(db_url)
    return _sync_manager
