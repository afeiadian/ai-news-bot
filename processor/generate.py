import os
import sys
from datetime import datetime, timezone
from storage import get_conn

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'web', 'output')
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'web', 'template.html')

ALL_CATS   = ['arXiv', 'AI Lab', 'AI Tools', 'AI Chip', 'Hacker News', 'Reddit', 'Newsletter']
ALL_TOPICS = ['基础大模型', '推理部署', '训练微调', '开发工具', 'AI芯片硬件', '学术论文', '行业资讯']


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
    if not iso_str:
        return ''
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    except Exception:
        return iso_str[:10]


def get_articles(limit=500, min_score=60):
    conn = get_conn()
    rows = conn.execute('''
        SELECT title, title_zh, url, source_name, category, topic, published_at, summary, score
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


def topic_color(topic):
    colors = {
        '基础大模型': '#1d4ed8',
        '推理部署':   '#0f766e',
        '训练微调':   '#7c3aed',
        '开发工具':   '#0369a1',
        'AI芯片硬件': '#b45309',
        '学术论文':   '#6d28d9',
        '行业资讯':   '#374151',
    }
    return colors.get(topic, '#9ca3af')


def build_html(articles):
    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        template = f.read()

    # 统计数量
    cat_counts   = {c: 0 for c in ALL_CATS}
    topic_counts = {t: 0 for t in ALL_TOPICS}
    for a in articles:
        if a['category'] in cat_counts:
            cat_counts[a['category']] += 1
        t = a.get('topic') or ''
        if t in topic_counts:
            topic_counts[t] += 1

    # 文章列表 HTML
    items_html = ''
    for i, a in enumerate(articles, 1):
        color    = category_color(a['category'])
        topic    = a.get('topic') or ''
        date_str = get_date(a['published_at'])

        title_zh_html = ''
        if a.get('title_zh') and a['title_zh'] != a['title']:
            title_zh_html = f'<div class="title-zh">{a["title_zh"]}</div>'

        topic_html = ''
        if topic:
            tc = topic_color(topic)
            topic_html = f'<span class="tag topic-tag" style="background:{tc}">{topic}</span>'

        summary_html = ''
        if a.get('summary'):
            summary_html = f'<p class="summary">{a["summary"]}</p>'

        items_html += f'''
        <tr class="item-row" data-category="{a["category"]}" data-topic="{topic}" data-date="{date_str}" data-score="{a["score"]}">
            <td class="rank">{i}</td>
            <td class="main">
                <div class="title-line">
                    <a class="title-link" href="{a["url"]}" target="_blank" rel="noopener">{a["title"]}</a>
                </div>
                {title_zh_html}
                {summary_html}
                <div class="meta">
                    <span class="tag" style="background:{color}">{a["category"]}</span>
                    {topic_html}
                    <span class="source">{a["source_name"]}</span>
                    <span class="dot">·</span>
                    <span class="time">{time_ago(a["published_at"])}</span>
                    <span class="dot">·</span>
                    <span class="score">相关度 {a["score"]}</span>
                </div>
            </td>
        </tr>
        <tr class="spacer" data-category="{a["category"]}" data-topic="{topic}" data-date="{date_str}" data-score="{a["score"]}"><td colspan="2"></td></tr>'''

    # 来源分类按钮（全显示）
    cat_buttons = ''
    for cat in ALL_CATS:
        count    = cat_counts.get(cat, 0)
        extra_cls = ' btn-empty' if count == 0 else ''
        cat_buttons += (
            f'<button class="filter-btn{extra_cls}" data-cat="{cat}" onclick="filterCat(this)">'
            f'{cat} <span class="btn-count">{count}</span></button>\n'
        )

    # 话题分类按钮（全显示）
    topic_buttons = ''
    for t in ALL_TOPICS:
        count     = topic_counts.get(t, 0)
        extra_cls = ' btn-empty' if count == 0 else ''
        tc        = topic_color(t)
        topic_buttons += (
            f'<button class="filter-btn{extra_cls}" data-topic="{t}" onclick="filterTopic(this)" '
            f'style="--topic-color:{tc}">'
            f'{t} <span class="btn-count">{count}</span></button>\n'
        )

    updated = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    html = template.replace('{{ITEMS}}', items_html)
    html = html.replace('{{COUNT}}', str(len(articles)))
    html = html.replace('{{UPDATED}}', updated)
    html = html.replace('{{CAT_BUTTONS}}', cat_buttons)
    html = html.replace('{{TOPIC_BUTTONS}}', topic_buttons)
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
