import html as _html
import os
import sys
import yaml
from datetime import datetime, timezone
from storage import get_conn

SCORING_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'scoring.yaml')
SOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.yaml')

def load_min_score():
    with open(SCORING_PATH, encoding='utf-8') as f:
        return yaml.safe_load(f).get('min_score', 65)


def build_sources_modal():
    with open(SCORING_PATH, encoding='utf-8') as f:
        scoring = yaml.safe_load(f)
    with open(SOURCES_PATH, encoding='utf-8') as f:
        sources = yaml.safe_load(f)

    html = []

    # === RSS 数据源 ===
    html.append('<div class="modal-section">')
    html.append('<h3>RSS 数据源</h3>')
    html.append('<table class="modal-table"><tr><th>分类</th><th>来源名称</th><th>说明</th></tr>')

    cat_map = {'lab': 'AI Lab', 'chip': 'AI Chip', 'tools': 'AI Tools',
               'newsletter': 'Newsletter', 'arxiv': 'arXiv', 'hackernews': 'Hacker News'}
    cat_colors = {'AI Lab': '#0369a1', 'AI Chip': '#b45309', 'AI Tools': '#0f766e',
                  'Newsletter': '#4f46e5', 'arXiv': '#7c3aed', 'Hacker News': '#ea580c'}

    for src in sources.get('rss_sources', []):
        cat = cat_map.get(src.get('category', ''), src.get('category', ''))
        color = cat_colors.get(cat, '#6b7280')
        html.append(f'<tr><td><span class="modal-tag" style="background:{color}">{cat}</span></td>'
                    f'<td>{_html.escape(src["name"])}</td>'
                    f'<td style="color:#888;font-size:11px">{_html.escape(src["url"][:60])}</td></tr>')

    # arXiv
    for src in sources.get('arxiv_sources', []):
        html.append(f'<tr><td><span class="modal-tag" style="background:#7c3aed">arXiv</span></td>'
                    f'<td>arXiv {src["id"]}</td>'
                    f'<td style="color:#888;font-size:11px">{_html.escape(src["name"])}</td></tr>')

    # HN
    for src in sources.get('hackernews_sources', []):
        html.append(f'<tr><td><span class="modal-tag" style="background:#ea580c">Hacker News</span></td>'
                    f'<td>{_html.escape(src["name"])}</td><td></td></tr>')

    html.append('</table></div>')

    # === X 平台账号 ===
    accounts = sources.get('twitter_accounts', [])
    html.append('<div class="modal-section">')
    html.append(f'<h3>X 平台追踪账号（{len(accounts)} 个）</h3>')
    html.append('<table class="modal-table"><tr><th>账号</th><th>身份说明</th></tr>')
    for acc in accounts:
        html.append(f'<tr><td><a href="https://x.com/{_html.escape(acc["handle"])}" target="_blank" '
                    f'style="color:#1d9bf0;text-decoration:none">@{_html.escape(acc["handle"])}</a></td>'
                    f'<td>{_html.escape(acc["name"])}</td></tr>')
    html.append('</table></div>')

    # === 关注领域 ===
    domains = scoring.get('domains', [])
    html.append('<div class="modal-section">')
    html.append('<h3>关注领域</h3>')
    html.append('<table class="modal-table"><tr><th>领域</th><th>涵盖内容</th></tr>')
    for d in domains:
        html.append(f'<tr><td style="white-space:nowrap;font-weight:bold">{_html.escape(d["name"])}</td>'
                    f'<td>{_html.escape(d["description"])}</td></tr>')
    html.append('</table></div>')

    # === 话题分类 ===
    topics = scoring.get('topics', [])
    topic_colors_map = {
        '基础大模型': '#1d4ed8', '推理部署': '#0f766e', '训练微调': '#7c3aed',
        '性能优化': '#065f46', '芯片软件栈': '#c2410c', 'AI芯片硬件': '#b45309',
        '开发工具': '#0369a1', '学术论文': '#6d28d9', '行业资讯': '#374151',
    }
    html.append('<div class="modal-section">')
    html.append('<h3>话题分类标签</h3>')
    html.append('<table class="modal-table"><tr><th>话题</th><th>涵盖内容</th></tr>')
    for t in topics:
        color = topic_colors_map.get(t['name'], '#6b7280')
        html.append(f'<tr><td><span class="modal-tag" style="background:{color}">{_html.escape(t["name"])}</span></td>'
                    f'<td>{_html.escape(t["description"])}</td></tr>')
    html.append('</table></div>')

    # === 评分规则 ===
    min_score = scoring.get('min_score', 70)
    quality_note = (scoring.get('quality_note') or '').strip()
    html.append('<div class="modal-section">')
    html.append(f'<h3>相关度评分规则（收录阈值：{min_score} 分）</h3>')
    if quality_note:
        html.append(f'<div class="modal-note">{_html.escape(quality_note)}</div>')
    html.append('</div>')

    # === 热度评分 ===
    html.append('<div class="modal-section">')
    html.append('<h3>热度评分（1–5 星）</h3>')
    html.append('<table class="modal-table"><tr><th>来源</th><th>基础分</th><th>互动加分</th></tr>')
    base_scores = [
        ('AI Lab', '4.0', '—'),
        ('Hacker News', '3.5', 'HN 点赞数：≥500→+2.0 / ≥200→+1.5 / ≥100→+1.0 / ≥30→+0.5'),
        ('X', '3.0', '点赞+转发×2：同上档位'),
        ('Newsletter', '3.0', '—'),
        ('arXiv', '2.5', '—'),
        ('AI Chip', '2.5', '—'),
        ('AI Tools', '2.0', '—'),
    ]
    for name, base, bonus in base_scores:
        html.append(f'<tr><td>{name}</td><td style="text-align:center">{base}</td><td style="font-size:11px;color:#666">{bonus}</td></tr>')
    html.append('</table></div>')

    return '\n'.join(html)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs')
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'web', 'template.html')

