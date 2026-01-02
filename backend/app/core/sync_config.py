"""
数据同步配置

支持两种同步模式：
1. 初始化模式：慢速降频，全量数据，适合首次部署
2. 日常模式：快速增量，只更新最新数据，适合日常定时任务
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SyncMode(str, Enum):
    """同步模式枚举"""
    INIT = "init"  # 初始化模式（慢速全量）
    DAILY = "daily"  # 日常模式（快速增量）


@dataclass
class SyncConfig:
    """同步配置

    Attributes:
        mode: 同步模式
        rate_limit: 速率限制（每秒请求数）
        burst_size: 突发请求容量
        days_to_fetch: 获取数据天数（None=全量）
        force_full_sync: 是否强制全量同步
        enable_github_backup: 是否启用 GitHub 备份
    """

    mode: SyncMode
    rate_limit: float
    burst_size: int
    days_to_fetch: Optional[int]
    force_full_sync: bool
    enable_github_backup: bool
    description: str


# 预定义配置
SYNC_CONFIGS = {
    SyncMode.INIT: SyncConfig(
        mode=SyncMode.INIT,
        rate_limit=0.1,  # 每10秒1个请求（超保守）
        burst_size=2,  # 突发容量2，避免累积误差
        days_to_fetch=None,  # None = 全量（近3年）
        force_full_sync=True,  # 强制全量同步
        enable_github_backup=True,  # 启用 GitHub 备份
        description="初始化模式：慢速全量同步（每10秒1个请求）"
    ),
    SyncMode.DAILY: SyncConfig(
        mode=SyncMode.DAILY,
        rate_limit=1.0,  # 每1秒1个请求（快速）
        burst_size=10,  # 突发容量10
        days_to_fetch=3,  # 只获取最近3天数据（增量）
        force_full_sync=False,  # 增量更新
        enable_github_backup=False,  # 不启用 GitHub 备份
        description="日常模式：快速增量同步（每1秒1个请求，只更新最新数据）"
    ),
}


def get_sync_config(mode: SyncMode = SyncMode.DAILY) -> SyncConfig:
    """获取同步配置

    Args:
        mode: 同步模式

    Returns:
        SyncConfig: 同步配置对象
    """
    return SYNC_CONFIGS[mode]


def get_sync_mode_by_name(name: str) -> SyncMode:
    """根据名称获取同步模式

    Args:
        name: 模式名称（init/daily）

    Returns:
        SyncMode: 同步模式枚举
    """
    for mode in SyncMode:
        if mode.value == name:
            return mode
    raise ValueError(f"未知的同步模式: {name}")
