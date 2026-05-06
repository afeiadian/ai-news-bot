"""给数据库中已有文章补填热度评分"""
import sys, time, os
sys.path.insert(0, '.')

from storage import init_db, get_articles_without_hotness, update_hotness
from hotness import calc_hotness


def main():
    init_db()
    articles = get_articles_without_hotness(limit=500)
    print(f'待评分：{len(articles)} 篇')

    for i, a in enumerate(articles, 1):
        print(f'[{i}/{len(articles)}] [{a["category"]}] {(a.get("title_zh") or a["title"])[:45]}')
        try:
            h = calc_hotness(a['category'], a['url'], a['title'])
            update_hotness(a['url'], h)
            print(f'  → {"★" * h}{"☆" * (5-h)} ({h}星)')
        except Exception as e:
            print(f'  ⚠️  {e}')
        time.sleep(0.5)

    print('\n✅ 热度评分完成')


if __name__ == '__main__':
    main()
