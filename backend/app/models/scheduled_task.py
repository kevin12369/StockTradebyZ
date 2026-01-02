"""定时任务配置模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from app.models.base import Base


class ScheduledTask(Base):
    """定时任务配置表

    管理系统的定时任务，如：
    - full_sync: 全量数据同步
    - calculate_top_performers: 涨幅榜计算
    - strategy_selection: 选股策略执行
    """
    __tablename__ = 'scheduled_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(100), nullable=False, unique=True, comment='任务名称')
    task_type = Column(String(50), nullable=False, comment='任务类型：full_sync/calculate_top_performers/strategy_selection')
    description = Column(String(500), comment='任务描述')
    config = Column(JSON, comment='任务配置（JSON格式，如选股策略ID列表）')

    # 定时配置
    enabled = Column(Boolean, default=True, comment='是否启用')
    cron_expression = Column(String(100), comment='Cron表达式（可选）')
    scheduled_time = Column(String(10), comment='定时时间（HH:MM格式）')

    # 执行状态
    last_run_at = Column(DateTime, comment='上次执行时间')
    last_run_status = Column(String(20), comment='上次执行状态：success/failed/running')
    last_run_message = Column(Text, comment='上次执行信息')
    next_run_at = Column(DateTime, comment='下次执行时间')

    # 统计信息
    total_runs = Column(Integer, default=0, comment='总执行次数')
    success_runs = Column(Integer, default=0, comment='成功次数')
    failed_runs = Column(Integer, default=0, comment='失败次数')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'task_type': self.task_type,
            'description': self.description,
            'config': self.config,
            'enabled': self.enabled,
            'cron_expression': self.cron_expression,
            'scheduled_time': self.scheduled_time,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_status': self.last_run_status,
            'last_run_message': self.last_run_message,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'total_runs': self.total_runs,
            'success_runs': self.success_runs,
            'failed_runs': self.failed_runs,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
