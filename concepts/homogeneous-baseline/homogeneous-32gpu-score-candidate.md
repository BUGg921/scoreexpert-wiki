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

## 1. 场景描述

- **状态**：`active`。知识库所有者于 2026-07-20 审核为成熟经验，匹配条件时直接生成部署策略，无需重新运行真实 Evaluation。
- **优化目标**：延迟优先；主指标使用平均、P50、P95 或 P99 latency 之一，护栏为 throughput、peak memory、OOM、通信时间和运行波动。
- **资源拓扑**：32 张正常 GPU，4 个节点，每节点 8 卡；每两个节点构成一个 16 卡亲和组。
- **通信层级**：节点内带宽最高，亲和组内跨节点次之，跨亲和组最低。
- **并行约束**：`PP×TP×DP=32`、`TP≤8`，模型在 `PP=1` 下不 OOM。
- **硬匹配条件**：无慢卡或显著设备异构，节点规模、亲和组、模型约束和候选空间与本页一致。
- **准入依据**：来源给出满卡、`TP:DP=2:1`、`PP=1`、`MBN=1` 四条经验；来源附件未包含原始 Evaluation 数值，但人工审核已完成准入。
- **目标总览**：[[latency-first-experience-summary]]。

## 2. 具体的并行策略

### 直接输出

```text
active_gpu=32
PP=1, TP=8, DP=4, MBN=1
映射：每节点一个 TP=8 group，4 个节点组成 DP=4
```

### 部署经验

- **卡的数量**：场景匹配时使用全部 32 卡；满卡消除 idle penalty。若通信、显存或延迟护栏触发，再切换到保持完整并行拓扑的少卡回退。
- **TP**：将 `TP=8` group 限制在单节点内，避免高频 TP 通信跨节点。
- **TP/DP**：在当前 32 卡离散空间使用 `TP:DP=2:1`，即 `TP=8,DP=4`；该比例不跨卡数或拓扑外推。
- **PP**：使用 `PP=1` 消除 pipeline bubble；OOM 时回退到满足显存约束的最小 PP。
- **PP/MBN**：`PP=1` 时使用 `MBN=1`；增加 PP 后必须重新选择 MBN。

### 部署动作

1. 启用全部 32 卡并设置 `PP=1,TP=8,DP=4,MBN=1`。
2. 按节点构造四个 8 卡 TP group，避免 TP 通信跨节点。
3. 运行时监控 latency、throughput、OOM 和通信护栏；未触发边界时保持主策略。

### 适用边界与回退

- 只允许同一拓扑内的 rank 重排；卡数、节点规模或亲和组变化时停止直接复用。
- `PP=1` OOM：回退到最小可行 PP，并重新组合 TP/DP/MBN。
- 出现慢卡：切换到 [[single-slow-gpu-isolation]]、[[two-slow-gpu-distributed-balance]] 或 [[four-slow-gpu-symmetric-replicas]]。
- 主回退候选：`PP=1,TP=4,DP=8,MBN=1`；其次使用浅 PP 或完整拓扑的少卡方案。

### 准入记录

- `ACCEPT_EXPERIENCE`；审核日期 2026-07-20，置信度 `high`。
