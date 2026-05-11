"""重新评分所有文章（使用最新 scoring.yaml 规则）"""
import sys
import time
import sqlite3
import os

sys.path.insert(0, '.')
from process import analyze_article
from storage import get_conn

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'news.db')


def get_all_articles():
    conn = get_conn()
    rows = conn.execute(
        'SELECT id, title, title_zh, url, source_name, category, summary FROM articles ORDER BY id'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_article(article_id, score, title_zh, topic, summary):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            'UPDATE articles SET score=?, title_zh=?, topic=?, summary=? WHERE id=?',
            (score, title_zh, topic, summary, article_id)
        )
        conn.commit()
    finally:
        conn.close()


def main():
    articles = get_all_articles()
    total = len(articles)
    print(f'共 {total} 篇文章，开始重新评分...\n')

    updated = skipped = errors = 0

    for i, a in enumerate(articles, 1):
        # 用 title + summary 作为内容输入（原始内容未存储）
        content = a.get('summary') or ''
        title = a.get('title') or ''

        print(f'[{i}/{total}] [{a["category"]}] {title[:55]}')

        try:
            result = analyze_article(
                title=title,
                content=content,
                source=a['source_name'],
            )
        except Exception as e:
            print(f'  ⚠️  API 失败: {e}')
            errors += 1
            time.sleep(1)
            continue

        old_score = 0  # 不单独查，直接覆盖
        new_score = result['score']
        print(f'  评分: {new_score} | 话题: {result["topic"] or "—"}')

        update_article(
            a['id'],
            score=new_score,
            title_zh=result['title_zh'] or a.get('title_zh') or '',
            topic=result['topic'],
            summary=result['summary'] or a.get('summary') or '',
        )
        updated += 1
        time.sleep(0.4)

    print(f'\n完成：更新 {updated} 篇，失败 {errors} 篇')


if __name__ == '__main__':
    main()
