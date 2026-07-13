# Wiki Schema

## Domain

本 Wiki 覆盖 ScoreExpert 在 GPU 集群上的部署经验：场景条件、PP/TP/DP/MBN 候选、证据、适用边界、反例、来源可信度，以及尚待仿真或 Evaluation 验证的假设。

## Conventions

- 文件名使用小写英文、连字符、不留空格，例如 `single-slow-gpu-isolation.md`。
- 每个知识页必须以 YAML frontmatter 开头，并满足下方字段契约。
- 每个知识页至少包含 2 个指向其他知识页的 `[[wikilinks]]`。
- 每个新知识页都必须加入 `index.md`，每次操作都必须追加到 `log.md`。
- 更新知识页时必须更新 `updated` 日期；原始来源只读，不在 `raw/` 内直接修订。
- 综合 3 个及以上来源时，在关键段落末尾追加 `^[raw/articles/source-file.md]` 来源标记。
- 正式经验固定按“场景 → 推荐策略 → 证据 → 适用边界/失效条件 → 证据缺口”组织。
- `active` 经验可以作为候选建议；`unverified` 假设只能进入验证计划，不能写成部署结论。
- 参数组合是特定条件下的候选，不得省略拓扑、慢卡分布、模型约束或搜索空间边界。

## Frontmatter

```yaml
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [来自下方标签表]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: false
contradictions: []
---
```

`confidence` 表示当前页面结论的证据强度，不等同于打分函数的 score。`contested` 与 `contradictions` 仅在存在尚未解决的相互冲突时使用。

## Raw Source Frontmatter

```yaml
---
source_url:
source_path: /absolute/or/original/path
ingested: YYYY-MM-DD
sha256: body-sha256
original_sha256: original-file-sha256
---
```

`sha256` 仅计算第二个 `---` 之后的 Markdown 正文，用于发现 Wiki 内原始快照漂移；`original_sha256` 记录导入时源文件的哈希。

## Tag Taxonomy

- `scoreexpert`：ScoreExpert 领域总标签
- `deployment`：部署决策与部署经验
- `experience`：可被召回的正式经验
- `gpu`：GPU 资源与硬件条件
- `topology`：节点、亲和组与通信拓扑
- `slow-gpu`：慢卡与异构设备
- `pp`：流水线并行
- `tp`：张量并行
- `dp`：数据并行
- `mbn`：微批次数
- `evidence`：证据、置信度与来源
- `hypothesis`：未验证或可证伪假设
- `governance`：审核、生命周期与写入门禁
- `comparison`：场景或策略对比
- `decision-guide`：选择流程与查询结论
- `simulation`：仿真计划与验证指标

规则：页面使用的每个标签都必须先出现在本标签表中。

## Page Thresholds

- 某个实体或概念出现在 2 个及以上来源中，或是单一来源的核心主题时，创建页面。
- 已有页面覆盖同一主题时，更新原页并补充来源，不创建近义重复页。
- 不为顺带提及、无决策价值的细节或领域外内容创建页面。
- 页面超过约 200 行时拆成子主题，并保留双向链接。
- 内容被完全替代时移入 `_archive/`，从索引移除，并修订所有入链。

## Experience Status Rules

| 状态 | Wiki 表达 | 能否作为部署建议 |
|---|---|---|
| `active` | 正式经验，仍需带置信度和边界 | 可以作为第一候选，不代表物理全局最优 |
| `superseded` | 历史经验，保留演化关系 | 不作为默认建议 |
| `unverified` / `partially_supported` | 假设或初步证据 | 不可以，只能生成验证计划 |
| `supported` | 可生成正式更新提案 | 仍需审核、dry-run 与显式写入 |
| `refuted` / `mixed` | 被反驳或需要拆边界 | 不直接推广，保留反证和条件分支 |

## Update Policy

1. 先比较来源日期、哈希、验证状态和直接 Evaluation 证据。
2. 新信息与现有页面冲突时，不静默覆盖；同时陈述两个结论及各自条件。
3. 真正冲突时设置 `contested: true`，并在 `contradictions` 中填写页面 slug。
4. 新结论先进入假设和仿真层；只有经支持、人工审核并通过正式写入门禁后，才能成为 active 经验。
5. 每次更新同步维护 `index.md` 和追加式 `log.md`。
