# AI 资讯日报

自动聚合 AI 技术领域最新资讯的每日简报网站，类 Hacker News 风格，支持多维度筛选。

## 功能

- **多源采集**：arXiv 6 个分类、Hacker News、Reddit 4 个版块、Hugging Face、NVIDIA、SemiAnalysis、Import AI、The Gradient 等共 16 个订阅源
- **AI 智能处理**：相关度评分（0–100%）、中文标题翻译、3–5 句内容摘要、话题自动分类
- **话题标签**：每篇文章自动打 1–3 个标签（基础大模型 / 推理部署 / 性能优化 / 训练微调 / 开发工具 / AI芯片硬件 / 学术论文 / 行业资讯）
- **热度评分**：1–5 星，综合来源权威度 + HN/Reddit 真实互动数
- **HN 风格网页**：五维筛选（日期 × 来源 × 话题 × 相关度 × 热度）+ 分页浏览
- **自动防积压**：每次运行只处理最近 2 天内的文章，自动清理历史积压

## 技术架构

```
RSSHub（Railway）    →  将各网站转为统一 RSS 格式
Miniflux（Railway）  →  RSS 聚合 + REST API
Python 处理脚本      →  拉取（2天内）→ AI 处理 → SQLite 存储
GitHub Actions       →  每日定时触发整个流程
GitHub Pages         →  静态 HTML 网页托管
```

**AI 模型**：DeepSeek（deepseek-v4-pro），用于相关度评分、话题分类、中文摘要、标题翻译

**热度数据**：HN Algolia API（真实点赞数）+ Reddit JSON API（真实 score）

## 项目结构

```
├── config/
│   ├── sources.yaml          # 数据源配置（RSS、arXiv、Reddit、X 账号）
│   └── scoring.yaml          # 相关度评分领域 + 收录阈值 + 话题分类定义
├── processor/
│   ├── run.py                # 主流程：清理积压 → 拉取 → AI 处理 → 存储
│   ├── fetch.py              # 从 Miniflux API 拉取最近文章，清理旧积压
│   ├── process.py            # DeepSeek AI：评分 + 翻译 + 话题 + 摘要
│   ├── hotness.py            # 热度评分：来源权威度 + HN/Reddit 互动数
│   ├── storage.py            # SQLite 数据库操作
│   ├── generate.py           # 生成静态 HTML 页面
│   ├── setup_feeds.py        # 一次性：批量添加订阅源到 Miniflux
│   ├── backfill_title_zh.py  # 补填脚本：历史文章中文标题
│   ├── backfill_topic.py     # 补填脚本：历史文章话题分类
│   └── backfill_hotness.py   # 补填脚本：历史文章热度评分
├── web/
│   ├── template.html         # 页面模板（HN 风格，纯静态）
│   └── output/               # 生成的静态文件（部署到 GitHub Pages）
├── docs/
│   └── criteria.md           # 所有分类与评分依据的详细说明
├── data/
│   └── news.db               # SQLite 数据库（本地，不上传 GitHub）
├── .env.example              # 环境变量模板
└── .github/workflows/        # GitHub Actions 定时任务配置
```

## 数据源（当前 16 个）

| 来源分类 | 具体来源 |
|---------|---------|
| AI Lab | Hugging Face Blog |
| AI Chip | NVIDIA Blog、SemiAnalysis |
| arXiv | cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |
| Hacker News | Top Links |
| Reddit | r/MachineLearning / r/LocalLLaMA / r/artificial / r/Semiconductors |
| Newsletter | Import AI、The Gradient |

> 扩展来源：编辑 `config/sources.yaml`，然后运行 `python3 processor/setup_feeds.py`

## 网页筛选功能

| 筛选维度 | 选项 |
|---------|------|
| 日期 | 全部 / 今天 / 昨天 / 近3天 / 近7天 / 近30天 + 具体日期下拉 |
| 来源 | 全部 / AI Lab / arXiv / AI Tools / AI Chip / Hacker News / Reddit / Newsletter |
| 话题 | 全部 / 基础大模型 / 推理部署 / 性能优化 / 训练微调 / 开发工具 / AI芯片硬件 / 学术论文 / 行业资讯 |
| 相关度 | 全部 / 70%+ / 80%+ / 90%+ |
| 热度 | 全部 / 2星以上 / 3星以上 / 4星以上 / 5星 |

五个维度可任意组合，每页显示 30 条，默认按热度降序排列。

## 本地运行

```bash
# 1. 安装依赖
pip install -r processor/requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 Miniflux、DeepSeek、RSSHub 的地址和 Key

# 3. 处理最新文章（自动只取最近2天）
cd processor && python3 run.py

# 4. 生成网页
python3 generate.py
open ../web/output/index.html
```

## 评分与分类说明

详见 [docs/criteria.md](docs/criteria.md)，包含：
- 相关度评分依据（6 个关注领域）与收录阈值
- 话题标签分类标准（8 个话题，每篇最多 3 个）
- 热度星级评分公式（来源权威度 + 真实互动数 + 计算示例）
- 来源分类颜色说明
- 各配置文件职责速查表

## 调整配置

| 想调整的内容 | 操作 |
|------------|------|
| 关注的 AI 技术领域 | 编辑 `config/scoring.yaml` → `domains` |
| 收录门槛（当前60%） | 编辑 `config/scoring.yaml` → `min_score` |
| 话题标签定义 | 编辑 `config/scoring.yaml` → `topics`，同步更新 `processor/generate.py` 的 `ALL_TOPICS` |
| 热度评分权重 | 编辑 `processor/hotness.py` 的 `SOURCE_BASE` 和 `ENGAGEMENT_TIERS` |
| 数据源增减 | 编辑 `config/sources.yaml`，运行 `python3 processor/setup_feeds.py` |
| 文章采集范围（天数） | 修改 `processor/run.py` 中 `days_back` 参数 |

## 备用 AI 模型

`.env` 中已预留 Kimi（月之暗面）配置，取消注释即可切换：

```env
# KIMI_API_KEY=your_kimi_api_key
# KIMI_BASE_URL=https://api.moonshot.cn/v1
# KIMI_MODEL=kimi-k2-0711-preview
```
