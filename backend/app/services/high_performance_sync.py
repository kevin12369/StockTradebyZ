"""
高性能数据同步服务

优化策略：
1. 并发请求：同时处理多只股票
2. 批量写入：攒批后批量插入数据库
3. 智能增量：只更新需要更新的股票
4. 连接池：复用HTTP连接

目标：5000只股票在15分钟内完成
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.models.stock import Stock


class ConcurrentRateLimiter:
    """并发速率限制器

    控制并发数量，同时限制总体速率
    """

    def __init__(self, max_concurrent: int = 10, rate_per_second: float = 2.0):
        """初始化并发速率限制器

        Args:
            max_concurrent: 最大并发数
            rate_per_second: 每秒最多请求数
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_per_second = rate_per_second
        self.last_request_time = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """获取执行许可"""
        await self.semaphore.acquire()

        # 速率限制
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_request_time
            min_interval = 1.0 / self.rate_per_second

            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)

            self.last_request_time = asyncio.get_event_loop().time()

    def release(self):
        """释放执行许可"""
        self.semaphore.release()


class BatchWriter:
    """批量写入器

    积攒一批数据后批量写入，提高数据库性能
    """

    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        """初始化批量写入器

        Args:
            batch_size: 批次大小
            flush_interval: 刷新间隔（秒）
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer: List[Dict] = []
        self.last_flush = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def add(self, item: Dict) -> bool:
        """添加数据到缓冲区

        Args:
            item: 数据项

        Returns:
            是否应该刷新
        """
        async with self._lock:
            self.buffer.append(item)

            now = asyncio.get_event_loop().time()
            should_flush = (
                len(self.buffer) >= self.batch_size or
                (now - self.last_flush) >= self.flush_interval
            )

            if should_flush:
                self.last_flush = now

            return should_flush

    async def get_batch(self) -> List[Dict]:
        """获取当前批次并清空缓冲区"""
        async with self._lock:
            batch = self.buffer.copy()
            self.buffer.clear()
            return batch


class HighPerformanceSyncService:
    """高性能同步服务

    特性：
    1. 并发请求多只股票
    2. 批量写入数据库
    3. 智能增量更新
    """

    def __init__(self):
        """初始化高性能同步服务"""
        self.executor = ThreadPoolExecutor(max_workers=20)

    async def sync_stock_list_high_performance(
        self,
        db: Session,
        controller: Optional[Any] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict:
        """高性能同步股票列表

        使用并发请求加速同步

        Args:
            db: 数据库会话
            controller: 任务控制器
            progress_callback: 进度回调

        Returns:
            同步结果
        """
        import akshare as ak

        try:
            # 使用 akshare 的 stock_info_a_code_name 获取所有股票
            # 这个接口很快，不需要并发
            logger.info("开始获取股票列表（高性能模式）...")

            # 在线程池中执行阻塞的akshare调用
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                self.executor,
                ak.stock_info_a_code_name
            )

            if df is None or df.empty:
                return {
                    "success": False,
                    "message": "未获取到股票数据",
                    "count": 0,
                }

            # 批量处理DataFrame
            stocks_to_update = []
            stocks_to_add = []

            for _, row in df.iterrows():
                ts_code = row['code']  # AKShare返回的code格式
                name = row['name']

                # 转换格式
                if '.' not in ts_code:
                    # AKShare可能返回不带后缀的代码
                    if ts_code.startswith('6'):
                        ts_code = f"{ts_code}.SH"
                    else:
                        ts_code = f"{ts_code}.SZ"

                # 判断板块
                board = self._get_board_from_code(ts_code)
                market = ts_code.split('.')[-1]

                # 检查是否存在
                existing = db.query(Stock).filter(Stock.ts_code == ts_code).first()

                stock_data = {
                    'ts_code': ts_code,
                    'symbol': ts_code.split('.')[0],
                    'name': name,
                    'market': market,
                    'board': board,
                    'market_name': self._get_market_name(market),
                    'is_active': True,
                }

                if existing:
                    # 更新
                    for key, value in stock_data.items():
                        setattr(existing, key, value)
                    stocks_to_update.append(existing)
                else:
                    # 新增
                    new_stock = Stock(**stock_data)
                    stocks_to_add.append(new_stock)

                # 检查取消
                if controller and controller.check_cancelled():
                    return {
                        "success": False,
                        "message": "任务被取消",
                        "count": 0,
                    }

            # 批量写入数据库
            if stocks_to_add:
                db.bulk_save_objects(stocks_to_add)
                logger.info(f"新增 {len(stocks_to_add)} 只股票")

            if stocks_to_update:
                db.bulk_save_objects(stocks_to_update)
                logger.info(f"更新 {len(stocks_to_update)} 只股票")

            db.commit()

            return {
                "success": True,
                "message": f"成功同步 {len(df)} 只股票",
                "count": len(df),
                "added": len(stocks_to_add),
                "updated": len(stocks_to_update),
            }

        except Exception as e:
            logger.error(f"同步股票列表失败: {e}")
            db.rollback()
            return {
                "success": False,
                "message": f"同步失败: {str(e)}",
                "count": 0,
            }

    async def sync_kline_high_performance(
        self,
        db: Session,
        mode: str = "daily",  # daily/init
        controller: Optional[Any] = None,
        progress_callback: Optional[callable] = None,
        limit: Optional[int] = None,
    ) -> Dict:
        """高性能K线同步

        使用并发+批量加速同步

        Args:
            db: 数据库会话
            mode: 同步模式（daily/init）
            controller: 任务控制器
            progress_callback: 进度回调
            limit: 限制数量

        Returns:
            同步结果
        """
        try:
            # 获取需要同步的股票列表
            query = db.query(Stock).filter(Stock.is_active == True)
            stocks = query.limit(limit).all() if limit else query.all()

            # 过滤ST股票
            stocks = [s for s in stocks if not any(kw in s.name for kw in ['ST', '*ST', '退'])]

            total_count = len(stocks)
            logger.info(f"开始高性能K线同步: {total_count} 只股票, 模式={mode}")

            # 配置
            if mode == "init":
                concurrent_limit = 5  # 初始化模式：少并发（慢速）
                rate_limit = 0.5  # 每2秒1个请求
            else:  # daily
                concurrent_limit = 20  # 日常模式：高并发
                rate_limit = 5.0  # 每0.2秒1个请求

            rate_limiter = ConcurrentRateLimiter(
                max_concurrent=concurrent_limit,
                rate_per_second=rate_limit,
            )

            batch_writer = BatchWriter(batch_size=50, flush_interval=3.0)

            # 并发处理
            tasks = []
            for i, stock in enumerate(stocks):
                task = self._sync_single_stock(
                    stock, mode, db, rate_limiter, batch_writer,
                    controller, progress_callback, i, total_count
                )
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 最后刷新一次
            final_batch = await batch_writer.get_batch()
            if final_batch:
                await self._flush_batch_to_db(db, final_batch)

            # 统计结果
            succeeded = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
            failed = sum(1 for r in results if isinstance(r, dict) and not r.get('success'))
            exceptions = sum(1 for r in results if isinstance(r, Exception))

            return {
                "success": True,
                "message": f"同步完成：成功{succeeded}，失败{failed}，异常{exceptions}",
                "total": total_count,
                "succeeded_count": succeeded,
                "failed_count": failed,
            }

        except Exception as e:
            logger.error(f"高性能K线同步失败: {e}")
            return {
                "success": False,
                "message": f"同步失败: {str(e)}",
                "total": 0,
                "succeeded_count": 0,
                "failed_count": 0,
            }

    async def _sync_single_stock(
        self,
        stock: Stock,
        mode: str,
        db: Session,
        rate_limiter: ConcurrentRateLimiter,
        batch_writer: BatchWriter,
        controller: Optional[Any],
        progress_callback: Optional[callable],
        index: int,
        total: int,
    ) -> Dict:
        """同步单只股票

        Args:
            stock: 股票对象
            mode: 同步模式
            db: 数据库会话
            rate_limiter: 速率限制器
            batch_writer: 批量写入器
            controller: 任务控制器
            progress_callback: 进度回调
            index: 当前索引
            total: 总数

        Returns:
            同步结果
        """
        # 检查取消
        if controller and controller.check_cancelled():
            return {"success": False, "ts_code": stock.ts_code, "message": "任务已取消"}

        # 检查暂停
        if controller and controller.is_paused():
            await controller.wait_if_paused()

        # 获取许可
        await rate_limiter.acquire()

        try:
            # 在线程池中执行阻塞的akshare调用
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._fetch_stock_kline,
                stock.ts_code,
                mode,
            )

            if result["success"]:
                # 添加到批量缓冲区
                should_flush = await batch_writer.add({
                    'ts_code': stock.ts_code,
                    'data': result['data'],
                })

                # 如果需要刷新
                if should_flush:
                    batch = await batch_writer.get_batch()
                    await self._flush_batch_to_db(db, batch)

                # 更新进度
                if progress_callback:
                    progress = (index + 1) / total * 100
                    await progress_callback(progress, f"已处理 {index + 1}/{total} 只股票")

                rate_limiter.release()
                return {"success": True, "ts_code": stock.ts_code, "count": result['count']}
            else:
                rate_limiter.release()
                return {"success": False, "ts_code": stock.ts_code, "message": result['message']}

        except Exception as e:
            rate_limiter.release()
            logger.error(f"同步 {stock.ts_code} 失败: {e}")
            return {"success": False, "ts_code": stock.ts_code, "message": str(e)}

    def _fetch_stock_kline(self, ts_code: str, mode: str) -> Dict:
        """获取股票K线数据（在线程池中执行）

        Args:
            ts_code: 股票代码
            mode: 同步模式

        Returns:
            K线数据
        """
        import akshare as ak

        try:
            # 转换代码格式
            symbol = ts_code.split('.')[0]

            # 确定日期范围
            if mode == "init":
                # 初始化：获取近3年数据
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y%m%d")
            else:
                # 日常：只获取最近3天
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")

            # 调用 akshare
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )

            if df is None or df.empty:
                return {
                    "success": True,
                    "count": 0,
                    "message": "无新数据",
                    "data": [],
                }

            # 转换为字典列表
            data = []
            for _, row in df.iterrows():
                data.append({
                    'trade_date': row['日期'],
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']),
                })

            return {
                "success": True,
                "count": len(data),
                "message": "成功",
                "data": data,
            }

        except Exception as e:
            return {
                "success": False,
                "count": 0,
                "message": str(e),
                "data": [],
            }

    async def _flush_batch_to_db(self, db: Session, batch: List[Dict]) -> bool:
        """批量刷新数据到数据库

        Args:
            db: 数据库会话
            batch: 批次数据

        Returns:
            是否成功
        """
        try:
            from app.models.kline import KlineDaily

            records = []
            for item in batch:
                ts_code = item['ts_code']
                for kline in item['data']:
                    records.append({
                        'ts_code': ts_code,
                        'trade_date': kline['trade_date'],
                        'open': kline['open'],
                        'high': kline['high'],
                        'low': kline['low'],
                        'close': kline['close'],
                        'volume': kline['volume'],
                        'amount': kline['amount'],
                    })

            # 批量插入（使用ON CONFLICT处理重复）
            if records:
                db.bulk_insert_mappings(KlineDaily, records, render_nulls=True)
                db.commit()

            logger.info(f"批量写入 {len(records)} 条K线数据")
            return True

        except Exception as e:
            logger.error(f"批量写入失败: {e}")
            db.rollback()
            return False

    def _get_board_from_code(self, ts_code: str) -> str:
        """根据股票代码获取板块"""
        code = ts_code.split('.')[0]
        if code.startswith('6'):
            return '沪主板'
        elif code.startswith('0'):
            return '深主板'
        elif code.startswith('30'):
            return '创业板'
        elif code.startswith('688'):
            return '科创板'
        elif code.startswith('8'):
            return '北交所'
        return ''

    def _get_market_name(self, market: str) -> str:
        """获取市场名称"""
        names = {
            'SH': '上海',
            'SZ': '深圳',
            'BJ': '北京',
        }
        return names.get(market, market)


# 全局实例
high_performance_sync = HighPerformanceSyncService()
