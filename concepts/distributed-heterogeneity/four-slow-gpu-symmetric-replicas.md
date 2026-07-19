---
title: 四张均匀慢卡的对称副本经验
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

# 四张均匀慢卡的对称副本经验

## Status

`partially_supported`。来源明确称 `PP=1,TP=8,DP=4,MBN=1` 为当前 Evaluation 最优，并说明一节点一张慢卡时的拓扑机制；但没有原始延迟、速度倍率、卡号、重复波动和位置扰动结果。

## 经验分类

- 主分类：**分布式异构**。
- 分布形态：一节点一张慢卡的对称分布；四个 DP replica 具有相同慢卡数量。
- 分类依据：异构覆盖全部节点，核心目标不是隔离单点，而是构造结构和预测执行时间尽量一致的副本。
- 目标总览：[[latency-first-experience-summary]]。

## 1. 要解决的决策

四张慢卡均匀覆盖四个节点时，是尝试用多个 PP stage 隔离慢卡，还是让每个 DP replica 具有相同的慢卡结构。

## 2. 一句话决策规则

**IF** 四个节点各有一张速度相近的慢卡，模型能在节点内 `TP=8` 下放入，**THEN** 设置 `PP=1,TP=8,DP=4,MBN=1`，让每个 DP replica 都包含一张慢卡，以牺牲绝对速度换取 replica 对称性；**ELSE** 按真实慢卡位置重新映射，不能套用“一节点一张”的均匀化结论。

## 3. 来源明确经验

来源明确提出：

1. 当慢卡均匀覆盖所有节点时，优先追求 replica 间对称性，而不是把慢卡放入多个 PP stage。
2. 每个节点内部组成一个 `TP=8` group，四个节点组成 `DP=4`。
3. 禁用不必要的 PP，并以 `MBN=1` 避免无流水线条件下的额外切分成本。
4. 该策略不能恢复慢卡造成的绝对性能损失，但可能降低 DP replica 间的 straggler skew。

## 4. 召回条件

### 必须满足

- 32 卡、4 个节点、每节点 8 卡、每亲和组 2 个节点。
- 四张慢卡均匀分布为“一节点一张”，且速度倍率相近。
- 模型在 `PP=1,TP=8` 下满足显存约束。
- TP group 严格限制在节点内。

### 明确排除

- 四张慢卡集中在少数节点或速度倍率差异明显。
- 实际卡号映射不满足每个 TP group 一张慢卡。
- 模型必须使用 PP 才能放入显存。
- 优化目标要求恢复绝对单 replica 性能，而不是降低 replica skew。

## 5. 部署动作

1. 将四张慢卡分配为每个节点一张；若物理位置不可调整，先核对实际 rank mapping。
2. 每个节点的 8 张卡组成一个 `TP=8` group，使四个 group 具有相同的慢卡数量。
3. 四个 TP group 组成 `DP=4`，保持 replica 结构对称。
4. 设置 `PP=1,MBN=1`，避免多个慢 stage 和不必要的 pipeline 填充。
5. 同时测量绝对 replica 时间和 replica 间方差，不能只看平均分数。

### 第一基线

```text
PP=1, TP=8, DP=4, MBN=1
4个节点 × 每节点1张慢卡 × 每节点1个TP group
```

### 最小对照集合

```text
A: PP=16, TP=2, DP=1, MBN=64   # 多慢 stage 隔离对照
B: PP=1,  TP=1, DP=32, MBN=1   # score 近邻
C: 相同参数但慢卡非均匀映射   # 验证“对称性”机制
```

## 6. 核心定量规则

本经验的可迁移条件不是“只要有四张慢卡就使用 8/4”，而是：

```text
每个 DP replica 的慢卡数量与速度分布尽量一致
```

可用 replica skew 表达验证目标：

```text
skew = (max(replica_time)-avg(replica_time)) / avg(replica_time)
```

推荐映射应使 skew 相对非均匀映射下降超过预先定义的 `δ_skew`。来源没有给出 `δ_skew` 和原始时间，因此只能作为待验证阈值。

## 7. 作用机制与证据

### Score 证据

- 与两慢卡场景相同，score 选择 `1/8/4/1`，分数为 `1007.520`。
- score 不读取慢卡数量、位置和速度，因此不能解释四张慢卡的均匀化机制。

### 拓扑与 Evaluation 证据

- 来源报告该组合是当前四慢卡 Evaluation 最优。
- 每个 TP group 各含一张慢卡，四个 replica 都会变慢，但执行速度更接近。
- 深 PP 可能产生多个慢 stage；最慢 stage 仍决定流水线吞吐。

## 8. 预期观测与验收

- 四个 TP group 均包含一张慢卡，没有纯快卡 replica。
- replica 间执行时间方差低于两慢卡或非均匀四慢卡映射。
- 绝对 latency 可能比两慢卡场景更差，这不构成机制失败；关键是 skew 是否下降以及端到端指标是否优于对照。
- 推荐映射必须在重复 Evaluation 中超过预定义的 `δ` 和 `δ_skew`。

来源没有提供这些数值，暂不能升级为 `active`。

## 9. 失效边界与回退

| 失效信号 | 回退动作 |
|---|---|
| 慢卡并非一节点一张 | 按实际位置重新构造对称 group |
| 慢卡速度差异明显 | 按预测时间而非数量做均衡 |
| 所有 replica 虽均衡但绝对过慢 | 比较少卡、隔离或替换设备方案 |
| `PP=1` OOM | 使用满足显存的最小 PP 并重新平衡 stage |
| 非均匀映射更快且 skew 可接受 | 收窄或反驳对称映射经验 |

## 10. 准入判定

- [x] 有明确的一节点一慢卡召回条件。
- [x] 来源报告当前 Evaluation 最优。
- [x] 有可执行节点级映射和可观测 skew。
- [ ] 有卡号、速度倍率和原始 Evaluation 数值。
- [ ] 有均匀与非均匀映射的直接对照。
- [ ] 经过慢卡位置、速度扰动仍成立。

结论：`partially_supported`，可生成验证提案，尚不能作为默认正式部署建议。相关场景见 [[two-slow-gpu-distributed-balance]]、[[homogeneous-32gpu-score-candidate]] 与 [[scoreexpert]]。
