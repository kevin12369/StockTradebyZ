"""
命令行工具

提供便捷的管理命令用于系统维护
"""
import sys
import io
from pathlib import Path
from typing import Optional

# 设置UTF-8编码输出（解决Windows终端GBK编码问题）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.logging import logger
from app.db.session import SessionLocal
from app.db.migrations.add_top_performer_tasks import upgrade, downgrade


def sync_tasks(action: str = "upgrade") -> dict:
    """同步定时任务配置

    Args:
        action: 操作类型 (upgrade/downgrade/info)

    Returns:
        操作结果
    """
    logger.info(f"🔄 开始同步定时任务配置 (action={action})...")

    if action == "upgrade":
        result = upgrade()
    elif action == "downgrade":
        result = downgrade()
    elif action == "info":
        # 显示当前任务配置信息
        from app.db.migrations.add_top_performer_tasks import get_default_tasks
        print("\n" + "=" * 60)
        print("涨幅榜计算任务配置")
        print("=" * 60)
        for task in get_default_tasks():
            print(f"\n📋 {task['name']}")
            print(f"   类型: {task['task_type']}")
            print(f"   描述: {task['description']}")
            print(f"   定时: {task['scheduled_time']} ({task['cron_expression']})")
            print(f"   状态: {'✅ 已启用' if task['enabled'] else '❌ 已禁用'}")
        print("=" * 60 + "\n")
        return {"success": True, "message": "已显示任务配置信息"}
    else:
        return {
            "success": False,
            "message": f"未知操作: {action}。可用操作: upgrade, downgrade, info"
        }

    return result


def list_tasks() -> dict:
    """列出数据库中所有定时任务

    Returns:
        任务列表
    """
    from app.models.scheduled_task import ScheduledTask

    db = SessionLocal()
    try:
        tasks = db.query(ScheduledTask).order_by(ScheduledTask.id).all()

        if not tasks:
            return {
                "success": True,
                "message": "数据库中暂无定时任务",
                "tasks": []
            }

        print("\n" + "=" * 80)
        print("数据库中的定时任务")
        print("=" * 80)
        print(f"{'ID':<5} {'名称':<20} {'类型':<30} {'状态':<8} {'定时'}")
        print("-" * 80)

        for task in tasks:
            status = "✅启用" if task.enabled else "❌禁用"
            scheduled = task.scheduled_time or task.cron_expression or "-"
            print(f"{task.id:<5} {task.name:<20} {task.task_type:<30} {status:<8} {scheduled}")

        print("=" * 80 + "\n")

        return {
            "success": True,
            "message": f"共找到 {len(tasks)} 个定时任务",
            "tasks": [{"id": t.id, "name": t.name, "type": t.task_type, "enabled": t.enabled} for t in tasks]
        }

    except Exception as e:
        logger.error(f"❌ 查询任务失败: {str(e)}")
        return {
            "success": False,
            "message": f"查询失败: {str(e)}"
        }
    finally:
        db.close()


def run_task_now(task_id: Optional[int] = None, task_name: Optional[str] = None) -> dict:
    """立即执行指定的定时任务

    Args:
        task_id: 任务ID
        task_name: 任务名称

    Returns:
        执行结果
    """
    from app.models.scheduled_task import ScheduledTask
    from app.core.scheduler import scheduler

    db = SessionLocal()
    try:
        # 查找任务
        if task_id:
            task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        elif task_name:
            task = db.query(ScheduledTask).filter(ScheduledTask.name == task_name).first()
        else:
            return {
                "success": False,
                "message": "必须提供 task_id 或 task_name 参数"
            }

        if not task:
            return {
                "success": False,
                "message": f"任务不存在 (id={task_id}, name={task_name})"
            }

        # 触发任务
        result = scheduler.run_task_now(task.id)
        return result

    except Exception as e:
        logger.error(f"❌ 触发任务失败: {str(e)}")
        return {
            "success": False,
            "message": f"触发失败: {str(e)}"
        }
    finally:
        db.close()


def print_help():
    """显示帮助信息"""
    help_text = """
╔════════════════════════════════════════════════════════════════════════╗
║                    股票选股系统 - 命令行工具                            ║
╚════════════════════════════════════════════════════════════════════════╝

用法: python -m app.cli <命令> [参数]

可用命令:

  📋 任务管理:
     sync-tasks [upgrade|downgrade|info]  同步涨幅榜计算任务配置
     list-tasks                          列出所有定时任务
     run-task <task_id>                  立即执行指定任务

  🗄️  数据库管理:
     init-db [--reset]                   初始化数据库 (加 --reset 重置)
     check-db                            检查数据库连接

  🔧 系统工具:
     help                                显示此帮助信息

示例:

  # 同步涨幅榜任务（添加缺失的任务）
  python -m app.cli sync-tasks

  # 查看任务配置信息
  python -m app.cli sync-tasks info

  # 列出所有任务
  python -m app.cli list-tasks

  # 立即执行涨幅榜计算
  python -m app.cli run-task 1

  # 初始化数据库
  python -m app.cli init-db

  # 重置数据库（危险操作！）
  python -m app.cli init-db --reset

═════════════════════════════════════════════════════════════════════════
    """
    print(help_text)


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = sys.argv[1].lower()
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    try:
        if command in ["help", "-h", "--help"]:
            print_help()

        elif command == "sync-tasks":
            action = args[0] if args else "upgrade"
            result = sync_tasks(action)
            print(f"\n{'✅' if result['success'] else '❌'} {result['message']}")
            sys.exit(0 if result["success"] else 1)

        elif command == "list-tasks":
            result = list_tasks()
            print(f"\n{result['message']}")
            sys.exit(0 if result["success"] else 1)

        elif command == "run-task":
            if not args:
                print("❌ 错误: 请提供任务ID")
                print("用法: python -m app.cli run-task <task_id>")
                sys.exit(1)

            task_id = int(args[0])
            result = run_task_now(task_id=task_id)
            print(f"\n{'✅' if result['success'] else '❌'} {result['message']}")
            sys.exit(0 if result["success"] else 1)

        elif command == "init-db":
            from app.db.init_db import init_db, reset_db

            if "--reset" in args:
                print("\n⚠️  警告：即将重置数据库，所有数据将被删除！")
                confirm = input("确认继续？[yes/N]: ")
                if confirm.lower() in ["yes", "y"]:
                    reset_db()
                else:
                    print("❌ 操作已取消")
                    sys.exit(1)
            else:
                init_db()

        elif command == "check-db":
            db = SessionLocal()
            try:
                db.execute("SELECT 1")
                print("\n✅ 数据库连接正常")
            except Exception as e:
                print(f"\n❌ 数据库连接失败: {str(e)}")
                sys.exit(1)
            finally:
                db.close()

        else:
            print(f"❌ 未知命令: {command}")
            print("使用 'python -m app.cli help' 查看帮助")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 执行命令失败: {str(e)}")
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
