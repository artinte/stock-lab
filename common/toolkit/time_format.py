from datetime import datetime


def get_time_scale_str(
    time: datetime,
    scale: str = "minute",
) -> str:
    """根据指定的时间和时间刻度，生成对应的数字字符串。

    参数:
        time (datetime): 时间。
        scale (str): 刻度类型，支持：
            - 'day'    : 天
            - 'hour'   : 小时
            - 'minute' : 分钟

    返回:
        str: 纯数字时间字符串。

    示例:
        time = datetime(2026, 9, 23, 11, 10)

        get_time_scale_str(time, "day")
        # "20260923"

        get_time_scale_str(time, "hour")
        # "2026092311"

        get_time_scale_str(time, "minute")
        # "202609231110"
    """
    if scale == "day":
        return time.strftime("%Y%m%d")
    elif scale == "hour":
        return time.strftime("%Y%m%d%H")
    elif scale == "minute":
        return time.strftime("%Y%m%d%H%M")
    else:
        raise ValueError(
            f"Unsupported scale: '{scale}'. " "Choose from 'day', 'hour', or 'minute'."
        )
