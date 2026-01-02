"""
日志配置模块
"""

import logging
import sys
from pathlib import Path

from loguru import logger as loguru_logger

from app.core.config import settings


def setup_logging() -> None:
    """配置应用日志

    使用 loguru 替代默认的 logging，提供更强大的日志功能
    """

    # 移除默认的 handler
    loguru_logger.remove()

    # 控制台输出格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 添加控制台 handler
    loguru_logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # 添加文件 handler
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    loguru_logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",  # 日志文件大小达到 10MB 时轮转
        retention="30 days",  # 保留 30 天的日志
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,  # 使用队列避免多进程写入冲突
        delay=True,  # 延迟文件创建，直到第一条日志写入时才创建
    )

    # 拦截标准 logging 模块的日志
    class InterceptHandler(logging.Handler):
        """将标准 logging 日志转发到 loguru"""

        def emit(self, record: logging.LogRecord) -> None:
            # 只记录WARNING及以上级别的日志，过滤INFO和DEBUG
            if record.levelno < logging.WARNING:
                return

            # 获取对应的 loguru level
            try:
                level = loguru_logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # 查找调用者
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            loguru_logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # 配置标准 logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # 只记录警告和错误
    logging.getLogger("fastapi").handlers = [InterceptHandler()]
    logging.getLogger("sqlalchemy").handlers = [InterceptHandler()]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # 只记录SQL警告和错误
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)


# 导出 logger
logger = loguru_logger
