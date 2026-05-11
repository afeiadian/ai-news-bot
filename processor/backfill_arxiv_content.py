"""为现有 arXiv 文章回填作者和摘要（从 arXiv API 获取）"""
import re
import sys
import time
import sqlite3
import os
import requests
import xml.etree.ElementTree as ET

sys.path.insert(0, '.')
from storage import get_conn

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'news.db')
ARXIV_API = 'https://export.arxiv.org/api/query'
NS = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}


def extract_arxiv_id(url):
    m = re.search(r'arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]+)', url)
    return m.group(1) if m else None


def fetch_arxiv_meta(paper_id):
    try:
        r = requests.get(ARXIV_API, params={'id_list': paper_id}, timeout=10)
        root = ET.fromstring(r.text)
        entry = root.find('atom:entry', NS)
        if entry is None:
            return None
        authors = [a.find('atom:name', NS).text for a in entry.findall('atom:author', NS)]
        abstract = (entry.findtext('atom:summary', '', NS) or '').strip().replace('\n', ' ')
        author_str = '；'.join(authors[:6])
        if len(authors) > 6:
            author_str += f' 等{len(authors)}人'
        content = f'作者：{author_str}\n\n{abstract[:1800]}'
        return content
    except Exception as e:
        return None


def main():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, url FROM articles WHERE category='arXiv' AND (content IS NULL OR content='') ORDER BY id"
    ).fetchall()
    conn.close()

    total = len(rows)
    print(f'待回填 arXiv 文章：{total} 篇')

    updated = failed = 0
    for i, row in enumerate(rows, 1):
        paper_id = extract_arxiv_id(row['url'])
        if not paper_id:
            failed += 1
            continue

        content = fetch_arxiv_meta(paper_id)
        if content:
            db = sqlite3.connect(DB_PATH)
            db.execute('UPDATE articles SET content=? WHERE id=?', (content, row['id']))
            db.commit()
            db.close()
            updated += 1
            if i % 20 == 0:
                print(f'  进度 {i}/{total}，已更新 {updated} 篇')
        else:
            failed += 1

        time.sleep(0.3)

    print(f'完成：更新 {updated} 篇，失败/跳过 {failed} 篇')


if __name__ == '__main__':
    main()
