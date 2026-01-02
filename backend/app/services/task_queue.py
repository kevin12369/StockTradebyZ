"""
异步任务队列服务

提供任务排队、速率限制、异步执行等功能
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

import sqlalchemy
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.backtest import DataUpdateLog


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"    # 失败
    CANCELLED = "cancelled"  # 已取消


class TaskInfo:
    """任务信息类"""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        params: Dict[str, Any],
        status: TaskStatus = TaskStatus.PENDING,
        progress: float = 0.0,
        message: str = "",
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        created_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.params = params
        self.status = status
        self.progress = progress
        self.message = message
        self.result = result
        self.error = error
        self.created_at = created_at or datetime.now()
        self.started_at = started_at
        self.completed_at = completed_at

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "params": self.params,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class RateLimiter:
    """速率限制器

    控制请求频率，避免对服务器造成过大压力
    """

    def __init__(
        self,
        requests_per_second: float = 0.2,  # 每秒最多请求数（默认0.2，即每5秒1个请求，批量查询优化后）
        burst_size: int = 3,  # 突发请求数（默认3，容忍时间波动，减少累积误差）
    ):
        """
        Args:
            requests_per_second: 每秒最多请求数（默认0.2，即每5秒1个请求）
            burst_size: 突发请求容量（默认3，可容忍15秒的突发请求）
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """获取令牌（优化版：减少累积误差）

        Args:
            tokens: 需要的令牌数
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # 补充令牌
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.requests_per_second
            )

            # 等待足够的令牌
            while self.tokens < tokens:
                # 计算需要等待的时间（精确计算，减少循环次数）
                needed = tokens - self.tokens
                wait_time = needed / self.requests_per_second

                # 最多等待1秒，避免长时间阻塞
                wait_time = min(wait_time, 1.0)

                # 等待并补充令牌
                await asyncio.sleep(wait_time)

                now = time.time()
                elapsed = now - self.last_update
                self.last_update = now
                self.tokens = min(
                    self.burst_size,
                    self.tokens + elapsed * self.requests_per_second
                )

            # 消耗令牌
            self.tokens -= tokens


class TaskQueue:
    """异步任务队列

    提供任务排队、执行、状态查询等功能
    """

    def __init__(self):
        """初始化任务队列"""
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[str, TaskInfo] = {}
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.rate_limiter = RateLimiter(
            requests_per_second=0.2,  # 每5秒1个请求（批量查询优化后，实际执行时间≈5秒）
            burst_size=3  # 增加突发大小，容忍时间波动，减少累积误差
        )

    def has_running_task_of_type(self, task_type: str) -> bool:
        """检查是否有指定类型的任务正在运行

        Args:
            task_type: 任务类型

        Returns:
            是否有正在运行的任务
        """
        for task in self.tasks.values():
            if task.task_type == task_type and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                return True
        return False

    async def submit(
        self,
        task_type: str,
        params: Dict[str, Any],
        executor: Callable,
    ) -> str:
        """提交任务到队列

        Args:
            task_type: 任务类型（sync_stock_list/sync_kline/batch_sync_kline）
            params: 任务参数
            executor: 任务执行函数

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid4())

        task = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            params=params,
            status=TaskStatus.PENDING,
            message="任务已加入队列，等待执行",
        )

        self.tasks[task_id] = task
        await self.queue.put((task_id, executor))

        # 启动工作线程（如果还没启动）
        if not self.is_running:
            await self.start()

        logger.info(f"任务已提交: {task_type} - {task_id}")
        return task_id

    async def start(self) -> None:
        """启动工作线程"""
        if self.is_running:
            return

        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())

        logger.info("任务队列工作线程已启动")

    async def stop(self) -> None:
        """停止工作线程"""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        logger.info("任务队列工作线程已停止")

    async def _worker(self) -> None:
        """工作线程，从队列中取任务并执行"""
        logger.info("工作线程开始运行")

        while self.is_running:
            try:
                # 从队列获取任务（超时1秒）
                task_id, executor = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )

                task = self.tasks.get(task_id)
                if not task:
                    continue

                # 更新任务状态
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                task.message = "任务正在执行..."
                task.progress = 0.0

                try:
                    # 执行任务
                    await executor(task, self.rate_limiter)

                    # 更新成功状态
                    task.status = TaskStatus.SUCCESS
                    task.completed_at = datetime.now()
                    task.progress = 100.0
                    task.message = "任务执行成功"

                    logger.info(f"任务执行成功: {task.task_type} - {task_id}")

                except Exception as e:
                    # 更新失败状态
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    task.error = str(e)
                    task.message = f"任务执行失败: {str(e)}"

                    logger.error(f"任务执行失败: {task.task_type} - {task_id}: {e}")

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info("工作线程被取消")
                break
            except Exception as e:
                logger.error(f"工作线程异常: {e}")

        logger.info("工作线程已退出")

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息，不存在则返回None
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskInfo]:
        """获取所有任务信息

        Returns:
            所有任务列表
        """
        return list(self.tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.message = "任务已被取消"
            logger.info(f"任务已取消: {task_id}")
            return True
        return False


# 全局任务队列实例
task_queue = TaskQueue()
