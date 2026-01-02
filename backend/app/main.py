"""
FastAPI 应用入口
股票选股系统后端主程序
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger, setup_logging


# 设置日志
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期管理

    启动时执行初始化，关闭时清理资源
    """
    # 启动时执行
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    logger.info(f"📦 数据库路径: {settings.DATABASE_URL}")
    logger.info(f"📁 数据目录: {settings.DATA_DIR}")

    # TODO: 初始化数据库
    # from app.db.init_db import init_db
    # init_db()

    # 启动定时任务调度器
    from app.core.scheduler import scheduler
    logger.info("⏰ 启动定时任务调度器...")
    scheduler.start()
    scheduler.load_tasks_from_db()

    yield

    # 关闭时执行
    logger.info("👋 应用关闭...")
    # 关闭调度器
    scheduler.shutdown()


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="个人投研学习平台 - 股票选股系统 API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """请求验证异常处理"""
    logger.warning(f"请求验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求参数验证失败",
            "data": {"errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": {"detail": str(exc) if settings.DEBUG else "内部错误"},
        },
    )


# 根路由
@app.get("/")
async def root() -> dict:
    """根路径"""
    return {
        "code": 200,
        "message": f"欢迎使用 {settings.APP_NAME}",
        "data": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else None,
        },
    }


# 健康检查
@app.get("/health")
async def health_check() -> dict:
    """健康检查接口"""
    return {
        "code": 200,
        "message": "系统运行正常",
        "data": {"status": "healthy"},
    }


# 注册路由
from app.api.v1 import stocks, strategies, tasks, scheduled_tasks, sync, task_management, high_performance_sync

app.include_router(stocks.router, prefix="/api/v1")
app.include_router(strategies.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任务管理"])
app.include_router(scheduled_tasks.router, prefix="/api/v1", tags=["定时任务管理"])
app.include_router(sync.router, prefix="/api/v1")
app.include_router(task_management.router, prefix="/api/v1")
app.include_router(high_performance_sync.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
