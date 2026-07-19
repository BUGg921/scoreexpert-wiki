---
title: 单慢卡局部隔离经验草案
created: 2026-07-15
updated: 2026-07-19
type: concept
tags: [scoreexpert, deployment, experience, local-heterogeneity, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence, hypothesis, decision-guide]
sources: [raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md]
confidence: low
contested: false
contradictions: []
experience_category: local-heterogeneity
---

# 单慢卡局部隔离经验草案

## Status

`unverified`。来源给出两套 score 及同一个最优组合，但没有可核验的真实 latency、吞吐和显存对照。本页只能用于生成单慢卡 Evaluation 基线。

## 经验分类

- 主分类：**局部异构**。
- 分类依据：只有一张慢卡且异常集中在一个局部区域，部署目标是缩小同步污染范围并尝试用 PP stage 隔离。
- 目标总览：[[latency-first-experience-summary]]。

## 1. 要解决的决策

32 卡中只有一张局部慢卡时，是继续使用节点内大 TP，还是缩小同步污染范围并用 PP 隔离慢卡。

## 2. 一句话决策规则

**IF** 只有一张约半速慢卡、异常局限在一个亲和组，模型允许 16 段流水线且能够做 stage/layer 再均衡，**THEN** 以 `PP=16,TP=2,DP=1,MBN=64` 作为隔离型 Evaluation 基线；**ELSE** 不直接复用深 PP，改测 [[homogeneous-32gpu-score-candidate]] 或重新搜索。

`MBN=64` 是来源搜索空间上界，不是物理最优常数。

## 3. 来源明确经验

来源的最终总结是：

1. 用小 TP 缩小慢卡同步污染范围。
2. 用 `DP=1` 避免多个副本被 straggler 同步拖累。
3. 用高 PP 吃满 32 卡，并把局部慢卡限制在少数 pipeline stage。
4. 用大 MBN 降低深 PP bubble；但 `MBN=64` 是 score 单调奖励和候选上界共同形成的边界解。

来源对应实例：

```text
slow_gpu_id=7, slow_speed≈0.5×
PP=16, TP=2, DP=1, MBN=64
```

## 4. 召回条件

### 必须满足

- 32 张 GPU，每节点 8 卡，每亲和组 16 卡。
- 仅 GPU 7 为慢卡，来源描述其计算速度约为正常卡的一半。
- 慢卡是局部异常，没有第二张慢卡跨亲和组出现。
- 模型允许 `PP=16`，并能为慢卡 stage 减少层数或计算量。
- 当前任务是选择验证基线，而不是跳过 Evaluation 直接上线。

### 明确排除

- 两张及以上慢卡分散在多个亲和组；此时参照 [[two-slow-gpu-distributed-balance]]。
- 模型层数、显存或调度器不支持 16 个有效 stage。
- 大 MBN 带来不可接受的端到端时延、显存或 kernel 调度开销。
- 无法确定慢卡 rank，或无法控制 TP group 与 PP stage 映射。

## 5. 部署动作

1. 将慢卡 GPU 7 放入一个 2 卡 TP group，使它最多直接拖慢同组另一张卡。
2. 构造 `16 stage × 2 GPU/stage`，保持 `DP=1`，避免跨 replica 等待。
3. 慢卡所在 stage 少分层或少分计算；来源没有给出具体层数，必须按 profile 生成映射。
4. 从来源候选 `MBN=64` 开始复现 score，同时至少测试较小 MBN，确认 64 不是纯边界伪优。
5. 与无 PP 基线和其他 PP/TP 因子对做真实 Evaluation。

### 第一基线

```text
PP=16, TP=2, DP=1, MBN=64
```

### 最小对照集合

```text
A: PP=1,  TP=8, DP=4, MBN=1
B: PP=8,  TP=4, DP=1, MBN=64
C: PP=4,  TP=8, DP=1, MBN=64
D: PP=16, TP=2, DP=1, MBN∈{16,32,64}
```

## 6. 核心定量规则

固定 `DP=1,MBN=64,PP×TP=32` 时，来源两套 score 都在所列因子对中选择 `PP=16,TP=2`：

| PP | TP | 策略一关键惩罚 | 策略二关键惩罚 |
|---:|---:|---:|---:|
| 32 | 1 | -23.95 | -29.32 |
| 16 | 2 | **-22.44** | **-28.49** |
| 8 | 4 | -29.42 | -35.93 |
| 4 | 8 | -50.46 | -57.24 |

可证规则是“在这两套权重和候选约束下，`TP=2` 的同步成本与 `PP=16` 的 bubble 达到 score 折中”；不能外推为所有单慢卡模型都固定使用 16/2。

## 7. 作用机制与证据边界

| 动作 | 预期机制 | 当前证据 |
|---|---|---|
| TP 从 8 降到 2 | 缩小慢卡同步污染组 | score 惩罚 TP；无真实 group 时间 |
| DP 降到 1 | 避免多副本 straggler 等待 | score 惩罚 DP；无真实同步时间 |
| PP 增到 16 | 将局部慢卡限制在少数 stage | 拓扑推理；无 stage profile |
| MBN 增到 64 | 降低 bubble | score 直接支持，但 64 是搜索上界 |

score 没有读取 GPU 7、速度倍率或真实 stage 时间，因此“慢卡隔离有效”仍需要 Evaluation。

## 8. 预期观测与验收

- 慢卡影响主要集中在其 TP group 和 PP stage。
- 慢卡 stage 经再均衡后不应持续成为唯一吞吐瓶颈。
- 推荐基线相对所有对照候选的目标指标改善超过预先定义的 `δ`，且重复实验差异大于测量波动。
- MBN=64 必须优于或合理折中于 16、32；否则回退到实际最优 MBN。

来源未给出 `δ` 和 Evaluation 数值，因此当前不能判定命中。

## 9. 失效边界与回退

| 失效信号 | 回退动作 |
|---|---|
| 出现第二张跨区域慢卡 | 切换到两慢卡经验，不继续加深 PP |
| 慢 stage 仍决定吞吐 | 重做 layer rebalance 或改用低 PP |
| MBN=64 增加端到端时延 | 扫描 MBN，取消边界值默认 |
| PP=16 不满足模型/显存约束 | 重新搜索可行的最小同步污染方案 |
| 无 PP 基线更快 | 反驳本草案并保留对照证据 |

## 10. 准入判定

- [x] 有明确召回条件、基线和对照集合。
- [x] 两套 score 都选择相同组合。
- [ ] 有真实 Evaluation 指标和重复波动。
- [ ] 有可执行的 stage/layer mapping。
- [ ] 证明 MBN=64 不是搜索上界伪优。

结论：保持 `unverified`；补证前不能作为默认正式部署建议。四场景入口见 [[scoreexpert]]。
