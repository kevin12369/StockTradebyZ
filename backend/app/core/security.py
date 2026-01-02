"""
安全相关模块
预留用于未来添加认证、授权等功能
"""

from passlib.context import CryptContext

# 密码加密上下文（预留）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)
