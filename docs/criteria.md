# AI 资讯日报 — 分类与评分依据

本文档说明系统中所有自动分类和评分的标准、依据及调整方法。

---

## 一、相关度评分（0–100）

**作用**：判断一篇文章是否与 AI 技术领域相关，过滤掉不相关内容。

**评分主体**：DeepSeek AI 模型（deepseek-v4-pro）

**输入内容**：文章标题 + 原文（最多 2000 字符）。原文优先级：
1. Miniflux RSS 自带 content（如 OpenAI/Anthropic/Microsoft Research/PyTorch/SemiAnalysis 等）
2. 若 RSS content 不足（HN/HF/DeepMind），调用 Jina Reader 抓取真实正文
3. Jina 失败时降级到 trafilatura
4. arXiv 用官方 API 获取作者 + 摘要

**收录阈值**：
- 默认 **70** 分（覆盖大部分来源）
- **X 平台单独 60 分**（推文短，AI 相关的简短评论也保留）

**关注领域**：

| 领域 | 涵盖内容 |
|------|---------|
| AI 芯片与硬件 | GPU/NPU/TPU 芯片架构、AI 数据中心、芯片互联（NVLink/InfiniBand）、NVIDIA/AMD/Intel/国产芯片 |
| AI 芯片软件栈 | CUDA/ROCm/XLA 编程框架、cuDNN/cuBLAS 算子库、AI 编译器（TVM/Triton）、Kernel 开发与优化、芯片软件适配 |
| 模型推理与部署 | vLLM/SGLang/TensorRT-LLM/llama.cpp、量化技术（GPTQ/AWQ/FP8）、推理 serving 架构、边缘部署 |
| 模型训练与微调 | 预训练、SFT/RLHF/DPO 对齐、分布式训练（Megatron/DeepSpeed）、LoRA/QLoRA 参数高效微调 |
| AI 开发框架与工具 | LangChain/LlamaIndex/Transformers、Profiling 工具、Benchmark 测评框架 |
| 大模型技术与应用 | 基础大模型架构（Transformer/MoE/SSM）、新模型发布、多模态模型、文生视频、行业应用 |

### 评分质量规则

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

**来源权威性加分**（在收录范围内额外 +10~+20）：
- 顶级 AI 公司官方博客：OpenAI、Anthropic、Google Research、DeepMind、NVIDIA、Meta AI
- 行业领袖 X 发文（内容涉及 AI 技术/产品/趋势）
- 顶级机构论文：Google/Meta/Microsoft/OpenAI/Anthropic 及 MIT/Stanford/CMU/Berkeley 等

**X 推文特别说明**（更宽容评分）：
- 提到 AI 公司/产品/模型/工具的任何内容（哪怕只 1-2 句、提到 Codex/Grok/Claude/Llama 等）→ 60+ 分
- 涉及具体 AI 技术/产品讨论 → 75-90 分
- 完全无关 AI 的个人生活、政治、火箭、单词回复 → ≤ 30 分

**arXiv 论文收录标准**（须满足至少一项才能 ≥ 70）：
1. 有明确 SOTA 声称且附有具体性能数据
2. 作者机构为主流 AI 企业或顶级院校
3. 直接解决工程实践痛点（推理加速、训练效率、量化精度等）
- cs.CL：过滤纯语言学/小型垂直 NLP 模型 → ≤ 40
- cs.CV：过滤传统图像分类/检测/医学影像 → ≤ 35；文生视频/多模态 VLM 正常评分

**如何调整**：
- 关注领域：编辑 `config/scoring.yaml` → `domains`
- 质量规则：编辑 `config/scoring.yaml` → `quality_note`
- 全局阈值：编辑 `config/scoring.yaml` → `min_score`
- X 阈值：编辑 `processor/generate.py` → `x_threshold`

---

## 二、抓取策略：分类配额

每次 Actions 运行从 Miniflux 拉取最多 200 篇未读。**不简单按时间倒序**——因为 arXiv 每天产出几百篇会挤掉其他高价值来源。改为按分类配额：

| 优先级 | 分类 | 每分类上限 | 说明 |
|------|------|------|------|
| 1 | lab | 100 | AI 公司官博（OpenAI/Anthropic/Google 等） |
| 1 | tools | 100 | PyTorch Blog 等 |
| 1 | chip | 100 | NVIDIA / SemiAnalysis |
| 1 | newsletter | 100 | Ahead of AI / Interconnects 等 |
| 1 | hackernews | 100 | HN Top Links |
| 2 | arxiv | 剩余配额 | 用前 5 类抓取后剩余的额度（通常 140-150 篇） |

典型一次运行：60 篇高价值 + 140 篇 arXiv = 200 篇总。

**实现**：`processor/fetch.py` → `fetch_unread_entries()`

---

## 三、话题分类（9 个标签）

**作用**：为每篇文章打上 1–3 个话题标签，支持按话题筛选。

