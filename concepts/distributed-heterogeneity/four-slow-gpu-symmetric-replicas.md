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
---

# 四张均匀慢卡的对称副本延迟经验

## 1. 场景描述

- **状态**：`active`。知识库所有者于 2026-07-20 审核为成熟经验，匹配条件时直接部署，无需重新运行真实 Evaluation。
- **优化目标**：延迟优先；主指标为端到端 latency，同时监控 replica skew、throughput、显存和 OOM。
- **资源拓扑**：32 卡，4 个 8 卡节点，两个 16 卡亲和组。
- **异构分布**：四张速度接近的慢卡均匀分布为一节点一张，使四个 DP replica 具有相同慢卡结构。
- **模型约束**：模型能在节点内 `TP=8,PP=1` 下满足显存要求，TP group 可以严格限制在节点内。
- **硬匹配条件**：每节点恰有一张速度接近的慢卡；若慢卡集中、速度差异明显或出现纯快 replica，本页经验不再直接适用。
- **准入依据**：来源明确给出保持 replica 对称、节点内 `TP=8`、`DP=4`、`PP=1,MBN=1` 的经验，并报告当前策略最优；附件未包含原始指标，但人工审核已完成准入。
- **目标总览**：[[latency-first-experience-summary]]。

## 2. 具体的并行策略

### 直接输出

```text
active_gpu=32
PP=1, TP=8, DP=4, MBN=1
映射：4 个节点 × 每节点 1 张慢卡 × 每节点 1 个 TP group
```

### 部署经验

- **卡的数量**：使用四个完整节点和全部 32 卡，以保留“一节点一张慢卡”的对称结构；减卡后必须重新检查 replica 对称性。
- **TP**：每节点建立一个 `TP=8` group，使每组都含一张速度接近的慢卡。
- **TP/PP**：慢卡覆盖所有节点后无法隔离到少数 stage，因此使用 `PP=1` 与节点内 TP，避免多个慢 stage。
- **DP**：四个节点内 TP group 组成 `DP=4`，让每个 replica 具有相同慢卡数量、速度分布和预测耗时。
- **PP/MBN**：`PP=1` 时不需要填充 pipeline，因此使用 `MBN=1`；增加 PP 后必须重新选择 MBN。

### 部署动作

1. 每节点的 8 张卡组成一个 TP group，并确保每组恰有一张慢卡。
2. 四个 TP group 组成 `DP=4`，保持副本结构对称。
3. 设置 `PP=1,MBN=1`，运行时同时监控绝对 latency 和 replica skew。

### 适用边界与回退

- 允许在保持“每 replica 一张速度接近慢卡”的前提下重排 rank。
- 慢卡速度差异明显：按预测执行时间而非数量重新均衡。
- 慢卡集中或出现纯快 replica：切换到 [[two-slow-gpu-distributed-balance]] 或 [[single-slow-gpu-isolation]]。
- `PP=1` OOM：使用满足显存的最小 PP，并按预测 stage time 重新分层。
- 无慢卡时使用 [[homogeneous-32gpu-score-candidate]]。

### 准入记录

- `ACCEPT_EXPERIENCE`；审核日期 2026-07-20，置信度 `high`。
