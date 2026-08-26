import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


# ==========================================
# ここに記録したいYouTube動画のURLを入れる
# ==========================================

VIDEOS = [
    # "https://www.youtube.com/watch?v=XXXXXXXXXXX",
    # "https://youtu.be/XXXXXXXXXXX",
]


DATA_FILE = Path("views.json")


def get_video_id(url):
    patterns = [
        r"[?&]v=([^&]+)",
        r"youtu\.be/([^?&]+)",
        r"youtube\.com/shorts/([^?&]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_video_info(url):
    video_id = get_video_id(url)

    if not video_id:
        print(f"動画IDを取得できませんでした: {url}")
        return None

    page_url = f"https://www.youtube.com/watch?v={video_id}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
    }

    response = requests.get(
        page_url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    html = response.text

    title_match = re.search(
        r'"title":"(.*?)"',
        html
    )

    views_match = re.search(
        r'"viewCount":"(\d+)"',
        html
    )

    if not views_match:
        print(f"再生数を取得できませんでした: {url}")
        return None

    title = (
        title_match.group(1)
        if title_match
        else video_id
    )

    views = int(views_match.group(1))

    return {
        "id": video_id,
        "url": page_url,
        "title": title,
        "views": views,
    }


def load_data():
    if not DATA_FILE.exists():
        return {}

    try:
        return json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}


def main():
    data = load_data()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    for url in VIDEOS:
        try:
            info = get_video_info(url)

            if not info:
                continue

            video_id = info["id"]

            if video_id not in data:
                data[video_id] = {
                    "id": video_id,
                    "url": info["url"],
                    "title": info["title"],
                    "history": []
                }

            data[video_id]["title"] = info["title"]
            data[video_id]["url"] = info["url"]

            data[video_id]["history"].append({
                "date": now,
                "views": info["views"]
            })

            # 履歴が増えすぎないように
            data[video_id]["history"] = \
                data[video_id]["history"][-1000:]

            print(
                f'{info["title"]}: '
                f'{info["views"]:,} views'
            )

        except Exception as e:
            print(f"エラー: {url}")
            print(e)

    DATA_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
