from __future__ import annotations

import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

# ============================================================
# 配置
# ============================================================

load_dotenv()

API_KEY = os.getenv("youtube_api_key")

# Clash / 代理端口
PROXY = "http://127.0.0.1:7890"

# 每 5 分钟检查一次
CHECK_INTERVAL = 300


# ============================================================
# 监控频道
# ============================================================

MONITOR_CHANNELS = {
    # =========================================================
    # 播客
    # =========================================================
    "All-In Podcast": "UCESLZhusAkFfsNsApnjF_Cg",
    "Bloomberg Originals": "UCUMZ7gohGI9HcU9VNsr2FJQ",
    "Lex Fridman": "UCSHZKyawb77ixDdsGog4iWA",
    "Silicon Valley Girl": "UCiq1FIgtEK7LRAOB1JXTPig",
    
    # =========================================================
    # AI / 大模型
    # =========================================================
    "Google": "UCK8sQmJBp8GCxrOtXWBpyEA",
    "NVIDIA": "UCHuiy8bXnmK5nisYHUd1J5g",
    "OpenAI": "UCXZCJLdBC09xxGZ6gcdrc6A",
    "Microsoft": "UCFtEEv80fQVKkD4h1PF-Xqw",
    "Amazon": "UCkLXELm63_pH7L-r-548kig",
    "Meta": "UC04FyDIvYXNecpbG8gyOw4A",
    "Anthropic": "UCrDwWp7EBBv4NwvScIpBDOA",
    "IBM Technology": "UCKWaEZ-_VweaEx1j62do_vQ",
    "Google DeepMind": "UCP7jMXSY2xbc3KCAE0MHQ-A",
    # =========================================================
    # 半导体 / 芯片
    # =========================================================
    "TSMC": "UC02yNxGj2MxhynehcWSxcLg",
    "Intel": "UCk7SjrXVXAj8m8BLgzh6dGA",
    "AMD": "UCHQDjDDW8w2RieO-IuqYlyg",
    "Qualcomm": "UCH6eZr6vbZ6Bx53TyuSzxrg",
    "Broadcom Inc.": "UCTr3zah69bISSVdBcHiKhpA",
    "Micron Technology": "UCBqcI352Dc2ExKq1uSdwZvg",
    "Texas Instruments": "UC-EXTfLnOmCKVRJrv8xoGrQ",
    "ASML": "UCIT9d3JjHEnsVi_w9guSXvA",
    "Applied Materials": "UCRtDxSpmTncPvzBvXLurThA",
    "Lam Research": "UCGBYhq34JyAzewhkas7r1OQ",
    "Arm®": "UCvcBJFXTzCfU_sILnYVd4gg",
    # =========================================================
    # 云计算 / 软件 / 企业服务
    # =========================================================
    "Amazon News": "UCzE5rz2KHTFYAkmMksUpPLA",
    "Google Cloud Tech": "UCJS9pqu9BzkAMNTmzNMNhvg",
    "Microsoft Azure": "UC0m-80FnNY2Qb7obvTL_2fA",
    "Oracle": "UCHCThmyZ-2yWkv0UVeBDdnQ",
    "Salesforce": "UCUpquzY878NEaZm5bc7m2sQ",
    "Cisco": "UCEWiIE6Htd8mvlOR6YQez1g",
    "Dell Technologies": "UCZHb3OEEJ0WkizEH9ErlgvA",
    # =========================================================
    # 消费电子 / 互联网
    # =========================================================
    "Apple": "UCE_M8A5yxnLfW0KghEeajjw",
    "Samsung": "UCWwgaK7x0_FR1goeSRazfsQ",
    "Xiaomi": "UCCspJ6mFfCwOV4qFjZWi2wg",
    "Huawei": "UCtjV1_XU6gvPYyreaFScxBQ",
    "Lenovo": "UCpvg0uZH-oxmCagOWJo9p9g",
    "Adobe": "UC5_SBQbLA9Kg7Jh5GpXoP3g",
    # =========================================================
    # 汽车 / 新能源 / 自动驾驶
    # =========================================================
    "Tesla": "UC5WjFrtBdufl6CZojX3D8dQ",
    "Volkswagen": "UC0US_GEXVmwMH04OMcNuhpQ",
    "Ford Motor Company": "UCKA96UxTdgFBwGZMGZ-135w",
    # =========================================================
    # 航天 / 商业航天
    # =========================================================
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "NASA": "UCLA_DiR1FfKNvjuUpBHmylQ",
    "Blue Origin": "UCVxTHEKKLxNjGcvVaZindlg",
    "Rocket Lab": "UCsWq7LZaizhIi-c-Yo_bcpw",
    "European Space Agency, ESA": "UCIBaDdAbGlFDeS33shmlD0A",
    # =========================================================
    # 金融 / 投资机构
    # =========================================================
    "Bank of America": "UCtHZ1qs5h4sx9TijVBQCMIA",
    # =========================================================
    # 财经媒体 / 宏观经济
    # =========================================================
    "财经风云": "UC-1F7DZmxTd1YZUJZUsA0nw",
    "CNBC Television": "UCrp_UI8XtuYfpiqluWLD7Lw",
    "Bloomberg Television": "UCIALMKvObZNtJ6AmdCLP7Lg",
    "Reuters": "UChqUTb7kYRX8-EiaN3XFrSQ",
    "Financial Times": "UCoUxsWakJucWg46KW5RsvPw",
    "The Wall Street Journal": "UCK7tptUDHh-RYDsdxO1-5QQ",
    "Yahoo Finance": "UCEAZeUIeJs0IjQiqTCdVSIg",
    "Forbes": "UCmh7afBz-uWwOSSNTqUBAhg",
    "The Economist": "UC0p5jTq6Xx_DosDFxVXnWaQ",    
}


# ============================================================
# 代理
# ============================================================

PROXIES = {
    "http": PROXY,
    "https": PROXY,
}


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