| 话题标签 | 标签颜色 | 涵盖内容 |
|---------|---------|---------|
| 基础大模型 | 蓝色 | 新模型发布、模型能力评测、多模态模型、模型架构创新（MoE/SSM等） |
| 推理部署 | 青绿色 | 推理加速、量化（GPTQ/AWQ/FP8）、vLLM/SGLang/TensorRT-LLM、serving、边缘部署 |
| 训练微调 | 紫色 | 预训练、SFT、RLHF、DPO、分布式训练、数据集构建、参数高效微调 |
| 性能优化 | 深绿色 | 系统级性能优化：算子/Kernel 优化、内存优化、并行策略、CUDA/Triton 优化 |
| 芯片软件栈 | 橙红色 | CUDA/ROCm/XLA、AI 编译器、算子库、Kernel 开发、芯片软件适配 |
| AI芯片硬件 | 棕橙色 | GPU/NPU/TPU 芯片架构、AI 数据中心硬件、芯片互联技术 |
| 开发工具 | 深蓝色 | AI 应用开发框架、SDK、Agent 框架、RAG 工具链、Profiling 工具 |
| 学术论文 | 靛紫色 | arXiv 论文、顶会研究成果、Benchmark 测评报告 |
| 行业资讯 | 深灰色 | 公司动态、产品发布、权威趋势预测与综述、技术路线分析 |

---

## 四、热度评分（1–5 星）

**作用**：反映文章的权威性和社会热度，综合来源权威度与真实互动数据。

**评分公式**：
```
热度星级 = round(来源基础分 + 互动加分)，结果限定在 1–5
```

### 4.1 来源基础分

| 来源分类 | 基础分 | 说明 |
|---------|--------|------|
| AI Lab | 4.0 | 顶级 AI 公司官博（OpenAI/Anthropic/Google 等），权威性最高 |
| Hacker News | 3.5 | 社区精选，能上 HN 本身已证明内容价值 |
| X | 3.0 | 只追踪行业领袖账号，少而精 |
| Newsletter | 3.0 | 专业编辑精选简报 |
| arXiv | 2.5 | 学术论文，质量参差，靠相关度评分筛选 |
| AI Chip | 2.5 | 芯片厂商官方博客 |
| AI Tools | 2.0 | 工具框架博客 |

### 4.2 互动加分（0–2.0）

**Hacker News**（HN Algolia API 取真实点赞数）：

| HN 点赞数 | 加分 |
|----------|------|
| ≥ 500 | +2.0 |
| ≥ 200 | +1.5 |
| ≥ 100 | +1.0 |
| ≥ 30  | +0.5 |
| < 30  | +0.0 |

**X 平台**（点赞 + 转发×2 合并计算）：相同档位 +0.0~+2.0。

### 4.3 计算示例

| 场景 | 计算过程 | 结果 |
|------|---------|------|
| OpenAI 官方发布新模型 | 4.0 + 0 = 4.0 | ★★★★☆ |
| HN 600 点赞技术文章 | 3.5 + 2.0 = 5.5 → 5 | ★★★★★ |
| HN 50 点赞技术文章 | 3.5 + 0.5 = 4.0 | ★★★★☆ |
| Karpathy 高赞推文（1000点赞）| 3.0 + 2.0 = 5.0 | ★★★★★ |
| 行业领袖普通推文 | 3.0 + 0 = 3.0 | ★★★☆☆ |
| arXiv 论文 | 2.5 + 0 = 2.5 → 3 | ★★★☆☆ |

---

### 4.4 X 账号选取与新增

X 平台共追踪 **35 个账号**，涵盖：
- **AI 公司 CEO/创始人**（10 人）：OpenAI、Anthropic、Google DeepMind、xAI、Mistral、SSI、Thinking Machines 等掌门
- **顶级研究者/学者**（14 人）：图灵奖得主（LeCun、Bengio）、Google AI 首席科学家（Jeff Dean）、Stanford HAI 共同负责人（Fei-Fei Li）、DeepLearning.AI 创始人（Andrew Ng）等
- **芯片/系统/工程专家**（4 人）：SemiAnalysis 主笔、MLIR/Mojo 作者、Tenstorrent CEO、llama.cpp 作者
- **官方账号**（6 个）：六大主流 AI 公司
- **论文推荐**（1 个）：@_akhaliq

**新增账号流程**：
1. 在 `config/sources.yaml` → `twitter_accounts` 添加 `- handle: xxx` 条目
2. 用 `python3 -c "from fetch_twitter import _get_user_id; print(_get_user_id('xxx'))"` 验证 handle 有效
3. 下次 Actions 自动开始抓取

---

## 五、来源分类（7 个类别）

