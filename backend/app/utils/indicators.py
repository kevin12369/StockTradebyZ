"""
技术指标计算模块

从现有 Selector.py 复用的技术指标计算函数
"""

from scipy.signal import find_peaks
import numpy as np
import pandas as pd


def compute_kdj(df: pd.DataFrame, n: int = 9) -> pd.DataFrame:
    """计算KDJ指标

    Args:
        df: 包含 open, high, low, close 的 DataFrame
        n: KDJ 参数，默认 9

    Returns:
        添加了 K, D, J 列的 DataFrame
    """
    if df.empty:
        return df.assign(K=np.nan, D=np.nan, J=np.nan)

    low_n = df["low"].rolling(window=n, min_periods=1).min()
    high_n = df["high"].rolling(window=n, min_periods=1).max()
    rsv = (df["close"] - low_n) / (high_n - low_n + 1e-9) * 100

    K = np.zeros_like(rsv, dtype=float)
    D = np.zeros_like(rsv, dtype=float)
    for i in range(len(df)):
        if i == 0:
            K[i] = D[i] = 50.0
        else:
            K[i] = 2 / 3 * K[i - 1] + 1 / 3 * rsv.iloc[i]
            D[i] = 2 / 3 * D[i - 1] + 1 / 3 * K[i]
    J = 3 * K - 2 * D
    return df.assign(K=K, D=D, J=J)


def compute_bbi(df: pd.DataFrame) -> pd.Series:
    """计算BBI指标（多空指标）

    Args:
        df: 包含 close 的 DataFrame

    Returns:
        BBI 值序列
    """
    ma3 = df["close"].rolling(3).mean()
    ma6 = df["close"].rolling(6).mean()
    ma12 = df["close"].rolling(12).mean()
    ma24 = df["close"].rolling(24).mean()
    return (ma3 + ma6 + ma12 + ma24) / 4


def compute_rsv(df: pd.DataFrame, n: int) -> pd.Series:
    """计算RSV指标

    Args:
        df: 包含 close, low, high 的 DataFrame
        n: 窗口大小

    Returns:
        RSV 值序列
    """
    low_n = df["low"].rolling(window=n, min_periods=1).min()
    high_close_n = df["close"].rolling(window=n, min_periods=1).max()
    rsv = (df["close"] - low_n) / (high_close_n - low_n + 1e-9) * 100.0
    return rsv


def compute_dif(df: pd.DataFrame, fast: int = 12, slow: int = 26) -> pd.Series:
    """计算MACD指标中的DIF

    Args:
        df: 包含 close 的 DataFrame
        fast: 快线周期
        slow: 慢线周期

    Returns:
        DIF 值序列
    """
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    return ema_fast - ema_slow


def compute_ma(df: pd.DataFrame, n: int) -> pd.Series:
    """计算移动平均线

    Args:
        df: 包含 close 的 DataFrame
        n: 周期

    Returns:
        MA 值序列
    """
    return df["close"].rolling(window=n, min_periods=1).mean()
