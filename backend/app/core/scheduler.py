"""定时任务调度器

使用APScheduler实现定时任务管理
"""
from datetime import datetime, time
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.scheduled_task import ScheduledTask
from app.db.session import SessionLocal
from app.services.top_performer_service import TopPerformerService
from app.services.akshare_service import AKShareService
from app.services.strategy_service import StrategyService


class TaskScheduler:
    """定时任务调度器

    管理所有定时任务的注册、执行、监控
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db: Optional[Session] = None

    def start(self):
        """启动调度器"""
        try:
            self.scheduler.start()
            logger.info("✅ 定时任务调度器启动成功")
        except Exception as e:
            logger.error(f"❌ 定时任务调度器启动失败: {str(e)}")

    def shutdown(self):
        """关闭调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("✅ 定时任务调度器已关闭")
        except Exception as e:
            logger.error(f"❌ 定时任务调度器关闭失败: {str(e)}")

    def load_tasks_from_db(self):
        """从数据库加载并注册所有启用的任务"""
        self.db = SessionLocal()
        try:
            tasks = self.db.query(ScheduledTask).filter(
                ScheduledTask.enabled == True
            ).all()

            for task in tasks:
                self.register_task(task)

            logger.info(f"✅ 从数据库加载了 {len(tasks)} 个定时任务")

        except Exception as e:
            logger.error(f"❌ 加载定时任务失败: {str(e)}")
        finally:
            self.db.close()

    def register_task(self, task: ScheduledTask):
        """注册单个任务到调度器

        Args:
            task: 定时任务配置
        """
        try:
            # 移除旧任务（如果存在）
            if self.scheduler.get_job(task.name):
                self.scheduler.remove_job(task.name)

            # 根据任务类型注册不同的触发器
            if task.scheduled_time:
                # 使用时间触发（每天固定时间）
                hour, minute = map(int, task.scheduled_time.split(':'))
                trigger = CronTrigger(hour=hour, minute=minute)
            elif task.cron_expression:
                # 使用Cron表达式
                trigger = CronTrigger.from_crontab(task.cron_expression)
            else:
                logger.warning(f"任务 {task.name} 没有配置触发时间，跳过注册")
                return

            # 注册任务
            self.scheduler.add_job(
                func=self.execute_task,
                trigger=trigger,
                id=task.name,
                args=[task.id],
                name=task.name,
                replace_existing=True
            )

            logger.info(f"✅ 注册定时任务: {task.name} ({task.scheduled_time or task.cron_expression})")

        except Exception as e:
            logger.error(f"❌ 注册任务 {task.name} 失败: {str(e)}")

    def execute_task(self, task_id: int):
        """执行定时任务（同步包装）

        Args:
            task_id: 任务ID
        """
        import asyncio
        import threading

        def run_in_new_thread():
            """在新线程中运行异步任务"""
            asyncio.set_event_loop(asyncio.new_event_loop())

            async def _run():
                db = SessionLocal()
                try:
                    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                    if not task:
                        logger.error(f"任务ID {task_id} 不存在")
                        return

                    logger.info(f"🚀 开始执行任务: {task.name}")

                    # 更新任务状态为运行中
                    task.last_run_at = datetime.now()
                    task.last_run_status = 'running'
                    task.total_runs += 1
                    db.commit()

                    # 根据任务类型执行不同的逻辑
                    result = await self._run_task_by_type(task, db)

                    # 更新任务执行结果
                    if result['success']:
                        task.last_run_status = 'success'
                        task.last_run_message = result['message']
                        task.success_runs += 1
                        logger.info(f"✅ 任务 {task.name} 执行成功: {result['message']}")
                    else:
                        task.last_run_status = 'failed'
                        task.last_run_message = result['message']
                        task.failed_runs += 1
                        logger.error(f"❌ 任务 {task.name} 执行失败: {result['message']}")

                    db.commit()

                except Exception as e:
                    logger.error(f"❌ 执行任务 {task_id} 时发生异常: {str(e)}")
                    if task:
                        task.last_run_status = 'failed'
                        task.last_run_message = f'异常: {str(e)}'
                        task.failed_runs += 1
                        db.commit()
                finally:
                    db.close()

            # 运行异步任务
            asyncio.run(_run())

        # 在新线程中执行，避免阻塞调度器
        thread = threading.Thread(target=run_in_new_thread)
        thread.start()

    async def _run_task_by_type(self, task: ScheduledTask, db: Session) -> dict:
        """根据任务类型执行具体逻辑

        Args:
            task: 任务配置
            db: 数据库会话

        Returns:
            执行结果
        """
        try:
            if task.task_type == 'calculate_top_performers':
                # 计算日涨幅榜
                service = TopPerformerService(db)
                result = service.calculate_and_save(limit=50, overwrite=True, period='daily')
                return result

            elif task.task_type == 'calculate_weekly_top_performers':
                # 计算周涨幅榜
                service = TopPerformerService(db)
                result = service.calculate_and_save(limit=50, overwrite=True, period='weekly')
                return result

            elif task.task_type == 'calculate_monthly_top_performers':
                # 计算月涨幅榜
                service = TopPerformerService(db)
                result = service.calculate_and_save(limit=50, overwrite=True, period='monthly')
                return result

            elif task.task_type == 'full_sync':
                # 全量数据同步
                ak_service = AKShareService()
                result = await self._full_data_sync(ak_service, db)
                return result

            elif task.task_type == 'strategy_selection':
                # 选股策略执行
                strategy_service = StrategyService()
                results = strategy_service.execute_strategies(
                    db=db,
                    strategy_ids=None,  # None表示执行所有启用的策略
                    trade_date=None     # None表示使用最新交易日
                )

                # 统计执行结果
                total = len(results)
                success_count = sum(1 for r in results if r.get('success', False))
                fail_count = total - success_count

                return {
                    'success': fail_count == 0,
                    'message': f'执行选股策略完成：共{total}个策略，成功{success_count}个，失败{fail_count}个',
                    'details': results
                }

            else:
                return {
                    'success': False,
                    'message': f'未知的任务类型: {task.task_type}'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'执行失败: {str(e)}'
            }

    async def _full_data_sync(self, ak_service: AKShareService, db: Session) -> dict:
        """全量数据同步

        Args:
            ak_service: AKShare服务
            db: 数据库会话

        Returns:
            执行结果
        """
        try:
            logger.info("开始全量数据同步...")

            # 1. 同步股票列表（同步方法）
            stock_result = ak_service.sync_stock_list_to_db(db)
            logger.info(f"同步股票列表完成: {stock_result.get('synced', 0)} 只股票")

            # 2. 批量同步K线数据（使用同步方法，智能增量更新）
            kline_result = ak_service.batch_sync_kline_to_db(
                db=db,
                limit=None,  # 不限制数量，同步所有需要更新的股票
                force_full_sync=False,  # 增量更新
                only_active=True  # 只同步活跃股票
            )

            logger.info(f"同步K线数据完成: {kline_result.get('synced', 0)} 只股票")

            return {
                'success': True,
                'message': f"全量同步完成: {stock_result.get('synced', 0)}只股票, {kline_result.get('synced', 0)}只K线"
            }

        except Exception as e:
            logger.error(f"全量数据同步失败: {str(e)}")
            return {
                'success': False,
                'message': f'同步失败: {str(e)}'
            }

    def run_task_now(self, task_id: int):
        """立即执行任务（手动触发）

        Args:
            task_id: 任务ID
        """
        db = SessionLocal()
        try:
            task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                return {'success': False, 'message': '任务不存在'}

            # 使用DateTrigger立即执行
            self.scheduler.add_job(
                func=self.execute_task,
                trigger=DateTrigger(run_date=datetime.now()),
                id=f'{task.name}_manual_{datetime.now().timestamp()}',
                args=[task_id],
                name=f'{task.name}_manual'
            )

            logger.info(f"✅ 手动触发任务: {task.name}")
            return {'success': True, 'message': f'任务 {task.name} 已触发执行'}

        except Exception as e:
            logger.error(f"❌ 手动触发任务失败: {str(e)}")
            return {'success': False, 'message': f'触发失败: {str(e)}'}
        finally:
            db.close()


# 全局调度器实例
scheduler = TaskScheduler()
