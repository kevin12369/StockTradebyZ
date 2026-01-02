"""
选股策略服务

封装现有 Selector.py 的策略逻辑，提供统一的服务接口
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径，以便导入 Selector
# strategy_service.py 位置: backend/app/services/
# 需要向上3级到项目根目录: services/ -> app/ -> backend/ -> 根目录
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from Selector import (
    BBIKDJSelector,
    SuperB1Selector,
    BBIShortLongSelector,
    PeakKDJSelector,
    MA60CrossVolumeWaveSelector,
)

from app.core.logging import logger
from app.models.backtest import SelectionResult
from app.models.kline import KlineDaily
from app.models.stock import Stock
from app.models.strategy import Strategy


# 策略类映射
STRATEGY_CLASS_MAP = {
    "BBIKDJSelector": BBIKDJSelector,
    "SuperB1Selector": SuperB1Selector,
    "BBIShortLongSelector": BBIShortLongSelector,
    "PeakKDJSelector": PeakKDJSelector,
    "MA60CrossVolumeWaveSelector": MA60CrossVolumeWaveSelector,
}


class StrategyService:
    """选股策略服务类

    提供：
    1. 执行选股策略
    2. 保存选股结果
    3. 获取选股结果
    """

    def __init__(self):
        """初始化服务"""
        self.strategy_map = STRATEGY_CLASS_MAP

    def _load_kline_from_db(
        self,
        db: Session,
        ts_code: str,
        max_window: int = 120,
    ) -> pd.DataFrame:
        """从数据库加载K线数据

        Args:
            db: 数据库会话
            ts_code: 股票代码
            max_window: 最大窗口大小

        Returns:
            K线数据 DataFrame
        """
        # 查询最近 max_window 天的数据
        query = (
            db.query(KlineDaily)
            .filter(KlineDaily.ts_code == ts_code)
            .order_by(KlineDaily.trade_date.desc())
            .limit(max_window)
        )

        klines = query.all()

        if not klines:
            return pd.DataFrame()

        # 转换为 DataFrame 并按日期升序排列
        data = {
            "date": [],
            "open": [],
            "close": [],
            "high": [],
            "low": [],
            "volume": [],
        }

        for kline in reversed(klines):
            data["date"].append(kline.trade_date)
            data["open"].append(float(kline.open) if kline.open else 0)
            data["close"].append(float(kline.close) if kline.close else 0)
            data["high"].append(float(kline.high) if kline.high else 0)
            data["low"].append(float(kline.low) if kline.low else 0)
            data["volume"].append(int(kline.volume) if kline.volume else 0)

        df = pd.DataFrame(data)
        # 将 date 列转换为 pd.Timestamp，避免与 select_timestamp 比较时报错
        df["date"] = pd.to_datetime(df["date"])
        return df

    def _get_strategy_instance(
        self, strategy_class: str, params: Dict[str, Any]
    ) -> Any:
        """获取策略实例

        Args:
            strategy_class: 策略类名
            params: 策略参数

        Returns:
            策略实例

        Raises:
            ValueError: 策略类不存在
        """
        if strategy_class not in self.strategy_map:
            raise ValueError(f"未知的策略类: {strategy_class}")

        strategy_cls = self.strategy_map[strategy_class]
        return strategy_cls(**params)

    def execute_strategy(
        self,
        db: Session,
        strategy_id: int,
        trade_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """执行单个选股策略

        Args:
            db: 数据库会话
            strategy_id: 策略ID
            trade_date: 选股日期（默认为最新交易日）

        Returns:
            选股结果统计
        """
        # 获取策略配置
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise ValueError(f"策略不存在: id={strategy_id}")

        if not strategy.is_active:
            logger.warning(f"策略未启用: {strategy.alias}")
            return {"success": False, "message": "策略未启用", "count": 0}

        # 解析策略参数
        params = json.loads(strategy.config_json)

        logger.info(f"🔄 开始执行策略: {strategy.alias}")

        # 获取策略实例
        try:
            selector = self._get_strategy_instance(strategy.class_name, params)
        except ValueError as e:
            logger.error(f"❌ {e}")
            raise

        # 获取所有股票列表（过滤掉ST、*ST和退市股票）
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        # 过滤掉ST、*ST和退市股票
        stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

        if not stocks:
            logger.warning("没有可用的股票数据")
            return {"success": False, "message": "没有可用股票", "count": 0}

        # 准备数据：构建原始 Selector.select() 需要的格式
        # Dict[str, pd.DataFrame]，key 为 ts_code，value 为 K线数据
        stock_data_map: Dict[str, pd.DataFrame] = {}

        # 预先计算需要的最大窗口大小
        max_window = params.get("max_window", 120)
        max_lookback = max_window

        # 检查是否是 SuperB1Selector（需要更大的窗口）
        if strategy.class_name == "SuperB1Selector":
            max_lookback = max(max_lookback, params.get("lookback_n", 60) + max_window)

        logger.info(f"开始加载 {len(stocks)} 只股票的K线数据...")

        for stock in stocks:
            df = self._load_kline_from_db(db, stock.ts_code, max_window=max_lookback + 20)

            if not df.empty and len(df) >= 60:
                # 原始 Selector 期望列名为 "date" 而不是 "trade_date"
                df = df.rename(columns={"trade_date": "date"})
                stock_data_map[stock.ts_code] = df

        if not stock_data_map:
            logger.warning("没有可用的K线数据")
            return {"success": False, "message": "没有可用K线数据", "count": 0}

        total_count = len(stock_data_map)

        # 执行选股策略（使用原始的 select 方法）
        try:
            # 将选股日期转换为 Timestamp
            if trade_date is None:
                trade_date = date.today()

            select_timestamp = pd.Timestamp(trade_date)

            # 调用原始 Selector 的 select 方法
            selected_codes = selector.select(select_timestamp, stock_data_map)

        except Exception as e:
            logger.error(f"策略执行失败: {e}")
            raise

        # 构建结果列表
        results = []
        for ts_code in selected_codes:
            stock = db.query(Stock).filter(Stock.ts_code == ts_code).first()
            if stock:
                results.append({
                    "ts_code": stock.ts_code,
                    "symbol": stock.symbol,
                    "name": stock.name,
                })

        # 保存结果到数据库
        saved_count = 0
        for result in results:
            # 检查是否已存在
            existing = (
                db.query(SelectionResult)
                .filter(
                    SelectionResult.strategy_id == strategy_id,
                    SelectionResult.ts_code == result["ts_code"],
                    SelectionResult.trade_date == trade_date,
                )
                .first()
            )

            if not existing:
                selection_result = SelectionResult(
                    strategy_id=strategy_id,
                    ts_code=result["ts_code"],
                    trade_date=trade_date,
                    reason=json.dumps(result, ensure_ascii=False),
                    created_at=datetime.now(),
                )
                db.add(selection_result)
                saved_count += 1

        db.commit()

        logger.info(f"✅ 策略 {strategy.alias} 执行完成：选中 {len(results)} 只股票")

        return {
            "success": True,
            "message": "执行成功",
            "strategy_id": strategy_id,
            "strategy_alias": strategy.alias,
            "trade_date": trade_date.isoformat(),
            "total_stocks": total_count,
            "selected_count": len(results),
            "saved_count": saved_count,
            "results": results,
        }

    def execute_strategies(
        self,
        db: Session,
        strategy_ids: Optional[List[int]] = None,
        trade_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """批量执行选股策略

        Args:
            db: 数据库会话
            strategy_ids: 策略ID列表（None表示执行所有启用的策略）
            trade_date: 选股日期

        Returns:
            所有策略的执行结果列表
        """
        if strategy_ids is None:
            # 获取所有启用的策略
            strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
            strategy_ids = [s.id for s in strategies]

        if not strategy_ids:
            logger.warning("没有可执行的策略")
            return []

        results = []
        for strategy_id in strategy_ids:
            # 为每个策略创建独立的 session，避免一个失败影响后续策略
            from app.db.session import SessionLocal
            strategy_db = SessionLocal()
            try:
                result = self.execute_strategy(strategy_db, strategy_id, trade_date)
                results.append(result)
            except Exception as e:
                logger.error(f"执行策略 {strategy_id} 失败: {e}")
                strategy_db.rollback()
                results.append(
                    {
                        "success": False,
                        "message": str(e),
                        "strategy_id": strategy_id,
                    }
                )
            finally:
                strategy_db.close()

        return results

    def get_selection_results(
        self,
        db: Session,
        strategy_id: Optional[int] = None,
        trade_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取选股结果

        Args:
            db: 数据库会话
            strategy_id: 策略ID（None表示所有策略）
            trade_date: 选股日期（None表示所有日期）
            page: 页码
            page_size: 每页数量

        Returns:
            选股结果列表
        """
        # 构建查询
        query = db.query(SelectionResult)

        if strategy_id is not None:
            query = query.filter(SelectionResult.strategy_id == strategy_id)

        if trade_date is not None:
            query = query.filter(SelectionResult.trade_date == trade_date)
        else:
            # 默认返回最近的结果
            query = query.order_by(SelectionResult.trade_date.desc())

        # 分页
        total = query.count()
        results = query.offset((page - 1) * page_size).limit(page_size).all()

        # 格式化结果
        items = []
        for result in results:
            reason_data = json.loads(result.reason) if result.reason else {}
            items.append(
                {
                    "id": result.id,
                    "strategy_id": result.strategy_id,
                    "ts_code": result.ts_code,
                    "trade_date": result.trade_date.isoformat(),
                    "score": float(result.score) if result.score else None,
                    "reason": reason_data,
                    "created_at": result.created_at.isoformat(),
                }
            )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }


# 导出服务实例
strategy_service = StrategyService()
