"""
选股策略 API 路由

提供策略管理、策略执行、选股结果等接口
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.dependencies import get_db
from app.models.backtest import SelectionResult
from app.models.strategy import Strategy
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.strategy import (
    SelectionResultResponse,
    StrategyExecuteRequest,
    StrategyExecuteResponse,
    StrategyResponse,
    StrategyUpdate,
)
from app.services.strategy_service import strategy_service

router = APIRouter(prefix="/strategies", tags=["选股策略"])


# ============================================================================
# 固定路径路由（必须在参数路由之前）
# ============================================================================

@router.post(
    "/run",
    response_model=ApiResponse[list[StrategyExecuteResponse]],
    summary="执行选股策略",
    description="批量执行选股策略并保存结果",
)
async def run_strategies(
    request: StrategyExecuteRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[list[StrategyExecuteResponse]]:
    """执行选股策略"""
    try:
        # 解析日期
        trade_date = None
        if request.trade_date:
            try:
                trade_date = datetime.strptime(request.trade_date, "%Y-%m-%d").date()
            except ValueError:
                return ApiResponse[list[StrategyExecuteResponse]](
                    code=400,
                    message="日期格式错误，请使用 YYYY-MM-DD 格式",
                    data=None,
                )

        # 执行策略
        results = strategy_service.execute_strategies(
            db,
            strategy_ids=request.strategy_ids,
            trade_date=trade_date,
        )

        # 格式化响应
        data = [StrategyExecuteResponse(**r) for r in results]

        return ApiResponse[list[StrategyExecuteResponse]](
            code=200,
            message="执行完成",
            data=data,
        )
    except Exception as e:
        logger.error(f"执行策略失败: {e}")
        return ApiResponse[list[StrategyExecuteResponse]](
            code=500,
            message=f"执行失败: {str(e)}",
            data=None,
        )


@router.get(
    "/results",
    response_model=ApiResponse[PageResponse[SelectionResultResponse]],
    summary="获取选股结果",
    description="分页获取选股结果，支持按策略和日期筛选",
)
async def get_selection_results(
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    trade_date: Optional[str] = Query(None, description="选股日期（YYYY-MM-DD）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[SelectionResultResponse]]:
    """获取选股结果"""
    # 解析日期
    parsed_date = None
    if trade_date:
        try:
            parsed_date = datetime.strptime(trade_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # 获取结果
    result = strategy_service.get_selection_results(
        db,
        strategy_id=strategy_id,
        trade_date=parsed_date,
        page=page,
        page_size=page_size,
    )

    # 格式化数据
    items = []
    for item in result["items"]:
        # 解析 reason JSON
        import json
        reason_data = {}
        if item.get("reason"):
            try:
                reason_data = json.loads(item["reason"])
            except:
                reason_data = {}

        # 获取股票名称和策略别名
        from app.models.stock import Stock
        from app.models.strategy import Strategy

        stock = db.query(Stock).filter(Stock.ts_code == item["ts_code"]).first()
        strategy = db.query(Strategy).filter(Strategy.id == item["strategy_id"]).first()

        if stock:
            reason_data["name"] = stock.name
            reason_data["symbol"] = stock.symbol
        if strategy:
            reason_data["strategy_alias"] = strategy.alias

        # 更新 item 的 reason
        item["reason"] = reason_data

        items.append(SelectionResultResponse(**item))

    return ApiResponse[PageResponse[SelectionResultResponse]](
        code=200,
        message="success",
        data=PageResponse[SelectionResultResponse](
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            items=items,
        ),
    )


@router.get(
    "/results/stats",
    response_model=ApiResponse[dict],
    summary="获取选股统计",
    description="获取选股结果的统计数据",
)
async def get_selection_stats(
    trade_date: Optional[str] = Query(None, description="选股日期（YYYY-MM-DD）"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """获取选股统计"""
    # 解析日期
    parsed_date = None
    if trade_date:
        try:
            parsed_date = datetime.strptime(trade_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # 构建查询
    query = db.query(SelectionResult)

    if parsed_date:
        query = query.filter(SelectionResult.trade_date == parsed_date)

    # 按策略统计
    from sqlalchemy import func

    stats = (
        query.with_entities(
            SelectionResult.strategy_id,
            Strategy.alias,
            func.count(SelectionResult.id).label("count"),
        )
        .join(Strategy, SelectionResult.strategy_id == Strategy.id)
        .group_by(SelectionResult.strategy_id, Strategy.alias)
        .all()
    )

    # 格式化结果
    data = {
        "trade_date": parsed_date.isoformat() if parsed_date else None,
        "strategies": [
            {"strategy_id": s[0], "strategy_alias": s[1], "count": s[2]}
            for s in stats
        ],
        "total": sum(s[2] for s in stats),
    }

    return ApiResponse[dict](
        code=200,
        message="success",
        data=data,
    )


# ============================================================================
# 参数路由（放在最后）
# ============================================================================

@router.get(
    "",
    response_model=ApiResponse[list[StrategyResponse]],
    summary="获取策略列表",
    description="获取所有选股策略",
)
async def get_strategies(
    is_active: Optional[bool] = Query(None, description="是否仅显示启用的策略"),
    db: Session = Depends(get_db),
) -> ApiResponse[list[StrategyResponse]]:
    """获取策略列表"""
    query = db.query(Strategy)

    if is_active is not None:
        query = query.filter(Strategy.is_active == is_active)

    strategies = query.order_by(Strategy.sort_order).all()

    data = [StrategyResponse.model_validate(s) for s in strategies]

    return ApiResponse[list[StrategyResponse]](
        code=200,
        message="success",
        data=data,
    )


@router.get(
    "/{strategy_id}",
    response_model=ApiResponse[StrategyResponse],
    summary="获取策略详情",
    description="根据策略ID获取策略详细信息",
)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[StrategyResponse]:
    """获取策略详情"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

    if not strategy:
        return ApiResponse[StrategyResponse](
            code=404,
            message="策略不存在",
            data=None,
        )

    return ApiResponse[StrategyResponse](
        code=200,
        message="success",
        data=StrategyResponse.model_validate(strategy),
    )


@router.put(
    "/{strategy_id}",
    response_model=ApiResponse[StrategyResponse],
    summary="更新策略配置",
    description="更新策略的配置参数",
)
async def update_strategy(
    strategy_id: int,
    update_data: StrategyUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[StrategyResponse]:
    """更新策略配置"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

    if not strategy:
        return ApiResponse[StrategyResponse](
            code=404,
            message="策略不存在",
            data=None,
        )

    # 更新字段
    if update_data.alias is not None:
        strategy.alias = update_data.alias
    if update_data.description is not None:
        strategy.description = update_data.description
    if update_data.is_active is not None:
        strategy.is_active = update_data.is_active
    if update_data.config_json is not None:
        strategy.config_json = update_data.config_json
    if update_data.sort_order is not None:
        strategy.sort_order = update_data.sort_order

    db.commit()
    db.refresh(strategy)

    return ApiResponse[StrategyResponse](
        code=200,
        message="更新成功",
        data=StrategyResponse.model_validate(strategy),
    )
