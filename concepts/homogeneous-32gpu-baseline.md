---
title: 32 卡同构部署基线
created: 2026-07-13
updated: 2026-07-13
type: concept
tags: [scoreexpert, deployment, experience, gpu, topology, pp, tp, dp, mbn, evidence]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md, raw/articles/scoreexpert-source-registry-2026-07-13.md]
confidence: medium
contested: false
contradictions: []
---

# 32 卡同构部署基线

## Scenario

- 32 张 GPU，每节点 8 张，每 16 张一个亲和组或相近拓扑。
- 没有慢卡，或当前输入与 score 没有建模异构。
- 不允许跨节点 TP，模型显存允许 `PP=1`。

## First candidate

`PP=1, TP=8, DP=4, MBN=1`

这是第一 Evaluation 候选，不是脱离模型、网络和 batch 条件的物理全局最优。

## Why it ranks first

- `PP=1` 没有 pipeline bubble；当前 score 没有显式奖励深 PP。
- `TP=8` 正好落在 8 卡单节点通信域，避免跨节点 TP。
- `DP=4` 补齐 32 卡；记录中的候选比较认为它优于 `TP=4, DP=8`。
- `MBN=1` 不引入额外 MBN 惩罚，且 `PP=1` 时增大 MBN 不再改善 bubble。

## Boundaries

在显存不足、DP all-reduce 成为主瓶颈、出现慢卡/慢网络、模型层数不能支持当前组合，或搜索器允许无约束跨节点 TP 时，应停止直接复用本经验。

## Evidence gaps

缺少真实 micro 定义、显存可行性、DP all-reduce latency，以及异构或更大模型下的策略翻转边界。因此置信度保持 `medium`；来源登记表中的历史报告仍是 `unverified_legacy`。

对照 [[single-slow-gpu-isolation]] 可看到慢卡如何改变并行形态；使用前先阅读 [[parallel-strategy-parameters]] 和 [[deployment-strategy-selection]]。
