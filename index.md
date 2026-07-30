# ScoreExpert 部署经验 Wiki

> 面向 GPU 部署选型的互链知识目录。
> Last updated: 2026-07-30 | Total pages: 3

## 当前状态

`raw/articles/` 当前保存 5 份场景来源：同构、单慢卡、两慢卡和四慢卡共 4 份成熟场景来源，以及五慢卡 2/1/1/1 分布的 Evolve 待验证来源。成熟场景都属于**延迟优先型**；稳定优先型目前没有场景经验。延迟优先入口下再按 **同构基线、局部异构、分布式异构** 选择场景知识。

新场景同时命中延迟优先总览规则和对应 raw 场景边界后，直接推理部署策略，无需重新运行真实 Evaluation；只有未命中、越界或冲突时才进入补库流程。

当前正式知识页为 ScoreExpert 入口、部署经验总库和延迟优先经验总览；5 个具体场景来源保存在 `raw/articles/`，其中 S7 只进入验证队列，未改写成熟部署规则。

四场景统一源文档、初始库和两次增量更新的筛选前后过程见 [经验库增量演示](outputs/experience-evolution-demo/README.md)。演示快照位于 `outputs/`，不计入正式知识页总数。

## Entities

- [[scoreexpert]] — ScoreExpert 部署经验的领域入口和当前知识状态。

## 部署经验

- [[deployment-objective-knowledge-framework]] — ScoreExpert 部署经验总库，永久保留延迟优先、稳定优先以及各自三类场景的完整框架；稳定优先当前标记为知识缺口。
- [[latency-first-experience-summary]] — 保存延迟优先的目标定义和三类场景规则；可迁移经验写参数求解规则，固定数值只保留为场景案例，并在独立“原因”中解释机制。
- 同构基线、局部异构和分布式异构统一按“场景定义 → 并行策略 → 原因 → 场景案例”展开。
- 三类场景定义：无稳定设备快慢差异为同构，影响可限制在一个局部范围为局部异构，异常跨多个独立拓扑范围为分布式异构。
- 总览负责可直接召回的场景规则、参数求解规则和原因；raw 场景来源负责实验设置、Score 推导、具体映射、固定参数实例和结论边界。

### 同构基线

- [标准 32 卡同构场景](raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md) — 使用 `PP=1,TP=8,DP=4,MBN=1` 和 `TP:DP=2:1`。

### 局部异构

- [单张慢卡场景](raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md) — 使用 `PP=16,TP=2,DP=1,MBN=64` 隔离局部慢卡并重平衡慢卡 stage。

### 分布式异构

- [两张慢卡场景](raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md) — 两张慢卡跨亲和组时使用 `PP=1,TP=8,DP=4,MBN=1`，处理快慢 replica 等待。
- [四张慢卡场景](raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md) — 四张慢卡一节点一张时使用相同参数构造对称 replica。
- [五张慢卡 2/1/1/1 Evolve 场景](raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-2026-07-30.md) — 当前已仿真候选最优为 `PP=16,TP=1,DP=2,MBN=64`；覆盖率 `65/873` 且缺少真实训练 Evaluation，保持 `KEEP_FOR_VALIDATION`，不作为默认部署经验。

## Comparisons

_暂无页面。_
