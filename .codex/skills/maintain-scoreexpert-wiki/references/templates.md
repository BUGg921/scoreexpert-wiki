# ScoreExpert Wiki 模板

## Raw 来源快照

````markdown
---
source_url:
source_path: /original/path
ingested: YYYY-MM-DD
sha256: <Markdown 正文 SHA-256>
original_sha256: <原文件 SHA-256>
---

# 原始来源：标题

> 导入时间、原路径和用途说明。

```text
完整来源内容
```
````

## 知识页 frontmatter

```markdown
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [scoreexpert, deployment]
sources: [raw/articles/source.md]
confidence: high | medium | low
contested: false
contradictions: []
---
```

## 历史兼容的正式经验页面（当前结构不创建）

仅用于读取或迁移旧项目中的经验卡；当前项目不创建此层，场景规则写入目标总览，场景细节写入 raw 来源。若迁移时暂时保留旧卡，文件位置必须是 `concepts/<experience_category>/<slug>.md`。

```markdown
---
title: <经验标题>
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept
tags: [scoreexpert, deployment, experience, <与 experience_category 对应的分类标签>]
sources: [raw/articles/source.md]
confidence: high | medium | low
contested: false
contradictions: []
experience_category: homogeneous-baseline | local-heterogeneity | distributed-heterogeneity
status: active | superseded | unverified | partially_supported | supported | refuted | mixed
optimization_priority: latency-first | stability-first
admitted_by: <审核主体；active 必填>
admitted_at: YYYY-MM-DD # active 必填
---

# 标题

## 1. 场景描述

- **资源拓扑**：<总卡数、每节点卡数、亲和组和可用卡范围>
- **异构分布**：<慢卡数量、位置、速度倍率和分布；同构场景写明无慢卡>
- **模型与映射约束**：<模型、batch、显存、搜索空间和 rank/group 映射能力>
- **硬匹配条件**：<允许直接召回本经验的目标、拓扑、异构和模型条件>
- **不适用条件**：<会停止匹配本经验的场景变化，并链接应切换的经验卡>

## 2. 具体的并行策略

### 部署策略

```text
active_gpu=?
PP=?, TP=?, DP=?, MBN=?
映射：<rank、TP group、DP replica 或 PP stage 映射>
执行：<把参数和映射落地的关键动作>
```

### 部署经验

- **卡的数量**：<卡数选择规则、拓扑完整性要求和本场景直接采用的 active_gpu>
- **TP**：<TP group 的边界、选择规则、作用与失效条件>
- **TP/PP 或 TP/DP**：<两个维度的联动关系、权衡和切换条件>
- **DP**：<replica 数量、映射、等待或均衡规则>
- **PP/MBN**：<流水线深度与 microbatch 的联动规则>

### 失效条件与回退

- **运行时失效条件**：<OOM、通信、skew、慢 stage 或其他护栏触发>
- **回退策略**：<失效后采用的参数调整或替代部署方案>

```

该模板仅用于兼容旧卡，不作为当前项目的新建模板。迁移旧卡时，正文只允许“场景描述”和“具体的并行策略”两个二级标题；完成迁移后应把规则合入目标总览、把场景细节合入 raw 来源，并清理旧卡入链。

## 按优化目标组织的知识入口

总经验库永久保留延迟优先、稳定优先及各自三类场景的完整框架；每个已有经验的目标维护一张总体经验总览，直接链接唯一 raw 场景来源。

```markdown
# <优化目标>部署经验总览

## 同构基线知识
### 场景定义
### 并行策略（写触发条件、具体 PP/TP/DP/MBN、TP:DP 比例和映射摘要）
### 原因（解释通信域、同步范围、PP bubble 和 MBN）
### 场景案例（概括场景条件和参数，链接 raw 场景来源）

## 局部异构处理知识
### 场景定义
### 并行策略（写触发条件、具体 PP/TP/DP/MBN、比例和映射摘要）
### 原因（逐项解释 TP 同步范围、PP stage、DP replica 和 MBN）
### 场景案例（概括场景条件和参数，链接 raw 场景来源）

## 分布式异构处理知识
### 场景定义
### 并行策略（写触发条件、具体 PP/TP/DP/MBN、TP:DP 比例和映射摘要）
### 原因（解释数值策略如何减少慢 stage、快慢 replica 等待并保持对称）
### 场景案例（按非对称、对称等具体案例概括并链接 raw 场景来源）
```

三类分支的“并行策略”直接写成熟场景的数值参数，“原因”只解释参数机制，“场景案例”概括条件和数值结果并链接 raw 来源。详细卡数、慢卡位置、rank 映射、Score 代码和结论边界只在 raw 来源维护。优化目标总览不设置“当前经验范围”，也不插入重复分类页或具体经验卡；稳定优先分支缺少经验时明确写“知识缺口”，不编造参数。

当前没有独立且不可替代内容时，不创建 `<experience_category>-knowledge-summary.md`、独立 Score 决策页、具体经验卡或通用验证页；把可召回规则写入目标总览，把场景细节写入 raw 来源。

## 查询结论页面

```markdown
# 问题

## Answer
## Decision flow
## Evidence and confidence
## Boundaries
## Related pages
```

## 经验候选审查记录

```markdown
## 筛选前

| Candidate ID | 来源与场景 | 原始候选 | 初始角色 |
|---|---|---|---|

## 审查

| ID | 可追溯 | 条件具体 | 动作可执行 | 非 score 机制 | 可观测 | 有边界 | 新增价值 | 判定 | 理由与去向 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|

判定只使用：`ACCEPT_EXPERIENCE`、`EVIDENCE_ONLY`、`KEEP_FOR_VALIDATION`、`REJECT`。
```

## 经验库阶段快照

```markdown
# 阶段 N：<本批输入>

## 输入
- 上一阶段：<路径或“无”>
- 新来源/场景：<路径>

## 筛选前
<完整候选表，不只列通过项>

## 审查过程
<逐项门槛、判定、拒绝或降级理由>

## 筛选后
<经验、证据、验证队列分别列出；经验带状态>

## 相比上一阶段
- 新增：
- 更新：
- 合并或拒绝：
- 数量变化：
```

阶段快照默认放入 `outputs/`。它是审核材料，不自动成为 active 经验，也不替代 `raw/` 或知识页。

## 日志条目

```markdown
## [YYYY-MM-DD] ingest | 来源标题

- Created: `raw/...`, `concepts/...`.
- Updated: `index.md`, related backlink pages.
- Confidence or conflict changes: ...
```
