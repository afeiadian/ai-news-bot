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
            url         TEXT NOT NULL UNIQUE,
            source_name TEXT,
            category    TEXT,
            published_at TEXT,
            summary     TEXT,
            score       INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_published ON articles(published_at DESC);
        CREATE INDEX IF NOT EXISTS idx_score ON articles(score DESC);
    ''')
    conn.commit()
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
                (source_id, title, url, source_name, category, published_at, summary, score)
            VALUES
                (:source_id, :title, :url, :source_name, :category, :published_at, :summary, :score)
        ''', data)
        conn.commit()
    finally:
        conn.close()


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
