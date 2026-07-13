---
title: PP TP DP MBN 部署参数
created: 2026-07-13
updated: 2026-07-13
type: concept
tags: [scoreexpert, deployment, pp, tp, dp, mbn, topology]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md]
confidence: medium
contested: false
contradictions: []
---

# PP、TP、DP、MBN 部署参数

## Definitions

| 参数 | 本 Wiki 中的部署含义 | 主要风险 |
|---|---|---|
| PP | 把模型分成流水线 stage | stage 不均衡与 pipeline bubble |
| TP | 在一组 GPU 内协同执行张量计算 | 同步域扩大，慢卡可能拖慢整个 TP group |
| DP | 复制模型并跨 replica 同步 | all-reduce 与 replica skew |
| MBN | 用多个 micro-batch 填充流水线 | 受 global batch、显存和搜索上界约束 |

## Hard constraints

当前经验使用的基本可行性约束是：`PP × TP × DP <= total_gpus`；未允许跨节点 TP 时，`TP <= gpus_per_node`；`MBN` 必须为正整数。满足硬约束只代表候选可枚举，不代表性能已验证。

## Interaction

[[homogeneous-32gpu-baseline]] 用 `PP=1` 消除 pipeline bubble，用节点内 `TP=8` 吃满单节点，再用 `DP=4` 补齐 32 卡。[[single-slow-gpu-isolation]] 则把 `TP` 降到 2、`DP` 降到 1，并用 `PP=16` 与大 MBN 尝试限制慢卡同步污染。

这些参数不能脱离 [[homogeneous-vs-single-slow-gpu]] 的场景对比单独复用；尤其 `MBN=64` 位于当前搜索空间上界，只是边界候选。
