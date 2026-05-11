# AI 资讯日报 — 分类与评分依据

本文档说明系统中所有自动分类和评分的标准、依据及调整方法。

---

## 一、相关度评分（0–100%）

**作用**：判断一篇文章是否与 AI 技术领域相关，过滤掉不相关内容。

**评分主体**：DeepSeek AI 模型（deepseek-v4-pro）

**输入内容**：文章标题 + 正文前 2000 字符

**收录阈值**：score ≥ 70 的文章才进入数据库展示

**关注领域**：AI 模型综合判断与以下 6 个技术领域的相关程度：

| 领域 | 涵盖内容 |
|------|---------|
| AI 芯片与硬件 | GPU/NPU/TPU 芯片架构、AI 数据中心硬件、芯片互联（NVLink/InfiniBand）、NVIDIA/AMD/Intel/国产芯片 |
| AI 芯片软件栈 | CUDA/ROCm/XLA 编程框架、cuDNN/cuBLAS 算子库、AI 编译器（TVM/Triton）、Kernel 开发与优化、芯片软件适配 |
| 模型推理与部署 | vLLM/SGLang/TensorRT-LLM/llama.cpp、量化技术（GPTQ/AWQ/FP8）、推理 serving 架构、边缘部署 |
| 模型训练与微调 | 预训练、SFT/RLHF/DPO 对齐、分布式训练（Megatron/DeepSpeed）、LoRA/QLoRA 参数高效微调 |
| AI 开发框架与工具 | LangChain/LlamaIndex/Transformers、Profiling 工具、Benchmark 测评框架 |
| 大模型技术与应用 | 基础大模型架构（Transformer/MoE/SSM）、新模型发布、多模态模型、文生视频、行业应用 |

### 评分质量规则

评分时同时考虑技术相关度与内容质量：

**收录范围**（与以下方向无关的内容直接给分 ≤ 30）：
- AI 芯片与硬件
- AI 芯片软件栈
- 大语言模型技术
- AI 基础设施
- AI 产品与行业

**明确排除**（直接给分 ≤ 30）：
- 非 AI 领域科技新闻（手机、电动车、区块链等）
- 纯商业/财经/政治新闻
- 将 AI 作为噱头的边缘应用报道
- 传统 CV/NLP 任务（目标检测、医学影像等与大模型无关的内容）
- X 平台上的个人生活、时事评论、非 AI 话题

**来源权威性加分**（在收录范围内，额外 +10~+20）：
- 顶级 AI 公司官方博客：OpenAI、Anthropic、Google Research、DeepMind、NVIDIA、Meta AI
- 行业领袖 X 发文（内容涉及 AI 技术/产品/趋势）
- 顶级机构论文：Google/Meta/Microsoft/OpenAI/Anthropic 及 MIT/Stanford/CMU/Berkeley 等

**arXiv 论文收录标准**（须满足至少一项）：
1. 有明确 SOTA 声称且附有具体性能数据
2. 作者机构为主流 AI 企业或顶级院校
3. 直接解决工程实践痛点（推理加速、训练效率、量化精度等）

**如何调整**：
- 修改关注领域：编辑 `config/scoring.yaml` → `domains`
- 修改质量规则：编辑 `config/scoring.yaml` → `quality_note`
- 修改收录阈值：编辑 `config/scoring.yaml` → `min_score`

---

## 二、话题分类（9 个标签）

**作用**：为每篇文章打上 1–3 个话题标签，支持按话题筛选浏览。

**分类主体**：DeepSeek AI 模型，根据标题、中文标题和摘要综合判断。

