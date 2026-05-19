# AI 资讯日报

自动聚合 AI 技术领域最新资讯的每日简报网站，类 Hacker News 风格，支持多维度筛选与原文展开。

**在线访问**：https://afeiadian.github.io/ai-news-bot/

## 关注领域

聚焦 AI 软硬件技术与行业动态：

- **AI 芯片与硬件**：GPU/NPU/TPU 架构、AI 数据中心、芯片互联技术
- **AI 芯片软件栈**：CUDA/ROCm/XLA、编译器、算子库、Kernel 优化、芯片适配
- **大语言模型技术**：LLM 架构、训练、对齐、推理、量化、多模态、文生视频
- **AI 基础设施**：分布式训练系统、推理 serving 框架、AI 集群网络
- **AI 产品与行业**：主流 AI 公司动态、重要模型发布、权威技术预测

## 功能

- **多源采集**：22 个 RSS 订阅源 + 22 个 X 平台行业领袖账号
- **分类配额抓取**：高价值来源（公司博客、Newsletter、HN）优先满抓，arXiv 用剩余配额，避免被海量论文挤掉
- **AI 智能处理**：相关度评分（0–100）、中文标题翻译、3–5 句内容摘要、话题自动分类
- **原文抓取**：Jina Reader + trafilatura 双备份，arXiv 用官方 API 获取作者和摘要
- **话题标签**：每篇文章自动打 1–3 个标签（9 个话题分类）
- **热度评分**：1–5 星，综合来源权威度 + HN 真实互动数 + X 推文点赞/转发数
- **显示原文**：每条资讯可展开查看原文（2000 字符上限）
- **网页交互**：
  - 五维筛选（日期 × 来源 × 话题 × 相关度 × 热度），三组分类按钮 count 实时联动
  - 排序按钮支持升降序切换（↓/↑ 切换）
  - 时间显示客户端实时计算（X 分钟/小时/天前）
  - 日期筛选使用浏览器本地时区
  - 每条资讯右下显示发布日期
  - 顶部按钮可查看完整数据来源 & 评分标准
  - 右上角显示累计浏览次数
- **每日自动更新**：北京时间每天 **15:00**（UTC 07:00），GitHub Actions 自动抓取并部署
- **自动清理**：保留 30 天内文章，旧文章自动删除并 VACUUM 回收空间

## 技术架构

```
RSSHub（Railway）      →  将部分网站转为 RSS（如 Anthropic）
Miniflux（Railway）    →  RSS 聚合 + REST API
X GraphQL API          →  直接抓取行业领袖推文（Cookie 认证）
Jina + trafilatura     →  抓取 HN/HF/DeepMind 等原文
Python 处理脚本        →  分类配额拉取 → AI 处理 → SQLite 存储
GitHub Actions         →  每天 UTC 07:00 自动触发
GitHub Pages           →  静态 HTML 网页托管
```

**AI 模型**：DeepSeek（deepseek-v4-pro），用于相关度评分、话题分类、中文摘要、标题翻译

## 项目结构

```
├── config/
│   ├── sources.yaml              # 数据源配置（RSS、arXiv、X 账号）
│   └── scoring.yaml              # 评分领域、收录阈值、话题分类、质量规则
├── processor/
│   ├── run.py                    # 主流程：清理旧数据 → 拉取 → AI 处理 → 存储
│   ├── fetch.py                  # 从 Miniflux API 按分类配额拉取
│   ├── fetch_twitter.py          # 从 X GraphQL API 抓取推文（含点赞/转发数）
│   ├── fetch_content.py          # Jina Reader + trafilatura 抓取文章原文
│   ├── process.py                # DeepSeek AI：评分 + 翻译 + 话题 + 摘要
│   ├── hotness.py                # 热度评分：来源权威度 + 互动数加分
│   ├── storage.py                # SQLite 数据库操作 + 30 天清理
│   ├── generate.py               # 生成静态 HTML 页面
│   ├── setup_feeds.py            # 一次性：批量添加订阅源到 Miniflux
│   ├── setup_twitter.py          # 参考脚本（已由 .env Cookie 认证替代）
│   ├── rescore_all.py            # 补填脚本：对全库文章重新评分
│   ├── backfill_arxiv_content.py # 补填脚本：从 arXiv API 获取作者和摘要
│   ├── backfill_title_zh.py      # 补填脚本：历史文章中文标题
│   ├── backfill_topic.py         # 补填脚本：历史文章话题分类
│   └── backfill_hotness.py       # 补填脚本：历史文章热度评分
├── web/
│   └── template.html             # 页面模板（HN 风格，纯静态）
├── docs/
│   ├── index.html                # 生成的静态网页（部署到 GitHub Pages）
│   └── criteria.md               # 分类与评分依据的详细说明
├── data/
│   └── news.db                   # SQLite 数据库（由 Actions 提交更新）
├── .env                          # 环境变量（不上传 GitHub）
└── .github/workflows/
    └── daily_update.yml          # GitHub Actions 定时任务
```

## 数据源（当前 22 个 RSS + 22 个 X 账号）

### RSS 订阅源

