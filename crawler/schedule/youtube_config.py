# ============================================================
# 独立运行
# ============================================================


import json
import os
from pathlib import Path


def load_api_key() -> str | None:
    """
    独立运行时读取 YouTube API Key。

    Service 正常运行时不使用这里，
    而是由 YouTubeService 传入 API Key。
    """

    key = os.getenv("youtube_api_key")

    if key:
        return key.strip()

    key = os.getenv("YOUTUBE_API_KEY")

    if key:
        return key.strip()

    return None


def load_standalone_channels() -> list[dict]:
    """
    独立运行时从：

        config/youtube_channel.json

    读取监控频道。

    正常情况下：

        YouTubeService
            ↓
        YouTubeMonitor

    Service 会直接把 channels
    传给 Monitor。
    """

    project_root = Path(__file__).resolve().parents[2]

    config_file = project_root / "config" / "youtube_channel.json"

    if not config_file.exists():
        print("❌ YouTube 频道配置文件不存在: " f"{config_file}")

        return []

    try:
        with config_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            config = json.load(file)

    except json.JSONDecodeError as exc:
        print("❌ YouTube 频道配置文件格式错误: " f"{exc}")

        return []

    except OSError as exc:
        print("❌ 读取 YouTube 频道配置失败: " f"{exc}")

        return []

    channels_config = config.get(
        "monitor_channels",
        {},
    )

    if not isinstance(
        channels_config,
        dict,
    ):
        return []

    channels: list[dict] = []

    for category, category_channels in channels_config.items():

        if not isinstance(
            category_channels,
            dict,
        ):
            continue

        for name, channel_id in category_channels.items():

            if not isinstance(
                channel_id,
                str,
            ):
                continue

            channels.append(
                {
                    "name": name,
                    "channel_id": channel_id,
                    "category": category,
                    "enabled": True,
                }
            )

    return channels
