---
title: ScoreExpert
created: 2026-07-14
updated: 2026-07-30
type: entity
tags: [scoreexpert, deployment, slow-gpu, evidence]
sources: [raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md, raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-2026-07-30.md, raw/articles/two-slow-gpu-same-node-evolve-analysis-2026-07-30.md, raw/articles/two-slow-gpu-same-affinity-evolve-analysis-2026-07-30.md, raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-reviewed-2026-07-30.md]
confidence: high
contested: false
contradictions: []
---

# ScoreExpert

## Overview

ScoreExpert 在本 Wiki 中用于把 GPU 部署场景、候选 PP/TP/DP/MBN、打分函数、拓扑解释、Evaluation 和适用边界组织成可追溯经验。

目标使用方式是“离线沉淀、在线推理”：成熟场景来源已经把实验条件、数值策略、原因和边界沉淀下来；后续新场景只要同时命中 [[latency-first-experience-summary]] 中的成熟场景规则和对应 raw 来源的边界，就直接输出部署策略。待验证来源不能进入这条直接推理路径。

当前经验库保存七个成熟的 32 卡延迟优先场景；raw 共八份快照，其中 S7 的旧版只保留历史审计，当前状态由重新审核后的快照支撑。总体经验汇总见 [[latency-first-experience-summary]]，完整结构见 [[deployment-objective-knowledge-framework]]。

标准 32 卡、单慢卡、三种双慢卡拓扑、四张均匀慢卡和五张 2/1/1/1 慢卡均作为成熟延迟优先经验保留；稳定优先目前仍没有部署经验。

## 两类优化目标入口

- 延迟优先：当前七个成熟场景均在此入口，以端到端 latency 为主目标，并设置吞吐、显存和稳定性护栏。
- 稳定优先：当前没有成熟场景经验；以后需以重复波动、尾延迟、OOM/失败率、超时或恢复为主指标，并设置性能下限。

## 当前三类场景知识

### 同构基线

- [标准 32 卡同构场景](../raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md)：无慢卡且硬条件匹配时使用 `PP=1,TP=8,DP=4,MBN=1`。

### 局部异构

- [单张慢卡场景](../raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md)：单张局部慢卡且映射可控时使用 `PP=16,TP=2,DP=1,MBN=64`。
- [同节点双慢卡场景](../raw/articles/two-slow-gpu-same-node-evolve-analysis-2026-07-30.md)：两张慢卡收敛在一个节点内 group/stage 时使用 `PP=4,TP=8,DP=1,MBN=8`。

### 分布式异构

- [两张慢卡场景](../raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md)：两张慢卡跨亲和组时使用无 PP、节点内 TP 和节点间 DP。
- [同亲和组跨节点双慢卡场景](../raw/articles/two-slow-gpu-same-affinity-evolve-analysis-2026-07-30.md)：使用 `PP=16,TP=1,DP=2,MBN=64`。
- [四张慢卡场景](../raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md)：四张慢卡一节点一张且速度接近时使用对称 DP replica。
- [五张慢卡 2/1/1/1 Evolve 场景](../raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-reviewed-2026-07-30.md)：重新审核准入 `PP=16,TP=1,DP=2,MBN=64`。

数值策略和总体原因保留在 [[latency-first-experience-summary]]，具体实验条件、Score 推导、映射和结论边界保留在 raw 场景来源中。

召回顺序：先核对优化目标、卡数与拓扑，再核对慢卡数量、位置和速度倍率，随后核对模型显存、rank mapping、score 版本和候选空间。命中总览规则和对应 raw 场景边界时直接输出策略；资源规模变化但命中总览已准入的换算规则时，按 `PP×TP×DP=active_gpu`、`TP:DP` 比例和完整拓扑约束重新求解，不能复制原实例参数；无法求得合法整数拓扑时进入补库流程。
