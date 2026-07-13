---
title: ScoreExpert
created: 2026-07-13
updated: 2026-07-13
type: entity
tags: [scoreexpert, deployment, experience, evidence]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md, raw/articles/scoreexpert-source-registry-2026-07-13.md]
confidence: medium
contested: false
contradictions: []
---

# ScoreExpert

## Overview

ScoreExpert 在本 Wiki 中指向一个条件化的 GPU 部署经验域：输入包括 GPU 数量、节点布局、亲和组、慢卡分布、模型与搜索空间；输出不是无条件的“最优参数”，而是带证据、适用边界和反例的 PP/TP/DP/MBN 第一候选。

当前正式库包含两条 active 经验：[[homogeneous-32gpu-baseline]] 与 [[single-slow-gpu-isolation]]。二者共享 32 卡、每节点 8 卡和不允许跨节点 TP 的基础条件，但对慢卡异构采取不同策略。

## Knowledge shape

| 层 | 回答的问题 |
|---|---|
| 场景 | 资源、拓扑、慢卡、模型和搜索空间是什么？ |
| 推荐 | 哪个参数组合作为第一 Evaluation 候选？ |
| 证据 | score、拓扑和 Evaluation 分别支持了什么？ |
| 边界 | 在什么条件下适用、失效或需要拆分？ |
| 缺口 | 还缺哪些指标或仿真才能提升置信度？ |

## How to use

先通过 [[deployment-strategy-selection]] 匹配场景，再查看 [[parallel-strategy-parameters]] 理解候选为何改变。任何新经验都必须经过 [[experience-governance]]，不能把 [[unverified-deployment-hypotheses]] 直接升级为结论。
