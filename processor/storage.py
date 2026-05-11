import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'news.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id   TEXT NOT NULL,
            title       TEXT NOT NULL,
            title_zh    TEXT,
            url         TEXT NOT NULL UNIQUE,
            source_name TEXT,
            category    TEXT,
            topic       TEXT,
            published_at TEXT,
            summary     TEXT,
            score       INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_published ON articles(published_at DESC);
        CREATE INDEX IF NOT EXISTS idx_score ON articles(score DESC);
    ''')
    # 兼容旧数据库：按需添加新列
    for col, typedef in [('title_zh', 'TEXT'), ('topic', 'TEXT'), ('hotness', 'INTEGER DEFAULT 0'), ('content', 'TEXT')]:
        try:
            conn.execute(f'ALTER TABLE articles ADD COLUMN {col} {typedef}')
            conn.commit()
        except Exception:
            pass
    conn.close()


def article_exists(url):
    conn = get_conn()
    row = conn.execute('SELECT 1 FROM articles WHERE url=?', (url,)).fetchone()
    conn.close()
    return row is not None


def save_article(data: dict):
    conn = get_conn()
    try:
        conn.execute('''
            INSERT OR IGNORE INTO articles
                (source_id, title, title_zh, url, source_name, category, topic, published_at, summary, score, hotness, content)
            VALUES
                (:source_id, :title, :title_zh, :url, :source_name, :category, :topic, :published_at, :summary, :score, :hotness, :content)
        ''', {**data, 'content': data.get('content', '')})
        conn.commit()
    finally:
        conn.close()


def get_articles_without_hotness(limit=500):
    conn = get_conn()
    rows = conn.execute(
        'SELECT url, title, title_zh, summary, source_name, category FROM articles WHERE hotness=0 OR hotness IS NULL LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_hotness(url: str, hotness: int):
    conn = get_conn()
    try:
        conn.execute('UPDATE articles SET hotness=? WHERE url=?', (hotness, url))
        conn.commit()
    finally:
        conn.close()


def get_articles_without_topic(limit=500):
    conn = get_conn()
    rows = conn.execute(
        'SELECT url, title, title_zh, summary FROM articles WHERE topic IS NULL OR topic="" LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_topic(url: str, topic: str):
    conn = get_conn()
    try:
        conn.execute('UPDATE articles SET topic=? WHERE url=?', (topic, url))
        conn.commit()
    finally:
        conn.close()


def update_title_zh(url: str, title_zh: str):
    conn = get_conn()
    try:
        conn.execute('UPDATE articles SET title_zh=? WHERE url=?', (title_zh, url))
        conn.commit()
    finally:
        conn.close()


def get_articles_without_title_zh(limit=200):
    conn = get_conn()
    rows = conn.execute(
        'SELECT url, title FROM articles WHERE title_zh IS NULL OR title_zh="" LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_articles(limit=100, min_score=60):
    conn = get_conn()
    rows = conn.execute('''
        SELECT * FROM articles
        WHERE score >= ?
        ORDER BY published_at DESC
        LIMIT ?
    ''', (min_score, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
