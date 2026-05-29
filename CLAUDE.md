# CLAUDE.md

给 Claude Code 会话准备的项目速查。详细介绍看 [README.md](./README.md),评分规则看 [docs/criteria.md](./docs/criteria.md),版本变更看 [CHANGELOG.md](./CHANGELOG.md)。

## 项目定位

每日自动聚合 AI 技术领域资讯的静态站点。Python + SQLite + DeepSeek + GitHub Actions + GitHub Pages。在线访问 https://afeiadian.github.io/ai-news-bot/。

## 文件生成关系(最容易踩坑)

- `web/template.html` — 源模板,**改这里**
- `docs/index.html` — 生成产物,**不要手改**(每次 Actions 跑会覆盖)
- `processor/generate.py` 把 7 个占位符填进模板:
  `{{ITEMS}}` `{{COUNT}}` `{{UPDATED}}` `{{CAT_BUTTONS}}` `{{TOPIC_BUTTONS}}` `{{DATE_OPTIONS}}` `{{SOURCES_CONTENT}}`
- 改了 template 后必须重跑 `python3 processor/generate.py`,否则页面看不到变化
- 浏览器里看不到新效果 → `⌘⇧R` 强刷

## 常用命令

```bash
# 全流程(抓取 → AI 处理 → 入库)
cd processor && python3 run.py

# 只重新生成网页(改了 template 后)
python3 processor/generate.py && open docs/index.html

# 补填脚本(都在 processor/)
python3 processor/rescore_all.py             # 全库重打分
python3 processor/backfill_title_zh.py       # 中文标题
python3 processor/backfill_topic.py          # 话题分类
python3 processor/backfill_hotness.py        # 热度
python3 processor/backfill_arxiv_content.py  # arXiv 摘要
```

## Git 工作流注意

- 每天 **北京时间 15:00** GitHub Actions 自动推 `chore: daily update YYYY-MM-DD`。本地推送前**必须** `git pull --rebase origin main`,否则 push 会被拒
- `data/news.db` 是二进制,冲突优先 `git merge -X ours`(先例 commit `85d83d1`)
- `docs/index.html` 每次 Actions 跑都会变,本地改 template 后记得 regenerate 再 commit
- 不要 `git add .`,按文件名加,避免误带入 `.env` 等

## 提交规范

- 前缀: `feat:` `fix:` `style:` `docs:` `chore:` `refactor:` `revert:` `regen:`
- 标题 <70 字符,细节进 body,中英混排可
- 提交体末尾加: `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`
- 用 HEREDOC 传 `-m` 保证换行格式

## 数据流向

```
RSS feeds ──┐
X GraphQL ──┼─► fetch_*.py ─► storage (SQLite)
arXiv API ──┘                     │
                                  ▼
                process.py  (DeepSeek: 评分/翻译/话题/摘要)
                hotness.py  (来源权威度 + 互动数)
                                  │
                                  ▼
                generate.py → docs/index.html → GitHub Pages
```

## 关键代码位置

| 内容 | 位置 |
|---|---|
| 数据源(RSS / X / arXiv) | `config/sources.yaml` |
| 评分阈值、领域、话题 | `config/scoring.yaml` |
| 类别全集 | `processor/generate.py:158` (`ALL_CATS`) |
| 话题全集 | `processor/generate.py:159` (`ALL_TOPICS`) — 加新话题要同步 |
| 类别颜色 | `processor/generate.py:204` (`category_color`) |
| 话题颜色 | `processor/generate.py:217` (`topic_color`) |
| 热度算法权重 | `processor/hotness.py` (`SOURCE_BASE`) |
| DeepSeek prompts | `processor/process.py` |
| HTML 模板 + JS | `web/template.html` |

**模板里 JS 依赖的 ID/class 不能改名**: `item-list` `item-row` `rank` `filter-bar` `sort-btn` `page-btn` `modal-overlay` 等 — 否则 JS 立刻断。

## 环境变量

`.env` 不上传 git;`.env.example` 是模板。必需变量:
`MINIFLUX_URL` `MINIFLUX_API_KEY` `RSSHUB_URL` `DEEPSEEK_API_KEY` `DEEPSEEK_BASE_URL` `DEEPSEEK_MODEL` `TWITTER_AUTH_TOKEN` `TWITTER_CT0`(从浏览器 x.com Cookie 复制)。

## 已踩过的坑

- **星星实心/空心**: 浏览器把 Unicode `★`/`☆` 当 emoji 渲染成彩色填充,CSS color 失效。项目改用 SVG(`generate.py` 里的 `STAR_FILL` / `STAR_LINE` 两条 path)。**不要回到字符方案**
- **`{{UPDATED}}` 是数据时间不是脚本时间**: 取所有文章 `published_at` 的最大值,转北京时区
- **热度筛选 N★ 是精确匹配**: 不是"N 或以上",见 commit `5b84f09`
- **arXiv 海量论文会挤掉小源**: `processor/fetch.py:fetch_unread_entries` 按分类配额抓取(优先级 1 给 lab/tools/chip/newsletter/HN,剩余给 arXiv),不要改回时间倒序
- **整天空白多因 Railway 后端挂掉**: 所有 RSS(arXiv/Lab/Chip/Tools/Newsletter/HN)都经 Miniflux,HN 还经 RSSHub,二者都托管在 Railway。Railway 服务下线时返回 `404 Application not found`,排查先 `curl $MINIFLUX_URL/healthcheck`。X 走 `fetch_twitter.py` 直连 x.com,与后端无关。`get_feeds()`/`_get_categories()` 已做兜底(后端挂时返回空、不再崩 `run.py`),所以后端故障会降级成"仅 X"而非整天空白。**Railway 换 URL 后**:要同步改 GitHub Secret `MINIFLUX_URL`/`RSSHUB_URL` + `config/sources.yaml` 里硬编码的 rsshub URL(第 4/14/132/135 行)+ 重跑 `setup_feeds.py`
- **GitHub 账号被封也会 push 失败**: Actions 全跑完但最后 `git push` 报 `403 account suspended`(先例 5-26),数据没推上去 → 页面停在旧版。和后端故障是两回事,看 Actions 日志末尾区分

## 协作风格偏好

- 中文回复,简洁不啰嗦
- 改 CSS 用小幅 Edit,不要整页重写
- 颜色用 CSS 变量(`--accent` `--bg` `--text-1` 等),不要写死十六进制
- 不主动加代码注释,除非有非显然的原因
- UI 风格已定型:浅米色背景 `#fbfaf5` + 暖橙强调 `#ea580c` + Geist / Geist Mono 字体,不要随意换风格基调
- 测试 UI 改动靠 `open docs/index.html`,没有自动化测试

## 调整配置速查

| 调整项 | 位置 |
|---|---|
| 关注领域 | `config/scoring.yaml` → `domains` |
| 全局收录门槛(当前 70) | `config/scoring.yaml` → `min_score` |
| X 单独阈值(当前 60) | `processor/generate.py` → `x_threshold` |
| 话题标签定义 | `config/scoring.yaml` → `topics`,同步 `ALL_TOPICS` |
| 热度权重 | `processor/hotness.py` → `SOURCE_BASE` |
| RSS 数据源 | `config/sources.yaml` + `python3 processor/setup_feeds.py` |
| X 追踪账号 | `config/sources.yaml` → `twitter_accounts` |
| 抓取分类配额 | `processor/fetch.py` → `fetch_unread_entries` |
| 数据保留天数(当前 30) | `processor/run.py` → `prune_old_articles(days=30)` |
| 自动更新时间 | `.github/workflows/daily_update.yml` → `cron` |
