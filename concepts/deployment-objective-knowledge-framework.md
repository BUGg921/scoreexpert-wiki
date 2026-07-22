---
title: ScoreExpert 部署经验总库
created: 2026-07-18
updated: 2026-07-22
type: summary
tags: [scoreexpert, deployment, decision-guide, governance, evidence]
sources: [raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md, raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md]
confidence: high
contested: false
contradictions: []
---

# ScoreExpert 部署经验总库

本页是 [[scoreexpert]] 的完整目标框架；当前成熟的数值部署经验集中在 [[latency-first-experience-summary]]。

## 1. 总库结构与当前状态
经验库使用二维结构：先按**优化目标**进入，再按**异构分布范围**选择场景知识。

```text
优化目标
├── 延迟优先型
│   ├── 同构基线知识
│   ├── 局部异构处理知识
│   └── 分布式异构处理知识
└── 稳定优先型
    ├── 同构基线知识
    ├── 局部异构处理知识
    └── 分布式异构处理知识
```

- “延迟优先 / 稳定优先”回答：**这次部署首先优化什么**。
- “同构基线 / 局部异构 / 分布式异构”回答：**硬件异常以什么范围分布，为什么需要改变策略**。
- 每个场景只保留一份 raw 来源；不同优化目标可以引用同一场景，但必须分别写出目标、指标和成立原因，不能复制一套结论。
- 本文件永久保留延迟优先和稳定优先的完整三类框架；当前四个成熟场景均属于延迟优先，稳定优先暂时没有部署经验，但其结构和知识缺口不能删除。

总库采用“离线沉淀、在线推理”：新场景同时命中 [[latency-first-experience-summary]] 的规则和对应 raw 场景边界时，直接复用策略，不强制重新 Evaluation。

## 2. 延迟优先型
延迟优先型以端到端 latency 为主目标。在线命中总览规则以及 raw 场景中的资源、拓扑、异构和模型边界后，直接输出策略，不要求新一轮真实 Evaluation。

### 2.1 同构基线知识
#### (1) 场景定义

- 参与部署的 GPU 属于同一性能等级，没有已知慢卡、故障卡或持续性的设备性能差异。
- 允许节点间存在通信层级，但不同 group、stage 或 replica 不因设备性能形成固定快慢结构。

#### (2) 并行策略

1. 在 `idle 的损失 > 通信优化收益` 时，使用满卡，设置 `PP=1, TP=8, DP=4, MBN=1`，即 `TP:DP=2:1`；每节点构造一个 `TP=8` group，四组组成 `DP=4`。

#### (3) 原因

- `PP=1` 消除流水线开销；`TP=8` 将高频通信限制在节点内；`DP=4` 使用四个完整节点；`MBN=1` 与无流水线匹配。

#### (4) 场景案例

- [标准 32 卡同构场景](../raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md)：32 张正常卡、4 个 8 卡节点使用 `PP=1, TP=8, DP=4, MBN=1`。

### 2.2 局部异构处理知识
#### (1) 场景定义

- 异常集中在一个可识别、可控制的局部拓扑范围内，能够通过 group、stage、layer 或计算映射限制主要影响。
- 局部性的判断依据是影响能否被限制；异常跨多个独立区域且无法收敛到一个局部范围时，属于分布式异构。

#### (2) 并行策略

1. 当异构影响能够限制在一个局部 group/stage，且 `保留异构设备并进行局部隔离的算力收益 > 深 PP 引入的流水线与调度成本` 时，在当前 32 卡拓扑下使用满卡，设置 `PP=16, TP=2, DP=1, MBN=64`，即 `TP:DP=2:1`；构造 16 个双卡 stage，并减少异常卡所在 stage 的层数或计算量。

#### (3) 原因

- `TP=2` 将同步污染限制在双卡 group；`PP=16` 将慢卡限制在一个 stage，并通过 stage 重平衡削弱瓶颈。
- `DP=1` 避免快 replica 等待含慢卡 replica；`MBN=64` 降低深流水线的 bubble。

#### (4) 场景案例

- [单张慢卡场景](../raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md)：32 卡单慢卡场景使用 `PP=16, TP=2, DP=1, MBN=64`。

### 2.3 分布式异构处理知识
#### (1) 场景定义

- 异常卡跨多个独立节点、亲和组、TP group 或 DP replica 分布，不能作为一个局部坏点处理。
- 按各 replica 的异常结构和预测耗时继续区分不对称分布与近似对称分布。

#### (2) 并行策略

