# 更新日志

本文件记录项目所有重要变更。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

每日内容更新(`chore: daily update`)不在此处记录,可通过 `git log` 查看。

## [Unreleased]

## [0.2.0] - 2026-05-20

### 页面重设计
- 整页改为简约科技风:浅米色背景 + 暖橙强调色(`#ea580c`,致敬 Hacker News),Geist / Geist Mono 字体,卡片式列表
- Sticky 顶栏 + 模糊背景;Logo 方块带橙色实时指示点
- 顶栏右上角文案改为「累计浏览」和「数据来源与筛选」
- 热度星星改用 SVG 矢量图(实心 / 空心),颜色稳定不受浏览器 emoji 渲染影响
- 数据更新时间改为显示最新文章的发布时间(北京时区,无 UTC 后缀),前缀「数据更新时间:」

### 新增
- **数据源扩充**: 新增 12 个 X 账号,含 Fei-Fei Li、Yann LeCun、Andrej Karpathy 等 AI 学者
- 元信息行右侧显示文章发布日期
- 筛选按钮的数量徽章随其他筛选条件实时更新
- 自动清理 30 天前的旧文章
- 顶栏添加累计浏览计数(counterapi.dev)
- 添加「数据来源 & 评分标准」模态弹窗
- 文章列表支持按 热度 / 相关度 / 时间 排序
- 添加 X / Twitter 数据源
- 文章可展开查看原文正文,通过 Jina Reader + trafilatura 备用抓取
- 添加 `rescore_all` 重新评分脚本
- 新增 6 个高价值 RSS 源,最低分数提升至 70
- 添加 GitHub Actions 每日自动运行工作流

### 优化
- 重做热度评分逻辑,提高 HN / X / AI Lab 权重
- 抓取配额按类别均衡,避免 arXiv 挤压其他来源
- 收紧 arXiv 筛选规则
- 对带「AI」关键词的 X 推文采用宽松评分(阈值 60)
- 摘要文本右边距与发布日期对齐

### 修复
- 热度筛选按钮(2★ / 3★ / 4★ / 5★)改为精确匹配,不再「N 及以上」
- 排序与筛选按钮的联动交互正确
- 相对时间(X 分钟 / 小时 / 天前)实时刷新
- 日期筛选改用本地时区,避免 UTC 偏移
- HN 文章正文回填讨论页 URL 与互动统计

### 文档
- 重写 README 与 criteria.md 反映当前项目状态
- 说明 X 账号的选择标准与添加方法

### 内部
- 输出目录切到 `docs/`,启用 GitHub Pages
- 把 DB 和生成结果纳入 git 跟踪
- 推送前 `git pull --rebase` 避免冲突
- 二进制文件冲突改用 `merge -X ours`
- 移除 Reddit 数据源

## [0.1.0] - 2026-05-06

- 项目初始公开版本

---

## 维护说明

每次发版前,把 `[Unreleased]` 下的内容迁移到新版本号区块,并在底部更新版本对比链接。常用分类:

- **新增** — 新功能
- **优化** — 既有功能的改进
- **修复** — Bug 修复
- **样式** — 视觉 / 布局调整
- **文档** — README、注释等文档更新
- **内部** — 重构、构建、CI 等不影响用户的改动
- **移除** — 移除的功能或数据源

[Unreleased]: https://github.com/afeiadian/ai-news-bot/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/afeiadian/ai-news-bot/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/afeiadian/ai-news-bot/releases/tag/v0.1.0
