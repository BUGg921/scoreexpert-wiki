# ScoreExpert 部署经验 Wiki

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/BUGg921/scoreexpert-wiki)

这是一个使用 Markdown 与 `[[wikilinks]]` 维护的 ScoreExpert GPU 部署经验库。它把不可变原始来源、综合知识页和维护规则分开保存，可直接使用 Obsidian、VS Code 或普通文本编辑器阅读。

核心目标是把历史验证成本沉淀为可复用经验：新场景同时命中目标总览规则和对应 raw 场景边界时，直接推理部署策略，不要求为每次部署重新运行真实 Evaluation。Evaluation、仿真或人工审核主要用于越界补库和冲突处理。

## 快速开始

- 从 [index.md](index.md) 查看当前经验目录；初始化状态下目录为空。
- 输入第一条经验前，阅读 [SCHEMA.md](SCHEMA.md) 中的页面、标签、来源和置信度规则。
- 使用 [`$maintain-scoreexpert-wiki`](.codex/skills/maintain-scoreexpert-wiki/SKILL.md) 导入新的来源和经验。

## 目录

```text
raw/          不可变来源快照
entities/     实体页
concepts/     部署总库和按优化目标组织的经验总览
comparisons/  场景与策略对比
queries/      值得沉淀的查询结论
outputs/      暂不写入经验库的独立分析结果
index.md      全部知识页索引
log.md        追加式维护日志
SCHEMA.md     Wiki 结构与更新契约
```

## 健康检查

```bash
python3 scripts/lint_wiki.py
```

检查范围包括 frontmatter、标签、孤立页、断链、索引完整性、原始快照 SHA-256、上游来源漂移、页面大小和日志轮换。

## 当前经验格式

经验库采用“优化目标 × 异构范围”的二维结构：

1. 一级入口：**延迟优先型、稳定优先型**。
2. 二级场景：**同构基线、局部异构、分布式异构**。

完整字段与当前证据覆盖见 [ScoreExpert 部署经验总库](concepts/deployment-objective-knowledge-framework.md)。总库永久保留延迟优先和稳定优先的完整框架；当前稳定优先分支缺少直接 Evaluation，只保留结构、对照场景和验证缺口，不生成默认部署结论。

三类二级场景分别是：

1. **同构基线**：无已知异构设备时的正常部署对照。
2. **局部异构**：异常集中在单个局部区域时的污染限制与隔离。
3. **分布式异构**：异常跨节点、亲和组或副本分布时的均衡与对称映射。

同构基线、局部异构和分布式异构统一按“场景定义 → 并行策略 → 原因 → 场景案例”组织。“并行策略”写成“触发条件 + `PP/TP/DP/MBN`、`TP:DP` 数值结果 + 拓扑映射”，“原因”解释条件为什么会导向该参数组合，“场景案例”链接对应 raw 场景来源。

当前采用“总经验库 → 优化目标总览 → raw 场景来源”的结构：目标总览给出可召回的场景定义、数值策略和原因；raw 来源保存实验条件、Score 代码、具体映射和结论边界。延迟/稳定仍是查询入口，同构/局部异构/分布式异构仍是场景分类。

```text
concepts/
├── deployment-objective-knowledge-framework.md  # 完整部署经验总库
└── latency-first-experience-summary.md           # 延迟优先三类场景策略与原因

raw/articles/
├── homogeneous-32gpu-deployment-analysis-2026-07-22.md
├── single-slow-gpu-deployment-analysis-2026-07-22.md
├── two-slow-gpu-deployment-analysis-2026-07-22.md
└── four-slow-gpu-deployment-analysis-2026-07-22.md
```

## 项目内 Codex Skill

打开本项目作为 Codex 工作目录后，可以使用 [`$maintain-scoreexpert-wiki`](.codex/skills/maintain-scoreexpert-wiki/SKILL.md) 导入来源、查询或更新经验、处理冲突、运行健康检查，以及在明确要求时维护 Git 提交。

## 维护流程

1. 在 `raw/` 新增带日期和 SHA-256 的来源快照，不修改旧快照。
2. 更新或新增知识页，补齐至少两个 Wiki 链接。
3. 同步更新 `index.md`，并向 `log.md` 追加操作记录。
4. 运行健康检查；确认无结构错误后提交 Git 变更。

## 经验库演化演示

四个场景的统一模板源文档，以及“正常卡 + 单慢卡 → 加入两慢卡 → 加入四慢卡”的筛选前后过程，保存在 [outputs/experience-evolution-demo/README.md](outputs/experience-evolution-demo/README.md)。这些文件是可审核的演示快照，不会自动升级为正式经验。
