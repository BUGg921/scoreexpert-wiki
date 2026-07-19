---
title: 四张均匀慢卡的对称副本延迟经验
created: 2026-07-15
updated: 2026-07-19
type: concept
tags: [scoreexpert, deployment, experience, distributed-heterogeneity, distribution-symmetric, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence, hypothesis, decision-guide]
sources: [raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
confidence: medium
contested: false
contradictions: []
experience_category: distributed-heterogeneity
---

# 四张均匀慢卡的对称副本延迟经验

## Status

`partially_supported`。来源报告 `PP=1,TP=8,DP=4,MBN=1` 是当前 Evaluation 最优，但缺少卡号、速度倍率、原始 latency、非均匀映射对照和重复波动。

## 优化目标与经验分类

- 主目标：**延迟优先**。
- 主分类：**分布式异构**；一节点一张慢卡，使四个 DP replica 具有相同慢卡数量。
- 主指标：端到端 latency，同时检查 replica skew。
- 护栏：throughput、显存、OOM、各 TP group 时间和重复波动。
- 目标总览：[[latency-first-experience-summary]]。

## 1. 场景定义

- 32 卡，4 个 8 卡节点，两个 16 卡亲和组。
- 四张速度接近的慢卡均匀分布为一节点一张。
- 模型能在节点内 `TP=8`、`PP=1` 下满足显存约束。

如果实际慢卡不是一节点一张，score 数值分析可能不变，但本页的对称映射经验不成立。

## 2. 来源明确经验

来源给出：

1. 慢卡均匀覆盖所有节点时，优先保持 replica 对称，不再尝试把所有慢卡隔离到少数 PP stage。
2. 每节点组成一个 `TP=8` group，四个节点组成 `DP=4`。
3. 使用 `PP=1,MBN=1`，避免多个慢 stage、pipeline bubble 和额外切分成本。
4. 该策略不能恢复绝对性能，但可能减少 DP replica 间的 straggler skew。

## 3. 分布式异构影响

- 四个 TP group 都含慢卡，所有 replica 的绝对速度都会下降。
- 每个 replica 的慢卡结构相同，副本时间方差可能低于非均匀映射。
- `replica 更均衡` 不等于端到端 latency 一定更低，必须同时验收。

## 4. 部署经验总结

### 资源规模部署经验

> 来源只给出当前 32 卡对称候选；少卡对照和场景重分类属于 Wiki 验证规则。

- **满卡条件**：当前使用四个完整节点、共 32 卡，才能直接形成“一节点一张慢卡”的四个对称 TP group；满卡的价值在于保留该对称结构，而不只是提高利用率。
- **少卡对照**：减少资源时必须重建完整 TP group 和 DP replica，并重新检查慢卡数量、速度和预测耗时是否仍然对称。
- **场景重分类**：减卡后若出现纯快 replica、慢卡集中或不完整节点，本页的对称经验已经失效，应按新的局部或非对称分布重新召回经验。
- **当前实例**：4 个 8 卡节点全部参与，`active_gpu=32`；来源没有证明这是所有资源规模下的延迟最优点。

### 并行策略部署经验

#### TP

- 每节点恰有一张速度接近的慢卡时，以节点为边界建立 `TP=8` group，使每组具有相同的慢卡结构。
- TP group 对称只能降低组间差异，不能恢复被慢卡拉低的绝对性能。

#### TP/PP

- 慢卡已覆盖所有节点时，把慢卡隔离进少数 PP stage 的空间消失；显存允许时先测试 `PP=1` 与节点内 TP。
- 如果 `PP=1` OOM，则使用可行的最小 PP，并按预测 stage time 重新分层，不能机械复用对称 TP 映射。

#### DP

- 用四个节点内 TP group 组成 `DP=4`，让每个 replica 含一张速度接近的慢卡，优先降低 replica skew。
- 慢卡速度不一致时按预测执行时间而非慢卡数量均衡；“一组一张”不再足够。

#### PP/MBN

- `PP=1` 时不需要填充 pipeline，从 `MBN=1` 起步；若增加 PP，则重新搜索 MBN。

### 当前场景实例与召回规则

```text
当前实例：PP=1, TP=8, DP=4, MBN=1
对称原则：每个DP replica的慢卡数量、速度分布和预测耗时尽量一致
```

### 触发条件

- 四张慢卡确实一节点一张且速度倍率接近。
- TP group 能严格限制在节点内，`PP=1` 不 OOM。

### 部署动作：均衡与对称

1. 每节点的 8 张卡组成一个 `TP=8` group，确保每组含一张慢卡。
2. 四个 TP group 组成 `DP=4`，保持副本结构对称。
3. 设置 `PP=1,MBN=1`，避免多个慢 stage 和不必要的 pipeline 填充。
4. 与相同参数的非均匀慢卡映射直接对照。

### 作用机制

- `PP=1` 避免四个慢点进入多个 pipeline stage。
- 对称映射把硬件异构转化为四个结构相同、性能接近的副本。
- 所有副本仍受慢卡限制，因此只能降低额外 skew，不能消除绝对 latency 损失。

### 预期观测

- 四个 TP group 均含一张慢卡，没有纯快卡 replica。
- replica skew 相对非均匀映射下降超过预定义 `δ_skew`。
- 端到端 latency 同时优于最小对照，且不超过业务上限。

### 失效边界与回退

- 慢卡集中在少数节点：按实际位置重新分组，不套用对称经验。
- 慢卡速度差异明显：按预测执行时间而非数量均衡。
- 所有 replica 均衡但绝对过慢：比较少卡、设备替换或其他隔离方案。
- `PP=1` OOM：使用满足显存的最小 PP，并重新平衡 stage。

## 5. 场景案例与最小对照

```text
第一候选：PP=1, TP=8, DP=4, MBN=1
映射：4个节点 × 每节点1张慢卡 × 每节点1个TP group
A：PP=16, TP=2, DP=1, MBN=64
B：PP=1,  TP=1, DP=32, MBN=1
C：相同1/8/4/1参数，但使用非均匀慢卡映射
```

## 6. 证据边界

- Score：与两慢卡场景完全相同，不读取慢卡数量、位置和速度。
- 拓扑：解释“所有副本变慢但更对称”的机制。
- Evaluation：来源报告第一候选最优，但没有原始数值和位置扰动实验。
- 判定：`KEEP_FOR_VALIDATION`；维持 `partially_supported`。

非对称分布对照见 [[two-slow-gpu-distributed-balance]]，局部隔离见 [[single-slow-gpu-isolation]]。