| 来源分类 | 颜色 | 当前订阅 |
|---------|------|-----------------|
| AI Lab | 蓝色 | OpenAI、Anthropic、Google Research、Google DeepMind、Meta AI Research、Microsoft Research、Hugging Face |
| AI Chip | 棕橙色 | NVIDIA Blog、NVIDIA Developer Blog、SemiAnalysis |
| AI Tools | 青色 | PyTorch Blog |
| Newsletter | 靛蓝色 | Ahead of AI、Interconnects、Import AI、The Gradient |
| Hacker News | 橙色 | Top Links（通过 RSSHub）|
| arXiv | 紫色 | cs.AI / cs.LG / cs.CL / cs.CV / cs.AR / cs.DC |
| X | 黑色 | 35 个行业领袖账号（详见首页"数据来源 & 评分标准"按钮）|

---

## 六、原文展示

每条资讯摘要下方有「显示原文 ▾」按钮，点击展开（最高 160px，带滚动条）。

| 来源类型 | 原文内容来源 |
|---------|---------|
| X/Twitter | 完整推文正文（fetch_twitter.py 抓取时存入）|
| arXiv | 作者列表 + 论文摘要（arXiv API 实时获取）|
| HN | 文章正文（Jina Reader 抓取真实链接内容）|
| AI Lab（HF/DeepMind） | trafilatura 抓取页面正文（Jina 被限速时降级方案）|
| 其他博客 | Miniflux RSS 自带的 content |
| 暂无内容 | 显示"暂无原文内容"灰色提示 |

原文内容最多显示 2000 字符。

---

## 七、网页交互特性

| 特性 | 说明 |
|------|------|
| 实时时间显示 | "X 分钟/小时/天前"由 JS 基于 ISO 时间戳计算，每次刷新都准确 |
| 本地时区日期 | "今天/昨天/近 N 天"使用浏览器本地时区，跨时区用户也准确 |
| 发布日期 | 每条资讯右下显示发布日期（YYYY-MM-DD，灰色小字），客户端按本地时区格式化 |
| 三维 facet 联动 | 点日期/来源/话题，另外两维的 count 实时重算（不联动自身）|
| 排序升降序 | 点同一排序按钮可切换 ↓ / ↑ |
| 显示原文 | 每条资讯可展开真实原文，带滚动条 |
| 数据来源弹窗 | 顶部按钮打开，展示完整来源 & 评分规则（ESC 或点外部关闭）|
| 累计浏览次数 | 右上角，counterapi.dev 计数 |

---

## 八、内容处理参数

| 参数 | 当前值 | 说明 | 修改位置 |
|------|--------|------|---------|
| 全局收录阈值 | 70 | score < 70 不展示（X 除外） | `config/scoring.yaml` → `min_score` |
| X 单独阈值 | 60 | X 推文较短，单独宽容 | `processor/generate.py` → `x_threshold` |
| 原文显示上限 | 2000 字符 | 展开面板的截取长度 | `processor/generate.py` |
| AI 输入上限 | 2000 字符 | 送给 DeepSeek 的正文长度 | `processor/process.py` |
| 文章采集时间窗 | 2 天 | 只处理最近 N 天发布的文章 | `processor/run.py` → `days_back=2` |
| 单次抓取上限 | 200 篇 | RSS 文章最多处理数 | `processor/run.py` → `limit=200` |
| 高价值分类配额 | 100/分类 | lab/tools/chip/newsletter/HN 每类上限 | `processor/fetch.py` |
| X 每账号上限 | 20 条 | 每个 X 账号最多抓取 | `processor/run.py` → `fetch_twitter_entries` |
| 数据保留天数 | 30 天 | 旧文章自动删除并 VACUUM | `processor/run.py` → `prune_old_articles(days=30)` |
| 每页显示数量 | 30 条 | 网页分页大小 | `web/template.html` → `PAGE_SIZE` |
| 每日更新时间 | UTC 07:00 / 北京 15:00 | GitHub Actions 触发（实际可能延迟 1-3 小时）| `.github/workflows/daily_update.yml` |

---

## 九、配置文件速查

| 文件 | 职责 |
|------|------|
| `config/scoring.yaml` | 评分领域、收录阈值、质量规则、话题分类定义 |
| `config/sources.yaml` | RSS 订阅源列表、arXiv 分类、X 平台账号 |
| `processor/hotness.py` | 热度评分：来源基础分表、互动数加分档位 |
| `processor/process.py` | AI 处理提示词、内容截取长度、摘要要求 |
| `processor/fetch.py` | 按分类配额拉取，避免 arXiv 挤掉高价值来源 |
| `processor/fetch_twitter.py` | X 平台推文抓取（GraphQL API + Cookie 认证）|
| `processor/fetch_content.py` | 原文抓取（Jina Reader → trafilatura 降级）|
| `processor/storage.py` | SQLite 操作 + 30 天自动清理 + VACUUM |
| `processor/generate.py` | 页面渲染：分类/话题颜色、原文按钮、数据来源弹窗 |
| `web/template.html` | 前端交互：筛选 + 排序 + 实时 count + 原文展开 |
| `.env` | API Keys、服务地址、X Cookie（不上传 GitHub）|