| 话题标签 | 标签颜色 | 涵盖内容 |
|---------|---------|---------|
| 基础大模型 | 蓝色 | 新模型发布、模型能力评测、多模态模型、模型架构创新（MoE/SSM等） |
| 推理部署 | 青绿色 | 推理加速、量化（GPTQ/AWQ/FP8）、vLLM/SGLang/TensorRT-LLM、serving架构、边缘部署 |
| 训练微调 | 紫色 | 预训练、SFT、RLHF、DPO、分布式训练、数据集构建、参数高效微调 |
| 性能优化 | 深绿色 | 系统级性能优化：算子/Kernel优化、内存优化、并行策略、CUDA/Triton优化 |
| 芯片软件栈 | 橙红色 | CUDA/ROCm/XLA、AI 编译器、算子库、Kernel开发、芯片软件适配 |
| AI芯片硬件 | 棕橙色 | GPU/NPU/TPU芯片架构、AI数据中心硬件、芯片互联技术 |
| 开发工具 | 深蓝色 | AI应用开发框架、SDK、Agent框架、RAG工具链、Profiling工具 |
| 学术论文 | 靛紫色 | arXiv论文、顶会研究成果、Benchmark测评报告 |
| 行业资讯 | 深灰色 | 公司动态、产品发布、权威趋势预测与综述、技术路线分析 |

**如何调整**：
- 修改话题描述：编辑 `config/scoring.yaml` → `topics`
- 新增话题：在 `scoring.yaml` 添加条目，同步更新：
  - `processor/generate.py` → `ALL_TOPICS` 列表
  - `processor/generate.py` → `topic_color()` 函数
- 对历史文章重新分类：`python3 processor/backfill_topic.py`

---

## 三、热度评分（1–5 星）

**作用**：反映文章的权威性和社会热度，综合来源权威度与真实互动数据。

**评分公式**：
```
热度星级 = round(来源基础分 + 互动加分)，结果限定在 1–5
```

### 3.1 来源基础分

| 来源分类 | 基础分 | 说明 |
|---------|--------|------|
| AI Lab | 4.0 | 顶级 AI 公司官博（OpenAI/Anthropic/Google等），权威性最高 |
| Hacker News | 3.5 | 社区精选，能上 HN 本身已证明内容价值 |
| X | 3.0 | 只追踪行业领袖账号，少而精 |
| Newsletter | 3.0 | 专业编辑精选简报 |
| arXiv | 2.5 | 学术论文，质量参差，靠相关度评分筛选 |
| AI Chip | 2.5 | 芯片厂商官方博客 |
| AI Tools | 2.0 | 工具框架博客 |

### 3.2 互动加分（0–2.0）

**Hacker News**（取文章 HN 点赞数）：

| HN 点赞数 | 加分 |
|----------|------|
| ≥ 500 | +2.0 |
| ≥ 200 | +1.5 |
| ≥ 100 | +1.0 |
| ≥ 30  | +0.5 |
| < 30  | +0.0 |

**X 平台**（取点赞数 + 转发数×2 合并计算）：

| 综合互动分 | 加分 |
|----------|------|
| ≥ 500 | +2.0 |
| ≥ 200 | +1.5 |
| ≥ 100 | +1.0 |
| ≥ 30  | +0.5 |
| < 30  | +0.0 |

**数据来源**：
- Hacker News：HN Algolia API，按文章标题搜索获取真实点赞数
- X：GraphQL API 返回的 `favorite_count`（点赞）和 `retweet_count`（转发）

### 3.3 计算示例

| 场景 | 计算过程 | 结果 |
|------|---------|------|
| OpenAI 官方发布新模型 | 4.0 + 0 = 4.0 | ★★★★☆ |
| HN 600 点赞技术文章 | 3.5 + 2.0 = 5.5 → 5 | ★★★★★ |
| HN 50 点赞技术文章 | 3.5 + 0.5 = 4.0 | ★★★★☆ |
| Karpathy 高赞推文（1000点赞）| 3.0 + 2.0 = 5.0 | ★★★★★ |
| 行业领袖普通推文 | 3.0 + 0 = 3.0 | ★★★☆☆ |
| arXiv 论文 | 2.5 + 0 = 2.5 → 3 | ★★★☆☆ |

**如何调整**：
- 修改各来源基础分：编辑 `processor/hotness.py` → `SOURCE_BASE`
- 修改互动数加分档位：编辑 `processor/hotness.py` → `ENGAGEMENT_TIERS`
- 对历史文章重新评分：`python3 processor/backfill_hotness.py`

---

