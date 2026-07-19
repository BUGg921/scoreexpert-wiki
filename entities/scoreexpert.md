---
title: ScoreExpert
created: 2026-07-14
updated: 2026-07-19
type: entity
tags: [scoreexpert, deployment, slow-gpu, evidence]
sources: [raw/articles/scoring-strategy-analysis-2026-07-14.md, raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md, raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
confidence: medium
contested: false
contradictions: []
---

# ScoreExpert

## Overview

ScoreExpert 在本 Wiki 中用于把 GPU 部署场景、候选 PP/TP/DP/MBN、打分函数、拓扑解释、Evaluation 和适用边界组织成可追溯经验。

当前经验库依据三份来源形成四张 32 卡场景经验卡，现有卡全部属于**延迟优先型**，汇总见 [[latency-first-experience-summary]]。知识入口仍先分为延迟优先型、稳定优先型，再按同构基线、局部异构、分布式异构组织；完整结构见 [[deployment-objective-knowledge-framework]]。

标准卡和单慢卡为 `unverified`；两张跨亲和组慢卡、四张均匀慢卡为 `partially_supported`，来源报告了 Evaluation 最优，但缺少原始指标和扰动验证。当前没有 `active` 正式经验，也没有获得直接 Evaluation 支持的稳定优先经验。

## 两类优化目标入口

- 延迟优先：当前四张经验卡均在此入口，以明确口径的端到端 latency 为主指标，并设置吞吐、显存和稳定性护栏。
- 稳定优先：当前没有经验卡；以后需以重复波动、尾延迟、OOM/失败率、超时或恢复为主指标，并设置性能下限。

## 当前三类场景知识

### 同构基线

- [[homogeneous-32gpu-score-candidate]]：无慢卡时选择标准 32 卡 Evaluation 基线。

### 局部异构

- [[single-slow-gpu-isolation]]：单张局部慢卡时测试小 TP、高 PP 隔离。

### 分布式异构

- [[two-slow-gpu-distributed-balance]]：两张慢卡跨亲和组时测试无 PP、节点内 TP 和节点间 DP。
- [[four-slow-gpu-symmetric-replicas]]：四张慢卡一节点一张时测试对称 DP replica。

Score 推导、验证指标和回退条件直接保留在四张具体经验卡及 [[latency-first-experience-summary]] 中，不再维护重复的独立支撑页。

召回顺序：先核对卡数与拓扑，再核对慢卡数量、位置和速度倍率，随后核对模型显存、score 版本和候选空间。条件不能完整匹配时，只复用决策方法，不复制参数组合。
