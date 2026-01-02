"""
双模式同步功能测试脚本

验证日常模式和初始化模式是否正常工作
"""

import asyncio
from app.core.sync_config import SyncMode, get_sync_config, get_sync_mode_by_name
from app.services.sync_manager import SyncManager


def test_sync_config():
    """测试同步配置"""
    print("\n========== 测试同步配置 ==========")

    # 测试获取配置
    daily_config = get_sync_config(SyncMode.DAILY)
    init_config = get_sync_config(SyncMode.INIT)

    print(f"\n日常模式配置:")
    print(f"  - 速率: {daily_config.rate_limit} req/s")
    print(f"  - 突发容量: {daily_config.burst_size}")
    print(f"  - 数据天数: {daily_config.days_to_fetch}")
    print(f"  - 强制全量: {daily_config.force_full_sync}")
    print(f"  - GitHub备份: {daily_config.enable_github_backup}")
    print(f"  - 描述: {daily_config.description}")

    print(f"\n初始化模式配置:")
    print(f"  - 速率: {init_config.rate_limit} req/s")
    print(f"  - 突发容量: {init_config.burst_size}")
    print(f"  - 数据天数: {init_config.days_to_fetch}")
    print(f"  - 强制全量: {init_config.force_full_sync}")
    print(f"  - GitHub备份: {init_config.enable_github_backup}")
    print(f"  - 描述: {init_config.description}")

    # 测试模式名称转换
    daily_mode = get_sync_mode_by_name("daily")
    init_mode = get_sync_mode_by_name("init")
    print(f"\n模式名称转换:")
    print(f"  - 'daily' -> {daily_mode}")
    print(f"  - 'init' -> {init_mode}")


def test_time_estimate():
    """测试时间估算"""
    print("\n========== 测试时间估算 ==========")

    # 模拟数据库URL
    db_url = "sqlite:///./test.db"

    # 创建同步管理器
    manager = SyncManager(db_url)

    # 测试不同股票数量的估算
    test_cases = [
        (100, SyncMode.DAILY),
        (1000, SyncMode.DAILY),
        (5000, SyncMode.DAILY),
        (100, SyncMode.INIT),
        (1000, SyncMode.INIT),
        (5000, SyncMode.INIT),
    ]

    print(f"\n{'股票数量':<10} {'模式':<10} {'估算时间'}")
    print("-" * 40)

    for stock_count, mode in test_cases:
        estimate = manager.estimate_sync_time(stock_count, mode)
        print(f"{stock_count:<10} {mode.value:<10} {estimate['formatted']}")


async def test_api_calls():
    """测试API调用（需要数据库）"""
    print("\n========== 测试API调用 ==========")

    # 注意：这需要真实的数据库连接
    # 这里只是演示调用方式

    print("\n日常模式调用示例:")
    print("  POST /api/v1/sync/quick?mode=daily")
    print("  或")
    print("  POST /api/v1/sync/daily")

    print("\n初始化模式调用示例:")
    print("  POST /api/v1/sync/quick?mode=init")
    print("  或")
    print("  POST /api/v1/sync/init")

    print("\n测试模式调用示例（只同步10只股票）:")
    print("  POST /api/v1/sync/quick?mode=daily&limit=10")

    print("\n时间估算调用示例:")
    print("  GET /api/v1/sync/estimate?stock_count=5000&mode=daily")


def main():
    """主函数"""
    print("\n=== 双模式同步系统测试 ===\n")

    # 测试配置
    test_sync_config()

    # 测试时间估算
    test_time_estimate()

    # 测试API调用
    asyncio.run(test_api_calls())

    print("\n=== 测试完成 ===")
    print("\n使用说明:")
    print("1. 日常模式: POST /api/v1/sync/daily (快速增量)")
    print("2. 初始化模式: POST /api/v1/sync/init (慢速全量+备份)")
    print("3. 快速同步: POST /api/v1/sync/quick?mode=daily")
    print("4. 时间估算: GET /api/v1/sync/estimate?stock_count=5000&mode=daily")


if __name__ == "__main__":
    main()
