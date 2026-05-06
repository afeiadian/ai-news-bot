# AI 资讯机器人 — 分类与评分依据

本文档说明系统中所有自动分类和评分的标准、依据及调整方法。如需修改任何标准，对应的配置文件或代码位置均已注明。

---

## 一、相关度评分（0–100%）

**作用**：判断一篇文章是否与 AI 技术领域相关，过滤掉不相关内容。

**评分主体**：DeepSeek AI 模型（deepseek-v4-pro）

**输入内容**：文章标题 + 正文前 2000 字符

**收录阈值**：score ≥ 60 的文章才进入数据库展示，低于 60 直接丢弃

**评分依据**：AI 模型综合判断与以下 6 个技术领域的相关程度：

| 领域 | 涵盖内容 |
|------|---------|
| 大语言模型 | LLM 相关技术、研究、产品发布，包括 GPT、Claude、Gemini、Llama、Qwen 等模型 |
| AI 开发工具与框架 | AI 应用开发框架、SDK、API，如 LangChain、LlamaIndex、vLLM、Ollama、SGLang 等 |
| 推理优化与部署 | 模型推理加速、量化、蒸馏、边缘部署、serving 架构、TensorRT 等 |
| 训练与微调技术 | 预训练、SFT、RLHF、DPO、数据集构建、对齐技术、分布式训练 |
| AI 芯片与硬件 | GPU、NPU、TPU 等 AI 芯片，数据中心，互联技术，NVIDIA、AMD、Intel、自研芯片 |
| 多模态与 AI Agent | 多模态模型（视觉/语音/视频）、AI Agent 框架、工具调用、自主系统 |

**如何调整**：
- 修改关注领域：编辑 `config/scoring.yaml` → `domains`，无需改代码
- 修改收录阈值：编辑 `config/scoring.yaml` → `min_score`（数字越大收录越严格）

---

## 二、话题分类（8 个标签）

**作用**：为每篇文章打上 1–3 个话题标签，支持按话题筛选浏览。

**分类主体**：DeepSeek AI 模型，根据标题、中文标题和摘要综合判断。

**规则**：一篇文章可同时属于多个话题（最多 3 个），例如一篇讲 vLLM 的文章可同时标注「推理部署」+「性能优化」+「开发工具」。

| 话题标签 | 标签颜色 | 涵盖内容 |
|---------|---------|---------|
| 基础大模型 | 蓝色 | 新模型发布、模型能力评测、多模态模型、模型架构创新 |
| 推理部署 | 青绿色 | 推理加速、量化、vLLM/ollama/TensorRT、serving、边缘部署 |
| 性能优化 | 深绿色 | 算子优化、内存优化、并行策略、吞吐量提升、延迟降低、CUDA 优化 |
| 训练微调 | 紫色 | 预训练、SFT、RLHF、数据集、对齐技术 |
| 开发工具 | 深蓝色 | SDK、框架、API、Agent 框架、RAG、工作流 |
| AI芯片硬件 | 棕橙色 | GPU、NPU、TPU、芯片架构、数据中心、互联技术 |
| 学术论文 | 靛紫色 | arXiv 论文、研究成果、Benchmark 测评 |
| 行业资讯 | 深灰色 | 公司动态、融资、产品发布、政策法规、市场分析 |

**如何调整**：
- 修改话题描述：编辑 `config/scoring.yaml` → `topics`
- 新增话题：在 `scoring.yaml` 添加条目，同时在以下两处同步添加同名条目：
  - `processor/generate.py` → `ALL_TOPICS` 列表（控制页面显示）
  - `processor/backfill_topic.py` → `TOPICS` 列表（控制补填脚本）
  - 并在 `generate.py` → `topic_color()` 中添加对应颜色
- 调整后对历史文章重新分类：`python3 processor/backfill_topic.py`

---

## 三、热度评分（1–5 星）

**作用**：反映文章的社会热度和重要性，综合来源权威度与真实社区互动数据。

**评分公式**：
```
热度星级 = round(来源基础分 + 互动加分)，结果限定在 1–5
```

### 3.1 来源基础分（1.5–3.0）

| 来源分类 | 基础分 | 说明 |
|---------|--------|------|
| AI Lab | 3.0 | Anthropic、OpenAI、DeepMind 等顶级机构官方博客 |
| arXiv | 2.5 | 学术论文，来源权威 |
| Newsletter | 2.5 | 高质量精选简报（SemiAnalysis、Import AI、The Gradient 等） |
| AI Chip | 2.5 | 芯片厂商官方博客（NVIDIA Blog 等） |
| AI Tools | 2.0 | 工具框架博客（Hugging Face Blog 等） |
| Hacker News | 2.0 | 社区聚合，质量主要由互动数决定 |
| Reddit | 1.5 | 社区讨论，质量主要由互动数决定 |

