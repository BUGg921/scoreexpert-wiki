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
### 并行策略（每条先写适用规则，再写资源使用、PP、TP、DP、MBN）
### 原因（解释资源使用、通信域、同步范围、PP bubble 和 MBN）
### 场景案例（概括场景条件和参数，链接 raw 场景来源）

## 局部异构处理知识
### 场景定义
### 并行策略（每条先写适用规则，再写资源使用、PP、TP、DP、MBN）
### 原因（逐项解释资源使用、TP 同步范围、PP stage、DP replica 和 MBN）
### 场景案例（概括场景条件和参数，链接 raw 场景来源）

## 分布式异构处理知识
### 场景定义
### 并行策略（每条先写适用规则，再写资源使用、PP、TP、DP、MBN）
### 原因（使用与并行策略相同的编号，解释资源使用和 PP、TP、DP、MBN 的选择）
### 场景案例（按非对称、对称等具体案例概括并链接 raw 场景来源）
```

三类分支的“场景定义”负责物理分类；每条“并行策略”先只用慢卡数量、rank、物理位置、节点/亲和组慢卡向量和速度倍率写可直接判断的适用规则，不重复优化目标，也不混入 raw 边界、模型/workload、显存、网络、映射能力或参数整数可行性；选中策略后再依次写资源使用、`PP`、`TP`、`DP`、`MBN` 的公式、整数约束、拓扑关系和最大/最小可行值，不写固定参数数字。满卡写成 `active_gpu=N`，留卡必须给出可计算规则。五项关系完全相同的场景合并为一个策略编号，适用规则用“或”保留各个已准入输入模式，机制和边界差异分别留在“原因”和“场景案例”；任一项不同则按参数特点拆分命名。“场景案例”只链接 raw。具体数值、实际 rank/group/stage/replica 映射、layer/计算量分配和运行验收保留在 raw，变量化关系不得自动扩大 raw 边界。

正式经验正文不得出现评分策略、评分权重、打分公式或 score 选择过程；“原因”只写算力利用、显存、通信、同步等待、流水线气泡、replica skew 和调度等部署机制。相关代码与候选排序证据只保留在 raw 和审核层。

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
