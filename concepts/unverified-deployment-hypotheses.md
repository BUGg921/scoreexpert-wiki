---
title: 未验证的部署假设
created: 2026-07-13
updated: 2026-07-13
type: concept
tags: [scoreexpert, deployment, slow-gpu, topology, hypothesis, evidence, simulation]
sources: [raw/articles/scoreexpert-learning-status-2026-07-13.md, raw/articles/scoreexpert-source-registry-2026-07-13.md]
confidence: low
contested: false
contradictions: []
---

# 未验证的部署假设

> 本页是验证队列，不是部署推荐。所有条目当前均为 `unverified`。

## Current hypotheses

| 假设 | 需要验证的决策边界 |
|---|---|
| 单慢卡速度倍率决定策略翻转 | 0.8 时同构基线是否更快；0.5/0.25 时隔离候选是否至少快 3% |
| 两慢卡拓扑对称性决定均衡或隔离 | 跨亲和组对称放置与同组集中放置是否产生不同赢家 |
| 高 DP 被 score 高估 | DP=32 是否因 replica skew 和跨亲和组同步在真实 latency 上落后 |
| 四慢卡对称均衡 | 每节点一张慢卡时，基线候选是否优于高 DP 与深 PP |
| rank mapping 逻辑对称性 | 相同物理慢卡分布下，对称 mapping 是否显著降低 replica skew |

## Required metrics

优先观测 `latency_ms`、`tp_group_straggler_pct`、`dp_replica_skew_pct`、`pp_slowest_stage_ratio`、`dp_all_reduce_ms` 与 `cross_affinity_sync_ms`。只有 score 排名而没有这些 Evaluation 指标时，不应提升置信度。

## Relationship to active experience

第一条假设直接检验 [[homogeneous-32gpu-baseline]] 与 [[single-slow-gpu-isolation]] 的翻转边界。其余假设不应被压缩成“慢卡数量越多就选某个固定策略”，而应通过 [[experience-governance]] 进入验证和审核流程。

新场景决策时，把本页作为 [[deployment-strategy-selection]] 的风险与实验清单，而不是候选答案。