| 分类 | 来源 |
|------|------|
| AI Lab | OpenAI News、Anthropic News、Google Research Blog、Google DeepMind Blog、Meta AI Research Blog、Microsoft Research Blog、Hugging Face Blog |
| AI Chip | NVIDIA Blog、NVIDIA Developer Blog、SemiAnalysis |
| AI Tools | PyTorch Blog |
| Newsletter | Ahead of AI、Interconnects、Import AI、The Gradient |
| Hacker News | Top Links |
| arXiv | cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |

### X 平台追踪账号

| 类别 | 账号 |
|------|------|
| AI 公司创始人/CEO | @karpathy、@sama、@darioamodei、@demishassabis、@elonmusk、@gdb、@arthurmensch |
| 顶级研究者 | @ylecun、@fchollet、@tri_dao、@drjimfan、@soumithchintala、@rasbt、@natolambert |
| 芯片/系统专家 | @dylan522p、@clattner_llvm |
| 官方账号 | @AnthropicAI、@OpenAI、@GoogleDeepMind、@huggingface、@nvidia、@xai |
| 论文推荐 | @_akhaliq |

## 抓取策略：分类配额

每次运行从 Miniflux 拉取最多 200 篇未读，但**不是简单按时间倒序**——因为 arXiv 每天产出几百篇会挤掉其他高价值来源。改为：

1. **优先级 1**：lab/tools/chip/newsletter/hackernews 每分类抓取上限 100 篇（实际通常 <30 篇）
2. **优先级 2**：剩余配额给 arXiv

这样保证 AI Lab、PyTorch、NVIDIA 等少量但高质量的来源不会被 arXiv 海量论文挤掉。

## 评分与筛选

- **min_score: 70**：所有来源默认阈值
- **X 单独阈值 60**：推文较短，AI 相关的简短评论也给保留
- **X 推文宽容评分**：提及任何 AI 公司/产品/模型/工具（Codex、Grok、Claude 等）一律 60+ 分
- **arXiv 严格筛选**：必须满足 SOTA 声称 / 顶级机构 / 工程实用价值之一

详见 [docs/criteria.md](docs/criteria.md)。

## 本地运行

```bash
# 1. 安装依赖
pip install -r processor/requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入以下 Key：
#   MINIFLUX_URL / MINIFLUX_API_KEY
#   RSSHUB_URL
#   DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL
#   TWITTER_AUTH_TOKEN / TWITTER_CT0   ← 从浏览器 x.com Cookie 获取

# 3. 抓取并处理最新文章（自动只取最近2天）
cd processor && python3 run.py

# 4. 生成网页并预览
python3 generate.py
open ../docs/index.html
```

### X 平台 Cookie 配置

X 平台采用浏览器 Cookie 认证，无需账号密码：

1. 浏览器登录 [x.com](https://x.com)
2. 开发者工具 → Network → 刷新页面 → 任意请求 → Request Headers → Cookie
3. 找到 `auth_token=...` 和 `ct0=...` 的值，填入 `.env`

Cookie 通常数周至数月有效，过期后重新获取即可。

## 调整配置

| 想调整的内容 | 操作 |
|------------|------|
| 关注的 AI 技术领域 | 编辑 `config/scoring.yaml` → `domains` |
| 全局收录门槛（当前 70） | 编辑 `config/scoring.yaml` → `min_score` |
| X 单独门槛（当前 60） | 编辑 `processor/generate.py` → `x_threshold` |
| 质量评分规则 | 编辑 `config/scoring.yaml` → `quality_note` |
| 话题标签定义 | 编辑 `config/scoring.yaml` → `topics`，同步更新 `processor/generate.py` 的 `ALL_TOPICS` |
| 热度评分权重 | 编辑 `processor/hotness.py` → `SOURCE_BASE` |
| 数据源增减（RSS） | 编辑 `config/sources.yaml`，运行 `python3 processor/setup_feeds.py` |
| X 平台追踪账号 | 编辑 `config/sources.yaml` → `twitter_accounts` |
| 抓取分类配额 | 编辑 `processor/fetch.py` → `fetch_unread_entries` |
| 数据保留天数（当前 30） | 编辑 `processor/run.py` → `prune_old_articles(days=30)` |
| 更新时间 | 编辑 `.github/workflows/daily_update.yml` → `cron` |

## GitHub Actions Secrets

部署时需在仓库 Settings → Secrets → Actions 中配置：

| Secret | 说明 |
|--------|------|
| `MINIFLUX_URL` | Miniflux 服务地址 |
| `MINIFLUX_API_KEY` | Miniflux API Key |
| `RSSHUB_URL` | RSSHub 服务地址 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | DeepSeek API Base URL |
| `DEEPSEEK_MODEL` | 使用的模型名称 |
| `TWITTER_AUTH_TOKEN` | X 平台 auth_token Cookie |
| `TWITTER_CT0` | X 平台 ct0 Cookie |

## 已知限制

- **GitHub Actions cron 不精确**：免费套餐可能延迟 1-3 小时
- **arXiv 入库延迟**：arXiv 在 UTC 04:00 发布当日论文，Miniflux 约 UTC 06:00 抓到，因此 cron 设为 UTC 07:00 以确保当日 arXiv 内容可用
- **静态站浏览量**：基于 counterapi.dev 免费服务，可能偶尔延迟
- **X Cookie 过期**：通常 1-3 个月，过期后需手动更新 Secret
