import sys
import time
from fetch import fetch_unread_entries, get_feeds, normalize_entry, mark_as_read, mark_old_as_read
from fetch_twitter import fetch_twitter_entries
from fetch_content import fetch_article_content
from process import analyze_article
from hotness import calc_hotness
from storage import init_db, article_exists, save_article, prune_old_articles

def main():
    init_db()
    prune_old_articles(days=30)     # 删除30天前的旧文章
    mark_old_as_read(days_back=2)   # 清理2天前的积压
    feeds = get_feeds()
    entries = fetch_unread_entries(limit=200, days_back=2)

    if not entries:
        print('没有新 RSS 文章')

    processed, saved, skipped = 0, 0, 0
    read_ids = []

    for entry in entries:
        article = normalize_entry(entry, feeds)
        url = article['url']

        if article_exists(url):
            read_ids.append(int(article['source_id']))
            skipped += 1
            continue

        print(f'[{processed+1}/{len(entries)}] {article["title"][:60]}')

        # HN 或内容过短时，用 Jina Reader 抓取原文
        if article['category'] == 'Hacker News' or len(article.get('content', '')) < 200:
            fetched = fetch_article_content(article['url'])
            if fetched:
                article['content'] = fetched
                print(f'  原文抓取成功（{len(fetched)} 字符）')

        try:
            result = analyze_article(
                title=article['title'],
                content=article['content'],
                source=article['source_name'],
            )
        except Exception as e:
            print(f'  ⚠️  AI 处理失败: {e}')
            continue

        print(f'  评分: {result["score"]} | {"✅ 收录" if result["relevant"] else "❌ 过滤"}')

        article['summary'] = result['summary']
        article['title_zh'] = result['title_zh']
        article['topic'] = result['topic']
        article['score'] = result['score']
        article['hotness'] = calc_hotness(article['category'], article['url'], article['title'])
        article['content'] = (article.get('content') or '')[:2000]

        save_article(article)
        read_ids.append(int(article['source_id']))
        processed += 1
        if result['relevant']:
            saved += 1

        time.sleep(0.5)

    mark_as_read(read_ids)

    print('\n--- 抓取 X 推文 ---')
    twitter_entries = fetch_twitter_entries(days_back=2)
    print(f'获取到 {len(twitter_entries)} 条推文')
    for article in twitter_entries:
        url = article['url']
        if article_exists(url):
            skipped += 1
            continue
        print(f'  {article["source_name"]}: {article["title"][:60]}')
        try:
            result = analyze_article(
                title=article['title'],
                content=article['content'],
                source=article['source_name'],
            )
        except Exception as e:
            print(f'  ⚠️  AI 处理失败: {e}')
            continue
        article['summary'] = result['summary']
        article['title_zh'] = result['title_zh']
        article['topic'] = result['topic']
        article['score'] = result['score']
        article['hotness'] = calc_hotness(
            article['category'], article['url'], article['title'],
            twitter_likes=article.get('twitter_likes', 0),
            twitter_retweets=article.get('twitter_retweets', 0),
        )
        article['content'] = (article.get('content') or '')[:2000]
        save_article(article)
        processed += 1
        if result['relevant']:
            saved += 1
        time.sleep(0.5)

    print(f'\n完成：处理 {processed} 篇，收录 {saved} 篇，跳过已存在 {skipped} 篇')


if __name__ == '__main__':
    sys.path.insert(0, '.')
    main()