### 3.2 互动加分（0–2.0）

适用于 **Hacker News**（取文章点赞数）和 **Reddit**（取帖子 score）：

| 互动数 | 加分 |
|--------|------|
| ≥ 500 | +2.0 |
| ≥ 200 | +1.5 |
| ≥ 100 | +1.0 |
| ≥ 30  | +0.5 |
| < 30  | +0.0 |

**数据来源**：
- Hacker News：HN Algolia API（`hn.algolia.com`），按文章标题搜索获取真实点赞数
- Reddit：Reddit JSON API，按帖子 ID 获取真实 score
- 其他来源（arXiv、博客等）：无互动数据，仅凭基础分

### 3.3 计算示例

| 场景 | 计算过程 | 结果 |
|------|---------|------|
| Anthropic 官方发布新模型 | 3.0 + 0 = 3.0 | ★★★☆☆ |
| HN 上 600 点赞的技术文章 | 2.0 + 2.0 = 4.0 | ★★★★☆ |
| HN 上 50 点赞的技术文章 | 2.0 + 1.0 = 3.0 | ★★★☆☆ |
| Reddit r/LocalLLaMA 250 分帖子 | 1.5 + 1.5 = 3.0 | ★★★☆☆ |
| arXiv 论文 | 2.5 + 0 = 2.5 → 3 | ★★★☆☆ |
| Reddit 冷门帖子（< 30 分） | 1.5 + 0 = 1.5 → 2 | ★★☆☆☆ |

**如何调整**：
- 修改各来源基础分：编辑 `processor/hotness.py` → `SOURCE_BASE`
- 修改互动数加分档位：编辑 `processor/hotness.py` → `ENGAGEMENT_TIERS`
- 调整后对历史文章重新评分：`python3 processor/backfill_hotness.py`

---

## 四、来源分类（7 个类别）

**作用**：标识文章来自哪个平台类型，支持在筛选栏按大类过滤。文章列表中显示具体网站名（如 `r/MachineLearning`、`NVIDIA Blog`）。

| 来源分类 | 颜色 | 当前订阅的具体来源 |
|---------|------|-----------------|
| AI Lab | 蓝色 | Hugging Face Blog |
| arXiv | 紫色 | cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |
| AI Tools | 青色 | （待补充） |
| AI Chip | 棕橙色 | NVIDIA Blog、SemiAnalysis |
| Hacker News | 橙色 | Top Links（通过 RSSHub 获取） |
| Reddit | 红色 | r/MachineLearning / r/LocalLLaMA / r/artificial / r/Semiconductors |
| Newsletter | 靛蓝色 | Import AI、The Gradient |

**如何调整**：
- 增减具体订阅源：编辑 `config/sources.yaml`，运行 `python3 processor/setup_feeds.py`
- 新增来源分类：修改 `processor/fetch.py` → `CATEGORY_MAP`，同步更新 `processor/generate.py` → `ALL_CATS` 和 `category_color()`

---

## 五、内容处理参数

| 参数 | 当前值 | 说明 | 修改位置 |
|------|--------|------|---------|
| 相关度收录阈值 | 60 | score < 60 直接丢弃 | `config/scoring.yaml` → `min_score` |
| AI 输入内容长度 | 2000 字符 | 正文截取长度，影响分析质量 | `processor/process.py` → `content[:2000]` |
| 摘要篇幅 | 3–5 句 | 中文摘要目标句数 | `processor/process.py` → prompt |
| 文章采集时间范围 | 2 天 | 只处理最近 N 天内的文章 | `processor/run.py` → `days_back=2` |
| 每次处理上限 | 200 篇 | 单次运行最多处理文章数 | `processor/run.py` → `limit=200` |
| 每页显示数量 | 30 条 | 网页分页大小 | `web/template.html` → `PAGE_SIZE` |

---

## 六、配置文件速查

| 文件 | 职责 |
|------|------|
| `config/scoring.yaml` | 相关度评分的关注领域、收录阈值、话题分类定义 |
| `config/sources.yaml` | RSS 订阅源列表、arXiv 分类、Reddit 版块、X 账号 |
| `processor/hotness.py` | 热度评分：来源基础分表、互动数加分档位表 |
| `processor/process.py` | AI 处理提示词、内容截取长度、摘要篇幅要求 |
| `processor/generate.py` | 页面展示：`ALL_TOPICS`、`ALL_CATS`、颜色映射函数 |
| `processor/fetch.py` | 采集时间范围、来源名称清洗规则（`clean_source_name`） |
| `web/template.html` | 页面交互：筛选按钮、分页逻辑、样式 |
| `.env` | API Keys、服务地址（不上传 GitHub） |
