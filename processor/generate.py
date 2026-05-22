import html as _html
import os
import sys
import yaml
from datetime import datetime, timezone, timedelta
from storage import get_conn

SCORING_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'scoring.yaml')
SOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.yaml')

def load_category_filters():
    """读取 config/scoring.yaml 里 category_filters 配置。

    返回 dict:  category -> {'min_score': int, 'max_articles': int}
    配置中未列出的 category 在 get_articles 阶段会被丢弃。
    """
    with open(SCORING_PATH, encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    return config.get('category_filters', {}) or {}


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

    # === 抓取策略 ===
    html.append('<div class="modal-section">')
    html.append('<h3>抓取策略：分类配额</h3>')
    html.append('<div class="modal-note">每天 UTC 07:00（北京 15:00）自动抓取，每次最多 200 篇。'
                '不是简单按时间倒序——arXiv 每天数百篇会挤掉其他来源，因此按分类配额：\n'
                '· 优先抓全部 lab / tools / chip / newsletter / hackernews（每类上限 100，实际通常 &lt;30）\n'
                '· 剩余配额给 arXiv（通常 140-150 篇）\n'
                '保证 AI 公司官博、NVIDIA、PyTorch 等高价值来源不被海量论文挤掉。</div>')
    html.append('</div>')

    # === 原文抓取 ===
    html.append('<div class="modal-section">')
    html.append('<h3>原文抓取来源</h3>')
    html.append('<table class="modal-table"><tr><th>来源类型</th><th>原文获取方式</th></tr>')
    fetch_methods = [
        ('X / Twitter', 'fetch_twitter.py 抓取时直接存推文正文'),
        ('arXiv', 'arXiv 官方 API 获取作者列表 + 论文摘要'),
        ('Hacker News', 'Jina Reader 抓取外链文章正文'),
        ('HF / DeepMind', 'trafilatura 抓取（Jina 被 Cloudflare 限速时降级）'),
        ('其他博客', 'Miniflux RSS 自带 content'),
    ]
    for src, method in fetch_methods:
        html.append(f'<tr><td style="white-space:nowrap;font-weight:bold">{src}</td>'
                    f'<td style="font-size:12px">{method}</td></tr>')
    html.append('</table></div>')

    # === 各来源独立筛选 ===
    cat_filters = scoring.get('category_filters') or {}
    quality_note = (scoring.get('quality_note') or '').strip()
    html.append('<div class="modal-section">')
    html.append('<h3>各来源独立筛选规则</h3>')
    if cat_filters:
        html.append('<table class="modal-table"><tr><th>来源</th><th>录用分数线</th><th>每日上限</th></tr>')
        for cat in ALL_CATS:
            cfg = cat_filters.get(cat)
            if not cfg:
                continue
            ms = cfg.get('min_score', 0)
            mn = cfg.get('max_articles', 0)
            html.append(
                f'<tr><td>{cat}</td>'
                f'<td style="text-align:center">≥ {ms} 分</td>'
                f'<td style="text-align:center">{mn} 条 / 日</td></tr>'
            )
        html.append('</table>')
        html.append('<div class="modal-note" style="margin-top:10px">'
                    '· 每个来源按相关度得分降序,在每个发布日期内独立排序,各取前 N 条\n'
                    '· 历史范围由 30 天数据保留期统一控制,不另设全局总数上限\n'
                    '· 来源之间不再混合排序,避免单一高产来源(如 arXiv)挤占其他来源</div>')
    html.append('</div>')

    # === 相关度评分细则 ===
    if quality_note:
        html.append('<div class="modal-section">')
        html.append('<h3>相关度评分细则（DeepSeek 评分主体)</h3>')
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

    # === 数据保留 ===
    html.append('<div class="modal-section">')
    html.append('<h3>数据更新与保留</h3>')
    html.append('<div class="modal-note">'
                '· 每日抓取时间：UTC 07:00 / 北京时间 15:00（GitHub Actions 可能延迟 1-3 小时）\n'
                '· 数据保留：自动保留最近 30 天的文章，旧文章自动删除并 VACUUM 回收空间\n'
                '· 文章采集窗口：每次只处理最近 2 天内发布的未读文章\n'
                '· 网页时间显示：客户端基于 ISO 时间戳实时计算，使用浏览器本地时区</div>')
    html.append('</div>')

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


_BJ_TZ = timezone(timedelta(hours=8))


def _bj_day(iso_str):
    """把 ISO 时间戳(UTC 或带时区)转成北京时区的 YYYY-MM-DD 字符串。"""
    if not iso_str:
        return ''
    try:
        d = datetime.fromisoformat(str(iso_str).replace('Z', '+00:00'))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(_BJ_TZ).strftime('%Y-%m-%d')
    except Exception:
        return str(iso_str)[:10]


def get_articles(limit=None):
    """各来源类别按"每日数量上限"独立筛选。

    流程:
    1. 读取所有文章(30 天数据保留范围内)
    2. 按 (category, 北京时区发布日期) 分组
    3. 对每个 (category, 日期) 组合,先按 min_score 过滤,
       再按 score 降序取前 max_articles 条(=该来源该日的上限)
    4. 未在 category_filters 中配置的来源整组丢弃
    5. 合并所有保留项,按热度 DESC、时间 DESC 排序
    6. 历史范围由 30 天数据保留期统一控制,不另设全局总数上限
    """
    filters = load_category_filters()
    conn = get_conn()
    rows = conn.execute('''
        SELECT title, title_zh, url, source_name, category, topic,
               published_at, summary, score, hotness, content
        FROM articles
        ORDER BY category, published_at DESC, score DESC
    ''').fetchall()
    conn.close()

    # (category, 北京日期) -> [articles]
    by_cat_day = {}
    for r in rows:
        d = dict(r)
        key = (d['category'], _bj_day(d.get('published_at')))
        by_cat_day.setdefault(key, []).append(d)

    selected = []
    for (cat, _day), articles in by_cat_day.items():
        cfg = filters.get(cat)
        if not cfg:
            continue
        min_s = int(cfg.get('min_score', 0) or 0)
        max_n = int(cfg.get('max_articles', 0) or 0)
        if max_n <= 0:
            continue
        kept = sorted(
            (a for a in articles if (a.get('score') or 0) >= min_s),
            key=lambda a: (a.get('score') or 0, a.get('published_at') or ''),
            reverse=True,
        )[:max_n]
        selected.extend(kept)

    selected.sort(key=lambda a: (
        a.get('hotness') or 0,
        a.get('published_at') or ''
    ), reverse=True)

    return selected[:limit] if limit else selected


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
        # SVG 实心 / 空心 两种星，避免 emoji 字体干扰
        STAR_PATH = ('M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61'
                     'L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z')
        STAR_FILL = (f'<svg class="star-ico" viewBox="0 0 24 24" width="12" height="12" '
                     f'fill="currentColor" aria-hidden="true"><path d="{STAR_PATH}"/></svg>')
        STAR_LINE = (f'<svg class="star-ico" viewBox="0 0 24 24" width="12" height="12" '
                     f'fill="none" stroke="currentColor" stroke-width="1.8" '
                     f'stroke-linejoin="round" aria-hidden="true">'
                     f'<path d="{STAR_PATH}"/></svg>')
        filled = STAR_FILL * hotness
        empty  = STAR_LINE * (5 - hotness)
        stars_html = (
            f'<span class="hotness-label">热度</span>'
            f'<span class="stars">'
            f'<span class="stars-on">{filled}</span>'
            f'<span class="stars-off">{empty}</span>'
            f'</span>'
            if hotness else ''
        )

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

    # 最新数据时间：取所有文章中最近的 published_at（UTC），转成北京时间
    BJ = timezone(timedelta(hours=8))
    latest_dt = None
    for a in articles:
        pub = a.get('published_at')
        if not pub:
            continue
        try:
            d = datetime.fromisoformat(str(pub).replace('Z', '+00:00'))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            if latest_dt is None or d > latest_dt:
                latest_dt = d
        except Exception:
            pass
    if latest_dt is not None:
        updated = latest_dt.astimezone(BJ).strftime('%Y-%m-%d %H:%M')
    else:
        updated = datetime.now(BJ).strftime('%Y-%m-%d %H:%M')
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
