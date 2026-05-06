# AI 资讯日报

自动聚合 AI 技术领域最新资讯的每日简报网站，类 Hacker News 风格，支持多维度筛选。

## 功能

- 每日自动抓取 arXiv、Hacker News、Reddit、AI Lab 官方博客等多个数据源
- AI 自动过滤（相关度评分）、中文标题翻译、内容摘要
- 自动打话题标签（基础大模型 / 推理部署 / 性能优化 / 训练微调 / 开发工具 / AI芯片硬件 / 学术论文 / 行业资讯）
- 热度评分（综合来源权威度 + HN/Reddit 真实互动数）
- 支持按日期、来源、话题、相关度、热度多维筛选，带分页

## 技术架构

```
RSSHub（Railway）    →  统一 RSS 格式
Miniflux（Railway）  →  RSS 聚合 + REST API
Python 处理脚本      →  拉取 → AI 评分 → 存入 SQLite
GitHub Actions       →  每日定时触发
GitHub Pages         →  静态网页托管
```

**AI 模型**：DeepSeek（deepseek-v4-pro），用于相关度评分、话题分类、中文摘要、标题翻译

**热度数据**：HN Algolia API + Reddit JSON API（真实点赞数）

## 项目结构

```
├── config/
│   ├── sources.yaml      # 数据源配置（RSS、arXiv、Reddit、X）
│   └── scoring.yaml      # 相关度评分域和话题分类定义
├── processor/
│   ├── run.py            # 主流程：拉取 → 处理 → 存储
│   ├── fetch.py          # 从 Miniflux API 拉取文章
│   ├── process.py        # DeepSeek AI 评分、翻译、分类
│   ├── hotness.py        # 热度评分（HN/Reddit 真实数据）
│   ├── storage.py        # SQLite 数据库操作
│   ├── generate.py       # 生成静态 HTML 页面
│   └── backfill_*.py     # 历史数据补填脚本
├── web/
│   ├── template.html     # 页面模板（HN 风格）
│   └── output/           # 生成的静态文件（GitHub Pages）
├── docs/
│   └── criteria.md       # 所有分类与评分依据详细说明
└── .github/workflows/    # GitHub Actions 自动化配置
```

## 数据源

| 类型 | 来源 |
|------|------|
| AI Lab 官博 | Anthropic、OpenAI、DeepMind、Meta AI、Hugging Face、NVIDIA 等 |
| 学术论文 | arXiv cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |
| 技术社区 | Hacker News Top Links |
| Reddit | r/MachineLearning / r/LocalLLaMA / r/artificial / r/Semiconductors |
| Newsletter | Import AI、The Gradient、SemiAnalysis |

## 本地运行

```bash
# 安装依赖
pip install -r processor/requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 处理新文章
cd processor && python3 run.py

# 生成网页
python3 generate.py
open ../web/output/index.html
```

## 评分与分类说明

详见 [docs/criteria.md](docs/criteria.md)，包含：
- 相关度评分依据（0–100 分）与收录阈值
- 话题标签分类标准（8 个话题）
- 热度星级评分公式（来源权威度 + 真实互动数）
- 来源分类说明
- 各配置文件速查表

## 调整配置

- **调整关注领域 / 收录门槛**：编辑 `config/scoring.yaml`
- **调整话题标签**：编辑 `config/scoring.yaml` + `processor/generate.py`（`ALL_TOPICS`）
- **调整热度权重**：编辑 `processor/hotness.py`
- **增减数据源**：编辑 `config/sources.yaml`
