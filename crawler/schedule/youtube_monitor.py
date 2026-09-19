from __future__ import annotations

import json
import os
from pathlib import Path
import time
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv


# ============================================================
# YouTube Monitor
# ============================================================


class YouTubeMonitor:
    """
    YouTube 视频监控器。

    主要职责：

    1. 调用 YouTube Data API
    2. 获取频道信息
    3. 获取频道最新视频
    4. 检查多个监控频道
    5. 将 YouTube 数据转换成统一的视频结构

    注意：

    本类不负责：

    - JSON 缓存
    - 视频去重
    - FastAPI
    - AI 分析
    - 前端
    - Service 业务逻辑

    推荐数据流：

        YouTubeService
            ↓
        YouTubeMonitor
            ↓
        YouTube Data API
            ↓
        list[dict]
            ↓
        YouTubeService.add_videos()
    """

    # ========================================================
    # 默认配置
    # ========================================================

    DEFAULT_BASE_URL = "https://www.googleapis.com/youtube/v3"

    DEFAULT_PROXY = "http://127.0.0.1:7890"

    DEFAULT_TIMEOUT = 15

    DEFAULT_MAX_RESULTS = 10

    # ========================================================
    # 初始化
    # ========================================================

    def __init__(
        self,
        api_key: str | None = None,
        proxy: str | None = DEFAULT_PROXY,
        timeout: int = DEFAULT_TIMEOUT,
        base_url: str = DEFAULT_BASE_URL,
    ):
        """
        初始化 YouTube Monitor。

        参数：

            api_key:
                YouTube Data API Key。

            proxy:
                HTTP / HTTPS 代理。
                传 None 表示不使用代理。

            timeout:
                HTTP 请求超时时间。

            base_url:
                YouTube Data API 地址。
        """

        self.api_key = api_key.strip() if api_key else None

        self.proxy = proxy

        self.timeout = timeout

        self.base_url = base_url.rstrip("/")

        self.proxies = None

        if self.proxy:

            self.proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }

    # ========================================================
    # API Key
    # ========================================================

    def set_api_key(
        self,
        api_key: str | None,
    ) -> None:
        """
        更新 API Key。
        """

        self.api_key = api_key.strip() if api_key else None

    def has_api_key(self) -> bool:
        """
        判断 API Key 是否存在。
        """

        return bool(self.api_key)

    # ========================================================
    # HTTP 请求
    # ========================================================

    def request(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict | None:
        """
        请求 YouTube Data API。

        不负责业务逻辑，只负责 HTTP 请求。
        """

        if not self.api_key:

            print("❌ YouTube API Key 未配置")

            return None

        url = f"{self.base_url}/" f"{endpoint.lstrip('/')}"

        request_params = dict(params)

        request_params["key"] = self.api_key

        try:

            response = requests.get(
                url,
                params=request_params,
                proxies=self.proxies,
                timeout=self.timeout,
            )

            if response.status_code != 200:

                print(
                    "❌ YouTube API 请求失败 "
                    f"[{response.status_code}]"
                )

                print(response.text[:1000])

                return None

            return response.json()

        except requests.exceptions.ProxyError as exc:

            print(f"❌ 代理连接失败: {exc}")

        except requests.exceptions.Timeout:

            print("❌ YouTube API 请求超时")

        except requests.exceptions.RequestException as exc:

            print(f"❌ YouTube API 请求异常: {exc}")

        except ValueError as exc:

            print(
                f"❌ YouTube API 返回数据格式错误: {exc}"
            )

        return None

    # ========================================================
    # 获取频道信息
    # ========================================================

    def get_channel(
        self,
        channel_id: str,
    ) -> dict | None:
        """
        获取频道基本信息。
        """

        channel_id = channel_id.strip()

        if not channel_id:

            return None

        data = self.request(
            "channels",
            {
                "part": "snippet",
                "id": channel_id,
            },
        )

        if not data:

            return None

        items = data.get(
            "items",
            [],
        )

        if not items:

            return None

        snippet = items[0].get(
            "snippet",
            {},
        )

        return {
            "channel_id": channel_id,
            "name": snippet.get(
                "title",
                "",
            ),
            "description": snippet.get(
                "description",
                "",
            ),
            "published_at": snippet.get(
                "publishedAt",
            ),
        }

    # ========================================================
    # 获取最新视频
    # ========================================================

    def get_latest_video(
        self,
        channel_id: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        upload_only: bool = True,
        save_description: bool = True,
    ) -> dict | None:
        """
        获取频道最新视频。

        返回统一的视频结构：

            {
                "video_id": "...",
                "channel_id": "...",
                "title": "...",
                "description": "...",
                "published_at": "...",
                "url": "...",
                "thumbnail": "..."
            }
        """

        channel_id = channel_id.strip()

        if not channel_id:

            return None

        data = self.request(
            "activities",
            {
                "part": ("snippet," "contentDetails"),
                "channelId": channel_id,
                "maxResults": max_results,
            },
        )

        if not data:

            return None

        for item in data.get(
            "items",
            [],
        ):

            snippet = item.get(
                "snippet",
                {},
            )

            # ------------------------------------------------
            # 只处理上传视频
            # ------------------------------------------------

            if upload_only:

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

            # ------------------------------------------------
            # 获取视频封面
            # ------------------------------------------------

            thumbnails = snippet.get(
                "thumbnails",
                {},
            )

            thumbnail = (
                thumbnails.get(
                    "maxres",
                    {},
                ).get("url")
                or thumbnails.get(
                    "standard",
                    {},
                ).get("url")
                or thumbnails.get(
                    "high",
                    {},
                ).get("url")
                or thumbnails.get(
                    "medium",
                    {},
                ).get("url")
                or thumbnails.get(
                    "default",
                    {},
                ).get("url")
                or ""
            )

            video = {
                "video_id": str(video_id).strip(),
                "channel_id": channel_id,
                "title": snippet.get(
                    "title",
                    "",
                ),
                "published_at": snippet.get(
                    "publishedAt",
                    "",
                ),
                "url": self.get_video_url(video_id),
                "thumbnail": thumbnail,
            }

            if save_description:

                video["description"] = snippet.get(
                    "description",
                    "",
                )

            return video

        return None

    # ========================================================
    # 视频链接
    # ========================================================

    @staticmethod
    def get_video_url(
        video_id: str,
    ) -> str:
        """
        获取 YouTube 视频链接。
        """

        return (
            "https://www.youtube.com/watch?v="
            f"{video_id}"
        )

    # ========================================================
    # 检查频道
    # ========================================================

    def check_channels(
        self,
        channels: list[dict],
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        upload_only: bool = True,
        save_description: bool = True,
    ) -> list[dict]:
        """
        检查多个频道。

        参数：

            channels:
                YouTubeService 提供的频道列表。

        返回：

            list[dict]

        注意：

            本方法只负责抓取，
            不负责缓存。
        """

        videos: list[dict] = []

        print()

        print(
            "["
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            "] 开始检查"
        )

        for channel in channels:

            if not isinstance(
                channel,
                dict,
            ):

                continue

            channel_name = str(
                channel.get(
                    "name",
                    "",
                )
            ).strip()

            channel_id = str(
                channel.get(
                    "channel_id",
                    "",
                )
            ).strip()

            category = str(
                channel.get(
                    "category",
                    "other",
                )
            ).strip()

            if not channel_id:

                print(
                    f"  ⚠️ {channel_name or '未知频道'}: "
                    "没有配置频道 ID"
                )

                continue

            # ------------------------------------------------
            # 跳过占位 ID
            # ------------------------------------------------

            if (
                channel_id.endswith("_CHANNEL_ID")
                or channel_id.endswith("_ID")
            ):

                print(
                    f"  ⚠️ {channel_name}: "
                    "还没有配置真实频道 ID"
                )

                continue

            print(
                f"  检查: {channel_name}"
            )

            video = self.get_latest_video(
                channel_id,
                max_results=max_results,
                upload_only=upload_only,
                save_description=save_description,
            )

            if not video:

                print(
                    "    ⚠️ 没有获取到视频"
                )

                continue

            # ------------------------------------------------
            # 补充 Service 所需要的频道信息
            # ------------------------------------------------

            video["channel_name"] = channel_name

            video["category"] = category or "other"

            videos.append(video)

            print(
                f"    ✓ {video['title']}"
            )

        print()

        print(
            f"检查完成，共获取 "
            f"{len(videos)} 个视频"
        )

        return videos

    # ========================================================
    # 对外统一入口
    # ========================================================

    def fetch_videos(
        self,
        channels: list[dict],
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        upload_only: bool = True,
        save_description: bool = True,
    ) -> list[dict]:
        """
        获取监控频道的视频。

        这是 YouTubeService
        调用 Monitor 的主要接口。
        """

        return self.check_channels(
            channels,
            max_results=max_results,
            upload_only=upload_only,
            save_description=save_description,
        )

    # ========================================================
    # API 测试
    # ========================================================

    def test_api(
        self,
        channel_id: str = (
            "UCK8sQmJBp8GCxrOtXWBpyEA"
        ),
    ) -> bool:
        """
        测试 YouTube Data API。
        """

        print()

        print("=" * 60)
        print("测试 YouTube API")
        print("=" * 60)

        if not self.has_api_key():

            print(
                "❌ 没有读取到 YouTube API Key"
            )

            return False

        print(
            "✅ API Key 已读取"
        )

        channel = self.get_channel(
            channel_id
        )

        if not channel:

            print(
                "❌ 获取频道失败"
            )

            return False

        print(
            f"✅ 频道: "
            f"{channel['name']}"
        )

        video = self.get_latest_video(
            channel_id
        )

        if not video:

            print(
                "❌ 获取最新视频失败"
            )

            return False

        print()

        print(
            "最新视频:"
        )

        print(
            f"标题: "
            f"{video['title']}"
        )

        print(
            f"时间: "
            f"{video['published_at']}"
        )

        print(
            f"链接: "
            f"{video['url']}"
        )

        print(
            f"封面: "
            f"{video['thumbnail']}"
        )

        print()

        print(
            "✅ YouTube API 测试成功"
        )

        return True


# ============================================================
# 独立运行
# ============================================================


def load_api_key() -> str | None:
    """
    独立运行时读取 YouTube API Key。

    Service 正常运行时不使用这里，
    而是由 YouTubeService 传入 API Key。
    """

    load_dotenv()

    key = os.getenv(
        "youtube_api_key"
    )

    if key:

        return key.strip()

    key = os.getenv(
        "YOUTUBE_API_KEY"
    )

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

    config_file = (
        project_root
        / "config"
        / "youtube_channel.json"
    )

    if not config_file.exists():

        print(
            "❌ YouTube 频道配置文件不存在: "
            f"{config_file}"
        )

        return []

    try:

        with config_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            config = json.load(file)

    except json.JSONDecodeError as exc:

        print(
            "❌ YouTube 频道配置文件格式错误: "
            f"{exc}"
        )

        return []

    except OSError as exc:

        print(
            "❌ 读取 YouTube 频道配置失败: "
            f"{exc}"
        )

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


def main() -> None:
    """
    独立测试 YouTube Monitor。
    """

    print("=" * 60)
    print("YouTube Monitor")
    print("=" * 60)

    api_key = load_api_key()

    if not api_key:

        print(
            "❌ 没有读取到 youtube_api_key"
        )

        print(
            "请检查 .env："
        )

        print(
            "youtube_api_key=你的API_KEY"
        )

        return

    monitor = YouTubeMonitor(
        api_key=api_key,
        proxy="http://127.0.0.1:7890",
    )

    print(
        "✅ API Key 已读取"
    )

    print(
        f"代理: {monitor.proxy}"
    )

    channels = load_standalone_channels()

    print(
        f"监控频道: {len(channels)}"
    )

    # --------------------------------------------------------
    # API 测试
    # --------------------------------------------------------

    if not monitor.test_api():

        print()

        print(
            "❌ API 测试失败，停止"
        )

        return

    # --------------------------------------------------------
    # 获取一次视频
    # --------------------------------------------------------

    print()

    print("=" * 60)
    print("获取监控频道")
    print("=" * 60)

    videos = monitor.fetch_videos(
        channels
    )

    print()

    print(
        f"获取完成: {len(videos)} 个视频"
    )


if __name__ == "__main__":
    main()