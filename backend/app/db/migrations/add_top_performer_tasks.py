"""
迁移脚本：添加涨幅榜计算定时任务

解决涨幅榜数据缺失问题，添加日/周/月涨幅榜计算任务
"""
import json
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.scheduled_task import ScheduledTask
from app.core.logging import logger


def get_default_tasks() -> list:
    """获取默认的涨幅榜任务配置

    Returns:
        任务配置列表
    """
    return [
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


def upgrade() -> dict:
    """执行迁移：添加缺失的涨幅榜计算任务

    Returns:
        迁移结果报告
    """
    db = SessionLocal()
    result = {
        "success": False,
        "added": [],
        "updated": [],
        "skipped": [],
        "errors": []
    }

    try:
        logger.info("🔄 开始迁移：添加涨幅榜计算任务...")

        default_tasks = get_default_tasks()

        for task_config in default_tasks:
            task_name = task_config["name"]

            # 检查任务是否已存在
            existing = db.query(ScheduledTask).filter(
                ScheduledTask.name == task_name
            ).first()

            if existing:
                # 任务已存在，检查是否需要更新
                needs_update = False
                update_fields = []

                for key in ["task_type", "description", "cron_expression", "scheduled_time"]:
                    if getattr(existing, key) != task_config.get(key):
                        needs_update = True
                        update_fields.append(key)
                        setattr(existing, key, task_config[key])

                # 检查enabled状态（如果原任务是禁用的，则启用它）
                if not existing.enabled and task_config["enabled"]:
                    needs_update = True
                    update_fields.append("enabled")
                    existing.enabled = True

                if needs_update:
                    result["updated"].append({
                        "name": task_name,
                        "fields": update_fields
                    })
                    logger.info(f"📝 更新任务: {task_name} (字段: {', '.join(update_fields)})")
                else:
                    result["skipped"].append(task_name)
                    logger.info(f"⏭️  跳过任务: {task_name} (已是最新配置)")
            else:
                # 任务不存在，创建新任务
                new_task = ScheduledTask(**task_config)
                db.add(new_task)
                result["added"].append(task_name)
                logger.info(f"✅ 添加任务: {task_name}")

        # 提交所有更改
        db.commit()

        # 构建成功消息
        total_changes = len(result["added"]) + len(result["updated"])
        if total_changes > 0:
            result["success"] = True
            msg_parts = []
            if result["added"]:
                msg_parts.append(f"添加{len(result['added'])}个任务")
            if result["updated"]:
                msg_parts.append(f"更新{len(result['updated'])}个任务")
            if result["skipped"]:
                msg_parts.append(f"跳过{len(result['skipped'])}个已存在任务")
            result["message"] = f"迁移完成: {', '.join(msg_parts)}"
        else:
            result["success"] = True
            result["message"] = f"所有任务已存在且为最新配置 (跳过{len(result['skipped'])}个)"

        logger.info(f"✅ 迁移完成: {result['message']}")

    except Exception as e:
        db.rollback()
        result["success"] = False
        result["message"] = f"迁移失败: {str(e)}"
        result["errors"].append(str(e))
        logger.error(f"❌ 迁移失败: {str(e)}")

    finally:
        db.close()

    return result


def downgrade() -> dict:
    """回滚迁移：删除涨幅榜计算任务

    Returns:
        回滚结果报告
    """
    db = SessionLocal()
    result = {
        "success": False,
        "deleted": [],
        "errors": []
    }

    try:
        logger.info("🔄 开始回滚：删除涨幅榜计算任务...")

        default_tasks = get_default_tasks()
        task_names = [task["name"] for task in default_tasks]

        # 删除所有涨幅榜相关任务
        deleted = db.query(ScheduledTask).filter(
            ScheduledTask.name.in_(task_names)
        ).delete(synchronize_session=False)

        db.commit()

        result["deleted"] = task_names
        result["success"] = True
        result["message"] = f"回滚完成: 删除了{deleted}个任务"

        logger.info(f"✅ 回滚完成: {result['message']}")

    except Exception as e:
        db.rollback()
        result["success"] = False
        result["message"] = f"回滚失败: {str(e)}"
        result["errors"].append(str(e))
        logger.error(f"❌ 回滚失败: {str(e)}")

    finally:
        db.close()

    return result


if __name__ == "__main__":
    import sys

    # 支持命令行参数
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "upgrade":
            result = upgrade()
        elif action == "downgrade":
            result = downgrade()
        elif action == "info":
            # 显示任务配置信息
            print("=" * 60)
            print("涨幅榜计算任务配置")
            print("=" * 60)
            for task in get_default_tasks():
                print(f"\n任务名称: {task['name']}")
                print(f"  类型: {task['task_type']}")
                print(f"  描述: {task['description']}")
                print(f"  定时: {task['cron_expression']} ({task['scheduled_time']})")
                print(f"  启用: {task['enabled']}")
            sys.exit(0)
        else:
            print(f"❌ 未知操作: {action}")
            print("用法: python add_top_performer_tasks.py [upgrade|downgrade|info]")
            sys.exit(1)
    else:
        # 默认执行 upgrade
        result = upgrade()

    # 打印结果
    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ " + result["message"])
        if result["added"]:
            print(f"   添加: {', '.join(result['added'])}")
        if result["updated"]:
            print(f"   更新: {', '.join([r['name'] for r in result['updated']])}")
        if result["skipped"]:
            print(f"   跳过: {', '.join(result['skipped'])}")
    else:
        print("❌ " + result["message"])
        if result["errors"]:
            print("   错误详情:")
            for err in result["errors"]:
                print(f"   - {err}")
    print("=" * 60)

    sys.exit(0 if result["success"] else 1)
