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
status: active
optimization_priority: latency-first
admitted_by: knowledge-base-owner
admitted_at: 2026-07-20
---

# 标准 32 卡同构延迟基线经验

## 1. 场景描述

- **资源拓扑**：32 张正常 GPU，4 个节点，每节点 8 卡；每两个节点构成一个 16 卡亲和组。
- **通信层级**：节点内带宽最高，亲和组内跨节点次之，跨亲和组最低。
- **并行约束**：`PP×TP×DP=32`、`TP≤8`，模型在 `PP=1` 下不 OOM。
- **硬匹配条件**：无慢卡或显著设备异构，节点规模、亲和组、模型约束和候选空间与本页一致。
- **不适用条件**：卡数、节点规模或亲和组发生变化，或者出现慢卡；异构场景改用 [[single-slow-gpu-isolation]]、[[two-slow-gpu-distributed-balance]] 或 [[four-slow-gpu-symmetric-replicas]]。

## 2. 具体的并行策略

### 部署策略

```text
active_gpu=32
PP=1, TP=8, DP=4, MBN=1
映射：每节点一个 TP=8 group，4 个节点组成 DP=4
执行：启用全部 32 卡；每节点构造一个 TP group，四个 TP group 组成 DP=4
```

### 部署经验

- **卡的数量**：场景匹配时使用全部 32 卡；满卡消除 idle penalty。若通信、显存或延迟护栏触发，再切换到保持完整并行拓扑的少卡回退。
- **TP**：将 `TP=8` group 限制在单节点内，避免高频 TP 通信跨节点。
- **TP/DP**：在当前 32 卡离散空间使用 `TP:DP=2:1`，即 `TP=8,DP=4`；该比例不跨卡数或拓扑外推。
- **PP**：使用 `PP=1` 消除 pipeline bubble；OOM 时回退到满足显存约束的最小 PP。
- **PP/MBN**：`PP=1` 时使用 `MBN=1`；增加 PP 后必须重新选择 MBN。

### 失效条件与回退

- 运行中 `PP=1` OOM：回退到满足显存约束的最小 PP，并重新组合 TP/DP/MBN。
- latency、throughput 或通信护栏触发：停止主策略，切换到保持完整并行拓扑的浅 PP 或少卡方案。
- 主回退候选：`PP=1,TP=4,DP=8,MBN=1`；其次使用浅 PP 或完整拓扑的少卡方案。
