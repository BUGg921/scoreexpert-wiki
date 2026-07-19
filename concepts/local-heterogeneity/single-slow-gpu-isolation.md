---
title: 单慢卡局部隔离延迟经验
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

# 单慢卡局部隔离延迟经验

## Status

`unverified`。两套 score 都选择同一组合，但没有真实 latency、TP group time、PP stage time、显存或 layer mapping Evaluation。

## 优化目标与经验分类

- 主目标：**延迟优先**。
- 主分类：**局部异构**；单张慢卡仍可限制在少量同步组或 stage。
- 主指标：端到端 latency，并同时测最慢 TP group 和最慢 PP stage。
- 护栏：throughput、peak memory、OOM、大 MBN 调度开销和重复运行波动。
- 目标总览：[[latency-first-experience-summary]]。

## 1. 场景定义

- 32 张 GPU，4 个 8 卡节点，两个 16 卡亲和组。
- GPU 7 为唯一慢卡，来源描述其计算速度约为正常卡的一半。
- 能识别慢卡 rank，并控制其 TP group、PP stage 和 layer mapping。

## 2. 来源明确经验

来源总结为：

1. 用小 TP 限制慢卡同步污染范围。
2. 用 `DP=1` 避免多副本 straggler 同步等待。
3. 用高 PP 使用全部 32 卡并把慢卡限制到局部 stage。
4. 用大 MBN 降低深 PP bubble。

来源同时明确警告：`MBN=64` 可能来自搜索空间上界，不是物理最优常数。

## 3. 局部异构影响

- `TP group`：`TP=8` 时一张慢卡可能让同组 7 张快卡等待；`TP=2` 将直接污染范围缩小到 2 卡组。
- `DP replica`：只有部分 replica 含慢卡时，快 replica 会等待慢 replica。
- `PP stage`：慢卡 stage 可能成为整条流水线瓶颈；只增加 PP 而不重平衡层数不算有效隔离。

## 4. 部署经验总结

### 资源规模部署经验

> 来源提供使用全部 32 卡的当前候选；少卡对照和拓扑重建属于 Wiki 验证规则，不是来源已验证结论。

- **满卡条件**：来源用全部 32 卡构造 `16 stage × 2 GPU/stage`，目的是在不闲置资源的情况下隔离慢卡；只有隔离后的真实延迟收益大于深 PP 成本时才保留满卡方案。
- **少卡对照**：增加一个不使用慢卡或减少资源的可执行候选，检验“保留慢卡并隔离”是否优于“放弃部分算力”；候选仍需满足模型显存与并行整除约束。
- **拓扑重建**：减卡后必须重新生成 TP group 和 PP stage，不能在 `16/2/1` 映射中直接留下不完整 group。
- **当前实例**：32 张卡中含一张约半速慢卡，当前候选仍使用全部 32 卡；这属于待 Evaluation 的资源选择，不是已验证结论。

### 并行策略部署经验

#### TP

- 缩小 TP group 可以限制慢卡引起的同步污染；当前用 `TP=2` 将直接受影响范围限制在一个 2 卡组。
- TP 过小也会增加 PP 深度或其他通信成本，因此应与 `TP=4`、`TP=8` 对照，不能推广为“TP 越小越好”。

#### TP/PP

- 在满 32 卡且 `DP=1` 的约束下，降低 TP 会要求更深的 PP；`TP=2,PP=16` 是“缩小 TP 污染范围”和“增加 PP bubble”之间的当前候选。
- PP 只有在慢卡 stage 同时减少层数或计算量时才形成隔离；只把 PP 调大不算完成隔离。

#### DP

- 异常仍局限于一张卡时，从 `DP=1` 起步，避免纯快 replica 等待含慢卡 replica。
- 慢卡跨多个区域分布后，`DP=1` 不再是默认规则，应切换到分布式异构经验重新均衡。

#### PP/MBN

- 深 PP 需要用较大 MBN 降低 bubble，但 MBN 同时会增加调度、显存或端到端时延。
- `MBN=64` 只是当前搜索上界实例，必须与 16、32 一起实测选择。

### 当前场景实例与召回规则

```text
当前实例：PP=16, TP=2, DP=1, MBN=64
隔离原则：小TP限制同步污染 + DP=1避免副本等待 + PP隔离局部慢点
```

### 触发条件

- 只有一张局部慢卡，且能够控制 rank/group/stage 映射。
- 模型和调度器支持 16 个有效 stage，并允许按预测耗时分层。

### 部署动作：隔离

1. 将慢卡放入一个 2 卡 TP group。
2. 构造 `16 stage × 2 GPU/stage`，保持 `DP=1`。
3. 根据 profile 给慢卡 stage 少分层或少分计算。
4. 以 `MBN=64` 复现来源，同时测试 16、32，排除边界伪优。

### 作用机制

- 小 TP 缩小慢卡同步污染范围。
- `DP=1` 消除快慢 replica 之间的同步等待。
- PP 把局部异常限制到少数 stage；stage 重平衡决定隔离是否真正有效。
- 大 MBN 降低 bubble，但可能增加 latency、显存和调度成本。

### 预期观测

- 慢卡影响主要出现在一个 TP group 和一个 PP stage。
- 重平衡后最慢 stage 不再长期支配端到端 latency。
- 推荐候选相对全部对照的目标 latency 改善超过预定义 `δ`。

### 失效边界与回退

- 出现第二张跨区域慢卡：转到 [[two-slow-gpu-distributed-balance]]。
- 慢 stage 仍决定周期：重新切层或回退到浅 PP/无 PP。
- `MBN=64` 增加 latency 或显存：采用真实 Evaluation 更优的 MBN。
- 无法控制 rank 或 stage mapping：停止复用隔离经验。

## 5. 场景案例与最小对照

```text
第一候选：PP=16, TP=2, DP=1, MBN=64
A：PP=1,  TP=8, DP=4, MBN=1
B：PP=8,  TP=4, DP=1, MBN=64
C：PP=4,  TP=8, DP=1, MBN=64
D：PP=16, TP=2, DP=1, MBN∈{16,32,64}
```

## 6. 证据边界

- Score：两套权重都在当前因子候选中选择 `16/2/1/64`。
- 拓扑：小 TP、低 DP 和慢 stage 重平衡属于可证伪机制；score 没有读取 GPU 7 或速度倍率。
- Evaluation：缺失。
- 判定：`KEEP_FOR_VALIDATION`；补齐 stage mapping 和真实指标前不得升级。

正常卡对照见 [[homogeneous-32gpu-score-candidate]]，四慢卡边界见 [[four-slow-gpu-symmetric-replicas]]。
