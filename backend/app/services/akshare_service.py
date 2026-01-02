"""
AKShare 数据服务（增强版）

封装 AKShare API，提供统一的股票数据获取接口

功能特性：
1. 增量更新K线数据（只更新缺失的数据）
2. 批量同步多只股票
3. 智能判断同步需求
4. 详细的同步日志
5. 异步任务队列支持（速率限制）
"""

import asyncio
import time
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Tuple

import akshare as ak
import pandas as pd
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.stock import Stock
from app.models.kline import KlineDaily
from app.models.backtest import DataUpdateLog
from app.core.config import settings


class AKShareService:
    """AKShare 数据服务类（增强版）

    提供：
    1. 获取股票列表
    2. 获取K线数据（增量更新）
    3. 批量同步K线数据
    4. 智能判断同步需求
    """

    def __init__(self):
        """初始化服务"""
        self.timeout = settings.AKSHARE_TIMEOUT
        self.max_retries = settings.AKSHARE_MAX_RETRIES
        # 历史数据默认获取近3年
        self.default_history_years = 3

    def _retry_request(self, func, *args, **kwargs):
        """带重试和超时控制的请求

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 重试次数用尽后抛出异常
        """
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

        # 超时时间（秒）
        REQUEST_TIMEOUT = 60

        last_error = None
        for attempt in range(self.max_retries):
            try:
                # 使用线程池执行函数，设置超时
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args, **kwargs)
                    try:
                        result = future.result(timeout=REQUEST_TIMEOUT)
                        return result
                    except FutureTimeoutError:
                        last_error = TimeoutError(f"请求超时（{REQUEST_TIMEOUT}秒）")
                        future.cancel()  # 取消任务
                        raise last_error

            except TimeoutError as e:
                last_error = e
                wait_time = (attempt + 1) * 3
                logger.warning(f"请求超时，{wait_time}秒后重试 ({attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)

            except Exception as e:
                last_error = e
                wait_time = (attempt + 1) * 3  # 递增等待时间：3, 6, 9秒
                logger.warning(f"请求失败，{wait_time}秒后重试 ({attempt + 1}/{self.max_retries}): {e}")
                time.sleep(wait_time)

        raise last_error

    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表

        使用 AKShare 的 stock_zh_a_spot_em 接口获取实时行情数据

        Returns:
            DataFrame: 股票列表数据
            - symbol: 股票代码（如：000001）
            - ts_code: 股票代码（如：000001.SZ）
            - name: 股票名称
            - market: 市场（SZ/SH/BJ）
            - price: 最新价格
            - change_pct: 涨跌幅
            - ...其他字段
        """
        try:
            logger.info("正在获取A股股票列表...")

            df = self._retry_request(ak.stock_zh_a_spot_em)

            if df.empty:
                logger.warning("获取的股票列表为空")
                return pd.DataFrame()

            # 标准化列名
            df = df.rename(columns={
                "代码": "symbol",
                "名称": "name",
                "最新价": "price",
                "涨跌幅": "change_pct",
                "涨跌额": "change_amount",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "最高": "high",
                "最低": "low",
                "今开": "open",
                "昨收": "pre_close",
                "换手率": "turnover",
            })

            # 解析股票代码和市场
            df["ts_code"] = df["symbol"].apply(self._convert_to_ts_code)
            df["market"] = df["symbol"].apply(self._get_market_from_symbol)

            logger.info(f"成功获取 {len(df)} 只股票信息")
            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise

    def _convert_to_ts_code(self, symbol: str) -> str:
        """将股票代码转换为 ts_code 格式

        Args:
            symbol: 股票代码（如：000001）

        Returns:
            ts_code 格式（如：000001.SZ）
        """
        if symbol.startswith("6"):
            return f"{symbol}.SH"
        elif symbol.startswith(("0", "3")):
            return f"{symbol}.SZ"
        elif symbol.startswith(("8", "4")):
            return f"{symbol}.BJ"
        else:
            return symbol

    def _get_market_from_symbol(self, symbol: str) -> str:
        """从股票代码获取市场

        Args:
            symbol: 股票代码

        Returns:
            市场标识（SZ/SH/BJ）
        """
        if symbol.startswith("6"):
            return "SH"
        elif symbol.startswith(("0", "3")):
            return "SZ"
        elif symbol.startswith(("8", "4")):
            return "BJ"
        else:
            return "UNKNOWN"

    def _extract_symbol_from_ts_code(self, ts_code: str) -> str:
        """从 ts_code 提取 symbol

        Args:
            ts_code: 股票代码（如：000001.SZ）

        Returns:
            symbol（如：000001）
        """
        return ts_code.split(".")[0]

    def get_stock_kline(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """获取股票K线数据

        Args:
            symbol: 股票代码（如：000001，不带后缀）
            start_date: 起始日期（格式：YYYYMMDD 或 YYYY-MM-DD）
            end_date: 结束日期（格式：YYYYMMDD 或 YYYY-MM-DD）
            adjust: 复权类型（qfq: 前复权, hfq: 后复权, "": 不复权）

        Returns:
            DataFrame: K线数据
            - trade_date: 交易日期
            - open: 开盘价
            - close: 收盘价
            - high: 最高价
            - low: 最低价
            - volume: 成交量
            - amount: 成交额
        """
        try:
            # 转换日期格式
            start_str = self._convert_date_format(start_date) if start_date else "19900101"
            end_str = self._convert_date_format(end_date) if end_date else datetime.now().strftime("%Y%m%d")

            # 调用 AKShare 接口
            df = self._retry_request(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust=adjust if adjust else "",
            )

            if df.empty:
                return pd.DataFrame()

            # 标准化列名
            df = df.rename(columns={
                "日期": "trade_date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
            })

            # 只保留需要的列
            df = df[["trade_date", "open", "close", "high", "low", "volume", "amount"]]

            # 转换日期类型
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

            # 添加 ts_code
            df["ts_code"] = self._convert_to_ts_code(symbol)

            return df

        except Exception as e:
            logger.error(f"获取K线数据失败 ({symbol}): {e}")
            raise

    def _convert_date_format(self, date_str: str) -> str:
        """转换日期格式为 YYYYMMDD

        Args:
            date_str: 日期字符串（支持多种格式）

        Returns:
            YYYYMMDD 格式的日期字符串
        """
        # 移除分隔符
        clean_date = date_str.replace("-", "").replace("/", "")

        # 如果是 today
        if clean_date.lower() == "today":
            return datetime.now().strftime("%Y%m%d")

        return clean_date

    def sync_stock_list_to_db(self, db: Session) -> dict:
        """同步股票列表到数据库（增量更新）

        策略：
        1. 更新已存在的股票信息
        2. 新增不存在的股票
        3. 标记已删除的股票为 is_active=False

        Args:
            db: 数据库会话

        Returns:
            同步结果统计
        """
        logger.info("开始同步股票列表到数据库...")

        try:
            # 获取股票列表
            df = self.get_stock_list()

            if df.empty:
                return {"success": False, "message": "股票列表为空", "count": 0}

            # 记录同步时间
            sync_time = datetime.now()

            # 获取数据库中所有股票
            existing_stocks = db.query(Stock.ts_code).all()
            existing_codes = set(s.ts_code for s in existing_stocks)
            api_codes = set(df["ts_code"].tolist())

            # 统计
            added_count = 0
            updated_count = 0
            deactivated_count = 0

            # 遍历API返回的股票
            for _, row in df.iterrows():
                stock = db.query(Stock).filter(Stock.ts_code == row["ts_code"]).first()

                if stock:
                    # 更新已存在的股票
                    stock.name = row["name"]
                    stock.market = row["market"]
                    stock.is_active = True
                    stock.updated_at = sync_time
                    updated_count += 1
                else:
                    # 新增股票
                    stock = Stock(
                        ts_code=row["ts_code"],
                        symbol=row["symbol"],
                        name=row["name"],
                        market=row["market"],
                        is_active=True,
                    )
                    db.add(stock)
                    added_count += 1

            # 标记已删除的股票（在API中不存在的）
            deactivated_stocks = existing_codes - api_codes
            for ts_code in deactivated_stocks:
                stock = db.query(Stock).filter(Stock.ts_code == ts_code).first()
                if stock and stock.is_active:
                    stock.is_active = False
                    stock.updated_at = sync_time
                    deactivated_count += 1

            # 提交事务
            db.commit()

            logger.info(f"股票列表同步完成：新增 {added_count}，更新 {updated_count}，停用 {deactivated_count}")

            # 记录同步日志
            self._log_update(
                db,
                data_type="stock_list",
                status="success",
                message=f"股票列表同步：新增{added_count}，更新{updated_count}，停用{deactivated_count}",
            )

            return {
                "success": True,
                "message": "同步成功",
                "count": len(df),
                "added": added_count,
                "updated": updated_count,
                "deactivated": deactivated_count,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"同步股票列表失败: {e}")
            self._log_update(db, data_type="stock_list", status="failed", message=str(e))
            raise

    def _get_latest_kline_date(self, db: Session, ts_code: str) -> Optional[date]:
        """获取股票的最新K线日期

        Args:
            db: 数据库会话
            ts_code: 股票代码

        Returns:
            最新K线日期，如果没有数据则返回None
        """
        latest = (
            db.query(KlineDaily.trade_date)
            .filter(KlineDaily.ts_code == ts_code)
            .order_by(KlineDaily.trade_date.desc())
            .first()
        )
        return latest[0] if latest else None

    def _get_latest_trade_date(self) -> Optional[date]:
        """获取最近交易日（排除周末和节假日）

        通过获取大盘指数（上证指数）的最新交易日来判断

        Returns:
            最近交易日日期，如果获取失败则返回昨天
        """
        try:
            # 获取上证指数最近的数据来判断交易日
            import akshare as ak

            df = ak.stock_zh_index_daily(symbol="sh000001")
            if not df.empty:
                latest_date = pd.to_datetime(df.iloc[-1]["date"]).date()
                # 确保不是未来日期
                today = date.today()
                if latest_date > today:
                    return today
                return latest_date
        except Exception as e:
            logger.warning(f"获取最近交易日失败: {e}，使用昨天日期")

        # 备用方案：返回昨天（排除周末）
        yesterday = date.today() - timedelta(days=1)
        # 如果是周六或周日，往前推到周五
        if yesterday.weekday() == 5:  # 周六
            yesterday -= timedelta(days=1)
        elif yesterday.weekday() == 6:  # 周日
            yesterday -= timedelta(days=2)

        return yesterday

    def sync_stock_kline_to_db(
        self,
        db: Session,
        ts_code: str,
        force_full_sync: bool = False,
    ) -> dict:
        """同步单只股票的K线数据到数据库（增量更新）

        策略：
        1. 查询数据库中该股票的最新K线日期
        2. 如果存在数据且不是强制全量同步，则只获取从最新日期+1天到今天的数据
        3. 如果不存在数据或强制全量同步，则获取近3年的历史数据
        4. 使用唯一约束防止重复插入

        Args:
            db: 数据库会话
            ts_code: 股票代码（如：000001.SZ）
            force_full_sync: 是否强制全量同步

        Returns:
            同步结果统计
        """
        try:
            # 提取 symbol（去除后缀）
            symbol = self._extract_symbol_from_ts_code(ts_code)

            # 获取最新K线日期
            latest_date = self._get_latest_kline_date(db, ts_code)

            # 计算起始日期
            if latest_date and not force_full_sync:
                # 增量更新：从最新日期+1天开始
                start_date = (latest_date + timedelta(days=1)).strftime("%Y%m%d")
                sync_mode = "增量"
            else:
                # 全量同步：获取近3年数据
                start_date = (datetime.now() - timedelta(days=365 * self.default_history_years)).strftime("%Y%m%d")
                sync_mode = "全量" if force_full_sync else "初始化"

            # 获取K线数据
            df = self.get_stock_kline(symbol, start_date=start_date)

            if df.empty:
                return {
                    "success": True,
                    "message": "无新数据",
                    "count": 0,
                    "sync_mode": sync_mode,
                }

            # 记录同步时间
            sync_time = datetime.now()

            # ========== 性能优化：批量查询替代逐行查询 ==========
            # 原先：逐行查询700-800次，性能瓶颈
            # 优化：一次性查询所有已存在的日期（1次查询）
            existing_dates = set(
                db.query(KlineDaily.trade_date)
                .filter(KlineDaily.ts_code == ts_code)
                .filter(KlineDaily.trade_date.in_(df["trade_date"].tolist()))
                .all()
            )
            # 扁平化结果：从 [(date1,), (date2,)] 转为 {date1, date2}
            existing_dates = {d[0] for d in existing_dates}

            # 批量插入/更新（使用内存判断，无需查询数据库）
            added_count = 0
            updated_count = 0
            total_rows = len(df)

            for idx, (_, row) in enumerate(df.iterrows(), 1):
                # 进度日志：每100条记录输出一次
                if idx % 100 == 0 or idx == total_rows:
                    logger.info(f"{ts_code} 数据处理进度: {idx}/{total_rows} ({idx/total_rows*100:.1f}%)")

                # 使用内存判断替代数据库查询（性能提升99%+）
                trade_date = row["trade_date"]
                if trade_date in existing_dates:
                    # 数据已存在，需要更新（一般情况下很少走到这里，因为增量更新）
                    kline = db.query(KlineDaily).filter(
                        KlineDaily.ts_code == row["ts_code"],
                        KlineDaily.trade_date == trade_date,
                    ).first()

                    if kline:
                        kline.open = row["open"]
                        kline.close = row["close"]
                        kline.high = row["high"]
                        kline.low = row["low"]
                        kline.volume = row["volume"]
                        kline.amount = row["amount"]
                        kline.created_at = sync_time
                        updated_count += 1
                else:
                    # 新数据，直接插入
                    kline = KlineDaily(
                        ts_code=row["ts_code"],
                        trade_date=trade_date,
                        open=row["open"],
                        close=row["close"],
                        high=row["high"],
                        low=row["low"],
                        volume=row["volume"],
                        amount=row["amount"],
                        created_at=sync_time,
                    )
                    db.add(kline)
                    added_count += 1
                    existing_dates.add(trade_date)  # 添加到已存在集合，避免重复

            # 提交事务
            db.commit()

            logger.info(f"{ts_code} K线数据同步完成（{sync_mode}）：新增 {added_count}，更新 {updated_count}")

            # 记录同步日志
            self._log_update(
                db,
                data_type="kline_single",
                status="success",
                message=f"{ts_code} K线同步（{sync_mode}）：新增{added_count}，更新{updated_count}",
                details={"ts_code": ts_code, "sync_mode": sync_mode, "added": added_count, "updated": updated_count},
            )

            return {
                "success": True,
                "message": "同步成功",
                "ts_code": ts_code,
                "count": len(df),
                "added": added_count,
                "updated": updated_count,
                "sync_mode": sync_mode,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"同步K线数据失败 ({ts_code}): {e}")
            self._log_update(
                db,
                data_type="kline_single",
                status="failed",
                message=f"{ts_code} K线同步失败: {str(e)}",
                details={"ts_code": ts_code, "error": str(e)},
            )
            raise

    def batch_sync_kline_to_db(
        self,
        db: Session,
        limit: Optional[int] = None,
        force_full_sync: bool = False,
        only_active: bool = True,
    ) -> dict:
        """批量同步股票K线数据（智能增量同步）

        策略：
        1. 获取最近交易日
        2. 跳过数据已经是最新的股票（避免无效请求）
        3. 只同步需要更新的股票：
           - 没有数据的股票
           - 最新数据日期 < 最近交易日的股票
        4. 按照最新K线日期排序，优先同步数据最旧的股票
        5. 逐个同步，失败不影响其他股票

        Args:
            db: 数据库会话
            limit: 限制同步数量（None表示全部同步）
            force_full_sync: 是否强制全量同步（跳过智能过滤）
            only_active: 是否只同步活跃股票

        Returns:
            批量同步结果统计
        """
        logger.info(f"开始批量同步K线数据（limit={limit}, force_full_sync={force_full_sync}）...")

        try:
            # 获取最近交易日
            latest_trade_date = self._get_latest_trade_date()
            logger.info(f"最近交易日: {latest_trade_date}")

            # 构建查询
            query = db.query(Stock)
            if only_active:
                query = query.filter(Stock.is_active == True)

            # 获取股票列表
            stocks = query.all()
            # 过滤掉ST、*ST和退市股票
            if only_active:
                stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

            if not stocks:
                return {
                    "success": False,
                    "message": "没有可同步的股票",
                    "total": 0,
                    "succeeded": [],
                    "failed": [],
                }

            # 智能过滤：跳过数据已经是最新的股票
            stock_priority = []
            skipped_count = 0  # 跳过的股票数量

            for stock in stocks:
                latest_date = self._get_latest_kline_date(db, stock.ts_code)

                # 如果不是强制全量同步，且数据已经是最新的，则跳过
                if not force_full_sync and latest_date is not None:
                    if latest_date >= latest_trade_date:
                        # 数据是最新的，跳过
                        skipped_count += 1
                        continue

                # 需要同步的股票
                stock_priority.append(
                    {
                        "stock": stock,
                        "latest_date": latest_date or date.min,
                    }
                )

            logger.info(f"智能过滤结果: 总股票数 {len(stocks)}，需要同步 {len(stock_priority)}，跳过 {skipped_count}")

            if not stock_priority:
                return {
                    "success": True,
                    "message": f"所有股票数据都是最新的（跳过 {skipped_count} 只）",
                    "total": 0,
                    "skipped": skipped_count,
                    "succeeded": [],
                    "failed": [],
                }

            # 排序：latest_date 越小越优先
            stock_priority.sort(key=lambda x: x["latest_date"])

            # 限制同步数量
            if limit:
                stock_priority = stock_priority[:limit]

            total_count = len(stock_priority)
            succeeded = []
            failed = []

            # 每处理10只股票输出一次进度日志
            progress_log_interval = max(1, total_count // 10) if total_count > 10 else 1

            for i, item in enumerate(stock_priority, 1):
                stock = item["stock"]
                latest_date = item["latest_date"]

                try:
                    # 每只股票都输出INFO级别的进度（重要！让用户看到实时进度）
                    logger.info(
                        f"[{i}/{total_count}] 正在同步: {stock.ts_code} {stock.name} "
                        f"(最新数据: {latest_date or '无'}, 预计剩余: {(total_count - i) * 5}秒)"
                    )

                    result = self.sync_stock_kline_to_db(
                        db,
                        stock.ts_code,
                        force_full_sync=force_full_sync,
                    )

                    if result["success"]:
                        succeeded.append(
                            {
                                "ts_code": stock.ts_code,
                                "name": stock.name,
                                "count": result["count"],
                                "sync_mode": result["sync_mode"],
                            }
                        )
                    else:
                        failed.append(
                            {
                                "ts_code": stock.ts_code,
                                "name": stock.name,
                                "error": result["message"],
                            }
                        )

                    # 避免请求过快（每5秒1个请求，避免被AKShare拒绝）
                    if i < total_count:
                        time.sleep(5)

                except Exception as e:
                    # 详细的错误日志
                    import traceback
                    error_type = type(e).__name__
                    error_msg = str(e)
                    logger.error(
                        f"同步 {stock.ts_code} {stock.name} 失败 [{error_type}]: {error_msg}\n"
                        f"错误详情: {traceback.format_exc()}"
                    )
                    failed.append(
                        {
                            "ts_code": stock.ts_code,
                            "name": stock.name,
                            "error": f"{error_type}: {error_msg}",
                        }
                    )

            logger.info(f"批量K线同步完成：成功 {len(succeeded)}，失败 {len(failed)}，跳过 {skipped_count}")

            # 输出失败的股票列表（如果有）
            if failed:
                logger.warning(f"失败的股票列表（共{len(failed)}只）:")
                for item in failed[:20]:  # 只输出前20个
                    logger.warning(f"  - {item['ts_code']} {item['name']}: {item['error']}")
                if len(failed) > 20:
                    logger.warning(f"  ... 还有 {len(failed) - 20} 只失败")

            # 记录同步日志
            self._log_update(
                db,
                data_type="kline_batch",
                status="success" if not failed else "partial",
                message=f"批量K线同步：成功{len(succeeded)}，失败{len(failed)}，跳过{skipped_count}",
                details={
                    "total": total_count,
                    "skipped_count": skipped_count,
                    "succeeded_count": len(succeeded),
                    "failed_count": len(failed),
                    "succeeded": succeeded[:10],  # 只记录前10个
                    "failed": failed[:10],
                },
            )

            return {
                "success": len(failed) == 0,
                "message": f"批量同步完成（跳过 {skipped_count} 只最新数据）",
                "total": total_count,
                "skipped": skipped_count,
                "succeeded_count": len(succeeded),
                "failed_count": len(failed),
                "succeeded": succeeded,
                "failed": failed,
            }

        except Exception as e:
            logger.error(f"批量同步K线数据失败: {e}")
            self._log_update(
                db,
                data_type="kline_batch",
                status="failed",
                message=f"批量K线同步失败: {str(e)}",
            )
            raise

    def get_stocks_kline_status(self, db: Session, limit: Optional[int] = None) -> List[Dict]:
        """获取股票K线数据状态

        Args:
            db: 数据库会话
            limit: 限制返回数量

        Returns:
            股票K线状态列表
        """
        query = db.query(Stock).filter(Stock.is_active == True)

        if limit:
            query = query.limit(limit)

        stocks = query.all()
        # 过滤掉ST、*ST和退市股票
        stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

        status_list = []
        for stock in stocks:
            latest_date = self._get_latest_kline_date(db, stock.ts_code)
            count = db.query(KlineDaily).filter(KlineDaily.ts_code == stock.ts_code).count()

            status_list.append(
                {
                    "ts_code": stock.ts_code,
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "market": stock.market,
                    "kline_count": count,
                    "latest_date": latest_date.isoformat() if latest_date else None,
                    "has_data": count > 0,
                }
            )

        return status_list

    def _log_update(
        self,
        db: Session,
        data_type: str,
        status: str,
        message: str,
        details: Optional[dict] = None,
    ):
        """记录数据更新日志

        Args:
            db: 数据库会话
            data_type: 数据类型（stock_list/kline_single/kline_batch）
            status: 状态（success/failed/partial）
            message: 消息
            details: 详细信息（JSON）
        """
        try:
            # 准备详细信息JSON
            details_json = None
            if details:
                import json
                details_json = json.dumps(details, ensure_ascii=False)

            # 创建日志记录
            log = DataUpdateLog(
                data_type=data_type,
                status=status,
                records_count=0,  # 可以后续扩展
                error_message=details_json if status == "failed" else None,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"记录更新日志失败: {e}")
            db.rollback()

    async def async_batch_sync_kline_to_db(
        self,
        db: Session,
        task_info: "TaskInfo",  # 类型注解字符串避免循环导入
        rate_limiter: "RateLimiter",
        limit: Optional[int] = None,
        force_full_sync: bool = False,
        only_active: bool = True,
    ) -> Dict:
        """异步批量同步股票K线数据（使用任务队列和速率限制器）

        与 batch_sync_kline_to_db 的区别：
        1. 异步执行，支持任务进度更新
        2. 使用速率限制器控制请求频率
        3. 更新任务状态和进度信息
        4. 内部创建新的Session（避免使用过期的Session）

        Args:
            db: 数据库会话（注意：此方法内部会创建新Session，不使用此参数）
            task_info: 任务信息对象（用于更新进度）
            rate_limiter: 速率限制器
            limit: 限制同步数量
            force_full_sync: 是否强制全量同步
            only_active: 是否只同步活跃股票

        Returns:
            同步结果字典
        """
        # 创建新的数据库会话（避免使用过期的Session）
        from app.db.session import SessionLocal

        new_db = SessionLocal()
        try:
            # 构建查询（不在这里limit，要获取所有股票后再排序）
            query = new_db.query(Stock).filter(Stock.is_active == True) if only_active else new_db.query(Stock)

            # 获取所有股票（注意：不在查询时limit，而是获取全部后再排序和限制）
            stocks = query.all()
            # 过滤掉ST、*ST和退市股票（不影响同步，但避免浪费时间）
            if only_active:
                stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

            if not stocks:
                task_info.message = "没有需要同步的股票"
                return {
                    "success": True,
                    "message": "没有需要同步的股票",
                    "total": 0,
                    "succeeded_count": 0,
                    "failed_count": 0,
                }

            # 按最新K线日期排序（优先同步数据最旧的）
            stock_priority = []
            for stock in stocks:
                latest_date = self._get_latest_kline_date(new_db, stock.ts_code)
                stock_priority.append(
                    {
                        "stock": stock,
                        "latest_date": latest_date or date.min,
                    }
                )

            # 排序：latest_date 越小越优先
            stock_priority.sort(key=lambda x: x["latest_date"])

            # 在这里限制数量（确保已经按K线日期排序）
            if limit:
                stock_priority = stock_priority[:limit]

            total_count = len(stock_priority)
            succeeded = []
            failed = []

            for i, item in enumerate(stock_priority, 1):
                stock = item["stock"]
                latest_date = item["latest_date"]

                try:
                    # 更新任务进度
                    progress = (i - 1) / total_count * 100
                    task_info.progress = progress
                    task_info.message = f"[{i}/{total_count}] 同步 {stock.ts_code} {stock.name}（最新数据：{latest_date}）..."

                    # 使用INFO级别记录每只股票的同步进度（用户需要看到实时进度）
                    logger.info(task_info.message)

                    # 等待速率限制器（重要！避免对AKShare服务器造成压力）
                    await rate_limiter.acquire()

                    # 同步单只股票（在executor中执行）
                    result = self.sync_stock_kline_to_db(
                        new_db,
                        stock.ts_code,
                        force_full_sync=force_full_sync,
                    )

                    if result["success"]:
                        succeeded.append(
                            {
                                "ts_code": stock.ts_code,
                                "name": stock.name,
                                "count": result["count"],
                                "sync_mode": result["sync_mode"],
                            }
                        )
                    else:
                        failed.append(
                            {
                                "ts_code": stock.ts_code,
                                "name": stock.name,
                                "error": result["message"],
                            }
                        )

                except Exception as e:
                    logger.error(f"同步 {stock.ts_code} 失败: {e}")
                    failed.append(
                        {
                            "ts_code": stock.ts_code,
                            "name": stock.name,
                            "error": str(e),
                        }
                    )

            # 更新最终进度
            task_info.progress = 100.0
            logger.info(f"批量K线同步完成：成功 {len(succeeded)}，失败 {len(failed)}")

            # 记录同步日志
            self._log_update(
                new_db,
                data_type="kline_batch",
                status="success" if not failed else "partial",
                message=f"批量K线同步：成功{len(succeeded)}，失败{len(failed)}",
                details={
                    "total": total_count,
                    "succeeded_count": len(succeeded),
                    "failed_count": len(failed),
                    "succeeded": succeeded[:10],  # 只记录前10个
                    "failed": failed[:10],
                },
            )

            return {
                "success": len(failed) == 0,
                "message": f"批量同步完成：成功 {len(succeeded)}，失败 {len(failed)}",
                "total": total_count,
                "succeeded_count": len(succeeded),
                "failed_count": len(failed),
                "succeeded": succeeded,
                "failed": failed,
            }

        except Exception as e:
            logger.error(f"异步批量同步K线数据失败: {e}")
            self._log_update(
                new_db,
                data_type="kline_batch",
                status="failed",
                message=f"异步批量K线同步失败: {str(e)}",
            )
            raise
        finally:
            # 确保关闭数据库会话
            new_db.close()


# 导出服务实例
akshare_service = AKShareService()
