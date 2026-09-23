import random
import time
from datetime import datetime


def get_time_scale_str(scale: str = "minute") -> str:
    """根据指定的时间刻度，生成对应的数字字符串。

    参数:
        scale (str): 刻度类型，支持 'day' (天), 'hour' (小时), 'minute' (分)

    返回:
        str: 纯数字时间字符串
    """
    now = datetime.now()

    if scale == "day":
        return now.strftime("%Y%m%d")  # 8位，如: 20260923
    elif scale == "hour":
        return now.strftime("%Y%m%d%H")  # 10位，如: 2026092311
    elif scale == "minute":
        return now.strftime("%Y%m%d%H%M")  # 12位，如: 202609231110
    else:
        raise ValueError(
            f"Unsupported scale: '{scale}'. Choose from 'day', 'hour', or 'minute'."
        )
