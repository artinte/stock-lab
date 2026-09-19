from __future__ import annotations

import json
import os
from pathlib import Path
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

# ============================================================
# 配置
# ============================================================
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = PROJECT_ROOT / "config"

YOUTUBE_CHANNEL_CONFIG = CONFIG_DIR / "youtube_channel.json"

API_KEY = os.getenv("youtube_api_key")

# Clash / 代理端口
PROXY = "http://127.0.0.1:7890"

# 每 5 分钟检查一次
CHECK_INTERVAL = 300

# ============================================================
# 代理
# ============================================================

PROXIES = {
    "http": PROXY,
    "https": PROXY,
}


# ============================================================
# 加载 YouTube 配置
# ============================================================
def load_youtube_config() -> dict:
    """
    加载 youtube_channel.json。
    """

    if not YOUTUBE_CHANNEL_CONFIG.exists():

        print(f"❌ YouTube 频道配置文件不存在: " f"{YOUTUBE_CHANNEL_CONFIG}")

        return {}

    try:

        with YOUTUBE_CHANNEL_CONFIG.open(
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except json.JSONDecodeError as e:

        print(f"❌ YouTube 频道配置文件格式错误: {e}")

    except OSError as e:

        print(f"❌ 读取 YouTube 频道配置失败: {e}")

    return {}


# ============================================================
# 加载监控频道
# ============================================================


def load_monitor_channels(
    config: dict,
) -> dict[str, str]:
    """
    从 youtube_channel.json 的 monitor_channels
    中加载所有频道。

    配置：

        "monitor_channels": {
            "播客": {
                "All-In Podcast": "UC..."
            },
            "AI / 大模型": {
                "Google": "UC..."
            }
        }

    返回：

        {
            "All-In Podcast": "UC...",
            "Google": "UC..."
        }
    """

    channels_config = config.get(
        "monitor_channels",
        {},
    )

    if not isinstance(channels_config, dict):

        print("❌ monitor_channels 配置格式错误")

        return {}

    monitor_channels: dict[str, str] = {}

    for category, channels in channels_config.items():

        if not isinstance(channels, dict):

            print(f"⚠️ 跳过无效分类: {category}")

            continue

        for name, channel_id in channels.items():

            if not isinstance(channel_id, str):

                print(f"⚠️ 跳过无效频道: {name}")

                continue

            monitor_channels[name] = channel_id

    return monitor_channels


# ============================================================
# 加载配置
# ============================================================

YOUTUBE_CONFIG = load_youtube_config()

YOUTUBE_ENABLED = YOUTUBE_CONFIG.get(
    "enabled",
    True,
)

MONITOR_CHANNELS = load_monitor_channels(YOUTUBE_CONFIG)


# ============================================================
# YouTube API 请求
# ============================================================


def youtube_request(
    endpoint: str,
    params: dict,
) -> dict | None:

    url = f"https://www.googleapis.com/youtube/v3/{endpoint}"

    params["key"] = API_KEY

    try:
        response = requests.get(
            url,
            params=params,
            proxies=PROXIES,
            timeout=15,
        )

        if response.status_code != 200:

            print(f"❌ YouTube API 请求失败 " f"[{response.status_code}]")

            print(response.text[:1000])

            return None

        return response.json()

    except requests.exceptions.ProxyError as e:

        print(f"❌ 代理连接失败: {e}")

    except requests.exceptions.Timeout:

        print("❌ YouTube API 请求超时")

    except Exception as e:

        print(f"❌ 请求异常: {e}")

    return None


# ============================================================
# 获取频道信息
# ============================================================


def get_channel(
    channel_id: str,
) -> dict | None:

    data = youtube_request(
        "channels",
        {
            "part": "snippet",
            "id": channel_id,
        },
    )

    if not data:
        return None

    items = data.get("items", [])

    if not items:
        return None

    snippet = items[0].get("snippet", {})

    return {
        "id": channel_id,
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "published_at": snippet.get("publishedAt"),
    }


# ============================================================
# 获取频道最新视频
# ============================================================


def get_latest_video(
    channel_id: str,
) -> dict | None:

    data = youtube_request(
        "activities",
        {
            "part": "snippet,contentDetails",
            "channelId": channel_id,
            "maxResults": 10,
        },
    )

    if not data:
        return None

    for item in data.get("items", []):

        snippet = item.get("snippet", {})

        # 只处理上传视频
        if snippet.get("type") != "upload":
            continue

        content_details = item.get(
            "contentDetails",
            {},
        )

        upload = content_details.get(
            "upload",
            {},
        )

        video_id = upload.get("videoId")

        if not video_id:
            continue

        return {
            "id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get(
                "description",
                "",
            ),
            "published_at": snippet.get(
                "publishedAt",
            ),
            "channel_id": channel_id,
        }

    return None


