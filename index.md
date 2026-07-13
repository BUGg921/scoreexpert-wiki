# ScoreExpert 部署经验 Wiki

> 面向 GPU 部署选型的互链知识目录。先从“查询”进入决策流程，再回到经验页检查证据与边界。
> Last updated: 2026-07-13 | Total pages: 8

## 快速入口

- 新场景选型：[[deployment-strategy-selection]]
- 两条正式经验对比：[[homogeneous-vs-single-slow-gpu]]
- 参数含义：[[parallel-strategy-parameters]]
- 当前未验证内容：[[unverified-deployment-hypotheses]]

## Entities

- [[scoreexpert]] — 部署经验库的领域对象、知识边界和当前正式经验入口。

## Concepts

- [[experience-governance]] — 区分正式经验、假设和来源证据，并约束更新流程。
- [[homogeneous-32gpu-baseline]] — 32 卡同构场景的 `PP=1, TP=8, DP=4, MBN=1` 第一候选。
- [[parallel-strategy-parameters]] — PP、TP、DP、MBN 的部署含义与硬约束。
- [[single-slow-gpu-isolation]] — 单张半速慢卡场景的深 PP、小 TP、低 DP 隔离候选。
- [[unverified-deployment-hypotheses]] — 两慢卡、四慢卡、速度倍率与 rank mapping 的待验证命题。

## Comparisons

- [[homogeneous-vs-single-slow-gpu]] — 同构基线和单慢卡隔离策略的条件化对比。

## Queries

- [[deployment-strategy-selection]] — 如何根据新场景选择、校验并验证部署策略。
