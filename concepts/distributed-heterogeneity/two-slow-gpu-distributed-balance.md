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
---

# 两张跨亲和组慢卡的均衡延迟经验

## 1. 场景描述

- **状态**：`active`。知识库所有者于 2026-07-20 审核为成熟经验，匹配条件时直接部署，无需重新运行真实 Evaluation。
- **优化目标**：延迟优先；主指标为端到端 latency 和 replica skew，护栏包括 throughput、显存、OOM 和快 replica 等待比例。
- **资源拓扑**：32 卡，4 个 8 卡节点，两个 16 卡亲和组。
- **异构分布**：两张慢卡分别位于两个亲和组，形成两个含慢卡 replica 和两个纯快卡 replica；异常已经不能视为单个局部坏点。
- **模型约束**：模型能在单节点 `TP=8,PP=1` 下满足显存要求，TP group 可以严格限制在节点内。
- **硬匹配条件**：两张慢卡跨亲和组分散，不能集中在同一节点或同一 TP group；四节点均可完整参与。
- **准入依据**：来源明确给出从局部 PP 隔离切换到节点内 TP、节点间 DP 的经验，并报告当前策略最优；附件未包含原始指标，但人工审核已完成准入。
- **目标总览**：[[latency-first-experience-summary]]。

## 2. 具体的并行策略

### 直接输出

```text
active_gpu=32
PP=1, TP=8, DP=4, MBN=1
映射：每节点一个 8 卡 TP group 和一个 DP replica
```

### 部署经验

- **卡的数量**：使用四个完整节点和全部 32 卡；减少资源时必须重建完整 TP/DP 拓扑，并重新判断慢卡是否仍属于分布式异构。
- **TP**：使用节点内 `TP=8`，避免高频 TP 通信跨节点；含慢卡 TP group 仍会整体变慢。
- **TP/PP**：慢卡跨区域后，深 PP 容易形成多个慢 stage，因此使用 `PP=1,TP=8`，从逐点隔离切换为节点内 TP。
- **DP**：使用 `DP=4` 扩展到四个节点；DP 不会自动消除快慢副本等待，运行时需监控 replica skew。
- **PP/MBN**：`PP=1` 消除 pipeline bubble，因此使用 `MBN=1`；增加 PP 后必须重新选择 MBN。

### 部署动作

1. 每节点建立一个 `TP=8` group，四个 TP group 组成 `DP=4`。
2. 设置 `PP=1,MBN=1`，避免多个慢 stage 和不必要的 microbatch 切分。
3. 标记两个含慢卡 replica 和两个纯快卡 replica，运行时监控 latency 与 skew 护栏。

### 适用边界与回退

- 允许在保持“两张慢卡跨亲和组”结构不变的前提下重排 rank。
- 慢卡集中到同一区域：场景重新分类为局部异构，切换到 [[single-slow-gpu-isolation]]。
- 每节点均出现慢卡：切换到 [[four-slow-gpu-symmetric-replicas]]。
- `PP=1` OOM 或 replica skew 超过业务护栏：回退到最小可行 PP、重新映射慢卡或重新组合并行参数。
- 无慢卡时使用 [[homogeneous-32gpu-score-candidate]]。

### 准入记录

- `ACCEPT_EXPERIENCE`；审核日期 2026-07-20，置信度 `high`。
