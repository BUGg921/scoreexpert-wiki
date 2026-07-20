---
title: 单慢卡局部隔离延迟经验
created: 2026-07-15
updated: 2026-07-20
type: concept
tags: [scoreexpert, deployment, experience, local-heterogeneity, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence, decision-guide]
sources: [raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md]
confidence: high
contested: false
contradictions: []
experience_category: local-heterogeneity
---

# 单慢卡局部隔离延迟经验

## Status

`active`。知识库所有者于 2026-07-20 将本页确认为成熟经验；匹配单慢卡、拓扑和映射条件时可直接部署，无需重新运行真实 Evaluation。来源附件缺少原始 latency、group/stage time 和显存数据，仅作为证据完整度说明。

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

> 来源提供使用全部 32 卡的成熟候选；少卡与拓扑重建作为失效后的回退规则保留。

- **满卡条件**：来源用全部 32 卡构造 `16 stage × 2 GPU/stage`；场景完全匹配时直接保留慢卡并用深 PP 隔离。
- **少卡回退**：慢 stage、显存或调度护栏触发失效时，改用不含慢卡或减少资源的可执行候选。
- **拓扑重建**：减卡后必须重新生成 TP group 和 PP stage，不能在 `16/2/1` 映射中直接留下不完整 group。
- **当前实例**：32 张卡中含一张约半速慢卡，成熟策略使用全部 32 卡。

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
- `MBN=64` 是本页成熟实例；16、32 仅作为显存、调度或时延护栏触发后的回退。

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
4. 设置 `MBN=64`；若显存、调度或时延护栏触发，再回退到 32 或 16。

### 作用机制

- 小 TP 缩小慢卡同步污染范围。
- `DP=1` 消除快慢 replica 之间的同步等待。
- PP 把局部异常限制到少数 stage；stage 重平衡决定隔离是否真正有效。
- 大 MBN 降低 bubble，但可能增加 latency、显存和调度成本。

### 预期观测

- 慢卡影响主要出现在一个 TP group 和一个 PP stage。
- 重平衡后最慢 stage 不再长期支配端到端 latency。
- 部署后的端到端 latency、显存和调度开销保持在业务护栏内。

### 失效边界与回退

- 出现第二张跨区域慢卡：转到 [[two-slow-gpu-distributed-balance]]。
- 慢 stage 仍决定周期：重新切层或回退到浅 PP/无 PP。
- `MBN=64` 触发 latency 或显存护栏：依次回退到 32 或 16。
- 无法控制 rank 或 stage mapping：停止复用隔离经验。

### 直接推理契约

- **硬匹配字段**：32 卡、4 个 8 卡节点、仅一张约半速慢卡、可识别慢卡 rank，并能控制 TP group、PP stage 和 layer mapping。
- **允许变换**：慢卡可在等价 rank 间重映射，但必须落入一个 2 卡 TP group 和一个减少计算量的 stage；不允许扩展到多慢卡。
- **直接输出**：`PP=16,TP=2,DP=1,MBN=64`，慢卡 stage 按预测耗时少分层或少分计算。
- **停止条件**：出现第二张跨区域慢卡、无法控制映射、OOM 或慢 stage 仍支配周期时，转入分布式经验或回退方案。

## 5. 主策略与回退

```text
主策略：PP=16, TP=2, DP=1, MBN=64
回退A：PP=1,  TP=8, DP=4, MBN=1
回退B：PP=8,  TP=4, DP=1, MBN=64
回退C：PP=4,  TP=8, DP=1, MBN=64
回退D：PP=16, TP=2, DP=1, MBN∈{32,16}
```

## 6. 证据边界

- Score：两套权重都在当前因子候选中选择 `16/2/1/64`。
- 拓扑：小 TP、低 DP 和慢 stage 重平衡属于可证伪机制；score 没有读取 GPU 7 或速度倍率。
- 来源附件：未包含原始 Evaluation 数值和可执行 layer mapping。
- 准入：`ACCEPT_EXPERIENCE`；知识库所有者于 2026-07-20 人工审核为成熟经验，状态为 `active`。

正常卡对照见 [[homogeneous-32gpu-score-candidate]]，四慢卡边界见 [[four-slow-gpu-symmetric-replicas]]。
