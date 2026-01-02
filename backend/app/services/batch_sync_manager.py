"""
智能分批同步管理器

功能：
1. 分批执行：将大批量任务拆分成小批次
2. 进度持久化：记录同步进度到数据库
3. 断点续传：支持从中断处继续
4. 智能跳过：自动跳过已同步的股票
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.stock import Stock
from app.services.akshare_service import AKShareService

logger = logging.getLogger(__name__)

# 全局批次进度存储
_batch_progress_store: Dict[str, Dict] = {}


class BatchSyncManager:
    """智能分批同步管理器"""

    def __init__(self, batch_size: int = 500):
        """
        Args:
            batch_size: 每批处理的股票数量（默认500只）
        """
        self.batch_size = batch_size
        self.akshare_service = AKShareService()

    def get_sync_progress(self, db: Session) -> Dict:
        """获取同步进度

        Returns:
            进度信息字典
        """
        # 查询所有活跃股票
        total_stocks = db.query(Stock).filter(Stock.is_active == True).count()

        # 过滤ST股票
        all_stocks = db.query(Stock).filter(Stock.is_active == True).all()
        valid_stocks = [s for s in all_stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

        # 获取每只股票的最新K线日期
        stock_status = []
        for stock in valid_stocks:
            latest_date = self.akshare_service._get_latest_kline_date(db, stock.ts_code)
            stock_status.append({
                'ts_code': stock.ts_code,
                'name': stock.name,
                'latest_date': latest_date,
            })

        # 统计需要更新的股票（基于最近交易日判断）
        latest_trade_date = self.akshare_service._get_latest_trade_date()
        logger.info(f"最近交易日: {latest_trade_date}")

        need_update = [s for s in stock_status if s['latest_date'] is None or s['latest_date'] < latest_trade_date]
        up_to_date = [s for s in stock_status if s['latest_date'] and s['latest_date'] >= latest_trade_date]

        return {
            'total_stocks': len(valid_stocks),
            'need_update': len(need_update),
            'up_to_date': len(up_to_date),
            'need_update_list': need_update[:10],  # 返回前10个示例
            'up_to_date_list': up_to_date[:10],
        }

    @staticmethod
    def get_batch_execution_progress(batch_id: str) -> Optional[Dict]:
        """获取批次执行进度

        Args:
            batch_id: 批次ID

        Returns:
            进度信息字典，如果批次不存在则返回None
        """
        return _batch_progress_store.get(batch_id)

    @staticmethod
    def clear_batch_progress(batch_id: str):
        """清除批次进度

        Args:
            batch_id: 批次ID
        """
        if batch_id in _batch_progress_store:
            del _batch_progress_store[batch_id]

    def create_batches(self, db: Session, force_full_sync: bool = False, batch_id_prefix: str = None) -> Tuple[List[Dict], str]:
        """创建同步批次

        Args:
            db: 数据库会话
            force_full_sync: 是否强制全量同步
            batch_id_prefix: 批次ID前缀（用于复用已创建的批次ID）

        Returns:
            (批次列表, 批次ID前缀)
        """
        # 生成批次ID前缀（如果未提供）
        if not batch_id_prefix:
            batch_id_prefix = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 获取需要同步的股票
        query = db.query(Stock).filter(Stock.is_active == True)
        stocks = query.all()

        # 过滤ST股票
        stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

        if not stocks:
            return []

        # 如果不是强制全量同步，智能过滤数据已经是最新的股票
        if not force_full_sync:
            # 获取最近交易日（排除周末、节假日）
            latest_trade_date = self.akshare_service._get_latest_trade_date()
            logger.info(f"最近交易日: {latest_trade_date}")

            filtered_stocks = []
            skipped_count = 0

            for stock in stocks:
                latest_date = self.akshare_service._get_latest_kline_date(db, stock.ts_code)
                # 使用交易日判断：如果数据已经是最新的交易日数据，跳过
                if latest_date and latest_date >= latest_trade_date:
                    skipped_count += 1
                else:
                    filtered_stocks.append(stock)

            logger.info(f"智能过滤（基于交易日）: 总股票 {len(stocks)}，需要同步 {len(filtered_stocks)}，跳过 {skipped_count}")
            stocks = filtered_stocks

        # 按最新K线日期排序（优先同步数据最旧的）
        stock_priority = []
        for stock in stocks:
            latest_date = self.akshare_service._get_latest_kline_date(db, stock.ts_code)
            stock_priority.append({
                'stock': stock,
                'latest_date': latest_date or date.min,
            })

        stock_priority.sort(key=lambda x: x['latest_date'])

        # 创建批次
        batches = []
        for i in range(0, len(stock_priority), self.batch_size):
            batch_stocks = stock_priority[i:i + self.batch_size]
            # 使用提供的批次ID前缀，或生成新的
            if batch_id_prefix:
                batch_id = f"{batch_id_prefix}_{i // self.batch_size + 1}"
            else:
                batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i // self.batch_size + 1}"

            batches.append({
                'batch_id': batch_id,
                'batch_index': len(batches) + 1,
                'total_batches': (len(stock_priority) + self.batch_size - 1) // self.batch_size,
                'stocks': batch_stocks,
                'stock_count': len(batch_stocks),
                'status': 'pending',
                'created_at': datetime.now(),
            })

        logger.info(f"创建 {len(batches)} 个批次，每批 {self.batch_size} 只股票")
        return batches, batch_id_prefix

    def execute_batch(
        self,
        db: Session,
        batch: Dict,
        force_full_sync: bool = False,
        progress_callback = None
    ) -> Dict:
        """执行单个批次

        Args:
            db: 数据库会话
            batch: 批次信息
            force_full_sync: 是否强制全量同步
            progress_callback: 进度回调函数

        Returns:
            批次执行结果
        """
        batch_id = batch['batch_id']
        stocks = batch['stocks']
        total_count = len(stocks)

        logger.info(f"开始执行批次 {batch_id}，共 {total_count} 只股票")

        # 初始化进度存储
        _batch_progress_store[batch_id] = {
            'batch_id': batch_id,
            'batch_index': batch['batch_index'],
            'total_batches': batch['total_batches'],
            'total_count': total_count,
            'current_index': 0,
            'current_stock': None,
            'progress': 0.0,
            'status': 'running',
            'succeeded_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'start_time': datetime.now().isoformat(),
            'message': f'准备执行批次 {batch["batch_index"]}/{batch["total_batches"]}',
        }

        succeeded = []
        failed = []
        skipped = 0

        # 创建新的数据库会话（避免长时间使用同一个会话）
        from app.db.session import SessionLocal
        new_db = SessionLocal()

        try:
            for i, item in enumerate(stocks, 1):
                stock = item['stock']
                latest_date = item['latest_date']

                try:
                    # 更新进度
                    progress = (i - 1) / total_count * 100
                    message = f"[批次 {batch['batch_index']}/{batch['total_batches']}] [{i}/{total_count}] 同步 {stock.ts_code} {stock.name}"

                    if progress_callback:
                        progress_callback(progress, message)

                    # 更新全局进度存储
                    if batch_id in _batch_progress_store:
                        _batch_progress_store[batch_id].update({
                            'current_index': i,
                            'current_stock': {
                                'ts_code': stock.ts_code,
                                'name': stock.name,
                            },
                            'progress': round(progress, 2),
                            'message': message,
                        })

                    logger.info(message)

                    # 检查是否需要跳过（数据已经是最新的）
                    from datetime import timedelta
                    recent_threshold = date.today() - timedelta(days=7)
                    if not force_full_sync and latest_date and latest_date >= recent_threshold:
                        logger.info(f"  跳过（数据最新）：{latest_date}")
                        skipped += 1
                        continue

                    # 同步单只股票
                    result = self.akshare_service.sync_stock_kline_to_db(
                        new_db,
                        stock.ts_code,
                        force_full_sync=force_full_sync,
                    )

                    if result['success']:
                        succeeded.append({
                            'ts_code': stock.ts_code,
                            'name': stock.name,
                            'count': result['count'],
                            'sync_mode': result['sync_mode'],
                        })
                    else:
                        failed.append({
                            'ts_code': stock.ts_code,
                            'name': stock.name,
                            'error': result['message'],
                        })

                except Exception as e:
                    import traceback
                    logger.error(f"同步 {stock.ts_code} 失败: {e}\n{traceback.format_exc()}")
                    failed.append({
                        'ts_code': stock.ts_code,
                        'name': stock.name,
                        'error': f"{type(e).__name__}: {str(e)}",
                    })

            # 批次结果
            result = {
                'batch_id': batch_id,
                'batch_index': batch['batch_index'],
                'total_batches': batch['total_batches'],
                'success': len(failed) == 0,
                'message': f"批次 {batch['batch_index']} 完成",
                'total': total_count,
                'skipped': skipped,
                'succeeded_count': len(succeeded),
                'failed_count': len(failed),
                'succeeded': succeeded,
                'failed': failed,
            }

            # 更新进度状态为完成
            if batch_id in _batch_progress_store:
                _batch_progress_store[batch_id].update({
                    'current_index': total_count,
                    'progress': 100.0,
                    'status': 'completed' if len(failed) == 0 else 'completed_with_errors',
                    'succeeded_count': len(succeeded),
                    'failed_count': len(failed),
                    'skipped_count': skipped,
                    'message': f"批次 {batch['batch_index']} 完成：成功 {len(succeeded)}，失败 {len(failed)}，跳过 {skipped}",
                    'end_time': datetime.now().isoformat(),
                })

            logger.info(f"批次 {batch_id} 完成：成功 {len(succeeded)}，失败 {len(failed)}，跳过 {skipped}")
            return result

        finally:
            new_db.close()


# 导出单例
batch_sync_manager = BatchSyncManager(batch_size=500)
