# ScoreExpert 部署经验 Wiki

> 面向 GPU 部署选型的互链知识目录。
> Last updated: 2026-08-03 | Total pages: 3

## 当前状态

`raw/articles/` 当前保留 5 份成熟场景来源，覆盖同构、单慢卡、两慢卡、四慢卡和五慢卡 2/1/1/1 非对称分布。五个场景当前都属于**延迟优先型**；稳定优先型目前没有场景经验。

新场景同时命中延迟优先总览规则和对应 raw 场景边界后，直接推理部署策略，无需重新运行真实 Evaluation；只有未命中、越界或冲突时才进入补库流程。

当前正式知识页为 ScoreExpert 入口、部署经验总库和延迟优先经验总览；5 个具体场景保存在 `raw/articles/`。

四场景统一源文档、初始库和两次增量更新的筛选前后过程见 [经验库增量演示](outputs/experience-evolution-demo/README.md)。演示快照位于 `outputs/`，不计入正式知识页总数。

## Entities

- [[scoreexpert]] — ScoreExpert 部署经验的领域入口和当前知识状态。

## 部署经验

- [[deployment-objective-knowledge-framework]] — ScoreExpert 部署经验总库，永久保留延迟优先、稳定优先以及各自三类场景的完整框架；稳定优先当前标记为知识缺口。
- [[latency-first-experience-summary]] — 从五份 raw 提取延迟优先策略；每条策略先用与总卡数无关的慢卡数量关系、节点/亲和组相对分布和速度特征给出适用规则，再给出资源使用及 `PP`、`TP`、`DP`、`MBN` 关系。五项策略相同的场景合并，策略不同的分支按参数特点命名。
- 同构基线、局部异构和分布式异构统一按“场景定义 → 并行策略 → 原因 → 场景案例”展开。
- 三类场景定义：无稳定设备快慢差异为同构，影响可限制在一个局部范围为局部异构，异常跨多个独立拓扑范围为分布式异构。
- 总览中的场景定义负责分类，每条并行策略的适用规则负责类内选路，随后给出资源使用以及 `PP/TP/DP/MBN`；raw 场景来源负责实验设置、候选证据、具体映射、固定参数实例和结论边界。

### 同构基线

- [标准同构场景](raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md) — 最小 PP、`TP:DP=2:1` 的满卡组合、最小 MBN。

### 局部异构

- [单张慢卡场景](raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md) — 小 TP、最小 DP、满卡深 PP、约束内最大 MBN。

### 分布式异构

- [两张慢卡场景](raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md) — 命中“最小 PP、TP 主导型满卡方案”，保留快慢 replica 等待边界。
- [四张慢卡场景](raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md) — 命中同一并行策略，保留 DP replica 慢卡结构对称机制。
- [五张慢卡 2/1/1/1 场景](raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-reviewed-2026-08-03.md) — 使用不同的“深 PP、最小 TP 双副本方案”，保留副本不对称边界。

## Comparisons

_暂无页面。_
