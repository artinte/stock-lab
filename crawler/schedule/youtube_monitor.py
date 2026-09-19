"""
YouTube Monitor
===============

YouTube Data API 数据采集模块。

主要职责：
    1. 调用 YouTube Data API
    2. 获取频道信息
    3. 获取频道上传视频
    4. 获取视频详细信息和统计数据
    5. 获取播放列表及其视频
    6. 搜索 YouTube 视频
    7. 获取直播相关信息
    8. 检查多个监控频道
    9. 将 YouTube 数据转换成统一的视频结构

推荐的数据流：

    YouTubeService
        ↓
    YouTubeMonitor
        ↓
    YouTube Data API
        ↓
    list[dict]
        ↓
    YouTubeService
        ↓
    缓存 / 去重 / 新闻信息流 / AI 分析

本模块不负责：

    - JSON 缓存
    - 视频去重
    - 数据库存储
    - FastAPI
    - AI 分析
    - 前端
    - Service 业务逻辑

频道视频监控推荐流程：

    channel_id
        ↓
    channels.list
        ↓
    uploads playlist_id
        ↓
    playlistItems.list
        ↓
    video_id
        ↓
    videos.list
        ↓
    统一的视频结构

说明：

    uploads playlist 适合频道视频监控。

    search.list 更适合关键词搜索和视频发现，
    不应该作为大量频道的高频监控入口。

独立运行：

    python youtube_monitor.py
"""

from __future__ import annotations


import json
import os
import requests

from datetime import datetime
from pathlib import Path
from typing import Any


