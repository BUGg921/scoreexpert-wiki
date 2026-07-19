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

## 经验分类

- 主分类：同构基线 | 局部异构 | 分布式异构
- 分类依据：<说明异构是否存在，以及是局部还是跨区域分布>

## 优化目标

- 主目标：延迟优先 | 稳定优先
- 主指标：<平均/P50/P95/P99 latency，或方差/失败率/超时/恢复指标>
- 护栏：<throughput、显存、OOM、稳定性或最低性能要求>
- 目标总览：[[<optimization-priority>-experience-summary]]

## 来源明确经验

> 仅当来源存在明确经验结论时使用，不要求固定标题。按来源顺序忠实提取实际存在的 N 条，N 不设上限或下限，不在本节加入 Wiki 自行推导。

- <来源经验及其原有限定条件；按实际数量逐条列出>
- <若来源给出比例、阈值、上下界或不等式，原样保留定量关系，并另列当前实例>

## 来源分散归纳

> 仅当来源没有显式总结、但分析或结果中存在明确决策时使用。每条归纳指向对应证据，不加入 Wiki 自行推理。

- <从分散证据归纳出的经验及证据位置；按实际数量列出>

## Wiki 推导假设

> 仅当来源没有部署结论、需要根据 score、拓扑或 Evaluation 推导时使用。默认标记为 `unverified`，与来源经验分开。

- <推导规则、推导链和证据缺口；按实际数量列出>

## 部署经验总结

### 资源规模部署经验

- **满卡条件**：<何时新增算力收益预计大于通信、同步或异构成本>
- **少卡对照**：<至少一个满足显存、整除和拓扑约束的反事实候选>
- **拓扑重建**：<减卡后如何重新形成完整 TP group、DP replica 或 PP stage>
- **当前实例**：<总卡数、active_gpu、节点规模；明确实例不是通用规则>

### 并行策略部署经验

> 只保留来源或证据支持的维度，不为填模板补造。先写可迁移规则，最后再写当前实例。

#### TP
- <TP group 的边界、选择规则、作用与失效条件>

#### TP/PP
- <TP 与 PP 的联动关系、权衡和切换条件>

#### DP
- <replica 数量、映射、等待或均衡规则>

#### PP/MBN
- <流水线深度与 microbatch 的联动规则>

### 当前场景实例与召回规则

```text
当前实例：PP=<n>, TP=<n>, DP=<n>, MBN=<n>
可迁移规则：<不能被实例替代的比例、阈值或条件化规则>
```

### 触发条件
- 写明可以召回本经验的拓扑、异构、模型或 score 条件。

### 部署动作
1. 使用命令式语句写出参数选择和 rank/group 映射。
2. 给出可直接采用的第一候选。

### 作用机制
- 逐条解释每个动作规避或利用了什么成本。

### 预期观测
- 写明 score、利用率、通信、显存或 Evaluation 中应出现的可检查现象。

### 失效边界
- 写明何时停止复用、改用对照候选或重新搜索。

## Scenario
- 总卡数、每节点卡数、亲和组
- 慢卡数量、ID、速度倍率、分布和 rank mapping
- 模型、batch、显存和搜索空间

## First candidate
`PP=?, TP=?, DP=?, MBN=?`

## Evidence
### Score evidence
### Topology evidence
### Evaluation evidence

## Boundaries
### Applies when
### Fails when

## Evidence gaps
```

“部署经验总结”是 active 页的必填主体。`First candidate` 和 `Evidence` 用来支撑经验，不能替代经验本身。

三个来源区块按实际情况择一或组合使用，不要全部机械填写。来源已有显式经验时，“来源明确经验”必填；只有分散结论时使用“来源分散归纳”；没有来源结论时才使用“Wiki 推导假设”。经验数量由来源决定，不得凑数。新增推理放入证据区并标记为“Wiki 补充推理”。

## 按优化目标组织的知识入口

优化目标框架页只定义分类格式；每个已启用目标维护一张总览，直接链接具体经验卡。

```markdown
# <优化目标>部署经验总览

## 同构基线知识
### 场景定义
### 资源规模部署经验（满卡条件、少卡对照、拓扑重建、当前实例）
### 并行策略部署经验（按 TP、TP/PP、DP、PP/MBN 等来源支持的维度）
### 场景案例

## 局部异构处理知识
### 场景定义
### 并行策略
### 局部异构的影响（TP group、DP replica、PP stage）
### 对策：隔离
### 场景案例

## 分布式异构处理知识
### 场景定义
### 并行策略
### 分布式异构的影响
### 对策：均衡与对称
### 场景案例
```

延迟优先的案例必须声明 latency 口径和护栏；稳定优先的案例必须声明方差、尾延迟、失败/OOM/超时或恢复指标和性能下限。每个案例继续补齐证据状态、验收阈值、失效边界与回退动作。优化目标总览直接引用具体经验卡，不再插入重复的分类总览页；缺少目标对应 Evaluation 时明确写“知识缺口”。

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
