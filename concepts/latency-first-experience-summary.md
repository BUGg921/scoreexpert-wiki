---
title: 延迟优先型部署经验总览
created: 2026-07-18
updated: 2026-07-22
type: summary
tags: [scoreexpert, deployment, decision-guide, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence]
sources: [raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md, raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md]
confidence: high
contested: false
contradictions: []
---

# 延迟优先型部署经验总览

在 [[scoreexpert]] 部署经验库中，延迟优先以端到端 latency 为主要优化目标，同时约束 throughput、显存、OOM 和运行波动；完整的延迟/稳定框架见 [[deployment-objective-knowledge-framework]]。

## 1. 同构基线知识

### (1) 场景定义

- 参与部署的 GPU 属于同一性能等级，没有已知慢卡、故障卡或持续性的设备性能差异。
- 节点和亲和组仍可存在通信层级，但不同 group、stage 或 replica 不因设备性能差异形成固定的快慢结构。
- 出现可重复识别的设备快慢差异时，不再属于同构场景。

### (2) 并行策略

1. **满卡方案**：在 `idle 的损失 > 通信优化收益` 时，使用满卡，设置 `PP=1, TP=8, DP=4, MBN=1`，即 `TP:DP=2:1`；每节点构造一个 `TP=8` group，四个 group 组成 `DP=4`。

### (3) 原因

- **`PP=1`**：消除流水线 stage 和 pipeline bubble。
- **`TP=8`**：把高频 TP 通信限制在单个 8 卡节点内，避免跨节点通信。
- **`DP=4`**：使用四个完整节点扩展计算，同时保持每个 DP replica 的结构一致。
- **`MBN=1`**：`PP=1` 不需要额外微批填充流水线。^[raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md]

### (4) 场景案例

- **标准 32 卡同构基线**：[场景来源](../raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md)在 32 张正常卡、4 个 8 卡节点的场景中使用 `PP=1, TP=8, DP=4, MBN=1`。

## 2. 局部异构处理知识

### (1) 场景定义

- 异常集中在一个可识别、可控制的局部拓扑范围内，例如一个 TP group、PP stage、节点或 DP replica。
- 能够识别异常 rank，并通过 group、stage、layer 或计算映射把主要影响限制在这个局部范围内。
- 局部性的判断依据是异构影响能否被限制，而不是机械地只看慢卡数量；异常跨越多个独立区域且无法收敛到一个局部范围时，属于分布式异构。

### (2) 并行策略

1. 当异构影响能够限制在一个局部 group/stage，且 `保留异构设备并进行局部隔离的算力收益 > 深 PP 引入的流水线与调度成本` 时，在当前 32 卡拓扑下使用满卡，设置 `PP=16, TP=2, DP=1, MBN=64`，即 `TP:DP=2:1`；构造 16 个双卡 stage，将异常卡放入一个 `TP=2` group，并减少异常卡所在 stage 的层数或计算量。

### (3) 原因

- **`TP=2`**：把慢卡引起的同步等待限制在一个双卡 TP group 内，避免污染更多正常卡。
- **`PP=16`**：用深 PP 把慢卡限制在一个 stage；慢卡 stage 同时减层或减计算，使其预计执行时间接近其他 stage。
- **`DP=1`**：避免形成纯快 replica 等待含慢卡 replica 的跨副本同步。
- **`MBN=64`**：为深流水线提供足够微批，降低 pipeline bubble。^[raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md]

### (4) 场景案例

- **单慢卡局部隔离**：[场景来源](../raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md)在 32 卡中存在一张约半速慢卡时，使用 `PP=16, TP=2, DP=1, MBN=64` 隔离慢卡并重平衡慢卡 stage。

## 3. 分布式异构处理知识

### (1) 场景定义

- 异常卡跨多个独立节点、亲和组、TP group 或 DP replica 分布，无法作为一个局部坏点处理。
- 分布式异构包含两种基本形态：各 replica 的异常结构或预测耗时不同的“不对称分布”，以及各 replica 的异常结构和预测耗时接近的“近似对称分布”。
- 分布范围按异常是否跨越多个独立拓扑区域判断，不以慢卡数量直接划分。

### (2) 并行策略

1. 当异常设备跨多个亲和组分布、各 DP replica 的异常结构或预测耗时不一致，且 `局部 PP 隔离收益 < 多个慢 stage 与流水线开销`、`满卡算力收益 > replica 等待与通信成本` 时，在当前 32 卡拓扑下使用满卡，设置 `PP=1, TP=8, DP=4, MBN=1`，即 `TP:DP=2:1`；每节点构造一个 `TP=8` group，四组组成 `DP=4`，并按预测执行时间调整异常卡映射。
2. 当异常设备能够按数量、速度和位置对称映射到各 DP replica，且 `副本对称收益 > 多个 PP stage 的隔离收益`、`满卡算力收益 > 节点内 TP 通信成本` 时，在当前 32 卡拓扑下使用相同的满卡参数；使每个节点内的 `TP=8` group 具有相同的异常设备结构，从而保持四个 DP replica 对称。

### (3) 原因

- **`PP=1`**：慢卡跨多个区域时，深 PP 容易形成多个慢 stage；无流水线可以避免多个 stage 瓶颈和 pipeline bubble。
- **`TP=8`**：把高频 TP 通信限制在单个 8 卡节点内，避免跨节点慢链路。
- **`DP=4`**：利用四个节点形成四个 replica；分布不对称时按预计执行时间调整映射，分布可对称时保持各 replica 的异常卡数量、速度和位置一致。
- **`MBN=1`**：`PP=1` 不需要用更多微批填充流水线，因此采用最小 MBN。^[raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md] ^[raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md]

### (4) 场景案例

- **两慢卡非对称均衡**：[场景来源](../raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md)在两张慢卡跨亲和组时，使用 `PP=1, TP=8, DP=4, MBN=1`，重点处理快慢 replica 等待。
- **四慢卡对称副本**：[场景来源](../raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md)在四张速度接近的慢卡一节点一张时，使用相同参数构造慢卡结构对称的 DP replica。
