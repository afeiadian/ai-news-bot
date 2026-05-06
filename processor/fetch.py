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


def get_feeds():
    resp = requests.get(f'{MINIFLUX_URL}/v1/feeds', headers=HEADERS)
    return {f['id']: f for f in resp.json()}


def fetch_unread_entries(limit=200):
    resp = requests.get(
        f'{MINIFLUX_URL}/v1/entries',
        headers=HEADERS,
        params={'status': 'unread', 'limit': limit, 'order': 'published_at', 'direction': 'desc'}
    )
    data = resp.json()
    entries = data.get('entries') or []
    print(f'获取到 {len(entries)} 条未读文章')
    return entries


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
        'source_name': feed.get('title', ''),
        'category': CATEGORY_MAP.get(cat_title, cat_title),
        'published_at': entry.get('published_at', ''),
        'content': (entry.get('content') or '')[:2000],
    }
