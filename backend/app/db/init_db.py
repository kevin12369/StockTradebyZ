"""
数据库初始化脚本

创建数据库表并初始化默认数据
"""

import json

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.base import Base
from app.models.stock import Stock
from app.models.kline import KlineDaily
from app.models.strategy import Strategy
from app.models.backtest import SelectionResult, DataUpdateLog
from app.models.scheduled_task import ScheduledTask
from app.core.config import settings


def init_db_data(db: Session) -> None:
    """初始化数据库默认数据

    Args:
        db: 数据库会话
    """
    # 初始化默认策略配置（从 configs.json 读取）
    try:
        # 尝试多个可能的位置
        config_paths = [
            settings.BASE_DIR / "configs.json",  # backend 目录
            settings.BASE_DIR.parent / "configs.json",  # 项目根目录
        ]

        config_file = None
        for path in config_paths:
            if path.exists():
                config_file = path
                break

        if not config_file:
            raise FileNotFoundError("configs.json not found in any expected location")

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        for strategy_config in config_data.get("selectors", []):
            # 检查策略是否已存在
            existing = db.query(Strategy).filter(
                Strategy.class_name == strategy_config["class"]
            ).first()

            if not existing:
                strategy = Strategy(
                    class_name=strategy_config["class"],
                    alias=strategy_config["alias"],
                    description=f"{strategy_config['alias']}选股策略",
                    is_active=strategy_config.get("activate", True),
                    config_json=json.dumps(strategy_config.get("params", {}), ensure_ascii=False),
                    sort_order=0,
                )
                db.add(strategy)
                logger.info(f"添加策略: {strategy.alias}")

        db.commit()
        logger.info("✅ 默认策略初始化完成")

    except FileNotFoundError:
        logger.warning("⚠️ configs.json 不存在，跳过策略初始化")
    except Exception as e:
        logger.error(f"❌ 策略初始化失败: {e}")
        db.rollback()

    # 初始化默认定时任务
    try:
        # 获取所有启用的策略ID
        strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
        strategy_ids = [s.id for s in strategies]

        # 默认定时任务列表
        default_tasks = [
            {
                "name": "每日选股",
                "task_type": "strategy_selection",
                "description": "工作日20:00自动执行所有启用的选股策略",
                "config": {"strategy_ids": strategy_ids} if strategy_ids else None,
                "enabled": False,  # 默认禁用，让用户自己决定是否启用
                "cron_expression": "0 20 * * MON-FRI",  # 工作日20:00
                "scheduled_time": "20:00",
            },
            {
                "name": "全量数据同步",
                "task_type": "full_sync",
                "description": "同步股票列表和批量同步K线数据",
                "enabled": False,
                "cron_expression": "0 18 * * MON-FRI",  # 工作日18:00
                "scheduled_time": "18:00",
            },
            {
                "name": "涨幅榜计算",
                "task_type": "calculate_top_performers",
                "description": "计算日涨跌幅榜Top50",
                "enabled": True,
                "cron_expression": "0 18:30 * * MON-FRI",  # 工作日18:30
                "scheduled_time": "18:30",
            },
            {
                "name": "周涨幅榜计算",
                "task_type": "calculate_weekly_top_performers",
                "description": "计算周涨跌幅榜Top50",
                "enabled": True,
                "cron_expression": "0 19:00 * * MON-FRI",  # 工作日19:00
                "scheduled_time": "19:00",
            },
            {
                "name": "月涨幅榜计算",
                "task_type": "calculate_monthly_top_performers",
                "description": "计算月涨跌幅榜Top50",
                "enabled": True,
                "cron_expression": "0 19:30 1 * *",  # 每月1日19:30
                "scheduled_time": "19:30",
            },
        ]

        for task_data in default_tasks:
            # 检查任务是否已存在
            existing = db.query(ScheduledTask).filter(
                ScheduledTask.name == task_data["name"]
            ).first()

            if not existing:
                task = ScheduledTask(**task_data)
                db.add(task)
                logger.info(f"添加定时任务: {task_data['name']}")

        db.commit()
        logger.info("✅ 默认定时任务初始化完成")

    except Exception as e:
        logger.error(f"❌ 定时任务初始化失败: {e}")
        db.rollback()


def init_db() -> None:
    """初始化数据库

    创建所有表并初始化默认数据
    """
    logger.info("🔧 开始初始化数据库...")

    # 创建所有表
    Base.metadata.create_all(bind=SessionLocal().bind)
    logger.info("✅ 数据库表创建完成")

    # 初始化默认数据
    db = SessionLocal()
    try:
        init_db_data(db)
    finally:
        db.close()

    logger.info("🎉 数据库初始化完成！")


def reset_db() -> None:
    """重置数据库（危险操作）

    删除所有表并重新创建
    """
    logger.warning("⚠️ 开始重置数据库...")

    # 删除所有表
    Base.metadata.drop_all(bind=SessionLocal().bind)
    logger.info("🗑️  数据库表已删除")

    # 重新创建
    init_db()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_db()
    else:
        init_db()
