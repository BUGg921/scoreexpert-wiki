---
title: 32 卡同构部署基线
created: 2026-07-13
updated: 2026-07-13
type: concept
tags: [scoreexpert, deployment, experience, gpu, topology, pp, tp, dp, mbn, evidence]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md, raw/articles/scoreexpert-source-registry-2026-07-13.md, raw/articles/32gpu-baseline-score-strategy-analysis-2026-07-13.md]
confidence: medium
contested: false
contradictions: []
---

# 32 卡同构部署基线

## Scenario

- 32 张 GPU，每节点 8 张，每 16 张一个亲和组或相近拓扑。
- 来源没有提供慢卡信息，因此本页按同构或未建模异构分析。
- `TP<=8` 是外部拓扑硬约束；score 本身没有 `tp_cross` 项。
- 完整搜索空间、`micro` 定义、模型层数、显存和 global batch 尚未给出。

来源明确把 `active=PP×TP×DP<=32`、`TP<=8`、`MBN>=1` 作为推导口径；若这些口径变化，必须重新枚举候选。^[raw/articles/32gpu-baseline-score-strategy-analysis-2026-07-13.md]

## First candidate

`PP=1, TP=8, DP=4, MBN=1`

这是第一 Evaluation 候选，不是脱离模型、网络和 batch 条件的物理全局最优。

## Classification

本次导入与现有 active 基线经验描述的是同一场景和同一候选，因此作为既有经验的来源补强，不创建重复经验页。它提供了可复查的 score 推导和拓扑解释，但没有真实 Evaluation 指标；置信度继续保持 `medium`。^[raw/articles/32gpu-baseline-score-strategy-analysis-2026-07-13.md]

## Evidence

### Score evidence

- `PP=1` 令 bubble 为 0；score 对深 PP 只有 bubble 惩罚，没有 overlap 或其他补偿奖励。
- `MBN=1` 位于 `-0.5×(MBN-1)^2` 的零惩罚点；`PP=1` 后增大 MBN 也不能继续降低 bubble。
- 空闲卡惩罚 `-2×(32-active)` 使候选优先使用满 32 卡。
- 固定 `PP=1`、`MBN=1` 和满卡后，`TP=8,DP=4` 的 TP/DP 项为 `5.2`，高于 `TP=4,DP=8` 的 `2.0`。^[raw/articles/32gpu-baseline-score-strategy-analysis-2026-07-13.md]

### Topology evidence

`TP=8` 与单节点 8 卡高速通信域对齐；`DP=4` 用跨节点副本补齐 32 卡；`PP=1` 避免 pipeline bubble、stage imbalance 和阶段间 activation 传输。这些是拓扑解释，不是实测性能证据。^[raw/articles/32gpu-baseline-score-strategy-analysis-2026-07-13.md]

### Evaluation evidence

当前来源没有 latency、显存峰值、DP all-reduce、吞吐或其他 Evaluation 指标，并明确要求用 Evaluation 验证。因此不能把“score 最优”提升为“真实硬件最优”。^[raw/articles/32gpu-baseline-score-strategy-analysis-2026-07-13.md]

## Boundaries

### Applies when

- 32 卡、每节点 8 卡、每 16 卡一个亲和组或相近拓扑。
- 无慢卡，或 score 与输入没有建模异构。
- 搜索器强制 `TP<=8`，并能把 `TP=8` 映射在单节点内。
- 模型显存允许 `PP=1`，`MBN=1` 不违反 batch 或吞吐要求。

### Fails when

- 显存不足，必须引入 PP 或其他切分。
- DP=4 的跨节点或跨亲和组 all-reduce 成为主瓶颈。
- 出现慢卡、慢网络、层数不均衡或其他异构因素。
- 搜索器允许 `TP>8`，但没有 `tp_cross` 硬过滤或惩罚。
- `micro` 实际由 DP、MBN 或 global batch 派生，并改变候选精确分数。

## Evidence gaps

优先补齐显存边界、DP 跨域成本、允许 `TP=16/32` 的反例、`MBN={1,2,4,8}` 扫描，以及插入单张慢卡后的策略翻转。来源文件已在本 Wiki 保存不可变哈希快照；本 Wiki 早先导入的来源登记快照仍把该历史报告标成 `unverified_legacy`。当前上游经验库已变为 schema v3，旧 `data/sources.json` 路径不再存在，因此正式来源登记必须按上游当前流程另行处理。

对照 [[single-slow-gpu-isolation]] 可看到慢卡如何改变并行形态，二者的证据成熟度见 [[homogeneous-vs-single-slow-gpu]]；使用前先阅读 [[parallel-strategy-parameters]] 和 [[deployment-strategy-selection]]。
