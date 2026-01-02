"""涨幅榜数据模型"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Index, Numeric
from app.models.base import Base


class TopPerformer(Base):
    """涨幅榜数据表

    存储每日计算的涨幅榜数据，支持不同时间维度
    """
    __tablename__ = 'top_performers'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    ts_code = Column(String(20), nullable=False, comment='股票代码')
    name = Column(String(100), comment='股票名称')
    date = Column(Date, nullable=False, comment='统计日期')
    period = Column(String(20), nullable=False, comment='时间周期：daily/weekly/monthly')

    # 涨跌幅数据
    change_pct = Column(Float, comment='涨跌幅(%)')
    amount = Column(Float, comment='成交额(元)')

    # 价格数据（用于前端显示）
    start_price = Column(Float, comment='期初价格')
    end_price = Column(Float, comment='期末价格')
    start_date = Column(Date, comment='期初日期')
    end_date = Column(Date, comment='期末日期')

    # 市场信息
    market = Column(String(10), comment='市场：SH/SZ/BJ')
    board = Column(String(50), comment='板块：沪主板/深主板/科创板/创业板/北交所')

    # 排名
    rank = Column(Integer, comment='排名')

    # 更新时间
    created_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 复合索引
    __table_args__ = (
        Index('idx_date_period', 'date', 'period'),
        Index('idx_ts_code_date', 'ts_code', 'date'),
        Index('idx_period_rank', 'period', 'rank'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'ts_code': self.ts_code,
            'name': self.name,
            'date': self.date.isoformat() if self.date else None,
            'period': self.period,
            'change_pct': self.change_pct,
            'amount': self.amount,
            'start_price': self.start_price,
            'end_price': self.end_price,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'market': self.market,
            'board': self.board,
            'rank': self.rank,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
