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

## 正式经验页面

文件位置必须是 `concepts/<experience_category>/<slug>.md`。

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

具体经验卡正文只允许“场景描述”和“具体的并行策略”两个二级标题。状态、优化目标、准入主体、准入日期、来源和置信度只写 frontmatter。来源已有显式经验时须忠实保留；只有分散结论时注明归纳依据；没有来源部署结论时才标记为 Wiki 推导。来源审计与附件缺口保留在来源层或审核日志，不新增正文治理章节。

## 按优化目标组织的知识入口

总经验库永久保留延迟优先、稳定优先及各自三类场景的完整框架；每个已有经验的目标维护一张总体经验总览，直接链接具体经验卡。

```markdown
# <优化目标>部署经验总览

## <优化目标>总体经验
- <跨同构、局部异构、分布式异构可复用的资源、并行、切换与验收规则>

## 同构基线知识
### 场景定义
### 资源规模部署经验（满卡条件、少卡对照、拓扑重建）
### 并行策略部署经验（按 TP、TP/PP、DP、PP/MBN 等来源支持的维度）
### 场景案例（使用具体案例名称，链接对应经验卡，并在此放卡数、拓扑和参数实例；不重复准入状态）

## 局部异构处理知识
### 场景定义
### 局部异构的影响（TP group、DP replica、PP stage）
### 并行策略（把隔离对策融入 TP、TP/PP、DP、PP/MBN）
### 场景案例（使用具体案例名称链接对应经验卡）

## 分布式异构处理知识
### 场景定义
### 分布式异构的影响
### 并行策略（把均衡与对称对策融入 TP、TP/PP、DP、PP/MBN）
### 场景案例（使用案例一、案例二等具体名称链接经验卡）
```

目标总体经验和各类规则中不写“当前经验范围”，也不放具体卡数、慢卡位置或参数实例；这些内容统一进入“场景案例”。场景案例不重复 `active` 等准入状态、审核日期或证据完整度，这些信息只在所链接的具体经验卡维护。优化目标总览直接引用具体经验卡，不再插入重复的分类总览页；稳定优先分支缺少经验时明确写“知识缺口”。

当前没有独立且不可替代内容时，不创建 `<experience_category>-knowledge-summary.md`、独立 Score 决策页或通用验证页；把这些内容写入目标总览或具体经验卡。

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
