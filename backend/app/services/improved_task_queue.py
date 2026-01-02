"""
改进的任务队列

支持：
1. 真正的后台异步执行（不阻塞事件循环）
2. 任务取消功能
3. 实时进度报告
4. 批次执行（可中断）
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from loguru import logger


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"  # 新增：暂停状态
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CancellableTask:
    """可取消的任务包装器"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._should_cancel = False
        self._is_paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # 初始为运行状态

    def check_cancelled(self) -> bool:
        """检查是否需要取消"""
        return self._should_cancel

    def request_cancel(self):
        """请求取消任务"""
        self._should_cancel = True

    def is_paused(self) -> bool:
        """检查是否暂停"""
        return self._is_paused

    def pause(self):
        """暂停任务"""
        self._is_paused = True
        self._pause_event.clear()

    def resume(self):
        """恢复任务"""
        self._is_paused = False
        self._pause_event.set()

    async def wait_if_paused(self):
        """如果暂停则等待恢复"""
        while self._is_paused:
            await self._pause_event.wait()


class TaskInfo:
    """改进的任务信息类"""

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

        # 可取消控制器
        self.controller: Optional[CancellableTask] = None

        # 详细进度信息
        self.details: Dict[str, Any] = {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "params": self.params,
            "status": self.status.value,
            "progress": round(self.progress, 2),
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "details": self.details,
        }

    def update_progress(
        self,
        progress: float,
        message: str = "",
        **details
    ):
        """更新进度

        Args:
            progress: 进度百分比 (0-100)
            message: 进度消息
            **details: 额外的详细信息
        """
        self.progress = progress
        if message:
            self.message = message
        self.details.update(details)


class ImprovedTaskQueue:
    """改进的任务队列

    特性：
    1. 支持任务取消和暂停
    2. 实时进度更新
    3. 批次执行，可中断
    """

    def __init__(self, max_workers: int = 1):
        """初始化任务队列

        Args:
            max_workers: 最大并发任务数
        """
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[str, TaskInfo] = {}
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.max_workers = max_workers
        self.current_tasks: Dict[str, asyncio.Task] = {}

    def has_running_task_of_type(self, task_type: str) -> bool:
        """检查是否有指定类型的任务正在运行"""
        for task in self.tasks.values():
            if task.task_type == task_type and task.status in [
                TaskStatus.PENDING,
                TaskStatus.RUNNING,
                TaskStatus.PAUSED,
            ]:
                return True
        return False

    async def submit(
        self,
        task_type: str,
        params: Dict[str, Any],
        executor: Callable,
    ) -> str:
        """提交任务到队列"""
        task_id = str(uuid4())

        task = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            params=params,
            status=TaskStatus.PENDING,
            message="任务已加入队列，等待执行",
        )
        task.controller = CancellableTask(task_id)

        self.tasks[task_id] = task
        await self.queue.put((task_id, executor))

        # 启动工作线程
        if not self.is_running:
            await self.start()

        logger.info(f"任务已提交: {task_type} - {task_id}")
        return task_id

    async def start(self) -> None:
        """启动工作线程"""
        if self.is_running:
            return

        self.is_running = True
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker(i))
            self.worker_tasks.append(worker_task)

        logger.info(f"任务队列已启动（{self.max_workers}个工作线程）")

    async def stop(self) -> None:
        """停止工作线程"""
        self.is_running = False

        # 取消所有工作线程
        for worker_task in self.worker_tasks:
            worker_task.cancel()

        # 等待所有工作线程结束
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()

        logger.info("任务队列已停止")

    async def _worker(self, worker_id: int) -> None:
        """工作线程"""
        logger.info(f"工作线程 #{worker_id} 开始运行")

        while self.is_running:
            try:
                # 从队列获取任务
                task_id, executor = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )

                task = self.tasks.get(task_id)
                if not task:
                    continue

                # 检查是否已被取消
                if task.controller.check_cancelled():
                    task.status = TaskStatus.CANCELLED
                    task.message = "任务在执行前被取消"
                    continue

                # 更新任务状态
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                task.message = "任务正在执行..."
                task.progress = 0.0

                self.current_tasks[task_id] = asyncio.current_task()

                try:
                    # 执行任务
                    await executor(task, task.controller)

                    # 更新成功状态
                    if not task.controller.check_cancelled():
                        task.status = TaskStatus.SUCCESS
                        task.completed_at = datetime.now()
                        task.progress = 100.0
                        task.message = "任务执行成功"
                        logger.info(f"任务执行成功: {task.task_type} - {task_id}")
                    else:
                        task.status = TaskStatus.CANCELLED
                        task.completed_at = datetime.now()
                        task.message = "任务已被取消"

                except asyncio.CancelledError:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.now()
                    task.message = "任务被系统中断"
                    logger.info(f"任务被取消: {task.task_type} - {task_id}")

                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    task.error = str(e)
                    task.message = f"任务执行失败: {str(e)}"
                    logger.error(f"任务执行失败: {task.task_type} - {task_id}: {e}")

                finally:
                    self.current_tasks.pop(task_id, None)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info(f"工作线程 #{worker_id} 被取消")
                break
            except Exception as e:
                logger.error(f"工作线程 #{worker_id} 异常: {e}")

        logger.info(f"工作线程 #{worker_id} 已退出")

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskInfo]:
        """获取所有任务信息"""
        return list(self.tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        # 如果任务还没开始执行
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.message = "任务已被取消（未开始执行）"
            logger.info(f"任务已取消: {task_id}")
            return True

        # 如果任务正在执行
        if task.status == TaskStatus.RUNNING and task.controller:
            task.controller.request_cancel()
            task.message = "正在取消任务..."
            logger.info(f"请求取消任务: {task_id}")
            return True

        return False

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        task = self.tasks.get(task_id)
        if task and task.controller and task.status == TaskStatus.RUNNING:
            task.controller.pause()
            task.status = TaskStatus.PAUSED
            task.message = "任务已暂停"
            logger.info(f"任务已暂停: {task_id}")
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        task = self.tasks.get(task_id)
        if task and task.controller and task.status == TaskStatus.PAUSED:
            task.controller.resume()
            task.status = TaskStatus.RUNNING
            task.message = "任务已恢复"
            logger.info(f"任务已恢复: {task_id}")
            return True
        return False


# 全局实例（替换原有的 task_queue）
improved_task_queue = ImprovedTaskQueue(max_workers=2)
