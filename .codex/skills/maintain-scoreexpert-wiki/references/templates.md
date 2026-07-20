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
---

# 标题

## 1. 场景描述

- **经验状态**：`active | candidate | archived`
- **优化目标**：延迟优先 | 稳定优先
- **主指标与护栏**：<延迟或稳定性指标，以及 throughput、显存、OOM 等约束>
- **场景分类**：同构基线 | 局部异构 | 分布式异构
- **资源拓扑**：<总卡数、每节点卡数、亲和组和可用卡范围>
- **异构分布**：<慢卡数量、位置、速度倍率和分布；同构场景写明无慢卡>
- **模型与映射约束**：<模型、batch、显存、搜索空间和 rank/group 映射能力>
- **硬匹配条件**：<允许直接召回本经验的目标、拓扑、异构和模型条件>
- **准入依据**：<来源结论、Evaluation、仿真或人工审核记录>
- **目标总览**：[[<optimization-priority>-experience-summary]]

## 2. 具体的并行策略

### 直接输出

`active_gpu=?, PP=?, TP=?, DP=?, MBN=?`

### 部署经验

- **卡的数量**：<卡数选择规则、拓扑完整性要求和本场景直接采用的 active_gpu>
- **TP**：<TP group 的边界、选择规则、作用与失效条件>
- **TP/PP 或 TP/DP**：<两个维度的联动关系、权衡和切换条件>
- **DP**：<replica 数量、映射、等待或均衡规则>
- **PP/MBN**：<流水线深度与 microbatch 的联动规则>

### 部署动作

1. <使用命令式语句写出参数选择。>
2. <写出 rank、TP group、DP replica 或 PP stage 的映射。>

### 适用边界与回退

- **允许变换**：<能够按哪些比例、阈值或公式调整参数>
- **停止条件**：<缺字段、越界、冲突或非 active 时停止直接复用>
- **回退策略**：<停止直接复用后采用的已知策略或补库任务>

### 准入记录

- <ACCEPT_EXPERIENCE 等判定、审核人、日期和依据。>
- <来源中的显式经验、分散结论、证据边界和缺口也在本章记录，不另建第三级正文结构。>
```

具体经验卡正文只允许“场景描述”和“具体的并行策略”两个二级标题。来源已有显式经验时须忠实保留；只有分散结论时注明归纳依据；没有来源部署结论时才标记为 Wiki 推导。上述内容全部归入第二章的部署经验、适用边界或准入记录，不再新增并列的正文一级章节。

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
### 场景案例（使用具体案例名称，链接对应经验卡，并在此放卡数、拓扑、参数实例和证据状态）

## 局部异构处理知识
### 场景定义
### 局部异构的影响（TP group、DP replica、PP stage）
### 并行策略（包含隔离对策，并使用具体案例名称链接对应经验卡）

## 分布式异构处理知识
### 场景定义
### 分布式异构的影响
### 并行策略（包含均衡与对称对策，并使用案例一、案例二等具体名称链接经验卡）
```

目标总体经验和各类规则中不写“当前经验范围”，也不放具体卡数、慢卡位置或参数实例；这些内容统一进入“场景案例”。延迟优先案例必须声明 latency 口径和护栏；稳定优先案例必须声明方差、尾延迟、失败/OOM/超时或恢复指标和性能下限。优化目标总览直接引用具体经验卡，不再插入重复的分类总览页；缺少目标对应 Evaluation 时明确写“知识缺口”。

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
