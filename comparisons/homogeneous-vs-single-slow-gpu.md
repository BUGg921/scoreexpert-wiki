---
title: 同构基线与单慢卡隔离策略对比
created: 2026-07-13
updated: 2026-07-13
type: comparison
tags: [scoreexpert, deployment, comparison, experience, slow-gpu, pp, tp, dp, mbn]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md]
confidence: medium
contested: false
contradictions: []
---

# 同构基线与单慢卡隔离策略对比

## Why compare

这两条 active 经验共享 32 卡和节点拓扑，却给出截然不同的并行形态。差异来自慢卡是否是局部单点异常，而不是参数偏好本身。

## Side-by-side

| 对比项 | [[homogeneous-32gpu-baseline]] | [[single-slow-gpu-isolation]] |
|---|---|---|
| 慢卡 | 0 张 | 1 张，种子场景为半速 |
| 第一候选 | `PP=1, TP=8, DP=4, MBN=1` | `PP=16, TP=2, DP=1, MBN=64` |
| 核心目标 | 避免无收益 PP，节点内 TP + 跨节点 DP | 缩小 TP 污染域并避免 DP straggler |
| PP | 浅，消除 bubble | 深，配合 MBN 填充 |
| TP | 8，吃满单节点 | 2，限制慢卡同步范围 |
| DP | 4，补齐 32 卡 | 1，避免 replica 同步拖尾 |
| 最大风险 | DP all-reduce 与模型显存 | 深 PP stage 不均衡和 MBN 上界效应 |
| 置信度 | medium | medium |

## Synthesis

选择策略时，先确认慢卡数量、位置、速度倍率和逻辑 rank mapping，再解释 [[parallel-strategy-parameters]] 的组合变化。单慢卡经验不能外推到两慢卡或四慢卡；这些边界仍在 [[unverified-deployment-hypotheses]] 中等待验证。

完整操作顺序见 [[deployment-strategy-selection]]。