1. 异常设备跨多个亲和组分布、各 DP replica 的异常结构或预测耗时不一致，且 `局部 PP 隔离收益 < 多个慢 stage 与流水线开销`、`满卡算力收益 > replica 等待与通信成本` 时，在当前 32 卡拓扑下使用满卡，设置 `PP=1, TP=8, DP=4, MBN=1`，即 `TP:DP=2:1`；每节点构造一个 `TP=8` group，四组组成 `DP=4`，并按预测执行时间调整异常卡映射。
2. 异常设备能够按数量、速度和位置对称映射到各 DP replica，且 `副本对称收益 > 多个 PP stage 的隔离收益`、`满卡算力收益 > 节点内 TP 通信成本` 时，在当前 32 卡拓扑下使用相同的满卡参数；使每个节点内的 `TP=8` group 具有相同的异常设备结构，从而保持四个 DP replica 对称。

#### (3) 原因

- `PP=1` 避免多个慢 stage 和流水线气泡；`TP=8` 把高频通信限制在单节点内；`MBN=1` 与无流水线匹配。
- `DP=4` 承载四个节点：分布不对称时按预测执行时间调整映射，分布可对称时保持各 replica 的异常卡结构一致。

#### (4) 场景案例

- [两张慢卡场景](../raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md)：两张慢卡跨亲和组的非对称分布。
- [四张慢卡场景](../raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md)：四张慢卡一节点一张的对称分布。

## 3. 稳定优先型

稳定优先型以结果波动、尾延迟、OOM/失败率、性能退化可控性和重复运行一致性为主目标。当前来源没有形成稳定性优先的直接 Evaluation，因此以下三个分支先固定知识格式和验证入口，不产生默认部署结论。

### 3.1 同构基线知识

#### (1) 场景定义

- 参与部署的 GPU 属于同一性能等级，没有已知慢卡、故障卡或持续性的设备性能差异。
- 允许节点间存在通信层级，但不同 group、stage 或 replica 不因设备性能形成固定快慢结构。

#### (2) 并行策略

- 当前没有成熟的稳定优先数值策略；后续经验必须在这里明确写出 `PP/TP/DP/MBN` 和必要映射。

#### (3) 原因

- [标准 32 卡同构场景](../raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md)只有延迟优先结论；缺少重复运行、OOM、超时、P99 和故障恢复数据，当前不能给出稳定优先参数及其原因。

#### (4) 场景案例

- [标准 32 卡同构场景](../raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md)目前只作为稳定优先知识缺口的对照场景。

### 3.2 局部异构处理知识

#### (1) 场景定义

- 异常集中在一个可识别、可控制的局部拓扑范围内，能够通过 group、stage、layer 或计算映射限制主要影响。
- 局部性的判断依据是影响能否被限制；异常跨多个独立区域且无法收敛到一个局部范围时，属于分布式异构。

#### (2) 并行策略

- 当前没有成熟的稳定优先数值策略；后续经验必须在这里明确写出 `PP/TP/DP/MBN` 和必要映射。

#### (3) 原因

- [单张慢卡场景](../raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md)只有延迟优先结论；缺少多次运行方差、超时、失败率和恢复结果，当前不能给出稳定优先参数及其原因。

#### (4) 场景案例

- [单张慢卡场景](../raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md)目前只作为稳定优先知识缺口的对照场景。

### 3.3 分布式异构处理知识

#### (1) 场景定义

- 异常卡跨多个独立节点、亲和组、TP group 或 DP replica 分布，不能作为一个局部坏点处理。
- 按各 replica 的异常结构和预测耗时继续区分不对称分布与近似对称分布。

#### (2) 并行策略

- 当前没有成熟的稳定优先数值策略；后续经验必须在这里明确写出 `PP/TP/DP/MBN` 和必要映射。

#### (3) 原因

- [两张慢卡场景](../raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md)和[四张慢卡场景](../raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md)只有延迟优先结论；缺少重复运行方差、P99、超时和故障恢复数据，当前不能给出稳定优先参数及其原因。

#### (4) 场景案例

- [两张慢卡场景](../raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md)和[四张慢卡场景](../raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md)目前只作为稳定优先知识缺口的对照场景。

## 4. 场景来源与直接推理

1. [[latency-first-experience-summary]] 保存三类场景的定义、数值并行策略、原因和场景案例。
2. 四份 raw 场景来源保存卡数、拓扑、慢卡数量/位置/速度、Score 代码、映射方式和结论边界。
3. 新场景同时命中总览规则和对应 raw 来源边界时，可以直接输出 `PP/TP/DP/MBN` 与映射，无需新的真实 Evaluation。
4. 资源、拓扑、慢卡分布、模型约束或搜索空间不匹配时停止直接复用，进入仿真、Evaluation 或人工补库流程。
