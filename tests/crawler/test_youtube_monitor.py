from crawler.schedule.youtube_monitor import YouTubeMonitor
from crawler.schedule.youtube_config import (
    load_api_key,
    load_standalone_channels,
)


def main() -> None:
    """
    独立测试 YouTube Monitor。
    """

    print("=" * 60)
    print("YouTube Monitor")
    print("=" * 60)

    api_key = load_api_key()

    if not api_key:
        print("❌ 没有读取到 youtube_api_key")

        print("请检查 .env：")

        print("youtube_api_key=你的API_KEY")

        return

    monitor = YouTubeMonitor(
        api_key=api_key,
        proxy="http://127.0.0.1:7890",
    )

    print("✅ API Key 已读取")

    print(f"代理: {monitor.proxy}")

    channels = load_standalone_channels()

    print(f"监控频道: {len(channels)}")

    # --------------------------------------------------------
    # API 测试
    # --------------------------------------------------------

    if not monitor.test_api():

        print()

        print("❌ API 测试失败，停止")

        return

    # --------------------------------------------------------
    # 获取监控频道
    # --------------------------------------------------------

    print()

    print("=" * 60)
    print("获取监控频道")
    print("=" * 60)

    videos = monitor.fetch_videos(
        channels,
        max_results=5,
    )

    print()

    print(f"获取完成: {len(videos)} 个视频")


if __name__ == "__main__":
    main()
