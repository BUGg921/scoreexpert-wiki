---
title: <用决策命名，例如“通信非瓶颈时优先满卡部署”>
type: experience
status: unverified | partially_supported | active | superseded
confidence: low | medium | high

decision_type: gpu-count | pp | tp | dp | mbn | rank-mapping | slow-gpu
retrieval_keys:
  gpu_count: <适用范围，例如 16-64>
  gpu_per_node: <数量或范围>
  affinity_group_size: <数量或 unknown>
  topology: <节点内/组内/跨组带宽关系>
  slow_gpu: <无慢卡/数量/位置/倍率>
  model_constraint: <显存、层数、计算通信比>
  objective: <latency/throughput/cost>
  score_version: <若结论依赖特定 score>

sources:
  - <原始报告或 Evaluation>
validated_scenarios: <已验证场景数量>
updated: YYYY-MM-DD
---

# <经验标题>

## 1. 要解决的决策

在以下场景中，需要决定：

> <明确写出一个问题，例如：使用全部GPU，还是减少GPU以降低通信开销？>

一条经验只解决一个主要决策。PP、TP/DP、MBN如果触发条件不同，应拆成不同经验。

## 2. 一句话决策规则

当满足：

- <条件A>
- <条件B>
- <量化阈值或范围>

执行：

> <明确、可直接执行的部署动作>

否则：

> <对照动作、回退策略或重新搜索条件>

推荐写成：

IF <可判断条件>
THEN <部署动作>
ELSE <替代动作或重新搜索>

## 3. 召回条件

### 必须满足

- GPU总数：<范围>
- 每节点GPU数：<范围>
- 网络拓扑：<条件>
- 慢卡分布：<条件>
- 模型/显存：<条件>
- 优化目标：<latency/throughput等>

### 可以变化

- <允许变化但不会改变结论的变量及范围>
- <例如GPU数量可以从16变化到32>

### 明确排除

- <不能使用本经验的场景>
- <例如存在跨节点TP、模型无法在PP=1下放入显存>

## 4. 部署动作

### 选择步骤

1. 检查：<前置条件或指标>。
2. 计算/比较：<公式、阈值或候选集合>。
3. 当 `<条件>` 时选择 `<参数或映射>`。
4. 当 `<另一条件>` 时选择 `<替代参数>`。
5. 无法判断时，比较 `<最小对照候选集合>`。

### 第一候选

```text
PP=?
TP=?
DP=?
MBN=?
active_gpu=?
rank/group mapping=?