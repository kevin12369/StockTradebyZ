"""
股票数据 API 路由

提供股票列表、股票详情、K线数据等接口

功能特性：
1. 股票列表CRUD
2. K线数据查询
3. 单只股票K线同步（增量更新）
4. 批量K线同步
5. K线数据状态查询
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.dependencies import get_db
from app.models.stock import Stock
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.stock import (
    KlineDataRequest,
    KlineDataResponse,
    StockListResponse,
    StockResponse,
)
from app.services.akshare_service import akshare_service

router = APIRouter(prefix="/stocks", tags=["股票数据"])


# ========== 辅助函数 ==========

def filter_normal_stocks(query):
    """过滤掉ST、*ST和退市股票

    排除名称中包含以下关键词的股票：
    - ST: 特别处理
    - *ST: 退市风险警示
    - 退: 退市股票

    Args:
        query: SQLAlchemy查询对象

    Returns:
        过滤后的查询对象
    """
    return query.filter(
        ~Stock.name.like("%ST%"),
        ~Stock.name.like("%*ST%"),
        ~Stock.name.like("%退%"),
    )


# ========== 请求/响应模型 ==========

class BatchSyncRequest(BaseModel):
    """批量同步请求"""
    limit: Optional[int] = None
    force_full_sync: bool = False


class BatchSyncResponse(BaseModel):
    """批量同步响应"""
    success: bool
    message: str
    total: int
    succeeded_count: int
    failed_count: int


# ========== 股票数据接口 ==========

@router.get(
    "",
    response_model=ApiResponse[PageResponse[StockListResponse]],
    summary="获取股票列表",
    description="分页获取股票列表，支持搜索和筛选",
)
async def get_stocks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（股票代码或名称）"),
    market: Optional[str] = Query(None, description="市场筛选（SZ/SH/BJ）"),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[StockListResponse]]:
    """获取股票列表"""
    # 构建查询（过滤掉ST、*ST和退市股票）
    query = db.query(Stock).filter(Stock.is_active == True)
    query = filter_normal_stocks(query)

    # 搜索筛选
    if search:
        query = query.filter(
            (Stock.ts_code.like(f"%{search}%"))
            | (Stock.symbol.like(f"%{search}%"))
            | (Stock.name.like(f"%{search}%"))
        )

    # 市场筛选
    if market:
        query = query.filter(Stock.market == market.upper())

    # 分页
    total = query.count()
    stocks = query.offset((page - 1) * page_size).limit(page_size).all()

    # 格式化响应（包含市场中文名称和板块）
    items = [
        StockListResponse(
            id=s.id,
            ts_code=s.ts_code,
            symbol=s.symbol,
            name=s.name,
            market=s.market,
            market_name=s.market_name,  # 添加市场中文名称
            board=s.board,  # 添加板块信息
        )
        for s in stocks
    ]

    return ApiResponse[PageResponse[StockListResponse]](
        code=200,
        message="success",
        data=PageResponse[StockListResponse](
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        ),
    )


# ========== 涨跌幅统计接口 ==========

@router.get(
    "/realtime/market-overview",
    response_model=ApiResponse[dict],
    summary="获取市场概览（实时）",
    description="从东方财富网获取实时市场概览（主要指数 + 涨跌统计）",
)
async def get_realtime_market_overview() -> ApiResponse[dict]:
    """获取市场概览（东方财富数据源）

    数据来源：东方财富网公开API
    更新频率：实时

    返回数据包括：
    - 主要指数（上证指数、深证成指、创业板指等）
    - 涨跌统计（上涨/平盘/下跌家数、涨停/跌停数量）
    """
    try:
        from app.services.eastmoney_service import eastmoney_service

        result = await eastmoney_service.get_market_overview()

        return ApiResponse[dict](
            code=200,
            message=f"获取到 {len(result['indices'])} 个指数和实时涨跌统计",
            data={
                "indices": result["indices"],
                "stats": result["stats"],
                "source": "eastmoney",
                "realtime": True,
            },
        )
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"获取失败: {str(e)}",
            data=None,
        )


@router.get(
    "/realtime/top-gainers",
    response_model=ApiResponse[dict],
    summary="获取实时涨幅榜",
    description="从东方财富网获取实时涨幅最高的股票（不依赖数据库）",
)
async def get_realtime_top_gainers(
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    market: Optional[str] = Query(None, description="市场筛选：SZ/SH/BJ"),
) -> ApiResponse[dict]:
    """获取实时涨幅榜（东方财富数据源）

    数据来源：东方财富网公开API
    更新频率：实时

    Args:
        limit: 返回股票数量
        market: 市场筛选（None=全部A股、SZ=深圳、SH=上海、BJ=北京）
    """
    try:
        from app.services.eastmoney_service import eastmoney_service

        result = await eastmoney_service.get_top_gainers(
            limit=limit,
            market=market,
        )

        return ApiResponse[dict](
            code=200,
            message=f"获取到 {len(result['data'])} 只股票的涨幅榜数据",
            data={
                "total": result["total"],
                "items": result["data"],
                "source": "eastmoney",
                "realtime": True,
            },
        )
    except Exception as e:
        logger.error(f"获取实时涨幅榜失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"获取失败: {str(e)}",
            data=None,
        )


@router.get(
    "/realtime/top-losers",
    response_model=ApiResponse[dict],
    summary="获取实时跌幅榜",
    description="从东方财富网获取实时跌幅最大的股票（不依赖数据库）",
)
async def get_realtime_top_losers(
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    market: Optional[str] = Query(None, description="市场筛选：SZ/SH/BJ"),
) -> ApiResponse[dict]:
    """获取实时跌幅榜（东方财富数据源）

    数据来源：东方财富网公开API
    更新频率：实时

    Args:
        limit: 返回股票数量
        market: 市场筛选
    """
    try:
        from app.services.eastmoney_service import eastmoney_service

        result = await eastmoney_service.get_top_losers(
            limit=limit,
            market=market,
        )

        return ApiResponse[dict](
            code=200,
            message=f"获取到 {len(result['data'])} 只股票的跌幅榜数据",
            data={
                "total": result["total"],
                "items": result["data"],
                "source": "eastmoney",
                "realtime": True,
            },
        )
    except Exception as e:
        logger.error(f"获取实时跌幅榜失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"获取失败: {str(e)}",
            data=None,
        )


@router.get(
    "/realtime/top-volume",
    response_model=ApiResponse[dict],
    summary="获取成交额榜",
    description="从东方财富网获取实时成交额最大的股票（不依赖数据库）",
)
async def get_realtime_top_volume(
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    market: Optional[str] = Query(None, description="市场筛选：SZ/SH/BJ"),
) -> ApiResponse[dict]:
    """获取实时成交额榜（东方财富数据源）

    数据来源：东方财富网公开API
    更新频率：实时

    Args:
        limit: 返回股票数量
        market: 市场筛选
    """
    try:
        from app.services.eastmoney_service import eastmoney_service

        result = await eastmoney_service.get_top_volume(
            limit=limit,
            market=market,
        )

        return ApiResponse[dict](
            code=200,
            message=f"获取到 {len(result['data'])} 只股票的成交额榜数据",
            data={
                "total": result["total"],
                "items": result["data"],
                "source": "eastmoney",
                "realtime": True,
            },
        )
    except Exception as e:
        logger.error(f"获取实时成交额榜失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"获取失败: {str(e)}",
            data=None,
        )


@router.get(
    "/top-performers",
    response_model=ApiResponse[list],
    summary="获取涨幅榜Top50",
    description="获取指定时间段涨幅最高的50只股票",
)
async def get_top_performers(
    period: str = Query("1day", description="时间周期：1day(今日)、1week(近7日)、1month(近1月)"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
) -> ApiResponse[list]:
    """获取涨幅榜Top50（优先使用预计算数据）"""
    try:
        from app.models.kline import KlineDaily
        from app.models.top_performer import TopPerformer
        from app.services.top_performer_service import TopPerformerService
        from datetime import timedelta, date as date_class
        from sqlalchemy import and_

        # 转换period格式
        period_map = {"1day": "daily", "1week": "weekly", "1month": "monthly"}
        db_period = period_map.get(period, "daily")

        # 优先从数据库获取预计算的涨幅榜数据
        service = TopPerformerService(db)
        cached_data = service.get_top_performers(period=db_period, limit=limit)

        if cached_data and len(cached_data) > 0:
            logger.info(f"从数据库获取涨幅榜数据: {len(cached_data)} 条")
            return ApiResponse[list](
                code=200,
                message=f"获取到 {len(cached_data)} 只股票的涨幅榜数据（已缓存）",
                data=cached_data,
            )

        # 如果没有缓存数据，返回友好提示
        logger.warning(f"数据库中暂无涨幅榜数据（period={period}）")
        return ApiResponse[list](
            code=200,
            message="暂无涨幅榜数据，请先在定时任务中执行'计算涨幅榜'任务，或等待定时任务自动执行",
            data=[],
        )

    except Exception as e:
        logger.error(f"获取涨幅榜失败: {e}")
        return ApiResponse[list](
            code=500,
            message=f"获取失败: {str(e)}",
            data=[],
        )


@router.get(
    "/{ts_code}/kline",
    response_model=ApiResponse[list[KlineDataResponse]],
    summary="获取K线数据",
    description="获取指定股票的K线数据，支持多周期（日/周/月/季/年）",
)
async def get_stock_kline(
    ts_code: str,
    period: str = Query("daily", description="K线周期：daily(日线)、weekly(周线)、monthly(月线)、quarterly(季线)、yearly(年线)"),
    start_date: Optional[str] = Query(None, description="起始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    limit: int = Query(500, ge=1, le=1000, description="返回数据条数限制"),
    db: Session = Depends(get_db),
) -> ApiResponse[list[KlineDataResponse]]:
    """获取K线数据（支持多周期）"""
    # 检查股票是否存在
    stock = db.query(Stock).filter(Stock.ts_code == ts_code.upper()).first()
    if not stock:
        return ApiResponse[list[KlineDataResponse]](
            code=404,
            message="股票不存在",
            data=None,
        )

    # 查询K线数据
    from app.models.kline import KlineDaily

    query = db.query(KlineDaily).filter(KlineDaily.ts_code == ts_code.upper())

    # 日期筛选
    if start_date:
        try:
            s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(KlineDaily.trade_date >= s_date)
        except ValueError:
            pass

    if end_date:
        try:
            e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(KlineDaily.trade_date <= e_date)
        except ValueError:
            pass

    # 排序并限制数量（获取足够的日线数据用于聚合）
    # 周期越大需要的数据越多：周线*5，月线*22，季线*66，年线*264
    period_multiplier = {"daily": 1, "weekly": 5, "monthly": 22, "quarterly": 66, "yearly": 264}
    multiplier = period_multiplier.get(period, 1)
    actual_limit = min(limit * multiplier, 2000)  # 最多2000条日线数据

    klines = query.order_by(KlineDaily.trade_date.desc()).limit(actual_limit).all()
    klines = list(reversed(klines))  # 按日期升序

    # 如果不是日线，进行聚合计算
    if period != "daily" and len(klines) > 0:
        klines = _aggregate_klines(klines, period, ts_code.upper())

    # 最终限制返回数量
    klines = klines[-limit:] if len(klines) > limit else klines

    # 格式化响应
    data = [KlineDataResponse.model_validate(k) for k in klines]

    period_name_map = {
        "daily": "日",
        "weekly": "周",
        "monthly": "月",
        "quarterly": "季",
        "yearly": "年",
    }

    return ApiResponse[list[KlineDataResponse]](
        code=200,
        message=f"获取到 {len(data)} 条{period_name_map.get(period, period)}K线数据",
        data=data,
    )


def _aggregate_klines(daily_klines, period: str, ts_code: str):
    """将日线K线聚合为指定周期的K线

    Args:
        daily_klines: 日线K线数据列表
        period: 目标周期（weekly/monthly/quarterly/yearly）
        ts_code: 股票代码

    Returns:
        聚合后的K线数据字典列表（包含id和ts_code字段）
    """
    if not daily_klines:
        return []

    import pandas as pd
    from decimal import Decimal

    # 转换为DataFrame便于处理
    df = pd.DataFrame([
        {
            "trade_date": k.trade_date,
            "open": float(k.open) if k.open else 0,
            "high": float(k.high) if k.high else 0,
            "low": float(k.low) if k.low else 0,
            "close": float(k.close) if k.close else 0,
            "volume": int(k.volume) if k.volume else 0,
            "amount": float(k.amount) if k.amount else 0,
        }
        for k in daily_klines
    ])

    if df.empty:
        return []

    # 设置日期为索引
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df.set_index("trade_date", inplace=True)

    # 确定聚合规则
    if period == "weekly":
        rule = "W"
    elif period == "monthly":
        rule = "ME"
    elif period == "quarterly":
        rule = "QE"
    elif period == "yearly":
        rule = "YE"
    else:
        rule = "D"

    # 聚合OHLCV数据
    agg_df = df.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "amount": "sum",
    }).dropna()

    # 转换为字典格式（直接返回字典，让Pydantic自动验证）
    result = []
    for idx, (date, row) in enumerate(agg_df.iterrows()):
        result.append({
            "id": idx,  # 使用索引作为伪ID
            "ts_code": ts_code,
            "trade_date": date.date(),
            "open": Decimal(str(row["open"])),
            "high": Decimal(str(row["high"])),
            "low": Decimal(str(row["low"])),
            "close": Decimal(str(row["close"])),
            "volume": int(row["volume"]),
            "amount": Decimal(str(row["amount"])),
        })

    return result


@router.get(
    "/{ts_code}",
    response_model=ApiResponse[StockResponse],
    summary="获取股票详情",
    description="根据股票代码获取股票详细信息",
)
async def get_stock(
    ts_code: str,
    db: Session = Depends(get_db),
) -> ApiResponse[StockResponse]:
    """获取股票详情"""
    stock = db.query(Stock).filter(Stock.ts_code == ts_code.upper()).first()

    if not stock:
        return ApiResponse[StockResponse](
            code=404,
            message="股票不存在",
            data=None,
        )

    return ApiResponse[StockResponse](
        code=200,
        message="success",
        data=StockResponse.model_validate(stock),
    )


# ========== 数据同步接口 ==========

@router.post(
    "/sync",
    response_model=ApiResponse[dict],
    summary="同步股票列表",
    description="从 AKShare 同步最新的股票列表到数据库（增量更新）",
)
async def sync_stock_list(
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """同步股票列表（增量更新）"""
    try:
        result = akshare_service.sync_stock_list_to_db(db)

        return ApiResponse[dict](
            code=200 if result["success"] else 500,
            message=result["message"],
            data=result,
        )
    except Exception as e:
        logger.error(f"同步股票列表失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"同步失败: {str(e)}",
            data=None,
        )


@router.post(
    "/{ts_code}/kline/sync",
    response_model=ApiResponse[dict],
    summary="同步单只股票K线数据",
    description="从 AKShare 同步指定股票的K线数据（增量更新）",
)
async def sync_stock_kline(
    ts_code: str,
    force_full_sync: bool = Query(False, description="是否强制全量同步"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """同步单只股票K线数据（增量更新）"""
    # 检查股票是否存在
    stock = db.query(Stock).filter(Stock.ts_code == ts_code.upper()).first()
    if not stock:
        return ApiResponse[dict](
            code=404,
            message="股票不存在",
            data=None,
        )

    try:
        result = akshare_service.sync_stock_kline_to_db(
            db,
            stock.ts_code,
            force_full_sync=force_full_sync,
        )

        return ApiResponse[dict](
            code=200 if result["success"] else 500,
            message=result["message"],
            data=result,
        )
    except Exception as e:
        logger.error(f"同步K线数据失败 ({ts_code}): {e}")
        return ApiResponse[dict](
            code=500,
            message=f"同步失败: {str(e)}",
            data=None,
        )


@router.post(
    "/kline/batch-sync",
    response_model=ApiResponse[dict],
    summary="批量同步K线数据（异步任务）",
    description="批量同步多只股票的K线数据（优先同步数据最旧的股票），返回任务ID供查询进度",
)
async def batch_sync_kline(
    request: BatchSyncRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """批量同步K线数据（异步任务版本）

    新版本特性：
    - 使用任务队列异步执行
    - 自动速率限制（每5秒1个请求，避免被AKShare拒绝连接）
    - 返回任务ID供查询进度
    - 支持任务状态追踪
    - 防止重复提交（同一时间只能有一个批量同步任务）

    策略：
    - 按照最新K线日期排序，优先同步数据最旧的股票
    - 如果指定了 limit，则只同步前 N 只股票
    - force_full_sync=True 时强制全量同步（获取近3年数据）
    - force_full_sync=False 时增量更新（只获取缺失的数据）
    """
    try:
        from app.services.task_queue import task_queue
        from app.services.akshare_service import akshare_service

        # 检查是否已有批量同步任务正在运行
        if task_queue.has_running_task_of_type("batch_sync_kline"):
            return ApiResponse[dict](
                code=400,
                message="已有批量同步任务正在执行，请等待当前任务完成后再提交",
                data=None,
            )

        # 创建任务执行器
        async def executor(task, rate_limiter):
            result = await akshare_service.async_batch_sync_kline_to_db(
                db,
                task_info=task,
                rate_limiter=rate_limiter,
                limit=request.limit,
                force_full_sync=request.force_full_sync,
                only_active=True,
            )
            task.result = result
            task.message = result.get("message", "批量同步完成")

        # 提交任务到队列
        task_id = await task_queue.submit(
            task_type="batch_sync_kline",
            params={
                "limit": request.limit,
                "force_full_sync": request.force_full_sync,
                "only_active": True,
            },
            executor=executor,
        )

        return ApiResponse[dict](
            code=200,
            message="批量同步任务已提交，请使用task_id查询进度",
            data={
                "task_id": task_id,
                "status": "pending",
                "message": "任务已加入队列，等待执行",
            },
        )
    except Exception as e:
        logger.error(f"提交批量同步任务失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"提交任务失败: {str(e)}",
            data=None,
        )


# ========== 数据状态接口 ==========

@router.get(
    "/kline/status",
    response_model=ApiResponse[list],
    summary="获取K线数据状态",
    description="获取所有股票的K线数据状态（是否有数据、最新日期等）",
)
async def get_kline_status(
    limit: Optional[int] = Query(None, description="限制返回数量"),
    db: Session = Depends(get_db),
) -> ApiResponse[list]:
    """获取K线数据状态"""
    try:
        status_list = akshare_service.get_stocks_kline_status(db, limit=limit)

        return ApiResponse[list](
            code=200,
            message=f"获取到 {len(status_list)} 只股票的状态",
            data=status_list,
        )
    except Exception as e:
        logger.error(f"获取K线数据状态失败: {e}")
        return ApiResponse[list](
            code=500,
            message=f"获取失败: {str(e)}",
            data=[],
        )


# ========== 智能分批同步接口 ==========

@router.get(
    "/kline/batch/progress",
    response_model=ApiResponse[dict],
    summary="获取智能分批同步进度",
    description="获取当前同步进度和统计信息",
)
async def get_batch_sync_progress(
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """获取智能分批同步进度"""
    try:
        from app.services.batch_sync_manager import batch_sync_manager

        progress = batch_sync_manager.get_sync_progress(db)

        return ApiResponse[dict](
            code=200,
            message="获取同步进度成功",
            data=progress,
        )
    except Exception as e:
        logger.error(f"获取同步进度失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"获取失败: {str(e)}",
            data=None,
        )


@router.post(
    "/kline/batch/create-batches",
    response_model=ApiResponse[dict],
    summary="创建智能分批同步计划",
    description="分析并创建分批同步计划（不立即执行）",
)
async def create_sync_batches(
    force_full_sync: bool = Query(False, description="是否强制全量同步"),
    batch_size: int = Query(500, description="每批股票数量"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """创建智能分批同步计划"""
    try:
        from app.services.batch_sync_manager import BatchSyncManager

        manager = BatchSyncManager(batch_size=batch_size)
        batches, batch_id_prefix = manager.create_batches(db, force_full_sync=force_full_sync)

        # 提取批次信息（不包含完整的stock对象）
        batch_info = []
        for batch in batches:
            batch_info.append({
                'batch_id': batch['batch_id'],
                'batch_index': batch['batch_index'],
                'total_batches': batch['total_batches'],
                'stock_count': batch['stock_count'],
                'status': batch['status'],
                'created_at': batch['created_at'].isoformat(),
            })

        return ApiResponse[dict](
            code=200,
            message=f"创建 {len(batches)} 个批次",
            data={
                'batch_id_prefix': batch_id_prefix,
                'total_batches': len(batches),
                'total_stocks': sum(b['stock_count'] for b in batches),
                'batches': batch_info,
            },
        )
    except Exception as e:
        logger.error(f"创建批次失败: {e}")
        import traceback
        return ApiResponse[dict](
            code=500,
            message=f"创建失败: {str(e)}\n{traceback.format_exc()}",
            data=None,
        )


@router.post(
    "/kline/batch/execute-single",
    response_model=ApiResponse[dict],
    summary="执行单个批次（同步）",
    description="执行单个批次的同步（用于测试或手动执行）",
)
async def execute_single_batch(
    batch_index: int = Query(..., description="批次索引（从1开始）"),
    batch_id_prefix: str = Query(..., description="批次ID前缀（来自createSyncBatches响应）"),
    force_full_sync: bool = Query(False, description="是否强制全量同步"),
    batch_size: int = Query(500, description="每批股票数量"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """执行单个批次（同步执行，用于测试）"""
    try:
        from app.services.batch_sync_manager import BatchSyncManager

        manager = BatchSyncManager(batch_size=batch_size)
        # 使用提供的批次ID前缀创建批次（确保batch_id一致）
        batches, _ = manager.create_batches(db, force_full_sync=force_full_sync, batch_id_prefix=batch_id_prefix)

        if batch_index < 1 or batch_index > len(batches):
            return ApiResponse[dict](
                code=400,
                message=f"批次索引无效，有效范围：1-{len(batches)}",
                data=None,
            )

        batch = batches[batch_index - 1]
        result = manager.execute_batch(db, batch, force_full_sync=force_full_sync)

        return ApiResponse[dict](
            code=200,
            message=f"批次 {batch_index} 执行完成",
            data=result,
        )
    except Exception as e:
        logger.error(f"执行批次失败: {e}")
        import traceback
        return ApiResponse[dict](
            code=500,
            message=f"执行失败: {str(e)}\n{traceback.format_exc()}",
            data=None,
        )


@router.get(
    "/kline/batch/execution-progress",
    response_model=ApiResponse[dict],
    summary="获取批次执行进度",
    description="获取正在执行的批次的实时进度",
)
async def get_batch_execution_progress(
    batch_id: str = Query(..., description="批次ID"),
):
    """获取批次执行进度"""
    try:
        from app.services.batch_sync_manager import BatchSyncManager

        progress = BatchSyncManager.get_batch_execution_progress(batch_id)

        if progress is None:
            return ApiResponse[dict](
                code=404,
                message=f"批次 {batch_id} 不存在或未开始执行",
                data=None,
            )

        return ApiResponse[dict](
            code=200,
            message="获取进度成功",
            data=progress,
        )
    except Exception as e:
        logger.error(f"获取批次进度失败: {e}")
        return ApiResponse[dict](
            code=500,
            message=f"获取失败: {str(e)}",
            data=None,
        )
