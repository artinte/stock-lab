from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class YouTubeService:
    """
    YouTube 信息流服务。

    主要职责：

    1. 管理监控频道
    2. 管理 YouTube 运行配置
    3. 管理视频 JSON 缓存
    4. 管理 AI 分析结果
    5. 提供 API 层所需要的数据
    6. 为后续 YouTube Crawler 提供统一入口

    注意：

    本 Service 不直接负责 HTTP。
    本 Service 也不负责前端页面。

    推荐数据流：

        FastAPI
            ↓
        YouTubeService
            ↓
        Crawler / JSON / AI
    """

    # ========================================================
    # 默认路径
    # ========================================================

    DEFAULT_DATA_DIR = Path("data") / "youtube"

    CHANNELS_FILE = "channels.json"
    CONFIG_FILE = "config.json"
    VIDEOS_FILE = "videos.json"
    AI_TOP_FILE = "ai_top.json"

    # ========================================================
    # 默认配置
    # ========================================================

    DEFAULT_CONFIG = {
        "enabled": True,
        "interval": 300,
        "max_results": 10,
        "upload_only": True,
        "save_description": True,
        "notification_enabled": True,
    }

    # ========================================================
    # 初始化
    # ========================================================

    def __init__(
        self,
        data_dir: str | Path | None = None,
    ):

        self.data_dir = (
            Path(data_dir) if data_dir is not None else self.DEFAULT_DATA_DIR
        )

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.channels_file = self.data_dir / self.CHANNELS_FILE

        self.config_file = self.data_dir / self.CONFIG_FILE

        self.videos_file = self.data_dir / self.VIDEOS_FILE

        self.ai_top_file = self.data_dir / self.AI_TOP_FILE

        # ----------------------------------------------------
        # 初始化 JSON 文件
        # ----------------------------------------------------

        self._ensure_files()

    # ========================================================
    # 生命周期
    # ========================================================

    def stop(self) -> None:
        """
        停止 YouTube 服务。

        当前 JSON 缓存不需要额外关闭操作。

        后续如果增加：

        - 后台监控线程
        - asyncio task
        - crawler session
        - scheduler

        可以在这里统一释放。
        """

    # ========================================================
    # JSON 基础操作
    # ========================================================

    def _ensure_files(self) -> None:
        """
        创建必要的 JSON 文件。
        """

        if not self.channels_file.exists():

            self._write_json(
                self.channels_file,
                {"channels": []},
            )

        if not self.config_file.exists():

            self._write_json(
                self.config_file,
                self.DEFAULT_CONFIG.copy(),
            )

        if not self.videos_file.exists():

            self._write_json(
                self.videos_file,
                {"videos": []},
            )

        if not self.ai_top_file.exists():

            self._write_json(
                self.ai_top_file,
                {"videos": []},
            )

    def _read_json(
        self,
        path: Path,
        default: Any,
    ) -> Any:
        """
        读取 JSON 文件。

        如果文件不存在、为空或 JSON 损坏，
        返回 default。
        """

        if not path.exists():

            return default

        try:

            with path.open(
                "r",
                encoding="utf-8",
            ) as file:

                return json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:

            print(f"⚠️ JSON 缓存读取失败：" f"{path} -> {exc}")

            return default

    def _write_json(
        self,
        path: Path,
        data: Any,
    ) -> None:
        """
        安全写入 JSON。

        先写临时文件，
        成功后再替换原文件。
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = path.with_suffix(path.suffix + ".tmp")

        try:

            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )

                file.write("\n")

            temp_path.replace(path)

        except Exception:

            if temp_path.exists():

                try:
                    temp_path.unlink()
                except OSError:
                    pass

            raise

    # ========================================================
    # API Key
    # ========================================================

    def get_api_key(self) -> str | None:
        """
        获取 YouTube API Key。

        优先读取环境变量：

            YOUTUBE_API_KEY

        同时兼容：

            youtube_api_key

        注意：

        不应该把 API Key 返回给前端。
        """

        key = os.getenv("YOUTUBE_API_KEY")

        if key:
            return key.strip()

        key = os.getenv("youtube_api_key")

        if key:
            return key.strip()

        # ----------------------------------------------------
        # 如果项目没有 python-dotenv，
        # FastAPI 启动时不会自动读取 .env。
        #
        # 这里提供一个轻量级 .env 读取方式，
        # 不增加额外依赖。
        # ----------------------------------------------------

        env_file = Path(".env")

        if not env_file.exists():
            return None

        try:

            with env_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                for line in file:

                    line = line.strip()

                    if not line:
                        continue

                    if line.startswith("#"):
                        continue

                    if "=" not in line:
                        continue

                    name, value = line.split(
                        "=",
                        1,
                    )

                    name = name.strip()
                    value = value.strip()

                    if name in {
                        "YOUTUBE_API_KEY",
                        "youtube_api_key",
                    }:

                        if value.startswith('"') and value.endswith('"'):

                            value = value[1:-1]

                        if value.startswith("'") and value.endswith("'"):

                            value = value[1:-1]

                        return value.strip()

        except OSError as exc:

            print(f"⚠️ 读取 .env 失败：{exc}")

        return None

    def has_api_key(self) -> bool:
        """
        判断 YouTube API Key 是否配置。
        """

        key = self.get_api_key()

        return bool(key)

    # ========================================================
    # API 状态
    # ========================================================

    def get_api_status(self) -> dict:
        """
        获取 YouTube Data API 状态。

        永远不返回真实 API Key。
        """

        configured = self.has_api_key()

        return {
            "configured": configured,
            "status": ("ready" if configured else "not_configured"),
            "message": (
                "YouTube API Key 已配置"
                if configured
                else (
                    "YouTube API Key 未配置。"
                    "请在项目 .env 文件中设置 "
                    "YOUTUBE_API_KEY=你的_API_KEY"
                )
            ),
        }

    # ========================================================
    # 配置
    # ========================================================

    def get_config(self) -> dict:
        """
        获取 YouTube 运行配置。

        注意：

        API Key 不属于 config.json，
        也不会出现在返回结果中。
        """

        config = self._read_json(
            self.config_file,
            self.DEFAULT_CONFIG.copy(),
        )

        if not isinstance(
            config,
            dict,
        ):

            config = self.DEFAULT_CONFIG.copy()

        result = self.DEFAULT_CONFIG.copy()

        result.update(config)

        return result

    def update_config(
        self,
        *,
        enabled: bool | None = None,
        interval: int | None = None,
        max_results: int | None = None,
        upload_only: bool | None = None,
        save_description: bool | None = None,
        notification_enabled: bool | None = None,
    ) -> dict:
        """
        更新 YouTube 运行配置。
        """

        config = self.get_config()

        if enabled is not None:

            config["enabled"] = enabled

        if interval is not None:

            if interval < 10:

                raise ValueError("检查间隔不能小于 10 秒")

            config["interval"] = interval

        if max_results is not None:

            if not 1 <= max_results <= 50:

                raise ValueError("max_results 必须在 1 到 50 之间")

            config["max_results"] = max_results

        if upload_only is not None:

            config["upload_only"] = upload_only

        if save_description is not None:

            config["save_description"] = save_description

        if notification_enabled is not None:

            config["notification_enabled"] = notification_enabled

        self._write_json(
            self.config_file,
            config,
        )

        return config

    # ========================================================
    # 频道
    # ========================================================

    def _read_channels(self) -> list[dict]:
        """
        读取频道缓存。
        """

        data = self._read_json(
            self.channels_file,
            {"channels": []},
        )

        if isinstance(
            data,
            dict,
        ):

            channels = data.get(
                "channels",
                [],
            )

        elif isinstance(
            data,
            list,
        ):

            channels = data

        else:

            channels = []

        if not isinstance(
            channels,
            list,
        ):

            return []

        return channels

    def _write_channels(
        self,
        channels: list[dict],
    ) -> None:
        """
        保存频道缓存。
        """

        self._write_json(
            self.channels_file,
            {"channels": channels},
        )

    def get_channels(
        self,
        category: str | None = None,
        keyword: str | None = None,
    ) -> list[dict]:
        """
        获取监控频道。

        支持分类和关键字过滤。
        """

        channels = self._read_channels()

        category_value = category.strip().lower() if category else None

        keyword_value = keyword.strip().lower() if keyword else None

        result = []

        for channel in channels:

            if not isinstance(
                channel,
                dict,
            ):

                continue

            if category_value:

                channel_category = str(
                    channel.get(
                        "category",
                        "other",
                    )
                ).lower()

                if channel_category != category_value:

                    continue

            if keyword_value:

                name = str(
                    channel.get(
                        "name",
                        "",
                    )
                ).lower()

                channel_id = str(
                    channel.get(
                        "channel_id",
                        "",
                    )
                ).lower()

                if keyword_value not in name and keyword_value not in channel_id:

                    continue

            result.append(channel)

        return result

    def add_channel(
        self,
        *,
        name: str,
        channel_id: str,
        category: str = "other",
        enabled: bool = True,
    ) -> dict:
        """
        添加监控频道。
        """

        name = name.strip()
        channel_id = channel_id.strip()
        category = category.strip().lower()

        if not name:

            raise ValueError("频道名称不能为空")

        if not channel_id:

            raise ValueError("Channel ID 不能为空")

        channels = self._read_channels()

        for channel in channels:

            if channel.get("channel_id") == channel_id:

                raise ValueError("该频道已经存在")

        channel = {
            "name": name,
            "channel_id": channel_id,
            "category": category or "other",
            "enabled": enabled,
        }

        channels.append(channel)

        self._write_channels(channels)

        return channel

    def update_channel(
        self,
        *,
        channel_id: str,
        name: str | None = None,
        category: str | None = None,
        enabled: bool | None = None,
    ) -> dict:
        """
        修改监控频道。
        """

        channel_id = channel_id.strip()

        channels = self._read_channels()

        for channel in channels:

            if channel.get("channel_id") != channel_id:
                continue

            if name is not None:

                name = name.strip()

                if not name:

                    raise ValueError("频道名称不能为空")

                channel["name"] = name

            if category is not None:

                category = category.strip()

                channel["category"] = category or "other"

            if enabled is not None:

                channel["enabled"] = enabled

            self._write_channels(channels)

            return channel

        raise ValueError("未找到指定频道")

    def remove_channel(
        self,
        channel_id: str,
    ) -> None:
        """
        删除监控频道。
        """

        channel_id = channel_id.strip()

        channels = self._read_channels()

        new_channels = [
            channel for channel in channels if channel.get("channel_id") != channel_id
        ]

        if len(new_channels) == len(channels):

            raise ValueError("未找到指定频道")

        self._write_channels(new_channels)

    # ========================================================
    # 视频
    # ========================================================

    def _read_videos(self) -> list[dict]:
        """
        读取视频缓存。
        """

        data = self._read_json(
            self.videos_file,
            {"videos": []},
        )

        if isinstance(
            data,
            dict,
        ):

            videos = data.get(
                "videos",
                [],
            )

        elif isinstance(
            data,
            list,
        ):

            videos = data

        else:

            videos = []

        if not isinstance(
            videos,
            list,
        ):

            return []

        return videos

    def _write_videos(
        self,
        videos: list[dict],
    ) -> None:
        """
        保存视频缓存。
        """

        # ----------------------------------------------------
        # 只保留最近 5000 条。
        # ----------------------------------------------------

        videos = videos[:5000]

        self._write_json(
            self.videos_file,
            {"videos": videos},
        )

    def add_videos(
        self,
        videos: list[dict],
    ) -> dict:
        """
        添加视频到缓存。

        通过 video_id 去重。

        这个方法就是未来 Crawler
        和 Service 之间最重要的接口之一。
        """

        if not videos:

            return {
                "added": 0,
                "updated": 0,
                "total": len(self._read_videos()),
            }

        current = self._read_videos()

        index = {}

        for item in current:

            video_id = item.get("video_id")

            if video_id:

                index[video_id] = item

        added = 0
        updated = 0

        for video in videos:

            if not isinstance(
                video,
                dict,
            ):

                continue

            video_id = video.get("video_id")

            if not video_id:

                continue

            video_id = str(video_id).strip()

            if not video_id:

                continue

            video["video_id"] = video_id

            if video_id in index:

                index[video_id].update(video)

                updated += 1

            else:

                index[video_id] = video

                added += 1

        # ----------------------------------------------------
        # 最新视频放在最前面
        # ----------------------------------------------------

        result = list(index.values())

        result.sort(
            key=lambda item: str(
                item.get(
                    "published_at",
                    "",
                )
            ),
            reverse=True,
        )

        self._write_videos(result)

        return {
            "added": added,
            "updated": updated,
            "total": len(result),
        }

    def get_videos(
        self,
        *,
        category: str | None = None,
        channel_id: str | None = None,
        keyword: str | None = None,
        today: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        """
        获取视频。

        支持：

        - 分类
        - 频道
        - 关键字
        - 今日视频
        - 数量限制
        """

        videos = self._read_videos()

        category_value = category.strip().lower() if category else None

        channel_value = channel_id.strip() if channel_id else None

        keyword_value = keyword.strip().lower() if keyword else None

        result = []

        for video in videos:

            if not isinstance(
                video,
                dict,
            ):

                continue

            # ------------------------------------------------
            # 分类
            # ------------------------------------------------

            if category_value:

                video_category = str(
                    video.get(
                        "category",
                        "other",
                    )
                ).lower()

                if video_category != category_value:

                    continue

            # ------------------------------------------------
            # 频道
            # ------------------------------------------------

            if channel_value:

                if (
                    str(
                        video.get(
                            "channel_id",
                            "",
                        )
                    )
                    != channel_value
                ):

                    continue

            # ------------------------------------------------
            # 关键字
            # ------------------------------------------------

            if keyword_value:

                title = str(
                    video.get(
                        "title",
                        "",
                    )
                ).lower()

                description = str(
                    video.get(
                        "description",
                        "",
                    )
                ).lower()

                channel_name = str(
                    video.get(
                        "channel_name",
                        "",
                    )
                ).lower()

                if (
                    keyword_value not in title
                    and keyword_value not in description
                    and keyword_value not in channel_name
                ):

                    continue

            # ------------------------------------------------
            # 今日
            # ------------------------------------------------

            if today:

                if not self._is_today(video.get("published_at")):

                    continue

            result.append(video)

            if len(result) >= limit:

                break

        return result

    # ========================================================
    # 今日视频数量
    # ========================================================

    def get_today_video_count(self) -> int:
        """
        获取今日视频数量。

        数量来自 videos.json，
        因此随着 Crawler 写入新视频会变化。
        """

        return len(
            self.get_videos(
                today=True,
                limit=5000,
            )
        )

    # ========================================================
    # AI TOP
    # ========================================================

    def _read_ai_top(self) -> list[dict]:
        """
        读取 AI 分析结果。
        """

        data = self._read_json(
            self.ai_top_file,
            {"videos": []},
        )

        if isinstance(
            data,
            dict,
        ):

            videos = data.get(
                "videos",
                [],
            )

        elif isinstance(
            data,
            list,
        ):

            videos = data

        else:

            videos = []

        if not isinstance(
            videos,
            list,
        ):

            return []

        return videos

    def update_ai_top(
        self,
        videos: list[dict],
    ) -> None:
        """
        更新 AI TOP 数据。

        未来 AI Analyzer 完成分析后，
        可以直接调用这个方法。
        """

        result = []

        for video in videos:

            if not isinstance(
                video,
                dict,
            ):

                continue

            result.append(video)

        result.sort(
            key=lambda item: float(
                item.get(
                    "ai_score",
                    0,
                )
                or 0
            ),
            reverse=True,
        )

        self._write_json(
            self.ai_top_file,
            {"videos": result[:100]},
        )

    def get_ai_top(
        self,
        limit: int = 10,
    ) -> list[dict]:
        """
        获取 AI TOP 视频。

        优先读取 ai_top.json。

        如果 AI TOP 缓存为空，
        则从 videos.json 中读取已有 ai_score
        进行排序。

        这样前端在 AI Analyzer 尚未完全接入时，
        也不会直接报错。
        """

        videos = self._read_ai_top()

        if not videos:

            videos = self._read_videos()

            videos = [video for video in videos if video.get("ai_score") is not None]

        videos.sort(
            key=lambda item: float(
                item.get(
                    "ai_score",
                    0,
                )
                or 0
            ),
            reverse=True,
        )

        return videos[:limit]

    # ========================================================
    # 整体状态
    # ========================================================

    def get_status(self) -> dict:
        """
        获取 YouTube 信息流整体状态。
        """

        config = self.get_config()

        channels = self._read_channels()

        enabled_channels = [
            channel
            for channel in channels
            if channel.get(
                "enabled",
                True,
            )
        ]

        videos = self._read_videos()

        return {
            "enabled": bool(
                config.get(
                    "enabled",
                    True,
                )
            ),
            "channelCount": len(enabled_channels),
            "totalChannelCount": len(channels),
            "todayVideoCount": (self.get_today_video_count()),
            "totalVideoCount": len(videos),
            "interval": config.get(
                "interval",
                300,
            ),
            "maxResults": config.get(
                "max_results",
                10,
            ),
            "apiConfigured": (self.has_api_key()),
        }

    # ========================================================
    # 立即检查
    # ========================================================

    def check_now(self) -> dict:
        """
        立即检查监控频道。

        当前版本先提供统一入口。

        后续接入真正的 YouTubeCrawler：

            crawler = YouTubeCrawler(...)

            videos = crawler.fetch(...)

            result = self.add_videos(videos)

        API 层完全不需要修改。
        """

        config = self.get_config()

        if not config.get(
            "enabled",
            True,
        ):

            return {
                "status": "disabled",
                "message": "YouTube 监控已关闭",
                "added": 0,
                "updated": 0,
            }

        if not self.has_api_key():

            return {
                "status": "not_configured",
                "message": (
                    "YouTube API Key 未配置。"
                    "请在 .env 文件中设置 "
                    "YOUTUBE_API_KEY=你的_API_KEY"
                ),
                "added": 0,
                "updated": 0,
            }

        channels = self.get_channels()

        enabled_channels = [
            channel
            for channel in channels
            if channel.get(
                "enabled",
                True,
            )
        ]

        if not enabled_channels:

            return {
                "status": "no_channels",
                "message": "没有启用的监控频道",
                "added": 0,
                "updated": 0,
            }

        # ----------------------------------------------------
        # TODO:
        #
        # 这里以后接入真正的 YouTubeCrawler。
        #
        # 当前不直接调用 YouTube API，
        # 防止 Service 和具体抓取实现耦合。
        # ----------------------------------------------------

        return {
            "status": "ready",
            "message": ("YouTube 服务已准备好，" "等待 Crawler 接入"),
            "channelCount": len(enabled_channels),
            "added": 0,
            "updated": 0,
        }

    # ========================================================
    # 日期
    # ========================================================

    @staticmethod
    def _is_today(
        value: Any,
    ) -> bool:
        """
        判断时间是否属于今天。

        支持 ISO 8601 字符串。
        """

        if not value:

            return False

        if isinstance(
            value,
            datetime,
        ):

            return value.date() == datetime.now().date()

        if not isinstance(
            value,
            str,
        ):

            return False

        try:

            normalized = value.strip()

            if normalized.endswith("Z"):

                normalized = normalized[:-1] + "+00:00"

            dt = datetime.fromisoformat(normalized)

            # ------------------------------------------------
            # 如果带时区：
            # 转换到本地时间后再比较。
            # ------------------------------------------------

            if dt.tzinfo is not None:

                dt = dt.astimezone()

            return dt.date() == datetime.now().date()

        except ValueError:

            return False