## 四、来源分类（8 个类别）

**作用**：标识文章来自哪个平台类型，支持在筛选栏按大类过滤。

| 来源分类 | 颜色 | 当前订阅的具体来源 |
|---------|------|-----------------|
| AI Lab | 蓝色 | OpenAI、Anthropic、Google Research、Google DeepMind、Meta AI Research、Microsoft Research、Hugging Face |
| AI Chip | 棕橙色 | NVIDIA Blog、NVIDIA Developer Blog、SemiAnalysis |
| arXiv | 紫色 | cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |
| Hacker News | 橙色 | Top Links（通过 RSSHub 获取） |
| Newsletter | 靛蓝色 | Ahead of AI、Interconnects、Import AI、The Gradient |
| AI Tools | 青色 | PyTorch Blog |
| X | 黑色 | 22 个行业领袖账号（详见 README） |

**如何调整**：
- 增减 RSS 订阅源：编辑 `config/sources.yaml`，运行 `python3 processor/setup_feeds.py`
- 增减 X 账号：编辑 `config/sources.yaml` → `twitter_accounts`
- 新增来源分类：修改 `processor/fetch.py` → `CATEGORY_MAP`，同步更新 `processor/generate.py` → `ALL_CATS` 和 `category_color()`

---

## 五、原文展示

每条资讯摘要下方有「显示原文 ▾」按钮，点击展开（最高 160px，带滚动条）：

| 来源类型 | 原文内容 |
|---------|---------|
| X/Twitter | 完整推文正文 |
| arXiv | 作者列表 + 论文摘要（通过 arXiv API 获取）|
| HN/博客/Newsletter | 文章描述/节选（来自 RSS feed）|
| 暂无内容 | 显示"暂无原文内容"灰色提示 |

原文内容最多显示 2000 字符。新抓取的文章自动存储原文内容，历史文章可通过补填脚本更新。

---

## 六、内容处理参数

| 参数 | 当前值 | 说明 | 修改位置 |
|------|--------|------|---------|
| 相关度收录阈值 | 70 | score < 70 不展示 | `config/scoring.yaml` → `min_score` |
| AI 输入内容长度 | 2000 字符 | 正文截取长度 | `processor/process.py` → `content[:2000]` |
| 原文显示上限 | 2000 字符 | 展开原文的截取长度 | `processor/generate.py` |
| 摘要篇幅 | 3–5 句 | 中文摘要目标句数 | `processor/process.py` → prompt |
| 文章采集时间范围 | 2 天 | 只处理最近 N 天内的文章 | `processor/run.py` → `days_back=2` |
| 每次处理上限 | 200 篇 | 单次运行最多处理 RSS 文章数 | `processor/run.py` → `limit=200` |
| X 每账号抓取上限 | 20 条 | 每个 X 账号最多抓取推文数 | `processor/run.py` → `fetch_twitter_entries` |
| 每页显示数量 | 30 条 | 网页分页大小 | `web/template.html` → `PAGE_SIZE` |
| 每日更新时间 | 09:00 北京时间 | GitHub Actions 触发时间（UTC 01:00）| `.github/workflows/daily_update.yml` |

---

## 七、配置文件速查

| 文件 | 职责 |
|------|------|
| `config/scoring.yaml` | 评分领域、收录阈值、质量规则、话题分类定义 |
| `config/sources.yaml` | RSS 订阅源列表、arXiv 分类、X 平台账号 |
| `processor/hotness.py` | 热度评分：来源基础分表、互动数加分档位 |
| `processor/process.py` | AI 处理提示词、内容截取长度、摘要要求 |
| `processor/fetch.py` | RSS 拉取逻辑、来源名称清洗 |
| `processor/fetch_twitter.py` | X 平台推文抓取（直接调 GraphQL API） |
| `processor/generate.py` | 页面展示：`ALL_TOPICS`、`ALL_CATS`、颜色映射 |
| `web/template.html` | 页面交互：筛选按钮、分页、原文展开、样式 |
| `.env` | API Keys、服务地址、X Cookie（不上传 GitHub）|
