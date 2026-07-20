---
title: 标准 32 卡同构延迟基线经验
created: 2026-07-14
updated: 2026-07-20
type: concept
tags: [scoreexpert, deployment, experience, homogeneous-baseline, gpu, topology, pp, tp, dp, mbn, evidence, decision-guide]
sources: [raw/articles/scoring-strategy-analysis-2026-07-14.md]
confidence: high
contested: false
contradictions: []
experience_category: homogeneous-baseline
---

# 标准 32 卡同构延迟基线经验

## Status

`active`。知识库所有者于 2026-07-20 将本页确认为成熟经验；匹配本页硬条件时可直接生成部署策略，无需重新运行真实 Evaluation。来源附件缺少原始 latency、throughput、显存和通信数据，仅作为证据完整度说明，不影响准入状态。

## 优化目标与经验分类

- 主目标：**延迟优先**。
- 主分类：**同构基线**；无已知慢卡或设备异构。
- 主指标：运行前指定平均、P50、P95 或 P99 latency 之一。
- 护栏：throughput、peak memory、OOM、通信时间和重复运行波动。
- 目标总览：[[latency-first-experience-summary]]。

## 1. 场景定义

- GPU：32 张，4 个节点，每节点 8 卡。
- 亲和组：每两个节点、共 16 卡为一组。
- 带宽：节点内最高，亲和组内跨节点次之，跨亲和组最低。
- 约束：`PP×TP×DP=32`、`TP≤8`，score 和候选空间与来源一致。

## 2. 来源明确经验

来源按顺序给出四条经验：

1. **满卡优先**：当前判断 idle 损失大于通信优化收益，因此优先使用全部 32 卡；需要用仿真寻找少卡反转边界。
2. **TP 与 DP 接近平衡并略偏 TP**：在当前约束中选择 `TP:DP=2:1`，实例为 `TP=8,DP=4`。
3. **PP 倾向于 1**：避免当前 score 中只有惩罚、没有收益的 pipeline bubble。
4. **MBN 倾向于 1**：`-0.5×(MBN-1)²` 在 1 处取最大值。

## 3. 部署经验总结

### 资源规模部署经验

> 来源明确支持当前 score 下的满卡优先；少卡反转和拓扑重建作为经验的失效与回退边界保留。

- **满卡条件**：当前 score 判断 idle 损失大于通信优化收益；场景完全匹配时直接使用全部可用卡。
- **少卡回退**：若运行护栏或已知通信边界触发失效，再采用满足模型显存与并行整除约束的 `active_gpu<32` 候选。
- **拓扑粒度**：减卡后应重新构造完整 TP group、DP replica 或 PP stage，不能只从现有 32 卡映射中随意去掉 rank。
- **当前实例**：集群可用 32 张正常卡，成熟策略使用 `active_gpu=32`；32 是本场景资源实例，不是固定部署经验。

### 并行策略部署经验

#### TP

- 当单节点有 8 卡且 `TP≤8` 时，优先把 TP group 限制在单节点内，避免高频 TP 通信跨节点。
- 当前 score 偏好较大的 TP；该规则只在本页拓扑和 `TP≤8` 边界内直接复用，不能推广为“TP 越大越好”。

#### TP/DP

- 在当前 32 卡离散空间中，直接使用 TP 与 DP 接近平衡且略偏 TP 的组合。
- `TP:DP=2:1`、即 `TP=8,DP=4` 是本场景实例，不是跨卡数、跨拓扑的固定比例。

#### PP

- 模型在 `PP=1` 下不 OOM 时，先用无流水线方案消除 bubble；若显存不满足，则选择可行的最小 PP 并重新搜索。

#### PP/MBN

- `PP=1` 时无需用更多 microbatch 填充流水线，因此从 `MBN=1` 起步。
- PP 增大后必须重新扫描 MBN，不能沿用 `MBN=1`。

### 当前场景实例与召回规则

```text
当前实例：PP=1, TP=8, DP=4, MBN=1, active_gpu=32
可迁移规则：匹配边界内使用满卡、无PP、低MBN和接近平衡的TP/DP
```

`TP:DP=2:1` 只属于当前 32 卡、`TP≤8` 的离散候选，不能跨卡数直接复用。

### 触发条件

- 32 张正常卡且拓扑与候选约束完全匹配。
- 模型能在 `PP=1` 下满足显存约束。
- 当前任务是生成延迟优先部署策略。

### 部署动作

1. 部署 `PP=1,TP=8,DP=4,MBN=1`。
2. 将 `TP=8` group 限制在单节点内；这是 Wiki 拓扑映射要求，不是 score 直接证明。
3. 将 `TP=4,DP=8`、浅 PP 和少卡候选保留为触发失效边界后的回退。

### 作用机制

- 满卡消除 idle penalty；是否真正降低 latency 仍取决于通信成本。
- `PP=1` 消除 bubble；`MBN=1` 避免当前二次惩罚。
- `8/4` 在当前 TP/DP 评分项中最高，但真实通信层级尚未进入公式。

### 预期观测

- 相同搜索约束下可复现 `1/8/4/1` 的 score 第一名。
- 部署后的目标 latency 保持在业务阈值内。
- 运行监控没有 OOM、throughput 或尾延迟不可接受的退化。

### 失效边界与回退

- `PP=1` OOM：选择满足显存约束的最小 PP 并重新搜索。
- 少卡候选更快：停止“满卡优先”，记录通信收益反转边界。
- TP/DP 对照更快：停止复用 `2:1`，按新卡数和拓扑重算。
- 出现慢卡：切换到 [[single-slow-gpu-isolation]] 或分布式慢卡经验。

### 直接推理契约

- **硬匹配字段**：32 张正常卡、4 个 8 卡节点、两个 16 卡亲和组、`TP≤8`、`PP×TP×DP=32`，且模型在 `PP=1` 下不 OOM。
- **允许变换**：只允许同一拓扑内的 rank 重排；`TP:DP=2:1` 不跨卡数或拓扑换算。
- **直接输出**：`active_gpu=32,PP=1,TP=8,DP=4,MBN=1`，每节点一个 `TP=8` group。
- **停止条件**：出现慢卡、OOM、节点规模或亲和组变化时停止直接复用，转入对应异构经验或补库。

## 4. 主策略与回退

```text
主策略：PP=1, TP=8, DP=4, MBN=1
回退A：PP=1, TP=4, DP=8, MBN=1
回退B：PP=2, TP=4, DP=4, MBN∈{1,2,4}
回退C：满足完整并行拓扑的 active_gpu<32 候选
```

## 5. 证据边界

- Score：能够解释满卡、`PP=1`、`TP=8,DP=4`、`MBN=1` 的当前排名。
- 拓扑：只有带宽层级描述，没有定量通信数据或来源明确的 rank mapping。
- 来源附件：未包含原始 Evaluation 数值。
- 准入：`ACCEPT_EXPERIENCE`；知识库所有者于 2026-07-20 人工审核为成熟经验，状态为 `active`。

相关分布式对照见 [[two-slow-gpu-distributed-balance]] 和 [[four-slow-gpu-symmetric-replicas]]。
