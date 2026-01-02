"""
后台任务执行器

使用线程池执行阻塞操作，避免阻塞事件循环
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar
from loguru import logger

T = TypeVar('T')


class BackgroundTaskExecutor:
    """后台任务执行器

    使用线程池执行阻塞操作，确保不阻塞事件循环
    """

    def __init__(self, max_workers: int = 3):
        """初始化后台任务执行器

        Args:
            max_workers: 线程池最大工作线程数
        """
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="background_task"
        )

    async def run_in_background(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """在后台线程中执行阻塞函数

        Args:
            func: 要执行的函数（可能是阻塞的）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数的返回值
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: func(*args, **kwargs)
        )

    async def shutdown(self, wait: bool = True):
        """关闭线程池

        Args:
            wait: 是否等待所有任务完成
        """
        self.executor.shutdown(wait=wait)
        logger.info("后台任务执行器已关闭")


# 全局单例
_background_executor: BackgroundTaskExecutor | None = None


def get_background_executor() -> BackgroundTaskExecutor:
    """获取后台任务执行器单例

    Returns:
        BackgroundTaskExecutor: 执行器实例
    """
    global _background_executor
    if _background_executor is None:
        _background_executor = BackgroundTaskExecutor(max_workers=3)
    return _background_executor


# 便捷装饰器
def run_in_background(func):
    """装饰器：将同步函数转换为异步后台执行

    Usage:
        @run_in_background
        def blocking_function(x):
            return x * 2

        # 使用
        result = await blocking_function(5)
    """
    async def wrapper(*args, **kwargs):
        executor = get_background_executor()
        return await executor.run_in_background(func, *args, **kwargs)
    return wrapper
