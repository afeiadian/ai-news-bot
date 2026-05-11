import re
import requests
from urllib.parse import quote

# 各来源基础权威分（1-3）
SOURCE_BASE = {
    'AI Lab':      3.0,
    'arXiv':       2.5,
    'Newsletter':  2.5,
    'AI Chip':     2.5,
    'X':           2.5,
    'AI Tools':    2.0,
    'Hacker News': 2.0,
    'Reddit':      1.5,
}

# 互动数 → 加分（0-2）
ENGAGEMENT_TIERS = [
    (500, 2.0),
    (200, 1.5),
    (100, 1.0),
    (30,  0.5),
    (0,   0.0),
]


def _engagement_bonus(count: int) -> float:
    for threshold, bonus in ENGAGEMENT_TIERS:
        if count >= threshold:
            return bonus
    return 0.0


def get_hn_engagement(title: str) -> tuple:
    """通过 HN Algolia API 搜索文章，返回 (points, comments)"""
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={quote(title[:80])}&tags=story&hitsPerPage=3"
        resp = requests.get(url, timeout=8, headers={'User-Agent': 'ai-news-bot/1.0'})
        hits = resp.json().get('hits', [])
        if hits:
            h = hits[0]
            return h.get('points', 0) or 0, h.get('num_comments', 0) or 0
    except Exception:
        pass
    return 0, 0


def get_reddit_engagement(url: str) -> tuple:
    """从 Reddit JSON API 获取帖子 score 和评论数"""
    try:
        m = re.search(r'/comments/([a-z0-9]+)/', url)
        r = re.search(r'/r/([^/]+)/', url)
        if not m or not r:
            return 0, 0
        post_id  = m.group(1)
        subreddit = r.group(1)
        api_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
        resp = requests.get(
            api_url, timeout=8,
            headers={'User-Agent': 'ai-news-bot/1.0'}
        )
        data = resp.json()
        post = data[0]['data']['children'][0]['data']
        return post.get('score', 0) or 0, post.get('num_comments', 0) or 0
    except Exception:
        pass
    return 0, 0


def calc_hotness(category: str, url: str, title: str) -> int:
    """
    计算热度星级 1-5。
    - 来源权威度作为基础分
    - HN / Reddit 真实互动数作为加分项
    """
    base  = SOURCE_BASE.get(category, 2.0)
    bonus = 0.0

    if category == 'Hacker News':
        points, comments = get_hn_engagement(title)
        bonus = _engagement_bonus(points)

    elif category == 'Reddit':
        score, comments = get_reddit_engagement(url)
        bonus = _engagement_bonus(score)

    result = round(base + bonus)
    return max(1, min(5, result))
