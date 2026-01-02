"""涨幅榜计算服务"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.core.logging import logger
from app.models.stock import Stock
from app.models.kline import KlineDaily
from app.models.top_performer import TopPerformer


class TopPerformerService:
    """涨幅榜计算服务

    计算、保存、查询涨幅榜数据
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_daily_top_performers(
        self,
        calc_date: Optional[date] = None,
        limit: int = 50
    ) -> List[TopPerformer]:
        """计算日涨幅榜

        Args:
            calc_date: 计算日期，默认为最近交易日
            limit: 返回前N名

        Returns:
            涨幅榜数据列表
        """
        if calc_date is None:
            calc_date = self._get_latest_trade_date()

        logger.info(f"开始计算 {calc_date} 的日涨幅榜（Top {limit}）")

        # 获取所有有效股票（过滤ST、退市）
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        # 过滤掉ST、*ST和退市股票
        stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

        # 计算涨跌幅
        performers = []
        for stock in stocks:
            # 获取计算日期和前一个交易日的K线数据
            kline = self.db.query(KlineDaily).filter(
                and_(
                    KlineDaily.ts_code == stock.ts_code,
                    KlineDaily.trade_date <= calc_date
                )
            ).order_by(KlineDaily.trade_date.desc()).first()

            if not kline or not kline.close:
                continue

            # 获取前一个交易日数据
            prev_kline = self.db.query(KlineDaily).filter(
                and_(
                    KlineDaily.ts_code == stock.ts_code,
                    KlineDaily.trade_date < kline.trade_date
                )
            ).order_by(KlineDaily.trade_date.desc()).first()

            if not prev_kline or not prev_kline.close:
                continue

            # 计算涨跌幅
            change_pct = ((kline.close - prev_kline.close) / prev_kline.close) * 100

            performers.append({
                'ts_code': stock.ts_code,
                'name': stock.name,
                'date': kline.trade_date,
                'period': 'daily',
                'change_pct': round(change_pct, 2),
                'amount': float(kline.amount) if kline.amount else 0,
                'market': stock.market,
                'board': stock.board,
                'start_price': float(prev_kline.close),  # 期初价格（前收盘）
                'end_price': float(kline.close),  # 期末价格（当期收盘）
                'start_date': prev_kline.trade_date,  # 期初日期
                'end_date': kline.trade_date,  # 期末日期
            })

        # 按涨跌幅排序
        performers.sort(key=lambda x: x['change_pct'], reverse=True)

        # 取前N名并添加排名
        top_performers = []
        for rank, p in enumerate(performers[:limit], start=1):
            p['rank'] = rank
            top_performers.append(TopPerformer(**p))

        logger.info(f"计算完成，共 {len(top_performers)} 只股票上榜")

        return top_performers

    def save_top_performers(
        self,
        performers: List[TopPerformer],
        overwrite: bool = True
    ) -> int:
        """保存涨幅榜数据到数据库

        Args:
            performers: 涨幅榜数据列表
            overwrite: 是否覆盖旧数据

        Returns:
            保存的记录数
        """
        saved_count = 0

        for performer in performers:
            if overwrite:
                # 删除同一天同周期的旧数据
                self.db.query(TopPerformer).filter(
                    and_(
                        TopPerformer.date == performer.date,
                        TopPerformer.period == performer.period,
                        TopPerformer.ts_code == performer.ts_code
                    )
                ).delete()

            self.db.add(performer)
            saved_count += 1

        self.db.commit()
        logger.info(f"保存涨幅榜数据完成，共 {saved_count} 条记录")

        return saved_count

    def get_top_performers(
        self,
        calc_date: Optional[date] = None,
        period: str = 'daily',
        limit: int = 50
    ) -> List[Dict]:
        """从数据库获取涨幅榜数据

        Args:
            calc_date: 查询日期，默认为最新
            period: 时间周期
            limit: 返回数量

        Returns:
            涨幅榜数据列表
        """
        if calc_date is None:
            calc_date = self._get_latest_trade_date()

        query = self.db.query(TopPerformer).filter(
            and_(
                TopPerformer.date == calc_date,
                TopPerformer.period == period
            )
        ).order_by(TopPerformer.rank)

        if limit:
            query = query.limit(limit)

        performers = query.all()
        return [p.to_dict() for p in performers]

    def calculate_and_save(
        self,
        calc_date: Optional[date] = None,
        limit: int = 50,
        overwrite: bool = True,
        period: str = 'daily'
    ) -> Dict:
        """计算并保存涨幅榜（一次性操作）

        Args:
            calc_date: 计算日期
            limit: 前N名
            overwrite: 是否覆盖
            period: 时间周期（daily/weekly/monthly）

        Returns:
            执行结果
        """
        try:
            # 根据周期选择计算方法
            if period == 'daily':
                performers = self.calculate_daily_top_performers(calc_date, limit)
            elif period == 'weekly':
                performers = self.calculate_weekly_top_performers(week_count=1, limit=limit)
            elif period == 'monthly':
                performers = self.calculate_monthly_top_performers(month_count=1, limit=limit)
            else:
                return {
                    'success': False,
                    'message': f'不支持的时间周期: {period}',
                    'count': 0
                }

            if not performers:
                return {
                    'success': False,
                    'message': '没有计算出涨幅榜数据',
                    'count': 0
                }

            # 保存
            saved_count = self.save_top_performers(performers, overwrite)

            period_name = {'daily': '日', 'weekly': '周', 'monthly': '月'}.get(period, period)
            return {
                'success': True,
                'message': f'成功计算并保存 {saved_count} 条{period_name}涨幅榜数据',
                'count': saved_count,
                'period': period,
                'date': performers[0].date.isoformat() if performers else None
            }

        except Exception as e:
            logger.error(f"计算涨幅榜失败: {str(e)}")
            self.db.rollback()
            return {
                'success': False,
                'message': f'计算失败: {str(e)}',
                'count': 0
            }

    def calculate_weekly_top_performers(
        self,
        week_count: int = 1,
        limit: int = 50
    ) -> List[TopPerformer]:
        """计算周涨幅榜（优化版本）

        逻辑：
        1. 获取最近完整周的最后一个交易日（本周五）
        2. 获取上一周的最后一个交易日（上周五）
        3. 计算每只股票在这两个交易日之间的涨跌幅

        Args:
            week_count: 计算最近N周（默认1周）
            limit: 返回前N名

        Returns:
            涨幅榜数据列表
        """
        logger.info(f"开始计算最近{week_count}周的周涨幅榜（Top {limit}）")

        from sqlalchemy import func, extract
        from datetime import timedelta, date as date_class

        # 获取所有周的最后一个交易日（按周分组）
        weekly_dates_query = self.db.query(
            func.max(KlineDaily.trade_date).label('last_date'),
            extract('year', KlineDaily.trade_date).label('year'),
            extract('week', KlineDaily.trade_date).label('week'),
        ).group_by(
            extract('year', KlineDaily.trade_date),
            extract('week', KlineDaily.trade_date)
        ).order_by(
            extract('year', KlineDaily.trade_date).desc(),
            extract('week', KlineDaily.trade_date).desc()
        ).limit(week_count + 1).all()  # 多取一周，用于对比

        if len(weekly_dates_query) < 2:
            logger.warning("数据不足，无法计算周涨幅")
            return []

        # 本周和上周的最后一个交易日
        current_week_end = weekly_dates_query[0][0]
        previous_week_end = weekly_dates_query[1][0]

        logger.info(f"本周最后一个交易日: {current_week_end}")
        logger.info(f"上周最后一个交易日: {previous_week_end}")

        # 获取这两个日期的所有K线数据
        klines = self.db.query(KlineDaily).filter(
            KlineDaily.trade_date.in_([current_week_end, previous_week_end])
        ).all()

        # 按股票和日期分组
        klines_dict = {}  # {ts_code: {date: kline}}
        for k in klines:
            if k.ts_code not in klines_dict:
                klines_dict[k.ts_code] = {}
            klines_dict[k.ts_code][k.trade_date] = k

        # 获取所有有效股票
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

        # 计算涨跌幅
        performers = []
        for stock in stocks:
            if stock.ts_code not in klines_dict:
                continue

            stock_klines = klines_dict[stock.ts_code]

            # 检查是否有本周和上周的数据
            if current_week_end not in stock_klines or previous_week_end not in stock_klines:
                continue

            week_end_kline = stock_klines[current_week_end]
            week_start_kline = stock_klines[previous_week_end]

            if not week_end_kline.close or not week_start_kline.close:
                continue

            # 计算周涨跌幅
            change_pct = ((week_end_kline.close - week_start_kline.close) / week_start_kline.close) * 100

            performers.append({
                'ts_code': stock.ts_code,
                'name': stock.name,
                'date': current_week_end,
                'period': 'weekly',
                'change_pct': round(change_pct, 2),
                'amount': float(week_end_kline.amount) if week_end_kline.amount else 0,
                'market': stock.market,
                'board': stock.board,
                'start_price': float(week_start_kline.close),
                'end_price': float(week_end_kline.close),
                'start_date': week_start_kline.trade_date,
                'end_date': week_end_kline.trade_date,
            })

        # 按涨跌幅排序
        performers.sort(key=lambda x: x['change_pct'], reverse=True)

        # 取前N名并添加排名
        top_performers = []
        for rank, p in enumerate(performers[:limit], start=1):
            p['rank'] = rank
            top_performers.append(TopPerformer(**p))

        logger.info(f"周涨幅榜计算完成，共 {len(top_performers)} 只股票上榜")
        return top_performers

    def calculate_monthly_top_performers(
        self,
        month_count: int = 1,
        limit: int = 50
    ) -> List[TopPerformer]:
        """计算月涨幅榜（优化版本）

        逻辑：
        1. 获取最近完整月的最后一个交易日
        2. 获取上一月的最后一个交易日
        3. 计算每只股票在这两个交易日之间的涨跌幅

        Args:
            month_count: 计算最近N月（默认1月）
            limit: 返回前N名

        Returns:
            涨幅榜数据列表
        """
        logger.info(f"开始计算最近{month_count}月的月涨幅榜（Top {limit}）")

        from sqlalchemy import func, extract
        from datetime import timedelta, date as date_class

        # 获取所有月的最后一个交易日（按月分组）
        monthly_dates_query = self.db.query(
            func.max(KlineDaily.trade_date).label('last_date'),
            extract('year', KlineDaily.trade_date).label('year'),
            extract('month', KlineDaily.trade_date).label('month'),
        ).group_by(
            extract('year', KlineDaily.trade_date),
            extract('month', KlineDaily.trade_date)
        ).order_by(
            extract('year', KlineDaily.trade_date).desc(),
            extract('month', KlineDaily.trade_date).desc()
        ).limit(month_count + 1).all()  # 多取一月，用于对比

        if len(monthly_dates_query) < 2:
            logger.warning("数据不足，无法计算月涨幅")
            return []

        # 本月和上月的最后一个交易日
        current_month_end = monthly_dates_query[0][0]
        previous_month_end = monthly_dates_query[1][0]

        logger.info(f"本月最后一个交易日: {current_month_end}")
        logger.info(f"上月最后一个交易日: {previous_month_end}")

        # 获取这两个日期的所有K线数据
        klines = self.db.query(KlineDaily).filter(
            KlineDaily.trade_date.in_([current_month_end, previous_month_end])
        ).all()

        # 按股票和日期分组
        klines_dict = {}  # {ts_code: {date: kline}}
        for k in klines:
            if k.ts_code not in klines_dict:
                klines_dict[k.ts_code] = {}
            klines_dict[k.ts_code][k.trade_date] = k

        # 获取所有有效股票
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        stocks = [s for s in stocks if not any(keyword in s.name for keyword in ['ST', '*ST', '退'])]

        # 计算涨跌幅
        performers = []
        for stock in stocks:
            if stock.ts_code not in klines_dict:
                continue

            stock_klines = klines_dict[stock.ts_code]

            # 检查是否有本月和上月的数据
            if current_month_end not in stock_klines or previous_month_end not in stock_klines:
                continue

            month_end_kline = stock_klines[current_month_end]
            month_start_kline = stock_klines[previous_month_end]

            if not month_end_kline.close or not month_start_kline.close:
                continue

            # 计算月涨跌幅
            change_pct = ((month_end_kline.close - month_start_kline.close) / month_start_kline.close) * 100

            performers.append({
                'ts_code': stock.ts_code,
                'name': stock.name,
                'date': current_month_end,
                'period': 'monthly',
                'change_pct': round(change_pct, 2),
                'amount': float(month_end_kline.amount) if month_end_kline.amount else 0,
                'market': stock.market,
                'board': stock.board,
                'start_price': float(month_start_kline.close),
                'end_price': float(month_end_kline.close),
                'start_date': month_start_kline.trade_date,
                'end_date': month_end_kline.trade_date,
            })

        # 按涨跌幅排序
        performers.sort(key=lambda x: x['change_pct'], reverse=True)

        # 取前N名并添加排名
        top_performers = []
        for rank, p in enumerate(performers[:limit], start=1):
            p['rank'] = rank
            top_performers.append(TopPerformer(**p))

        logger.info(f"月涨幅榜计算完成，共 {len(top_performers)} 只股票上榜")
        return top_performers

    def _get_latest_trade_date(self) -> date:
        """获取最新交易日期"""
        latest = self.db.query(KlineDaily.trade_date).order_by(
            KlineDaily.trade_date.desc()
        ).first()

        if latest:
            return latest[0]

        # 如果没有数据，返回昨天
        return (date.today() - timedelta(days=1))
