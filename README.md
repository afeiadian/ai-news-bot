# AI 资讯日报

自动聚合 AI 技术领域最新资讯的每日简报网站，类 Hacker News 风格，支持多维度筛选。

**在线访问**：https://afeiadian.github.io/ai-news-bot/

## 关注领域

聚焦 AI 软硬件技术与行业动态，具体包括：

- **AI 芯片与硬件**：GPU/NPU/TPU 架构、AI 数据中心、芯片互联技术
- **AI 芯片软件栈**：CUDA/ROCm/XLA、编译器、算子库、Kernel 优化、芯片适配
- **大语言模型技术**：LLM 架构、训练、对齐、推理、量化、多模态、文生视频
- **AI 基础设施**：分布式训练系统、推理 serving 框架、AI 集群网络
- **AI 产品与行业**：主流 AI 公司动态、重要模型发布、权威技术预测

## 功能

- **多源采集**：22 个 RSS 订阅源 + 22 个 X 平台行业领袖账号（共约 30 个数据源）
- **AI 智能处理**：相关度评分（0–100%）、中文标题翻译、3–5 句内容摘要、话题自动分类
- **话题标签**：每篇文章自动打 1–3 个标签（9 个话题分类）
- **热度评分**：1–5 星，综合来源权威度 + HN 真实互动数 + X 推文点赞/转发数
- **显示原文**：每条资讯支持展开查看原文/摘要（arXiv 显示作者与论文摘要）
- **HN 风格网页**：五维筛选（日期 × 来源 × 话题 × 相关度 × 热度）+ 分页浏览
- **每日自动更新**：北京时间每天 09:00，GitHub Actions 自动抓取处理并更新网页

## 技术架构

```
RSSHub（Railway）    →  将部分网站转为 RSS 格式（如 Anthropic）
Miniflux（Railway）  →  RSS 聚合 + REST API
X GraphQL API        →  直接抓取行业领袖推文（Cookie 认证）
Python 处理脚本      →  拉取（2天内）→ AI 处理 → SQLite 存储
GitHub Actions       →  每天 09:00 北京时间自动触发
GitHub Pages         →  静态 HTML 网页托管
```

**AI 模型**：DeepSeek（deepseek-v4-pro），用于相关度评分、话题分类、中文摘要、标题翻译

## 项目结构

```
├── config/
│   ├── sources.yaml              # 数据源配置（RSS、arXiv、X 账号）
│   └── scoring.yaml              # 评分领域、收录阈值、话题分类、质量规则
├── processor/
│   ├── run.py                    # 主流程：清理积压 → 拉取 → AI 处理 → 存储
│   ├── fetch.py                  # 从 Miniflux API 拉取最近文章
│   ├── fetch_twitter.py          # 从 X 平台抓取行业领袖推文（直接调 GraphQL API）
│   ├── process.py                # DeepSeek AI：评分 + 翻译 + 话题 + 摘要
│   ├── hotness.py                # 热度评分：来源权威度 + 互动数加分
│   ├── storage.py                # SQLite 数据库操作
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
| arXiv | cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |
| Hacker News | Top Links |
| Newsletter | Ahead of AI、Interconnects、Import AI、The Gradient |
| AI Tools | PyTorch Blog |

### X 平台追踪账号

| 类别 | 账号 |
|------|------|
| AI 公司创始人/CEO | @karpathy、@sama、@darioamodei、@demishassabis、@elonmusk、@gdb、@arthurmensch |
| 顶级研究者 | @ylecun、@fchollet、@tri_dao、@drjimfan、@soumithchintala、@rasbt、@natolambert |
| 芯片/系统专家 | @dylan522p、@clattner_llvm |
| 官方账号 | @AnthropicAI、@OpenAI、@GoogleDeepMind、@huggingface、@nvidia、@xai |
| 论文推荐 | @_akhaliq |

## 网页筛选功能

| 筛选维度 | 选项 |
|---------|------|
| 日期 | 全部 / 今天 / 昨天 / 近3天 / 近7天 / 近30天 + 具体日期下拉 |
| 来源 | 全部 / AI Lab / arXiv / AI Tools / AI Chip / Hacker News / Newsletter / X |
| 话题 | 全部 / 基础大模型 / 推理部署 / 训练微调 / 性能优化 / 芯片软件栈 / AI芯片硬件 / 开发工具 / 学术论文 / 行业资讯 |
| 相关度 | 全部 / 70%+ / 80%+ / 90%+ |
| 热度 | 全部 / 2星以上 / 3星以上 / 4星以上 / 5星 |

五个维度可任意组合，每页显示 30 条，默认按热度降序排列。

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

### X 平台认证配置

X 平台采用浏览器 Cookie 认证，无需账号密码：

1. 在浏览器登录 [x.com](https://x.com)
2. 打开开发者工具 → Network → 刷新页面 → 任意请求 → Request Headers → Cookie
3. 找到 `auth_token=...` 和 `ct0=...` 的值，填入 `.env`

Cookie 通常数周至数月有效，过期后重新获取即可。

## 评分与分类说明

详见 [docs/criteria.md](docs/criteria.md)，包含：
- 相关度评分依据（6 个关注领域）、质量评分规则与收录阈值
- 话题标签分类标准（9 个话题）
- 热度星级评分公式（来源权威度 + 真实互动数 + 计算示例）
- 来源分类与颜色说明
- 各配置文件职责速查表

## 调整配置

| 想调整的内容 | 操作 |
|------------|------|
| 关注的 AI 技术领域 | 编辑 `config/scoring.yaml` → `domains` |
| 收录门槛（当前70%） | 编辑 `config/scoring.yaml` → `min_score` |
| 质量评分规则 | 编辑 `config/scoring.yaml` → `quality_note` |
| 话题标签定义 | 编辑 `config/scoring.yaml` → `topics`，同步更新 `processor/generate.py` 的 `ALL_TOPICS` |
| 热度评分权重 | 编辑 `processor/hotness.py` → `SOURCE_BASE` |
| 数据源增减（RSS） | 编辑 `config/sources.yaml`，运行 `python3 processor/setup_feeds.py` |
| X 平台追踪账号 | 编辑 `config/sources.yaml` → `twitter_accounts` |
| 文章采集范围（天数） | 修改 `processor/run.py` 中 `days_back` 参数 |
| 更新时间 | 修改 `.github/workflows/daily_update.yml` → `cron` |

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
