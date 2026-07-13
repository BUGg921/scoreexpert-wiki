---
title: 如何为新场景选择部署策略
created: 2026-07-13
updated: 2026-07-13
type: query
tags: [scoreexpert, deployment, decision-guide, experience, topology, evidence, simulation]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md, raw/articles/scoreexpert-source-registry-2026-07-13.md, raw/articles/scoreexpert-learning-status-2026-07-13.md]
confidence: high
contested: false
contradictions: []
---

# 如何为新场景选择部署策略

本流程是 [[scoreexpert]] 的默认查询入口；它先约束证据和场景，再给出可验证的第一候选。

## Decision flow

1. **结构化场景**：记录总 GPU、每节点 GPU、亲和组、是否允许跨节点 TP、慢卡数量/ID/速度倍率/分布、模型层数/显存/global batch 和 PP/TP/DP/MBN 搜索空间。
2. **先过硬约束**：确认 `PP × TP × DP <= total_gpus`、TP 不越过允许的通信边界、MBN 为正整数。参见 [[parallel-strategy-parameters]]。
3. **只召回 active 经验**：无慢卡时优先比较 [[homogeneous-32gpu-baseline]]；单张局部半速慢卡时比较 [[single-slow-gpu-isolation]]。两者都只是第一 Evaluation 候选。^[raw/articles/scoreexpert-experience-store-2026-07-13.md]
4. **检查来源和边界**：来源表中的历史报告仍为 `unverified_legacy`，不能把 medium 置信度包装成已证实最优。^[raw/articles/scoreexpert-source-registry-2026-07-13.md]
5. **遇到未覆盖场景就转验证**：两慢卡、四慢卡、未知 rank mapping 或速度倍率变化应进入 [[unverified-deployment-hypotheses]]，生成单变量仿真，而不是直接复制最近经验。^[raw/articles/scoreexpert-learning-status-2026-07-13.md]
6. **用真实指标裁决**：比较 latency、TP straggler、DP replica skew、PP slowest stage、all-reduce 与跨亲和组同步。
7. **通过治理门禁更新**：支持假设只生成提案；人工审核、dry-run 和显式写入后，再按 [[experience-governance]] 更新 Wiki。

## Minimal answer template

```text
场景：...
第一候选：PP=?, TP=?, DP=?, MBN=?
为什么：score 证据 / 拓扑证据 / Evaluation 证据分别为...
适用边界：...
失效条件：...
缺失证据：...
下一步仿真：只改变一个关键变量，观察指定指标和最小效应阈值。
```

已有两条经验的参数相变见 [[homogeneous-vs-single-slow-gpu]]。
