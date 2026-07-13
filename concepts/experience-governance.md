---
title: 部署经验治理与更新门禁
created: 2026-07-13
updated: 2026-07-13
type: concept
tags: [scoreexpert, deployment, experience, evidence, hypothesis, governance, simulation]
sources: [raw/articles/scoreexpert-experience-store-2026-07-13.md, raw/articles/scoreexpert-source-registry-2026-07-13.md, raw/articles/scoreexpert-learning-status-2026-07-13.md]
confidence: high
contested: false
contradictions: []
---

# 部署经验治理与更新门禁

## Three knowledge states

1. 原始来源：场景、报告、Evaluation 和哈希登记，只读保存。
2. 综合经验：active/superseded 记录，包含场景、推荐、证据、边界与生命周期。^[raw/articles/scoreexpert-experience-store-2026-07-13.md]
3. 待验证假设：可证伪预测、仿真队列和成熟状态，不能直接作为正式经验。^[raw/articles/scoreexpert-learning-status-2026-07-13.md]

## Source quality

来源登记表区分 `hash_verified` 与 `unverified_legacy`。两条正式种子经验都引用了已校验的结构化场景，同时也引用尚无不可变本地快照的历史报告；因此经验页保持 `medium` 置信度。^[raw/articles/scoreexpert-source-registry-2026-07-13.md]

## Promotion gate

假设只有在仿真或 Evaluation 支持后才能生成正式更新提案；提案仍需人工审核、dry-run 校验和显式写入。`supported` 不等于自动成为 active 经验。^[raw/articles/scoreexpert-learning-status-2026-07-13.md]

## Wiki update rule

当正式经验库发生变化时，先在 `raw/articles/` 新增带日期和哈希的快照，再更新受影响页面、双向链接、`index.md` 与追加式 `log.md`。旧快照不修改。

这个门禁保护 [[homogeneous-32gpu-baseline]] 与 [[single-slow-gpu-isolation]] 不被弱证据静默覆盖，也把 [[unverified-deployment-hypotheses]] 保留在正确层级。