# ============================================================
# 获取视频链接
# ============================================================


def get_video_url(video_id: str) -> str:

    return "https://www.youtube.com/watch?v=" f"{video_id}"


# ============================================================
# 保存新视频
# ============================================================


def save_video(
    channel_name: str,
    video: dict,
):
    """
    后面这里直接接你的 News 模型。

    目前先打印。
    """

    video_id = video["id"]

    print()
    print("🆕 发现新视频")

    print(f"来源: {channel_name}")
    print(f"标题: {video['title']}")
    print(f"时间: {video['published_at']}")

    print(f"链接: {get_video_url(video_id)}")

    print()


# ============================================================
# 检查频道
# ============================================================


def check_channels(
    last_videos: dict[str, str],
):
    """
    检查所有监控频道。
    """

    print()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] " "开始检查")

    for name, channel_id in MONITOR_CHANNELS.items():

        # 跳过还没有填写真实 ID 的频道
        if channel_id.endswith("_CHANNEL_ID"):
            print(f"  ⚠️ {name}: " "还没有配置频道 ID")
            continue

        if channel_id.endswith("_ID"):
            print(f"  ⚠️ {name}: " "还没有配置频道 ID")
            continue

        print(f"  检查: {name}")

        video = get_latest_video(channel_id)

        if not video:

            print("    ⚠️ 没有获取到视频")

            continue

        video_id = video["id"]

        # 第一次运行
        if channel_id not in last_videos:
            last_videos[channel_id] = video_id
            print("    📌 当前最新视频")
            print(f"    频道:   {name}")
            print(f"    频道ID: {channel_id}")
            print(f"    视频ID: {video_id}")
            print(f"    标题:   {video['title']}")
            print(f"    时间:   {video['published_at']}")
            print(f"    链接:   " f"https://www.youtube.com/watch?v={video_id}")
            # print(f"    描述: {video['description'] or '-'}")
            print()
            continue

        # 没有新视频
        if last_videos[channel_id] == video_id:
            print("    没有新视频")
            continue

        # 发现新视频
        save_video(
            name,
            video,
        )

        # 更新最新视频
        last_videos[channel_id] = video_id


# ============================================================
# 测试 API
# ============================================================


def test_api():

    print()
    print("=" * 60)
    print("测试 YouTube API")
    print("=" * 60)

    if not API_KEY:

        print("❌ 没有读取到 youtube_api_key")

        return False

    print("✅ API Key 已读取")

    # 使用已经验证成功的 Google
    channel_id = "UCK8sQmJBp8GCxrOtXWBpyEA"

    channel = get_channel(channel_id)

    if not channel:

        print("❌ 获取频道失败")

        return False

    print(f"✅ 频道: " f"{channel['title']}")

    video = get_latest_video(channel_id)

    if not video:

        print("❌ 获取最新视频失败")

        return False

    print()
    print("最新视频:")
    print(f"标题: {video['title']}")
    print(f"时间: {video['published_at']}")
    print(f"链接: " f"{get_video_url(video['id'])}")

    print()
    print("✅ YouTube API 测试成功")

    return True


# ============================================================
# 主程序
# ============================================================


def main():

    print("=" * 60)
    print("YouTube 股票信息流监控")
    print("=" * 60)

    if not API_KEY:

        print("❌ 没有读取到 youtube_api_key")

        print("请检查 .env：")

        print("youtube_api_key=你的API_KEY")

        return

    print("✅ API Key 已读取")
    print(f"代理: {PROXY}")
    print(f"监控频道: " f"{len(MONITOR_CHANNELS)}")
    print(f"检查间隔: " f"{CHECK_INTERVAL} 秒")

    # --------------------------------------------------------
    # 先测试 API
    # --------------------------------------------------------

    if not test_api():

        print()
        print("❌ API 测试失败，停止监控")

        return

    # --------------------------------------------------------
    # 保存每个频道目前最新的视频
    # --------------------------------------------------------

    last_videos: dict[str, str] = {}

    print()
    print("=" * 60)
    print("开始监控")
    print("=" * 60)

    # --------------------------------------------------------
    # 循环监控
    # --------------------------------------------------------

    while True:
        try:
            check_channels(last_videos)

        except KeyboardInterrupt:
            print()
            print("监控已停止")

            break

        except Exception as e:
            print(f"❌ 监控发生异常: {e}")

        print()
        print(f"等待 {CHECK_INTERVAL} 秒...")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
