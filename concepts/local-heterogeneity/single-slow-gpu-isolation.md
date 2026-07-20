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

## 1. 场景描述

- **状态**：`active`。知识库所有者于 2026-07-20 审核为成熟经验，匹配条件时直接部署，无需重新运行真实 Evaluation。
- **优化目标**：延迟优先；主指标为端到端 latency，同时监控最慢 TP group 和最慢 PP stage。
- **资源拓扑**：32 张 GPU，4 个 8 卡节点，两个 16 卡亲和组。
- **异构分布**：只有一张约半速慢卡；当前案例为 GPU 7，异常仍能限制在一个局部 TP group 和 PP stage。
- **映射能力**：能够识别慢卡 rank，控制其 TP group、PP stage 和 layer mapping；调度器支持 16 个有效 stage。
- **硬匹配条件**：慢卡只有一张、速度约为正常卡一半、模型允许 `16 stage × 2 GPU/stage`，并能按预测耗时给慢卡 stage 少分层或少分计算。
- **准入依据**：来源明确给出小 TP、`DP=1`、高 PP 和大 MBN 四条经验；附件未包含原始 Evaluation 数值和可执行 layer mapping，但人工审核已完成准入。
- **目标总览**：[[latency-first-experience-summary]]。

## 2. 具体的并行策略

### 直接输出

```text
active_gpu=32
PP=16, TP=2, DP=1, MBN=64
映射：16 个 stage × 每 stage 2 卡；慢卡位于一个 2 卡 TP group
```

### 部署经验

- **卡的数量**：保留全部 32 卡，通过深 PP 隔离慢卡；显存、调度或慢 stage 护栏触发后，才回退到少卡或剔除慢卡方案。
- **TP**：使用 `TP=2` 将慢卡直接污染范围限制在一个 2 卡同步组。
- **TP/PP**：`TP=2` 与 `PP=16` 联动；深 PP 只有配合慢卡 stage 减层或减计算才构成有效隔离。
- **DP**：使用 `DP=1`，消除纯快 replica 等待含慢卡 replica 的同步问题。
- **PP/MBN**：深 PP 使用 `MBN=64` 降低 bubble；若显存、调度或 latency 护栏触发，依次回退到 32、16。

### 部署动作

1. 将慢卡映射到一个 2 卡 TP group。
2. 构造 `16 stage × 2 GPU/stage`，保持 `DP=1`。
3. 按预测 stage time 给慢卡 stage 少分层或少分计算。
4. 设置 `MBN=64`，并监控端到端 latency、最慢 stage、显存和调度开销。

### 适用边界与回退

- 允许慢卡在等价 rank 间重映射，但必须保持单慢卡、2 卡 TP group 和可重平衡 stage。
- 出现第二张跨区域慢卡：切换到 [[two-slow-gpu-distributed-balance]]。
- 每节点均出现慢卡：切换到 [[four-slow-gpu-symmetric-replicas]]。
- 无法控制 rank/stage mapping、OOM 或慢 stage 仍支配周期：回退到浅 PP、无 PP 或剔除慢卡方案。
- 正常卡场景改用 [[homogeneous-32gpu-score-candidate]]。

### 准入记录

- `ACCEPT_EXPERIENCE`；审核日期 2026-07-20，置信度 `high`。