ALL_CATS   = ['arXiv', 'AI Lab', 'AI Tools', 'AI Chip', 'Hacker News', 'Newsletter', 'X']
ALL_TOPICS = ['基础大模型', '推理部署', '训练微调', '性能优化', '芯片软件栈', 'AI芯片硬件', '开发工具', '学术论文', '行业资讯']


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


def get_articles(limit=500, min_score=None):
    if min_score is None:
        min_score = load_min_score()
    # X 推文较短信息密度低，单独放宽到 60 分
    x_threshold = 60
    conn = get_conn()
    rows = conn.execute('''
        SELECT title, title_zh, url, source_name, category, topic, published_at, summary, score, hotness, content
        FROM articles
        WHERE (category != 'X' AND score >= ?) OR (category = 'X' AND score >= ?)
        ORDER BY hotness DESC, published_at DESC
        LIMIT ?
    ''', (min_score, x_threshold, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def category_color(category):
    colors = {
        'arXiv':       '#7c3aed',
        'AI Lab':      '#0369a1',
        'AI Tools':    '#0f766e',
        'AI Chip':     '#b45309',
        'Hacker News': '#ea580c',
        'Newsletter':  '#4f46e5',
        'X':           '#000000',
    }
    return colors.get(category, '#6b7280')


def topic_color(topic):
    colors = {
        '基础大模型': '#1d4ed8',
        '推理部署':   '#0f766e',
        '训练微调':   '#7c3aed',
        '性能优化':   '#065f46',
        '芯片软件栈': '#c2410c',
        'AI芯片硬件': '#b45309',
        '开发工具':   '#0369a1',
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
    date_counts  = {}
    for a in articles:
        if a['category'] in cat_counts:
            cat_counts[a['category']] += 1
        for t in (a.get('topic') or '').split(','):
            t = t.strip()
            if t in topic_counts:
                topic_counts[t] += 1
        d = get_date(a['published_at'])
        if d:
            date_counts[d] = date_counts.get(d, 0) + 1

    # 文章列表 HTML
    items_html = ''
    for i, a in enumerate(articles, 1):
        color    = category_color(a['category'])
        topic_raw = a.get('topic') or ''
        topics    = [t.strip() for t in topic_raw.split(',') if t.strip()]
        date_str  = get_date(a['published_at'])

        title_zh_html = ''
        if a.get('title_zh') and a['title_zh'] != a['title']:
            title_zh_html = f'<div class="title-zh">{a["title_zh"]}</div>'

        topic_html = ''
        for t in topics:
            tc = topic_color(t)
            topic_html += f'<span class="tag topic-tag" style="background:{tc}">{t}</span>'

        hotness = a.get('hotness') or 0
        stars_html = f'<span class="hotness-label">热度</span><span class="stars">{"★" * hotness}{"☆" * (5 - hotness)}</span>' if hotness else ''

        summary_html = ''
        if a.get('summary'):
            summary_html = f'<p class="summary">{a["summary"]}</p>'

        # 原文按钮（所有文章都显示）
        raw_content = (a.get('content') or '').strip()[:2000]
        escaped = _html.escape(raw_content) if raw_content else '<span style="color:#aaa">暂无原文内容</span>'
        original_html = (
            f'<button class="show-original-btn" onclick="toggleOriginal(this,\'oc{i}\')">显示原文 ▾</button>'
            f'<div class="original-content" id="oc{i}">{escaped}</div>'
        )

        items_html += f'''
        <tr class="item-row" data-category="{a["category"]}" data-topic="{topic_raw}" data-date="{date_str}" data-iso="{a["published_at"]}" data-score="{a["score"]}" data-hotness="{hotness}">
            <td class="rank">{i}</td>
            <td class="main">
                <div class="title-block">
                    <a class="title-link" href="{a["url"]}" target="_blank" rel="noopener">{a["title"]}</a>
                    {title_zh_html}
                </div>
                {f'<div class="topic-tags">{topic_html}</div>' if topic_html else ''}
                {summary_html}
                {original_html}
                <div class="meta">
                    <span class="source-cat" style="color:{color}">{a["category"]}</span>
                    <span class="source">{a["source_name"]}</span>
                    <span class="dot">·</span>
                    <span class="time" data-iso="{a["published_at"]}">{time_ago(a["published_at"])}</span>
                    <span class="dot">·</span>
                    <span class="score">相关度 {a["score"]}%</span>
                    {stars_html}
                    <span class="pub-date" data-iso="{a["published_at"]}">{date_str}</span>
                </div>
            </td>
        </tr>
        <tr class="spacer" data-category="{a["category"]}" data-topic="{topic_raw}" data-date="{date_str}" data-score="{a["score"]}" data-hotness="{hotness}"><td colspan="2"></td></tr>'''

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

    # 具体日期下拉选项（有文章的日期，降序，最近 30 天）
    date_options = '<option value="">指定日期...</option>\n'
    for d in sorted(date_counts.keys(), reverse=True)[:30]:
        label = d[5:]  # MM-DD
        count = date_counts[d]
        date_options += f'<option value="{d}">{label}（{count}篇）</option>\n'

    updated = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    html = template.replace('{{ITEMS}}', items_html)
    html = html.replace('{{COUNT}}', str(len(articles)))
    html = html.replace('{{UPDATED}}', updated)
    html = html.replace('{{CAT_BUTTONS}}', cat_buttons)
    html = html.replace('{{TOPIC_BUTTONS}}', topic_buttons)
    html = html.replace('{{DATE_OPTIONS}}', date_options)
    html = html.replace('{{SOURCES_CONTENT}}', build_sources_modal())
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
