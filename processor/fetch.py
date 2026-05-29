import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MINIFLUX_URL = os.getenv('MINIFLUX_URL')
HEADERS = {'X-Auth-Token': os.getenv('MINIFLUX_API_KEY')}

CATEGORY_MAP = {
    'lab': 'AI Lab',
    'tools': 'AI Tools',
    'chip': 'AI Chip',
    'newsletter': 'Newsletter',
    'arxiv': 'arXiv',
    'hackernews': 'Hacker News',
    'reddit': 'Reddit',
}

import re as _re

def clean_source_name(name: str) -> str:
    """将 RSS feed 标题转为简洁的网站名"""
    # Reddit: "newest submissions : MachineLearning" → "r/MachineLearning"
    m = _re.match(r'newest submissions\s*:\s*(.+)', name)
    if m:
        return f'r/{m.group(1).strip()}'
    # HN: "Top Links | Hacker News" → "Hacker News"
    if 'Hacker News' in name:
        return 'Hacker News'
    # arXiv: "cs.AI updates on arXiv.org" → "arXiv cs.AI"
    m = _re.match(r'(cs\.\w+)\s+updates on arXiv', name)
    if m:
        return f'arXiv {m.group(1)}'
    return name


def _miniflux_list(path):
    """GET 一个预期返回 list 的 Miniflux 端点。

    Miniflux/RSSHub 托管在 Railway，服务下线时会返回错误 dict
    (如 {"status":"error","code":404,"message":"Application not found"})，
    旧代码直接 {x['id'] for x in resp.json()} 会因为遍历 dict 得到字符串键
    而抛 TypeError，进而让整个 run.py 崩溃、连独立的 X 抓取都跑不到。
    这里统一兜底：拿不到 list 就打印原因并返回 None，由上层降级处理。
    """
    try:
        resp = requests.get(f'{MINIFLUX_URL}{path}', headers=HEADERS, timeout=30)
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f'⚠️  Miniflux {path} 请求失败：{e}')
        return None
    if not isinstance(data, list):
        print(f'⚠️  Miniflux {path} 异常响应：HTTP {resp.status_code} {str(data)[:120]}')
        return None
    return data


def get_feeds():
    data = _miniflux_list('/v1/feeds')
    return {f['id']: f for f in data} if data else {}


def _get_categories():
    """返回 {category_name: category_id}"""
    data = _miniflux_list('/v1/categories')
    return {c['title']: c['id'] for c in data} if data else {}


def fetch_unread_entries(limit=200, days_back=1):
    """
    按分类配额抓取最近 days_back 天的未读文章，避免 arXiv 把高价值来源挤出去。
    优先抓全部 lab/tools/chip/newsletter/hackernews，剩余配额给 arXiv。
    """
    from datetime import datetime, timezone, timedelta
    after_ts = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())

    cats = _get_categories()
    # 优先级：高价值来源全抓（数量很少），arXiv 用剩余配额
    priority_cats = ['lab', 'tools', 'chip', 'newsletter', 'hackernews']

    all_entries = []
    for cat_name in priority_cats:
        cat_id = cats.get(cat_name)
        if not cat_id:
            continue
        r = requests.get(
            f'{MINIFLUX_URL}/v1/entries',
            headers=HEADERS,
            params={
                'status': 'unread',
                'limit': 100,  # 高价值来源每分类上限 100，通常 <20
                'order': 'published_at',
                'direction': 'desc',
                'after': after_ts,
                'category_id': cat_id,
            }
        )
        ents = r.json().get('entries') or []
        all_entries.extend(ents)
        if ents:
            print(f'  {cat_name}: 抓取 {len(ents)} 条')

    # 剩余配额给 arXiv
    arxiv_quota = max(0, limit - len(all_entries))
    arxiv_id = cats.get('arxiv')
    if arxiv_id and arxiv_quota > 0:
        r = requests.get(
            f'{MINIFLUX_URL}/v1/entries',
            headers=HEADERS,
            params={
                'status': 'unread',
                'limit': arxiv_quota,
                'order': 'published_at',
                'direction': 'desc',
                'after': after_ts,
                'category_id': arxiv_id,
            }
        )
        ents = r.json().get('entries') or []
        all_entries.extend(ents)
        print(f'  arxiv: 抓取 {len(ents)} 条（剩余配额 {arxiv_quota}）')

    print(f'共获取 {len(all_entries)} 条未读文章（最近 {days_back} 天）')
    return all_entries


def mark_old_as_read(days_back=2):
    """将超过 days_back 天的未读文章批量标记为已读，避免积压"""
    from datetime import datetime, timezone, timedelta
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())
    total = 0
    while True:
        r = requests.get(f'{MINIFLUX_URL}/v1/entries', headers=HEADERS,
                         params={'status': 'unread', 'before': cutoff, 'limit': 500}).json()
        entries = r.get('entries') or []
        if not entries:
            break
        ids = [e['id'] for e in entries]
        requests.put(f'{MINIFLUX_URL}/v1/entries', headers=HEADERS,
                     json={'entry_ids': ids, 'status': 'read'})
        total += len(ids)
        if len(ids) < 500:
            break
    if total:
        print(f'清理积压：已标记 {total} 篇旧文章为已读')


def mark_as_read(entry_ids: list):
    if not entry_ids:
        return
    requests.put(
        f'{MINIFLUX_URL}/v1/entries',
        headers=HEADERS,
        json={'entry_ids': entry_ids, 'status': 'read'}
    )


def normalize_entry(entry: dict, feeds: dict) -> dict:
    feed = feeds.get(entry['feed_id'], {})
    cat = feed.get('category', {})
    cat_title = cat.get('title', 'other')

    return {
        'source_id': str(entry['id']),
        'title': entry.get('title', '').strip(),
        'url': entry.get('url', ''),
        'source_name': clean_source_name(feed.get('title', '')),
        'category': CATEGORY_MAP.get(cat_title, cat_title),
        'published_at': entry.get('published_at', ''),
        'content': (entry.get('content') or '')[:2000],
    }
