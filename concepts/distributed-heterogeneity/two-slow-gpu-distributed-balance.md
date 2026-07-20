---
title: 两张跨亲和组慢卡的均衡延迟经验
created: 2026-07-15
updated: 2026-07-20
type: concept
tags: [scoreexpert, deployment, experience, distributed-heterogeneity, distribution-imbalanced, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence, decision-guide]
sources: [raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md, raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
confidence: high
contested: false
contradictions: []
experience_category: distributed-heterogeneity
status: active
optimization_priority: latency-first
admitted_by: knowledge-base-owner
admitted_at: 2026-07-20
---

# 两张跨亲和组慢卡的均衡延迟经验

## 1. 场景描述

- **资源拓扑**：32 卡，4 个 8 卡节点，两个 16 卡亲和组。
- **异构分布**：两张慢卡分别位于两个亲和组，形成两个含慢卡 replica 和两个纯快卡 replica；异常已经不能视为单个局部坏点。
- **模型约束**：模型能在单节点 `TP=8,PP=1` 下满足显存要求，TP group 可以严格限制在节点内。
- **硬匹配条件**：两张慢卡跨亲和组分散，不能集中在同一节点或同一 TP group；四节点均可完整参与。
- **不适用条件**：慢卡集中到一个局部区域、每节点均出现慢卡或不存在慢卡；分别切换到 [[single-slow-gpu-isolation]]、[[four-slow-gpu-symmetric-replicas]] 或 [[homogeneous-32gpu-score-candidate]]。

## 2. 具体的并行策略

### 部署策略

```text
active_gpu=32
PP=1, TP=8, DP=4, MBN=1
映射：每节点一个 8 卡 TP group 和一个 DP replica
执行：每节点建立一个 TP group，四组组成 DP=4；标记两个含慢卡 replica 和两个纯快卡 replica
```

### 部署经验

- **卡的数量**：使用四个完整节点和全部 32 卡；减少资源时必须重建完整 TP/DP 拓扑，并重新判断慢卡是否仍属于分布式异构。
- **TP**：使用节点内 `TP=8`，避免高频 TP 通信跨节点；含慢卡 TP group 仍会整体变慢。
- **TP/PP**：慢卡跨区域后，深 PP 容易形成多个慢 stage，因此使用 `PP=1,TP=8`，从逐点隔离切换为节点内 TP。
- **DP**：使用 `DP=4` 扩展到四个节点；DP 不会自动消除快慢副本等待，运行时需监控 replica skew。
- **PP/MBN**：`PP=1` 消除 pipeline bubble，因此使用 `MBN=1`；增加 PP 后必须重新选择 MBN。

### 失效条件与回退

- 运行中 `PP=1` OOM：回退到满足显存约束的最小 PP，并重新组合 TP/DP/MBN。
- replica skew 超过业务护栏：按预测执行时间重新映射慢卡；仍无法收敛时重新组合并行参数。
