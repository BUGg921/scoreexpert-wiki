---
title: 单慢卡局部隔离策略
created: 2026-07-13
updated: 2026-07-13
type: concept
tags: [scoreexpert, deployment, experience, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md, raw/articles/scoreexpert-source-registry-2026-07-13.md]
confidence: medium
contested: false
contradictions: []
---

# 单慢卡局部隔离策略

## Scenario

- 32 张 GPU，每节点 8 张，每 16 张一个亲和组或相近拓扑。
- 只有 1 张局部异常慢卡；种子场景为 GPU 7、速度倍率 0.5。
- 不允许跨节点 TP，搜索空间允许深 PP 与 `MBN=64`。

## First candidate

`PP=16, TP=2, DP=1, MBN=64`

该组合是隔离慢卡的第一 Evaluation 候选；`MBN=64` 位于搜索空间上界，不能解释为物理必然最优。

## Why it ranks first

- `TP=2` 尝试把慢卡影响限制在 2 卡 TP group，而不是拖慢 8 卡 group。
- `DP=1` 避免多个 replica 因一个慢 replica 同步等待。
- `PP=16` 与 `TP=2` 使用 32 卡，把慢卡更局部地暴露为某个 stage 瓶颈。
- 大 MBN 用于稀释深 PP bubble，但必须通过真实 batch 和 Evaluation 验证。

## Boundaries

慢卡扩展到两张以上、跨节点分散、多个 stage 同时变慢、MBN 上界降低、模型层数无法均匀切成 16 段，或显存/batch 不允许时，本经验可能失效。

## Evidence gaps

仍缺 stage time、TP group straggler、DP replica skew、MBN 扫描和速度倍率翻转边界。历史分析来源仍为 `unverified_legacy`，所以置信度保持 `medium`。

与 [[homogeneous-32gpu-baseline]] 的差异见 [[homogeneous-vs-single-slow-gpu]]；速度倍率翻转问题仍属于 [[unverified-deployment-hypotheses]]。