class YouTubeMonitor:
    """YouTube Data API 数据采集器。"""

    # ========================================================
    # 默认配置
    # ========================================================

    DEFAULT_BASE_URL = "https://www.googleapis.com/youtube/v3"

    DEFAULT_PROXY = "http://127.0.0.1:7890"

    DEFAULT_TIMEOUT = 15

    DEFAULT_MAX_RESULTS = 10

    DEFAULT_SEARCH_MAX_RESULTS = 10

    # YouTube API 单次 list 请求通常最多返回 50 条。
    MAX_RESULTS_LIMIT = 50

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
    # 工具方法
    # ========================================================

    @staticmethod
    def _normalize_max_results(
        max_results: int,
        default: int = DEFAULT_MAX_RESULTS,
    ) -> int:
        """
        标准化 max_results。

        YouTube Data API 单次 list 请求最大支持 50 条。
        """

        if not isinstance(max_results, int):
            return default

        if max_results <= 0:
            return default

        return min(
            max_results,
            YouTubeMonitor.MAX_RESULTS_LIMIT,
        )

    @staticmethod
    def _normalize_ids(
        ids: list[str] | tuple[str, ...],
    ) -> list[str]:
        """
        清理 ID 列表并去重。
        """

        result: list[str] = []

        seen: set[str] = set()

        for item in ids:
            if not isinstance(item, str):
                continue

            item = item.strip()

            if not item:
                continue

            if item in seen:
                continue

            seen.add(item)

            result.append(item)

        return result

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
                print("❌ YouTube API 请求失败 " f"[{response.status_code}]")

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
            print("❌ YouTube API 返回数据格式错误: " f"{exc}")

        return None

    # ========================================================
    # Channel
    # ========================================================

    def get_channel(
        self,
        channel_id: str,
        *,
        include_statistics: bool = True,
    ) -> dict | None:
        """
        获取频道基本信息。

        返回：

            {
                "channel_id": "...",
                "name": "...",
                "description": "...",
                "published_at": "...",
                "thumbnail": "...",
                "custom_url": "...",
                "country": "...",
                "uploads_playlist_id": "...",
                "subscriber_count": 0,
                "view_count": 0,
                "video_count": 0,
            }
        """

        channel_id = channel_id.strip()

        if not channel_id:
            return None

        parts = [
            "snippet",
            "contentDetails",
        ]

        if include_statistics:
            parts.append("statistics")

        data = self.request(
            "channels",
            {
                "part": ",".join(parts),
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

        item = items[0]

        snippet = item.get(
            "snippet",
            {},
        )

        content_details = item.get(
            "contentDetails",
            {},
        )

        statistics = item.get(
            "statistics",
            {},
        )

        thumbnails = snippet.get(
            "thumbnails",
            {},
        )

        thumbnail = (
            thumbnails.get(
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

        related_playlists = content_details.get(
            "relatedPlaylists",
            {},
        )

        result = {
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
                "",
            ),
            "thumbnail": thumbnail,
            "custom_url": snippet.get(
                "customUrl",
                "",
            ),
            "country": snippet.get(
                "country",
                "",
            ),
            "uploads_playlist_id": (
                related_playlists.get(
                    "uploads",
                    "",
                )
            ),
        }

        if include_statistics:
            result.update(
                {
                    "subscriber_count": self._to_int(statistics.get("subscriberCount")),
                    "view_count": self._to_int(statistics.get("viewCount")),
                    "video_count": self._to_int(statistics.get("videoCount")),
                }
            )

        return result

    @staticmethod
    def _to_int(
        value: Any,
    ) -> int:
        """
        将 API 返回的数字字符串转换成 int。
        """

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0

    # ========================================================
    # Channel Uploads Playlist
    # ========================================================

    def get_uploads_playlist_id(
        self,
        channel_id: str,
    ) -> str | None:
        """
        获取频道的 uploads playlist ID。

        YouTube 会为频道维护一个上传视频播放列表，
        用于获取该频道发布的视频。
        """

        channel = self.get_channel(
            channel_id,
            include_statistics=False,
        )

        if not channel:
            return None

        playlist_id = channel.get(
            "uploads_playlist_id",
            "",
        )

        if not playlist_id:
            return None

        return str(playlist_id).strip() or None

    # ========================================================
    # Playlist Items
    # ========================================================

    def get_playlist_items(
        self,
        playlist_id: str,
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        page_token: str | None = None,
    ) -> list[dict]:
        """
        获取播放列表中的视频项目。

        返回原始 playlist item 数据。
        """

        playlist_id = playlist_id.strip()

        if not playlist_id:
            return []

        max_results = self._normalize_max_results(max_results)

        params: dict[str, Any] = {
            "part": ("snippet," "contentDetails"),
            "playlistId": playlist_id,
            "maxResults": max_results,
        }

        if page_token:
            params["pageToken"] = page_token

        data = self.request(
            "playlistItems",
            params,
        )

        if not data:
            return []

        return data.get(
            "items",
            [],
        )

    # ========================================================
    # Playlist Videos
    # ========================================================

    def get_playlist_videos(
        self,
        playlist_id: str,
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        include_details: bool = True,
        save_description: bool = True,
    ) -> list[dict]:
        """
        获取播放列表中的视频。

        参数：

            playlist_id:
                YouTube Playlist ID。

            max_results:
                获取的视频数量。

            include_details:
                是否进一步获取视频详细信息。

            save_description:
                是否保存视频描述。

        返回：

            list[dict]
        """

        playlist_id = playlist_id.strip()

        if not playlist_id:
            return []

        max_results = self._normalize_max_results(max_results)

        items = self.get_playlist_items(
            playlist_id,
            max_results=max_results,
        )

        videos: list[dict] = []

        video_ids: list[str] = []

        for item in items:

            snippet = item.get(
                "snippet",
                {},
            )

            content_details = item.get(
                "contentDetails",
                {},
            )

            resource_id = snippet.get(
                "resourceId",
                {},
            )

            video_id = resource_id.get("videoId") or content_details.get("videoId")

            if not video_id:
                continue

            video = {
                "video_id": str(video_id).strip(),
                "channel_id": snippet.get("videoOwnerChannelId")
                or snippet.get(
                    "channelId",
                    "",
                ),
                "channel_name": snippet.get("videoOwnerChannelTitle") or "",
                "title": snippet.get(
                    "title",
                    "",
                ),
                "description": (
                    snippet.get(
                        "description",
                        "",
                    )
                    if save_description
                    else ""
                ),
                "published_at": snippet.get(
                    "publishedAt",
                    "",
                ),
                "url": self.get_video_url(video_id),
                "thumbnail": self._get_thumbnail(
                    snippet.get(
                        "thumbnails",
                        {},
                    )
                ),
            }

            videos.append(video)

            video_ids.append(str(video_id).strip())

        if include_details and video_ids:
            detailed_videos = self.get_videos(
                video_ids,
                save_description=save_description,
            )

            detail_map = {
                video["video_id"]: video
                for video in detailed_videos
                if video.get("video_id")
            }

            merged_videos: list[dict] = []

            for video in videos:

                video_id = video.get("video_id")

                detail = detail_map.get(
                    video_id,
                    {},
                )

                merged = {
                    **video,
                    **detail,
                }

                merged_videos.append(merged)

            return merged_videos

        return videos

    # ========================================================
    # Latest Videos
    # ========================================================

    def get_latest_videos(
        self,
        channel_id: str,
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        save_description: bool = True,
        include_details: bool = True,
    ) -> list[dict]:
        """
        获取频道最近上传的视频。

        推荐的频道监控入口。

        工作流程：

            channel_id
                ↓
            uploads playlist
                ↓
            playlistItems
                ↓
            videos
        """

        channel_id = channel_id.strip()

        if not channel_id:
            return []

        playlist_id = self.get_uploads_playlist_id(channel_id)

        if not playlist_id:
            return []

        videos = self.get_playlist_videos(
            playlist_id,
            max_results=max_results,
            include_details=include_details,
            save_description=save_description,
        )

        # 某些 API 返回数据中频道 ID 可能为空，
        # 这里使用传入的 channel_id 进行补充。
        for video in videos:

            if not video.get("channel_id"):
                video["channel_id"] = channel_id

        return videos

    # ========================================================
    # Video
    # ========================================================

    def get_video(
        self,
        video_id: str,
        *,
        save_description: bool = True,
    ) -> dict | None:
        """
        获取单个视频详细信息。

        包含：

            - 基本信息
            - 发布时间
            - 封面
            - 视频时长
            - 播放量
            - 点赞数
            - 评论数
            - 标签
            - 视频链接
        """

        videos = self.get_videos(
            [video_id],
            save_description=save_description,
        )

        if not videos:
            return None

        return videos[0]

    def get_videos(
        self,
        video_ids: list[str] | tuple[str, ...],
        *,
        save_description: bool = True,
    ) -> list[dict]:
        """
        批量获取视频详细信息。

        YouTube API 支持通过逗号分隔的 video ID
        一次获取多个视频。

        返回：

            list[dict]
        """

        ids = self._normalize_ids(video_ids)

        if not ids:
            return []

        # API 单次最多处理一批 ID。
        # 为了保持方法稳定，这里按 50 个分组。
        videos: list[dict] = []

        for start in range(
            0,
            len(ids),
            50,
        ):
            batch = ids[start : start + 50]

            data = self.request(
                "videos",
                {
                    "part": ("snippet," "contentDetails," "statistics"),
                    "id": ",".join(batch),
                },
            )

            if not data:
                continue

            for item in data.get(
                "items",
                [],
            ):
                video = self._parse_video(
                    item,
                    save_description=(save_description),
                )

                if video:
                    videos.append(video)

        return videos

    def _parse_video(
        self,
        item: dict,
        *,
        save_description: bool = True,
    ) -> dict | None:
        """
        将 YouTube video resource
        转换成统一的视频结构。
        """

        if not isinstance(
            item,
            dict,
        ):
            return None

        video_id = str(item.get("id", "")).strip()

        if not video_id:
            return None

        snippet = item.get(
            "snippet",
            {},
        )

        content_details = item.get(
            "contentDetails",
            {},
        )

        statistics = item.get(
            "statistics",
            {},
        )

        thumbnails = snippet.get(
            "thumbnails",
            {},
        )

        video = {
            "video_id": video_id,
            "channel_id": snippet.get(
                "channelId",
                "",
            ),
            "channel_name": snippet.get(
                "channelTitle",
                "",
            ),
            "title": snippet.get(
                "title",
                "",
            ),
            "published_at": snippet.get(
                "publishedAt",
                "",
            ),
            "url": self.get_video_url(video_id),
            "thumbnail": self._get_thumbnail(thumbnails),
            "duration": content_details.get(
                "duration",
                "",
            ),
            "definition": content_details.get(
                "definition",
                "",
            ),
            "caption": content_details.get(
                "caption",
                "",
            ),
            "view_count": self._to_int(statistics.get("viewCount")),
            "like_count": self._to_int(statistics.get("likeCount")),
            "comment_count": self._to_int(statistics.get("commentCount")),
        }

        if save_description:
            video["description"] = snippet.get(
                "description",
                "",
            )

        tags = snippet.get(
            "tags",
            [],
        )

        if isinstance(
            tags,
            list,
        ):
            video["tags"] = tags
        else:
            video["tags"] = []

        video["category_id"] = snippet.get(
            "categoryId",
            "",
        )

        return video

    @staticmethod
    def _get_thumbnail(
        thumbnails: dict,
    ) -> str:
        """
        按优先级获取视频封面。
        """

        if not isinstance(
            thumbnails,
            dict,
        ):
            return ""

        return (
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

        return "https://www.youtube.com/watch?v=" f"{video_id}"

    # ========================================================
    # Search
    # ========================================================

    def search_videos(
        self,
        query: str,
        *,
        channel_id: str | None = None,
        max_results: int = DEFAULT_SEARCH_MAX_RESULTS,
        order: str = "relevance",
        published_after: str | None = None,
        published_before: str | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        """
        搜索 YouTube 视频。

        适合：

            - 关键词发现
            - 新闻发现
            - 公司搜索
            - 股票相关视频搜索
            - AI / 科技热点搜索
            - 直播发现

        注意：

            search.list 的 quota 成本较高，
            不建议用于高频频道监控。

        参数：

            query:
                搜索关键词。

            channel_id:
                限定某个频道。

            max_results:
                最大结果数量。

            order:
                relevance / date / rating / viewCount

            published_after:
                ISO 8601 时间。

            published_before:
                ISO 8601 时间。

            event_type:
                live / upcoming / completed
        """

        query = query.strip()

        if not query:
            return []

        max_results = self._normalize_max_results(
            max_results,
            default=self.DEFAULT_SEARCH_MAX_RESULTS,
        )

        params: dict[str, Any] = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": order,
        }

        if channel_id:
            params["channelId"] = channel_id.strip()

        if published_after:
            params["publishedAfter"] = published_after

        if published_before:
            params["publishedBefore"] = published_before

        if event_type:
            params["eventType"] = event_type

        data = self.request(
            "search",
            params,
        )

        if not data:
            return []

        results: list[dict] = []

        video_ids: list[str] = []

        for item in data.get(
            "items",
            [],
        ):
            id_data = item.get(
                "id",
                {},
            )

            video_id = id_data.get("videoId")

            if not video_id:
                continue

            snippet = item.get(
                "snippet",
                {},
            )

            results.append(
                {
                    "video_id": str(video_id).strip(),
                    "channel_id": snippet.get(
                        "channelId",
                        "",
                    ),
                    "channel_name": snippet.get(
                        "channelTitle",
                        "",
                    ),
                    "title": snippet.get(
                        "title",
                        "",
                    ),
                    "description": snippet.get(
                        "description",
                        "",
                    ),
                    "published_at": snippet.get(
                        "publishedAt",
                        "",
                    ),
                    "url": self.get_video_url(video_id),
                    "thumbnail": (
                        self._get_thumbnail(
                            snippet.get(
                                "thumbnails",
                                {},
                            )
                        )
                    ),
                }
            )

            video_ids.append(str(video_id).strip())

        # 搜索结果只包含基础 snippet。
        # 如果需要完整统计，则再调用 videos.list。
        if video_ids:
            details = self.get_videos(video_ids)

            detail_map = {
                video["video_id"]: video for video in details if video.get("video_id")
            }

            merged_results: list[dict] = []

            for result in results:

                detail = detail_map.get(
                    result.get("video_id"),
                    {},
                )

                merged_results.append(
                    {
                        **result,
                        **detail,
                    }
                )

            return merged_results

        return results

    # ========================================================
    # Live
    # ========================================================

    def get_live_videos(
        self,
        query: str,
        *,
        max_results: int = DEFAULT_SEARCH_MAX_RESULTS,
    ) -> list[dict]:
        """
        搜索正在直播的视频。

        这是 search.list 的一个便捷封装。
        """

        return self.search_videos(
            query,
            max_results=max_results,
            order="date",
            event_type="live",
        )

    def get_upcoming_live_videos(
        self,
        query: str,
        *,
        max_results: int = DEFAULT_SEARCH_MAX_RESULTS,
    ) -> list[dict]:
        """
        搜索即将开始的直播。
        """

        return self.search_videos(
            query,
            max_results=max_results,
            order="date",
            event_type="upcoming",
        )

    # ========================================================
    # Playlists
    # ========================================================

    def get_playlists(
        self,
        channel_id: str,
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> list[dict]:
        """
        获取频道的公开播放列表。
        """

        channel_id = channel_id.strip()

        if not channel_id:
            return []

        max_results = self._normalize_max_results(max_results)

        data = self.request(
            "playlists",
            {
                "part": "snippet,contentDetails",
                "channelId": channel_id,
                "maxResults": max_results,
            },
        )

        if not data:
            return []

        playlists: list[dict] = []

        for item in data.get(
            "items",
            [],
        ):
            snippet = item.get(
                "snippet",
                {},
            )

            content_details = item.get(
                "contentDetails",
                {},
            )

            playlists.append(
                {
                    "playlist_id": item.get(
                        "id",
                        "",
                    ),
                    "channel_id": snippet.get(
                        "channelId",
                        channel_id,
                    ),
                    "channel_name": snippet.get(
                        "channelTitle",
                        "",
                    ),
                    "title": snippet.get(
                        "title",
                        "",
                    ),
                    "description": snippet.get(
                        "description",
                        "",
                    ),
                    "published_at": snippet.get(
                        "publishedAt",
                        "",
                    ),
                    "item_count": self._to_int(content_details.get("itemCount")),
                    "thumbnail": (
                        self._get_thumbnail(
                            snippet.get(
                                "thumbnails",
                                {},
                            )
                        )
                    ),
                }
            )

        return playlists

    # ========================================================
    # 检查单个频道
    # ========================================================

    def check_channel(
        self,
        channel: dict,
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        save_description: bool = True,
        include_details: bool = True,
    ) -> list[dict]:
        """
        检查单个监控频道。

        参数：

            channel:
                YouTubeService 提供的频道配置。

        返回：

            list[dict]
        """

        if not isinstance(
            channel,
            dict,
        ):
            return []

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
            print(f"  ⚠️ {channel_name or '未知频道'}: " "没有配置频道 ID")

            return []

        # ------------------------------------------------
        # 跳过占位 ID
        # ------------------------------------------------

        if channel_id.endswith("_CHANNEL_ID") or channel_id.endswith("_ID"):
            print(f"  ⚠️ {channel_name}: " "还没有配置真实频道 ID")

            return []

        videos = self.get_latest_videos(
            channel_id,
            max_results=max_results,
            save_description=save_description,
            include_details=include_details,
        )

        for video in videos:
            video["channel_name"] = video.get("channel_name") or channel_name

            video["category"] = category or "other"

        return videos

    # ========================================================
    # 检查多个频道
    # ========================================================

    def check_channels(
        self,
        channels: list[dict],
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        save_description: bool = True,
        include_details: bool = True,
    ) -> list[dict]:
        """
        检查多个频道。

        参数：

            channels:
                YouTubeService 提供的频道列表。

            max_results:
                每个频道获取的视频数量。

        返回：

            list[dict]

        注意：

            本方法只负责抓取，
            不负责缓存和去重。
        """

        videos: list[dict] = []

        print()

        print("[" f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" "] 开始检查")

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

            print(f"  检查: " f"{channel_name or '未知频道'}")

            channel_videos = self.check_channel(
                channel,
                max_results=max_results,
                save_description=save_description,
                include_details=include_details,
            )

            if not channel_videos:
                print("    ⚠️ 没有获取到视频")

                continue

            videos.extend(channel_videos)

            for video in channel_videos:
                print("    ✓ " f"{video.get('title', '')}")

        print()

        print(f"检查完成，共获取 " f"{len(videos)} 个视频")

        return videos

    # ========================================================
    # 对外统一入口
    # ========================================================

    def fetch_videos(
        self,
        channels: list[dict],
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        save_description: bool = True,
        include_details: bool = True,
    ) -> list[dict]:
        """
        获取监控频道的视频。

        这是 YouTubeService
        调用 Monitor 的主要接口。

        注意：

            max_results 表示每个频道
            获取多少条视频。

        本方法不负责：

            - 缓存
            - 去重
            - 数据库存储
        """

        return self.check_channels(
            channels,
            max_results=max_results,
            save_description=save_description,
            include_details=include_details,
        )

    # ========================================================
    # API 测试
    # ========================================================

    def test_api(
        self,
        channel_id: str = ("UCK8sQmJBp8GCxrOtXWBpyEA"),
    ) -> bool:
        """
        测试 YouTube Data API。

        测试：

            1. API Key
            2. 频道信息
            3. 最近视频
            4. 视频详细信息
        """

        print()

        print("=" * 60)
        print("测试 YouTube API")
        print("=" * 60)

        if not self.has_api_key():
            print("❌ 没有读取到 YouTube API Key")

            return False

        print("✅ API Key 已读取")

        # ------------------------------------------------
        # 频道测试
        # ------------------------------------------------

        channel = self.get_channel(channel_id)

        if not channel:
            print("❌ 获取频道失败")

            return False

        print(f"✅ 频道: " f"{channel['name']}")

        print(f"   uploads playlist: " f"{channel.get('uploads_playlist_id', '-')}")

        # ------------------------------------------------
        # 视频测试
        # ------------------------------------------------

        videos = self.get_latest_videos(
            channel_id,
            max_results=3,
            include_details=True,
        )

        if not videos:
            print("❌ 获取最新视频失败")

            return False

        print()

        print(f"最新视频: {len(videos)} 个")

        for index, video in enumerate(
            videos,
            start=1,
        ):
            print()

            print(f"[{index}] " f"{video.get('title', '')}")

            print(f"时间: " f"{video.get('published_at', '')}")

            print(f"链接: " f"{video.get('url', '')}")

            print(f"播放: " f"{video.get('view_count', 0)}")

        print()

        print("✅ YouTube API 测试成功")

        return True


