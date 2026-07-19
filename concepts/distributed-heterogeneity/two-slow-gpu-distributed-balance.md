---
title: 两张跨亲和组慢卡的无流水线均衡经验
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

# 两张跨亲和组慢卡的无流水线均衡经验

## Status

`partially_supported`。来源明确称 `PP=1,TP=8,DP=4,MBN=1` 为当前 Evaluation 最优，并给出 score 复算和拓扑解释；但没有提供慢卡 ID、速度倍率、原始延迟、重复波动和完整候选 Evaluation 表。

## 经验分类

- 主分类：**分布式异构**。
- 分布形态：跨亲和组、非对称分布；两个慢 replica 与两个快 replica 并存。
- 分类依据：慢卡已跨多个局部区域分散，核心问题从单点隔离转为避免多个慢 stage，并控制 DP replica skew。
- 目标总览：[[latency-first-experience-summary]]。

## 1. 要解决的决策

两张慢卡分别进入两个亲和组后，是否继续使用单慢卡的深 PP 隔离策略，还是取消流水线并使用节点内 TP、节点间 DP。

## 2. 一句话决策规则

**IF** 两张慢卡跨亲和组分散、模型能在单个 8 卡 TP group 中放下，且深 PP 会形成多个慢 stage，**THEN** 以 `PP=1,TP=8,DP=4,MBN=1` 构造四个节点内 TP replica，并重点测量快慢 replica skew；**ELSE** 根据慢卡实际位置重新分组，不直接套用该组合。

## 3. 来源明确经验

两份来源共同表达了从“隔离”到“均衡”的策略切换：

1. 一张慢卡是局部异常，可以尝试小 TP、高 PP 隔离。
2. 两张慢卡跨亲和组分布后，深 PP 容易形成多个慢 stage，隔离收益下降。
3. 若模型能在一个节点内放下，优先取消深流水线，在节点内使用 TP，再通过 DP 扩展。
4. `PP=1` 时从 `MBN=1` 起步，避免无流水线条件下增加额外 microbatch 成本。

当前实例：

```text
PP=1, TP=8, DP=4, MBN=1
```

## 4. 召回条件

### 必须满足

- 32 卡、每节点 8 卡、每亲和组 16 卡。
- 两张慢卡分别位于两个亲和组，并落在两个节点中。
- 模型在 `PP=1,TP=8` 下满足显存约束。
- TP group 能按节点边界构造，避免 TP 跨节点。

### 仍需补齐

- 两张慢卡的实际 GPU ID、速度倍率和是否位于同一节点内位置。
- 原始 Evaluation latency、吞吐、显存和重复波动。

### 明确排除

- 两张慢卡集中在同一节点或同一 TP group。
- 四个节点都被慢卡覆盖；此时使用 [[four-slow-gpu-symmetric-replicas]]。
- 模型必须使用 PP 才能放入显存。

## 5. 部署动作

1. 设置 `PP=1`，避免把两个慢点串入多个 pipeline stage。
2. 每个节点建立一个 `TP=8` group，禁止 TP 跨节点。
3. 四个节点组成 `DP=4`；记录哪两个 replica 含慢卡、哪两个为纯快卡。
4. 设置 `MBN=1` 作为无流水线起点。
5. 与单慢卡隔离组合和 score 近邻候选做 Evaluation，测量 replica skew。

### 第一基线与映射

```text
PP=1, TP=8, DP=4, MBN=1
Node 0..3：各自构成一个 8 卡 TP group 和一个 DP replica
```

### 最小对照集合

```text
A: PP=16, TP=2, DP=1, MBN=64   # 单慢卡隔离策略
B: PP=1,  TP=1, DP=32, MBN=1   # score 仅低 0.28 的近邻
C: PP=2,  TP=4, DP=4, MBN=16   # 浅 PP 对照
```

## 6. 核心定量规则

在来源的 `num_layers=32,GBS=8,total_devices=32` 和当前 score 下：

```text
Score(PP=1,TP=8,DP=4,MBN=1) = 1007.520
Score(PP=1,TP=1,DP=32,MBN=1) = 1007.240
差值 = 0.28
```

因此 score 对 `8/4` 只有弱偏好。可复用的强规则是：模型允许时先比较“无 PP、低 MBN”方案；`TP=8,DP=4` 必须由节点映射和 Evaluation 共同确认，不能仅凭 score 外推。

## 7. 作用机制与证据

### Score 证据

- `-300×bubble` 强制偏向 `PP=1`。
- `PP=1` 后，`-0.15×TP×MBN` 使 `MBN=1` 更有利。
- score 不读取慢卡数量、位置和速度；两慢卡与四慢卡得到相同分数。

### 拓扑与 Evaluation 证据

- 来源明确报告该组合是两慢卡场景的 Evaluation 最优。
- 两张慢卡使两个 TP replica 变慢、两个保持较快；DP step 会等待慢 replica。
- 取消深 PP 避免形成多个慢 stage，但不会消除 DP replica imbalance。

## 8. 预期观测与验收

- `PP=1` 时 bubble 为 0。
- 两个含慢卡 replica 的迭代时间高于两个纯快卡 replica。
- 推荐组合的端到端目标指标应优于最小对照集合，并超过预先定义的最小有效差值 `δ`。
- 必须报告 `max(replica_time)-avg(replica_time)` 或等价 skew；若 skew 不可接受，应重新映射或重新搜索。

来源只报告“Evaluation 最优”，没有原始数值，因此暂不能升级为 `active`。

## 9. 失效边界与回退

| 失效信号 | 回退动作 |
|---|---|
| 两张慢卡集中到同一节点 | 重新比较局部隔离与重映射 |
| DP replica skew 过大 | 调整慢卡分布或减少不对称副本 |
| `PP=1` OOM | 选择满足显存的最小 PP，重新测慢 stage |
| 深 PP 对照更快 | 恢复隔离分支并记录慢卡位置边界 |
| 慢卡数量增至每节点一张 | 切换到四慢卡对称经验 |

## 10. 准入判定

- [x] 有明确的跨亲和组分布条件。
- [x] 来源报告当前 Evaluation 最优。
- [x] 有 score 复算、对照候选和可观测 skew。
- [ ] 有原始 Evaluation 数值、重复波动和慢卡 ID/倍率。
- [ ] 经过慢卡位置扰动仍成立。

结论：`partially_supported`，可生成验证提案，尚不能作为默认正式部署建议。相关场景见 [[single-slow-gpu-isolation]] 与 [[scoreexpert]]。
