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
status: active
optimization_priority: latency-first
admitted_by: knowledge-base-owner
admitted_at: 2026-07-20
---

# 单慢卡局部隔离延迟经验

## 1. 场景描述

- **资源拓扑**：32 张 GPU，4 个 8 卡节点，两个 16 卡亲和组。
- **异构分布**：只有一张约半速慢卡；当前案例为 GPU 7，异常仍能限制在一个局部 TP group 和 PP stage。
- **映射能力**：能够识别慢卡 rank，控制其 TP group、PP stage 和 layer mapping；调度器支持 16 个有效 stage。
- **硬匹配条件**：慢卡只有一张、速度约为正常卡一半、模型允许 `16 stage × 2 GPU/stage`，并能按预测耗时给慢卡 stage 少分层或少分计算。
- **不适用条件**：无法控制 rank/stage mapping，出现第二张跨区域慢卡、每节点均出现慢卡或场景恢复为全正常卡；分别切换到 [[two-slow-gpu-distributed-balance]]、[[four-slow-gpu-symmetric-replicas]] 或 [[homogeneous-32gpu-score-candidate]]。

## 2. 具体的并行策略

### 部署策略

```text
active_gpu=32
PP=16, TP=2, DP=1, MBN=64
映射：16 个 stage × 每 stage 2 卡；慢卡位于一个 2 卡 TP group
执行：构造 16 个双卡 stage，保持 DP=1；慢卡 stage 按预测耗时减少层数或计算量
```

### 部署经验

- **卡的数量**：保留全部 32 卡，通过深 PP 隔离慢卡；显存、调度或慢 stage 护栏触发后，才回退到少卡或剔除慢卡方案。
- **TP**：使用 `TP=2` 将慢卡直接污染范围限制在一个 2 卡同步组。
- **TP/PP**：`TP=2` 与 `PP=16` 联动；深 PP 只有配合慢卡 stage 减层或减计算才构成有效隔离。
- **DP**：使用 `DP=1`，消除纯快 replica 等待含慢卡 replica 的同步问题。
- **PP/MBN**：深 PP 使用 `MBN=64` 降低 bubble；若显存、调度或 latency 护栏触发，依次回退到 32、16。

### 失效条件与回退

- 运行中 OOM 或调度开销超过护栏：将 MBN 从 64 依次回退到 32、16，必要时减少 PP 深度。
- 完成 stage 重平衡后慢 stage 仍支配流水线周期：回退到浅 PP、无 PP 或剔除慢卡方案。
