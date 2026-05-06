import os
import sys
from datetime import datetime, timezone
from storage import get_conn

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'web', 'output')
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'web', 'template.html')


def time_ago(iso_str):
    if not iso_str:
        return ''
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = int((now - dt).total_seconds())
        if diff < 3600:
            return f'{diff // 60} 分钟前'
        if diff < 86400:
            return f'{diff // 3600} 小时前'
        return f'{diff // 86400} 天前'
    except Exception:
        return iso_str[:10]


def get_date(iso_str):
    """提取 YYYY-MM-DD 用于前端日期筛选"""
    if not iso_str:
        return ''
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    except Exception:
        return iso_str[:10]


def get_articles(limit=500, min_score=60):
    conn = get_conn()
    rows = conn.execute('''
        SELECT title, url, source_name, category, published_at, summary, score
        FROM articles
        WHERE score >= ?
        ORDER BY published_at DESC
        LIMIT ?
    ''', (min_score, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def category_color(category):
    colors = {
        'arXiv':       '#7c3aed',
        'AI Lab':      '#0369a1',
        'AI Tools':    '#0f766e',
        'AI Chip':     '#b45309',
        'Hacker News': '#ea580c',
        'Reddit':      '#dc2626',
        'Newsletter':  '#4f46e5',
    }
    return colors.get(category, '#6b7280')


def build_html(articles):
    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        template = f.read()

    # 统计各分类数量
    cat_counts = {}
    for a in articles:
        cat_counts[a['category']] = cat_counts.get(a['category'], 0) + 1

    # 生成文章列表 HTML
    items_html = ''
    for i, a in enumerate(articles, 1):
        color = category_color(a['category'])
        summary_html = ''
        if a.get('summary'):
            summary_html = f'<p class="summary">{a["summary"]}</p>'
        date_str = get_date(a['published_at'])

        items_html += f'''
        <tr class="item-row" data-category="{a["category"]}" data-date="{date_str}">
            <td class="rank">{i}</td>
            <td class="main">
                <div class="title-line">
                    <a class="title-link" href="{a["url"]}" target="_blank" rel="noopener">{a["title"]}</a>
                </div>
                {summary_html}
                <div class="meta">
                    <span class="tag" style="background:{color}">{a["category"]}</span>
                    <span class="source">{a["source_name"]}</span>
                    <span class="dot">·</span>
                    <span class="time">{time_ago(a["published_at"])}</span>
                    <span class="dot">·</span>
                    <span class="score">相关度 {a["score"]}</span>
                </div>
            </td>
        </tr>
        <tr class="spacer" data-category="{a["category"]}" data-date="{date_str}"><td colspan="2"></td></tr>'''

    # 生成分类按钮 HTML
    all_cats = ['arXiv', 'AI Lab', 'AI Tools', 'AI Chip', 'Hacker News', 'Reddit', 'Newsletter']
    cat_buttons = ''
    for cat in all_cats:
        count = cat_counts.get(cat, 0)
        if count == 0:
            continue
        cat_buttons += f'<button class="filter-btn" data-cat="{cat}" onclick="filterCat(this)">{cat} <span class="btn-count">{count}</span></button>\n'

    updated = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    html = template.replace('{{ITEMS}}', items_html)
    html = html.replace('{{COUNT}}', str(len(articles)))
    html = html.replace('{{UPDATED}}', updated)
    html = html.replace('{{CAT_BUTTONS}}', cat_buttons)
    return html


def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    articles = get_articles()
    html = build_html(articles)
    out_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ 生成 {len(articles)} 篇文章 → {out_path}')


if __name__ == '__main__':
    sys.path.insert(0, '.')
    generate()
