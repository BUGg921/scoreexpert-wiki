---
title: 四张均匀慢卡的对称副本延迟经验
created: 2026-07-15
updated: 2026-07-20
type: concept
tags: [scoreexpert, deployment, experience, distributed-heterogeneity, distribution-symmetric, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence, decision-guide]
sources: [raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
confidence: high
contested: false
contradictions: []
experience_category: distributed-heterogeneity
status: active
optimization_priority: latency-first
admitted_by: knowledge-base-owner
admitted_at: 2026-07-20
---

# 四张均匀慢卡的对称副本延迟经验

## 1. 场景描述

- **资源拓扑**：32 卡，4 个 8 卡节点，两个 16 卡亲和组。
- **异构分布**：四张速度接近的慢卡均匀分布为一节点一张，使四个 DP replica 具有相同慢卡结构。
- **模型约束**：模型能在节点内 `TP=8,PP=1` 下满足显存要求，TP group 可以严格限制在节点内。
- **硬匹配条件**：每节点恰有一张速度接近的慢卡；若慢卡集中、速度差异明显或出现纯快 replica，本页经验不再直接适用。
- **不适用条件**：慢卡速度差异明显时改为按预测耗时重新均衡；出现纯快 replica 时改用 [[two-slow-gpu-distributed-balance]]；慢卡集中到可隔离的局部范围时改用 [[single-slow-gpu-isolation]]；不存在慢卡时改用 [[homogeneous-32gpu-score-candidate]]。

## 2. 具体的并行策略

### 部署策略

```text
active_gpu=32
PP=1, TP=8, DP=4, MBN=1
映射：4 个节点 × 每节点 1 张慢卡 × 每节点 1 个 TP group
执行：每节点构造一个含一张慢卡的 TP group，四组组成结构对称的 DP=4
```

### 部署经验

- **卡的数量**：使用四个完整节点和全部 32 卡，以保留“一节点一张慢卡”的对称结构；减卡后必须重新检查 replica 对称性。
- **TP**：每节点建立一个 `TP=8` group，使每组都含一张速度接近的慢卡。
- **TP/PP**：慢卡覆盖所有节点后无法隔离到少数 stage，因此使用 `PP=1` 与节点内 TP，避免多个慢 stage。
- **DP**：四个节点内 TP group 组成 `DP=4`，让每个 replica 具有相同慢卡数量、速度分布和预测耗时。
- **PP/MBN**：`PP=1` 时不需要填充 pipeline，因此使用 `MBN=1`；增加 PP 后必须重新选择 MBN。


