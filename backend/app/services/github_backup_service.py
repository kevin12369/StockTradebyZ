"""
GitHub 备份服务

将数据库备份到 GitHub Release，支持数据恢复和共享
"""

import os
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.logging import logger


class GitHubBackupService:
    """GitHub 备份服务

    功能：
    1. 导出数据库为 SQL 文件
    2. 压缩为 .gz 格式
    3. 上传到 GitHub Release
    4. 支持从 Release 恢复数据
    """

    def __init__(self, timeout: int = 300):
        """初始化 GitHub 备份服务

        Args:
            timeout: HTTP 请求超时时间（秒）
        """
        self.timeout = timeout

        # 从环境变量读取配置
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO", "your-username/stocktrade-data")
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
        self.backup_dir.mkdir(exist_ok=True)

        if not self.github_token:
            logger.warning("未设置 GITHUB_TOKEN 环境变量，GitHub 备份功能将不可用")

    async def backup_to_github(
        self,
        db_url: str,
        tag_name: Optional[str] = None,
        release_name: Optional[str] = None,
    ) -> dict:
        """备份数据库到 GitHub Release

        Args:
            db_url: 数据库连接 URL
            tag_name: Release 标签（默认：backup-YYYY-MM-DD）
            release_name: Release 名称（默认：数据备份 - YYYY-MM-DD）

        Returns:
            dict: 备份结果
        """
        if not self.github_token:
            return {
                "success": False,
                "message": "未配置 GITHUB_TOKEN，无法备份到 GitHub",
            }

        try:
            # 生成默认标签和名称
            date_str = datetime.now().strftime("%Y-%m-%d")
            if not tag_name:
                tag_name = f"backup-{date_str}"
            if not release_name:
                release_name = f"数据备份 - {date_str}"

            # 1. 导出数据库为 SQL 文件
            logger.info("开始导出数据库...")
            sql_file = await self._export_database(db_url)

            # 2. 压缩 SQL 文件
            logger.info("开始压缩文件...")
            gz_file = await self._compress_file(sql_file)

            # 3. 上传到 GitHub Release
            logger.info(f"开始上传到 GitHub Release: {tag_name}")
            result = await self._upload_to_github(
                gz_file,
                tag_name,
                release_name,
            )

            # 4. 清理临时文件
            sql_file.unlink(missing_ok=True)
            gz_file.unlink(missing_ok=True)

            logger.info(f"备份完成: {result.get('html_url')}")
            return {
                "success": True,
                "message": "备份成功",
                "tag_name": tag_name,
                "release_name": release_name,
                "file_size": gz_file.stat().st_size,
                "html_url": result.get("html_url"),
                "api_url": result.get("url"),
            }

        except Exception as e:
            logger.error(f"备份失败: {e}")
            return {
                "success": False,
                "message": f"备份失败: {str(e)}",
            }

    async def _export_database(self, db_url: str) -> Path:
        """导出数据库为 SQL 文件

        Args:
            db_url: 数据库连接 URL

        Returns:
            Path: SQL 文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_file = self.backup_dir / f"stocktrade_{timestamp}.sql"

        # 使用 sqlite3 导出（仅支持 SQLite）
        if db_url.startswith("sqlite"):
            import sqlite3

            # 从 URL 提取数据库文件路径
            db_path = db_url.replace("sqlite:///", "")

            # 连接数据库并导出
            conn = sqlite3.connect(db_path)
            with open(sql_file, "w", encoding="utf-8") as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            conn.close()

            logger.info(f"数据库导出完成: {sql_file} ({sql_file.stat().st_size} bytes)")
            return sql_file
        else:
            raise NotImplementedError(f"暂不支持 {db_url} 数据库的导出")

    async def _compress_file(self, file_path: Path) -> Path:
        """压缩文件为 .gz 格式

        Args:
            file_path: 原始文件路径

        Returns:
            Path: 压缩文件路径
        """
        gz_file = file_path.with_suffix(file_path.suffix + ".gz")

        with open(file_path, "rb") as f_in:
            with gzip.open(gz_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        logger.info(
            f"文件压缩完成: {gz_file} "
            f"({file_path.stat().st_size} -> {gz_file.stat().st_size} bytes, "
            f"压缩率: {100 * (1 - gz_file.stat().st_size / file_path.stat().st_size):.1f}%)"
        )
        return gz_file

    async def _upload_to_github(
        self,
        file_path: Path,
        tag_name: str,
        release_name: str,
    ) -> dict:
        """上传文件到 GitHub Release

        Args:
            file_path: 文件路径
            tag_name: Release 标签
            release_name: Release 名称

        Returns:
            dict: Release 信息
        """
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. 检查 Release 是否存在
            releases_url = f"https://api.github.com/repos/{self.github_repo}/releases/tags/{tag_name}"
            response = await client.get(releases_url, headers=headers)

            if response.status_code == 200:
                # Release 已存在，删除旧版本
                release_data = response.json()
                release_id = release_data["id"]

                # 删除旧 Release
                delete_url = f"https://api.github.com/repos/{self.github_repo}/releases/{release_id}"
                await client.delete(delete_url, headers=headers)
                logger.info(f"删除旧 Release: {tag_name}")

            # 2. 创建 Release
            create_url = f"https://api.github.com/repos/{self.github_repo}/releases"
            release_data = {
                "tag_name": tag_name,
                "name": release_name,
                "body": f"自动数据备份 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "draft": False,
                "prerelease": False,
            }

            response = await client.post(create_url, headers=headers, json=release_data)
            response.raise_for_status()
            release_info = response.json()
            upload_url = release_info["upload_url"].replace("{?name,label}", "")

            logger.info(f"创建 Release 成功: {release_info['html_url']}")

            # 3. 上传文件
            file_name = file_path.name
            upload_url_with_name = f"{upload_url}?name={file_name}"

            with open(file_path, "rb") as f:
                file_content = f.read()

            upload_headers = {
                **headers,
                "Content-Type": "application/gzip",
            }

            response = await client.post(
                upload_url_with_name,
                headers=upload_headers,
                content=file_content,
            )
            response.raise_for_status()

            logger.info(f"文件上传成功: {file_name} ({len(file_content)} bytes)")
            return release_info

    async def list_backups(self, limit: int = 10) -> list:
        """列出最近的备份

        Args:
            limit: 返回数量

        Returns:
            list: 备份列表
        """
        if not self.github_token:
            return []

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"https://api.github.com/repos/{self.github_repo}/releases"
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            releases = response.json()

            # 只返回自动备份（标签以 backup- 开头）
            backups = [
                {
                    "tag_name": r["tag_name"],
                    "name": r["name"],
                    "created_at": r["created_at"],
                    "html_url": r["html_url"],
                    "assets": [
                        {
                            "name": a["name"],
                            "size": a["size"],
                            "download_url": a["browser_download_url"],
                        }
                        for a in r["assets"]
                    ],
                }
                for r in releases
                if r["tag_name"].startswith("backup-")
            ][:limit]

            return backups


# 全局实例
github_backup_service = GitHubBackupService()
