---
title: 两张跨亲和组慢卡的均衡延迟经验
created: 2026-07-15
updated: 2026-07-19
type: concept
tags: [scoreexpert, deployment, experience, distributed-heterogeneity, distribution-imbalanced, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence, hypothesis, decision-guide]
sources: [raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md, raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
confidence: medium
contested: false
contradictions: []
experience_category: distributed-heterogeneity
---

# 两张跨亲和组慢卡的均衡延迟经验

## Status

`partially_supported`。来源报告 `PP=1,TP=8,DP=4,MBN=1` 是当前 Evaluation 最优，但缺少慢卡 ID/倍率、原始 latency、完整候选表和重复波动。

## 优化目标与经验分类

- 主目标：**延迟优先**。
- 主分类：**分布式异构**；两张慢卡跨亲和组分散，形成快慢不均的 DP replica。
- 主指标：端到端 latency 和 replica skew。
- 护栏：throughput、显存、OOM、TP group time、快 replica 等待比例和重复波动。
- 目标总览：[[latency-first-experience-summary]]。

## 1. 场景定义

- 32 卡，4 个 8 卡节点，两个 16 卡亲和组。
- 两张慢卡分别位于两个亲和组；具体卡号和速度倍率未提供。
- 模型能在单节点 `TP=8`、`PP=1` 下满足显存约束。

## 2. 来源明确经验

两份来源共同给出从“隔离”到“均衡”的切换：

1. 单慢卡是局部异常，可以用小 TP、高 PP 隔离。
2. 两张慢卡跨亲和组后，深 PP 容易形成多个慢 stage，隔离收益下降。
3. 模型能在单节点 TP group 中放下时，取消深流水线，在节点内使用 TP、节点间使用 DP。
4. `PP=1` 时从 `MBN=1` 起步，避免额外 microbatch 通信成本。

## 3. 分布式异构影响

- 深 PP 会把多个慢点串进同一条流水线，最慢 stage 继续决定周期。
- `PP=1,TP=8,DP=4` 下预计形成两个慢 replica 和两个快 replica。
- 快 replica 等待慢 replica，主要风险从“局部污染”变为 replica skew。

## 4. 部署经验总结

### 资源规模部署经验

> 来源只给出当前 32 卡候选；少卡对照和场景重分类属于 Wiki 验证规则。

- **满卡条件**：当前候选使用四个完整节点、共 32 卡，以节点内 TP 和节点间 DP 使用全部资源；是否优于少卡方案仍由端到端 latency 决定。
- **少卡对照**：减卡候选必须保持可执行的 TP/DP 拓扑，并重新记录两张慢卡落入哪些 group 或 replica。
- **场景重分类**：如果减卡或重映射使两张慢卡集中到同一区域，场景已经从分布式异构变为局部异构，不能把收益只归因于卡数减少。
- **当前实例**：4 个 8 卡节点全部参与，`active_gpu=32`；当前来源没有给出少卡 Evaluation。

### 并行策略部署经验

#### TP

- 模型能在单节点 TP group 中放下时，优先使用节点内 `TP=8`，避免高频 TP 通信跨节点。
- 含慢卡的 TP group 仍会整体变慢，因此必须观测 group time，不能把节点内 TP 当作消除异构。

#### TP/PP

- 慢卡跨多个区域后，深 PP 容易形成多个慢 stage；若显存允许，先比较 `PP=1,TP=8` 与深 PP 隔离候选。
- 当前经验从逐卡 PP 隔离切换为节点内 TP，不代表所有分布式慢卡场景都应取消 PP。

#### DP

- 四节点用 `DP=4` 保持满卡，但两张慢卡会形成慢 replica 与快 replica；DP 负责扩展，不负责自动均衡。
- 部署时必须同时测各 replica time 和等待比例，skew 超阈值时重新映射慢卡或搜索组合。

#### PP/MBN

- `PP=1` 消除 pipeline bubble，此时从 `MBN=1` 起步，避免没有流水线收益的额外切分。
- 若因显存回退到 `PP>1`，必须重新扫描 MBN。

### 当前场景实例与召回规则

```text
当前实例：PP=1, TP=8, DP=4, MBN=1
切换原则：异构跨区域后，从逐点PP隔离切换到节点内TP + 节点间DP
```

### 触发条件

- 两张慢卡确实跨亲和组分散，而不是集中在同一节点或同一 TP group。
- TP group 能严格限制在节点内，`PP=1` 不 OOM。

### 部署动作：均衡

1. 设置 `PP=1`，避免形成多个慢 stage。
2. 每节点建立一个 `TP=8` group，四个节点组成 `DP=4`。
3. 标记两个含慢卡 replica 和两个纯快卡 replica，测量实际时间差。
4. 设置 `MBN=1`，并与深 PP、浅 PP 和 score 近邻候选直接对照。

### 作用机制

- `PP=1` 消除权重最大的 bubble 和多慢 stage 风险。
- 节点内 TP 避免高频 TP 通信跨节点。
- DP 扩展使用全部 32 卡，但不会自动消除快慢副本等待。

### 预期观测

- `PP=1` 时 bubble 为 0。
- 含慢卡 replica 的 step time 高于纯快卡 replica。
- 推荐候选的端到端 latency 超过全部对照至少 `δ`，且 replica skew 在业务阈值内。

### 失效边界与回退

- 慢卡集中在同一节点：重新比较局部隔离与重映射。
- replica skew 不可接受：调整慢卡分布或重新搜索并行组合。
- `PP=1` OOM：使用满足显存的最小 PP，并重新测多个慢 stage。
- 每节点均出现慢卡：切换到 [[four-slow-gpu-symmetric-replicas]]。

## 5. 场景案例与最小对照

```text
第一候选：PP=1, TP=8, DP=4, MBN=1
映射：每节点一个8卡TP group和一个DP replica
A：PP=16, TP=2, DP=1, MBN=64
B：PP=1,  TP=1, DP=32, MBN=1
C：PP=2,  TP=4, DP=4, MBN=16
```

当前 score 中 `1/8/4/1` 只比 `1/1/32/1` 高 `0.28` 分；无 PP、低 MBN 是强偏好，`TP=8,DP=4` 是弱偏好，必须由拓扑和 Evaluation 共同确认。

## 6. 证据边界

- Score：不读取慢卡数量、位置和速度，不能独立证明“均衡”机制。
- 拓扑：解释多慢 stage 和快慢 replica 等待；节点内 TP 是部署映射。
- Evaluation：来源报告第一候选最优，但没有原始数值。
- 判定：`KEEP_FOR_VALIDATION`；维持 `partially_supported`。

局部隔离对照见 [[single-slow-gpu-isolation]]，同构基线见 [[homogeneous-32gpu-score-candidate]]。
