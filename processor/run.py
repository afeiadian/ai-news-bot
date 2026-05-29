import sys
import time
from fetch import fetch_unread_entries, get_feeds, normalize_entry, mark_as_read, mark_old_as_read
from fetch_twitter import fetch_twitter_entries
from fetch_content import fetch_article_content
from process import analyze_article
from hotness import calc_hotness
from storage import init_db, article_exists, save_article, prune_old_articles
from run_log import RunLog, STEP_BACKEND, STEP_FETCH

# 经 Miniflux 抓取的 RSS 来源类别（用于日志里完整列出，即便当天 0 条）
RSS_CATEGORIES = ['arXiv', 'AI Lab', 'AI Chip', 'AI Tools', 'Newsletter', 'Hacker News']


def main():
    log = RunLog()
    try:
        _run(log)
    except Exception as e:
        log.fatal = f'{type(e).__name__}: {e}'
        raise
    finally:
        payload = log.save()
        print(f'\n📋 运行日志已记录（{payload["run_at_bj"]}，耗时 {payload["duration_sec"]}s）')


def _run(log):
    init_db()
    prune_old_articles(days=30)     # 删除30天前的旧文章

    processed, saved, skipped = 0, 0, 0

    # ===== RSS（经 Miniflux / RSSHub）=====
    try:
        mark_old_as_read(days_back=2)   # 清理2天前的积压
    except Exception as e:
        print(f'⚠️  清理积压失败：{e}')

    feeds = get_feeds()
    miniflux_ok = bool(feeds)
    log.backend('Miniflux (RSS)', miniflux_ok,
                '' if miniflux_ok else 'feeds 接口无响应，后端可能下线')

    entries = []
    if miniflux_ok:
        for cat in RSS_CATEGORIES:
            log.src(cat)                # 预登记，保证每个来源都在日志里出现
        entries = fetch_unread_entries(limit=200, days_back=2)
    else:
        # 后端连不上：所有 RSS 来源标记为「卡在后端连接」
        for cat in RSS_CATEGORIES:
            log.fail_source(cat, STEP_BACKEND, 'Miniflux 不可用')
        print('没有新 RSS 文章（Miniflux 不可用）')

    if miniflux_ok and not entries:
        print('没有新 RSS 文章')

    # 先归一化并按类别统计原始抓取条数
    normalized = []
    for entry in entries:
        article = normalize_entry(entry, feeds)
        normalized.append(article)
        log.src(article['category']).fetched += 1

    read_ids = []
    for article in normalized:
        stat = log.src(article['category'])
        url = article['url']

        if article_exists(url):
            read_ids.append(int(article['source_id']))
            stat.dup += 1
            skipped += 1
            continue

        print(f'[{processed+1}/{len(normalized)}] {article["title"][:60]}')

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
            stat.proc_fail += 1
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
        stat.new += 1
        processed += 1
        if result['relevant']:
            stat.kept += 1
            saved += 1

        time.sleep(0.5)

    try:
        mark_as_read(read_ids)
    except Exception as e:
        print(f'⚠️  标记已读失败：{e}')

    # ===== X 推文（直连 x.com，独立于 Miniflux）=====
    print('\n--- 抓取 X 推文 ---')
    xstat = log.src('X')
    try:
        twitter_entries = fetch_twitter_entries(days_back=2)
        log.backend('X / Twitter', True, f'{len(twitter_entries)} 条')
    except Exception as e:
        twitter_entries = []
        log.backend('X / Twitter', False, f'{type(e).__name__}: {e}')
        log.fail_source('X', STEP_FETCH, str(e)[:80])
        print(f'⚠️  X 抓取失败：{e}')

    print(f'获取到 {len(twitter_entries)} 条推文')
    for article in twitter_entries:
        xstat.fetched += 1
        url = article['url']
        if article_exists(url):
            xstat.dup += 1
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
            xstat.proc_fail += 1
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
        xstat.new += 1
        processed += 1
        if result['relevant']:
            xstat.kept += 1
            saved += 1
        time.sleep(0.5)

    print(f'\n完成：处理 {processed} 篇，收录 {saved} 篇，跳过已存在 {skipped} 篇')


if __name__ == '__main__':
    sys.path.insert(0, '.')
    main()
