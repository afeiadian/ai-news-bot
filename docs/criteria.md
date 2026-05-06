# AI 资讯机器人 — 分类与评分依据

本文档说明系统中所有自动分类和评分的标准、依据及调整方法。

---

## 一、相关度评分（0–100 分）

**作用**：判断一篇文章是否与 AI 技术领域相关，过滤掉不相关内容。

**评分主体**：DeepSeek AI 模型（deepseek-v4-pro）

**收录阈值**：score ≥ 60 的文章才进入数据库展示，低于 60 的直接丢弃。

**评分依据**：AI 模型根据文章标题和正文前 800 字，判断与以下技术领域的相关程度：

| 领域 | 涵盖内容 |
|------|---------|
| 大语言模型 | LLM 相关技术、研究、产品发布，包括 GPT、Claude、Gemini、Llama、Qwen 等模型 |
| AI 开发工具与框架 | AI 应用开发框架、SDK、API，如 LangChain、LlamaIndex、vLLM、Ollama、SGLang 等 |
| 推理优化与部署 | 模型推理加速、量化、蒸馏、边缘部署、serving 架构、TensorRT 等 |
| 训练与微调技术 | 预训练、SFT、RLHF、DPO、数据集构建、对齐技术、分布式训练 |
| AI 芯片与硬件 | GPU、NPU、TPU 等 AI 芯片，数据中心，互联技术，NVIDIA、AMD、Intel、自研芯片 |
| 多模态与 AI Agent | 多模态模型（视觉/语音/视频）、AI Agent 框架、工具调用、自主系统 |

**如何调整**：编辑 `config/scoring.yaml` 中的 `domains` 列表，增删领域或修改描述即可，无需改代码。调整 `min_score` 可控制收录严格程度。

---

## 二、话题分类（8 个标签）

**作用**：为每篇文章打上 1–3 个话题标签，支持按话题筛选浏览。

**分类主体**：DeepSeek AI 模型，根据标题、中文标题和摘要综合判断。

| 话题标签 | 涵盖内容 |
|---------|---------|
| 基础大模型 | 新模型发布、模型能力评测、多模态模型、模型架构创新 |
| 推理部署 | 推理加速、量化、vLLM/ollama/TensorRT、serving、边缘部署 |
| 性能优化 | 推理或训练的性能优化技术，包括算子优化、内存优化、并行策略、吞吐量提升、延迟降低、CUDA 优化等 |
| 训练微调 | 预训练、SFT、RLHF、数据集、对齐技术 |
| 开发工具 | SDK、框架、API、Agent 框架、RAG、工作流 |
| AI芯片硬件 | GPU、NPU、TPU、芯片架构、数据中心、互联技术 |
| 学术论文 | arXiv 论文、研究成果、Benchmark 测评 |
| 行业资讯 | 公司动态、融资、产品发布、政策法规、市场分析 |

**注意**：一篇文章可同时拥有多个话题标签（最多 3 个）。

**如何调整**：
- 修改话题描述：编辑 `config/scoring.yaml` 中的 `topics` 列表
- 新增话题：在 `scoring.yaml` 添加条目，同时在 `processor/generate.py` 的 `ALL_TOPICS` 列表中添加同名条目，并在 `processor/backfill_topic.py` 的 `TOPICS` 列表中添加
- 调整后对历史文章重新分类：运行 `python3 processor/backfill_topic.py`

---

## 三、热度评分（1–5 星）

**作用**：反映文章的社会热度和重要性，综合来源权威度与真实社区互动数据。

**评分公式**：
```
热度星级 = round(来源基础分 + 互动加分)，范围限定在 1–5
```

### 3.1 来源基础分（1.5–3.0）

| 来源分类 | 基础分 | 说明 |
|---------|--------|------|
| AI Lab | 3.0 | Anthropic、OpenAI、DeepMind 等顶级机构官方博客 |
| arXiv | 2.5 | 学术论文，来源权威 |
| Newsletter | 2.5 | 高质量精选简报（The Batch、SemiAnalysis 等） |
| AI Chip | 2.5 | 芯片厂商官方博客（NVIDIA、Groq 等） |
| AI Tools | 2.0 | 工具框架博客（Hugging Face、vLLM 等） |
| Hacker News | 2.0 | 社区聚合，质量由互动数决定 |
| Reddit | 1.5 | 社区讨论，质量由互动数决定 |

### 3.2 互动加分（0–2.0）

适用于 **Hacker News**（取点赞数）和 **Reddit**（取帖子 score）：

| 互动数 | 加分 |
|--------|------|
| ≥ 500 | +2.0 |
| ≥ 200 | +1.5 |
| ≥ 100 | +1.0 |
| ≥ 30  | +0.5 |
| < 30  | +0.0 |

**数据来源**：
- Hacker News：通过 HN Algolia API（`hn.algolia.com`）按文章标题搜索，获取真实点赞数
- Reddit：通过 Reddit JSON API 按帖子 ID 获取真实 score

### 3.3 最终热度示例

| 场景 | 计算 | 结果 |
|------|------|------|
| Anthropic 官方发布 Claude 新版 | 3.0 + 0 = 3.0 | ★★★☆☆ |
| HN 上 600 点赞的 AI 技术文章 | 2.0 + 2.0 = 4.0 | ★★★★☆ |
| Reddit r/LocalLLaMA 250 分帖子 | 1.5 + 1.5 = 3.0 | ★★★☆☆ |
| arXiv 论文 | 2.5 + 0 = 2.5 → 3 | ★★★☆☆ |

**如何调整**：编辑 `processor/hotness.py` 中的 `SOURCE_BASE` 和 `ENGAGEMENT_TIERS` 常量。调整后对历史文章重新评分：运行 `python3 processor/backfill_hotness.py`

---

## 四、来源分类（7 个类别）

**作用**：标识文章来自哪个平台/类型的来源，支持按来源筛选。

| 分类标签 | 颜色 | 对应数据源 |
|---------|------|-----------|
| AI Lab | 蓝色 | Anthropic、OpenAI、DeepMind、Meta AI 等官方博客 |
| arXiv | 紫色 | cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |
| AI Tools | 青色 | Hugging Face、vLLM Blog 等开发工具博客 |
| AI Chip | 橙棕色 | NVIDIA、Groq、Cerebras、SemiAnalysis 等 |
| Hacker News | 橙色 | HN Top Links（通过 RSSHub 获取） |
| Reddit | 红色 | r/MachineLearning / r/LocalLLaMA / r/artificial / r/Semiconductors |
| Newsletter | 靛蓝色 | Import AI、The Gradient、The Batch 等 |

**如何调整**：编辑 `config/sources.yaml` 增减具体订阅源；如需新增分类，修改 `processor/fetch.py` 中的 `CATEGORY_MAP` 并在 `processor/generate.py` 的 `ALL_CATS` 和 `category_color()` 中同步添加。

---

## 五、配置文件速查

| 文件 | 控制内容 |
|------|---------|
| `config/scoring.yaml` | 相关度评分领域、收录阈值、话题分类定义 |
| `config/sources.yaml` | RSS 订阅源、arXiv 分类、Reddit 版块、X 账号 |
| `processor/hotness.py` | 热度评分：来源基础分、互动数加分档位 |
| `processor/generate.py` | 页面展示：话题/来源列表、颜色映射 |
| `.env` | API Keys、服务地址（不上传 GitHub） |
