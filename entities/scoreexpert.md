---
title: ScoreExpert
created: 2026-07-14
updated: 2026-08-03
type: entity
tags: [scoreexpert, deployment, slow-gpu, evidence]
sources: [raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md, raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-reviewed-2026-08-03.md]
confidence: high
contested: false
contradictions: []
---

# ScoreExpert

## Overview

ScoreExpert 在本 Wiki 中用于把 GPU 部署场景、候选 PP/TP/DP/MBN、拓扑机制、Evaluation 和适用边界组织成可追溯经验。

目标使用方式是“离线沉淀、在线推理”：成熟场景来源已经把实验条件、数值策略、原因和边界沉淀下来；后续新场景只要同时命中 [[latency-first-experience-summary]] 中的成熟场景规则和对应 raw 来源的边界，就直接输出部署策略。待验证来源不能进入这条直接推理路径。

当前经验库保存五份独立的 32 卡场景来源，全部属于**延迟优先型**，总体经验汇总见 [[latency-first-experience-summary]]。知识入口仍先分为延迟优先型、稳定优先型，再按同构基线、局部异构、分布式异构组织；完整结构见 [[deployment-objective-knowledge-framework]]。

标准 32 卡、单慢卡、两张跨亲和组慢卡、四张均匀慢卡和五张按 2/1/1/1 分布的慢卡均作为成熟的延迟优先场景经验保留；稳定优先目前仍没有部署经验。

## 两类优化目标入口

- 延迟优先：当前五个场景均在此入口，以端到端 latency 为主目标，并设置吞吐、显存和稳定性护栏。
- 稳定优先：当前没有成熟场景经验；以后需以重复波动、尾延迟、OOM/失败率、超时或恢复为主指标，并设置性能下限。

## 当前三类场景知识

### 同构基线

- [标准同构场景](../raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md)：使用最小 PP、`TP:DP=2:1` 的满卡组合和最小 MBN。

### 局部异构

- [单张慢卡场景](../raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md)：使用小 TP、最小 DP、满卡深 PP 和约束内最大 MBN。

### 分布式异构

- [两张慢卡场景](../raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md)与[四张慢卡场景](../raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md)：共用“最小 PP、TP 主导型满卡方案”；前者保留快慢 replica 等待边界，后者保留副本对称机制。
- [五张慢卡 2/1/1/1 场景](../raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-reviewed-2026-08-03.md)：使用不同的“深 PP、最小 TP 双副本方案”。

数值策略和总体原因保留在 [[latency-first-experience-summary]]，具体实验条件、候选证据、映射和结论边界保留在五份 raw 场景来源中。

召回顺序：先核对优化目标、可用卡数、节点与亲和组，再统计每个节点和每个亲和组中的慢卡数量、位置与速度倍率；先用场景定义完成分类，再根据这些异构输入计算适用规则并选出策略，最后核对 raw、模型显存、映射能力、候选空间和参数整数可行性。TP group、PP stage 和 DP replica 只有在参数与 rank mapping 确定后才生成并检查，不能作为原始场景输入。唯一命中总览规则和对应 raw 边界时直接输出策略；资源规模变化但命中已准入换算规则时，按 `PP×TP×DP=active_gpu`、比例和完整拓扑约束重新求解，不能复制原实例参数；未命中、多条冲突或无法求得合法整数拓扑与映射时进入补库流程。
