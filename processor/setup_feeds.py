import os
import yaml
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MINIFLUX_URL = os.getenv('MINIFLUX_URL')
API_KEY = os.getenv('MINIFLUX_API_KEY')
HEADERS = {'X-Auth-Token': API_KEY, 'Content-Type': 'application/json'}


def get_or_create_category(name):
    resp = requests.get(f'{MINIFLUX_URL}/v1/categories', headers=HEADERS)
    for cat in resp.json():
        if cat['title'] == name:
            return cat['id']
    resp = requests.post(f'{MINIFLUX_URL}/v1/categories', headers=HEADERS, json={'title': name})
    return resp.json()['id']


def add_feed(url, category_id, title=None):
    payload = {'feed_url': url, 'category_id': category_id}
    resp = requests.post(f'{MINIFLUX_URL}/v1/feeds', headers=HEADERS, json=payload)
    if resp.status_code == 201:
        feed_id = resp.json().get('feed_id')
        print(f'  ✅ 添加成功 (id={feed_id}): {url}')
    elif 'already_subscribed' in resp.text:
        print(f'  ⏭️  已存在: {url}')
    else:
        print(f'  ❌ 失败 {resp.status_code}: {url} -> {resp.text[:80]}')


def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.yaml')
    with open(config_path) as f:
        config = yaml.safe_load(f)

    print('\n=== 添加 RSS 订阅源 ===')
    cat_map = {}
    for source in config.get('rss_sources', []):
        cat_name = source['category']
        if cat_name not in cat_map:
            cat_map[cat_name] = get_or_create_category(cat_name)
        print(f"[{source['name']}]")
        add_feed(source['url'], cat_map[cat_name])

    print('\n=== 添加 arXiv 订阅源 ===')
    arxiv_cat_id = get_or_create_category('arxiv')
    for source in config.get('arxiv_sources', []):
        print(f"[{source['name']}]")
        add_feed(source['url'], arxiv_cat_id)

    print('\n=== 添加 Hacker News ===')
    hn_cat_id = get_or_create_category('hackernews')
    for source in config.get('hackernews_sources', []):
        print(f"[{source['name']}]")
        add_feed(source['url'], hn_cat_id)

    print('\n=== 添加 Reddit 订阅源 ===')
    reddit_cat_id = get_or_create_category('reddit')
    for source in config.get('reddit_sources', []):
        print(f"[{source['name']}]")
        add_feed(source['url'], reddit_cat_id)

    print('\n=== 完成，查看当前订阅数量 ===')
    resp = requests.get(f'{MINIFLUX_URL}/v1/feeds', headers=HEADERS)
    print(f'共 {len(resp.json())} 个订阅源')


if __name__ == '__main__':
    main()
