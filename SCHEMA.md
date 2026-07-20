# Wiki Schema

## Domain

本 Wiki 覆盖 ScoreExpert 在 GPU 集群上的部署经验：场景条件、PP/TP/DP/MBN 候选、证据、适用边界、反例、来源可信度，以及尚待仿真或 Evaluation 验证的假设。

## Conventions

- 文件名使用小写英文、连字符、不留空格，例如 `deployment-topic.md`。
- `concepts/` 中的部署经验必须放入与 `experience_category` 同名的一级子目录；支撑知识可以保留在 `concepts/` 根目录。
- 经验库使用“总经验库 → 优化目标总体经验 → 具体场景经验卡”三层结构，不为每个 `experience_category` 创建重复的分类总览页。总经验库永久保留延迟优先、稳定优先及各自三类场景的完整框架，即使某个目标暂时没有经验。
- 每个知识页必须以 YAML frontmatter 开头，并满足下方字段契约。
- 每个知识页至少包含 2 个指向其他知识页的 `[[wikilinks]]`。
- 每个新知识页都必须加入 `index.md`，每次操作都必须追加到 `log.md`。
- 更新知识页时必须更新 `updated` 日期；原始来源只读，不在 `raw/` 内直接修订。
- 综合 3 个及以上来源时，在关键段落末尾追加 `^[raw/articles/source-file.md]` 来源标记。
- 具体场景经验卡的正文固定只有两个一级章节：`1. 场景描述` 和 `2. 具体的并行策略`。成熟状态、优化目标、资源拓扑、异构分布、模型/映射约束、硬匹配条件和准入依据写入第一章；直接输出、资源使用、TP/PP/DP/MBN 规则、部署动作、适用边界、回退与准入记录写入第二章。
- “并行策略”必须先按来源支持的维度拆成可复用部署经验，例如 `TP`、`TP/PP`、`DP`、`PP/MBN`；每个维度说明选择规则、作用机制或切换条件，参数元组只作为当前场景实例，不能替代经验。
- “卡的数量”必须写成资源规模部署经验，而不是资源清单：说明满卡触发条件、少卡对照、减卡后的拓扑/并行重建方式和当前资源实例。异构场景减卡后若慢卡分布类别改变，必须重新分类，不能把收益只归因于卡数。
- 来源存在显式“经验总结”“结论”“建议”或“最佳实践”时，在“具体的并行策略”中忠实保留其结论、限定词和因果关系，不另建第三个一级章节。Wiki 新增推理必须明确标注，不能冒充来源结论。
- 不规定经验条数或来源标题。显式结论使用“来源明确经验”；没有总结段落但存在分散决策时使用“来源分散归纳”；完全没有部署结论时使用“Wiki 推导假设”并默认保持 `unverified`。同一来源可组合使用，但三类内容必须分开。
- 来源强调的比例、阈值、上下界和不等式必须作为定量经验保留；同时记录可迁移规则与当前实例，例如规则 `TP:DP≈2:1`、实例 `TP=8,DP=4`。不得用实例或模糊趋势替代定量规则。
- `active` 经验在硬条件和量化边界匹配时可直接生成部署策略，无需为新场景重新运行真实 Evaluation；`unverified` 或 `partially_supported` 只能生成候选与补库计划，不能冒充直接部署结论。
- 经验成熟度与来源附件完整度分开管理。知识库所有者明确确认某条经验成熟，可作为人工审核准入依据；仍需保留缺失的原始指标说明、适用边界、直接推理契约和审核日期，但不得仅因附件不完整把成熟经验自动降级。
- 参数组合是特定条件下的候选，不得省略拓扑、慢卡分布、模型约束或搜索空间边界。
- 来源提取与正式经验写入之间必须有候选审查层。每条候选按“来源可追溯、触发条件、部署动作、非 score 机制、预期观测、失效边界、新增价值、证据状态”判定为经验、证据、待验证或拒绝；纯 score 解释不得单独成为正式经验。
- 筛选不得删除来源明确结论。未通过经验门槛的来源结论继续保留在来源整理或证据层，并记录降级/拒绝理由。
- 参数元组相同不代表经验重复；只有触发条件、动作、机制、观测和边界均等价时才合并。反之，同一参数在不同场景下可以形成不同条件化经验。
- 用户要求展示增量演化时，在 `outputs/` 保存每批输入的筛选前、逐项审查、筛选后和差异快照；快照不自动获得正式经验状态。

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

正式经验页还必须包含：

```yaml
experience_category: homogeneous-baseline | local-heterogeneity | distributed-heterogeneity
```

正文只允许以下两个一级章节；所需证据和直接推理字段通过二级标题或列表并入其中：

```markdown
## 1. 场景描述
## 2. 具体的并行策略
```

## Experience Knowledge Categories

经验库先按优化目标提供两个一级入口，再按异构分布范围组织二级知识：

1. `latency-first`（延迟优先型）：主验收指标必须明确为平均、P50、P95、P99 或单步最大 latency，并设置吞吐、显存、OOM 和稳定性护栏。
2. `stability-first`（稳定优先型）：主验收指标必须包含重复运行方差、尾延迟、OOM/失败率、超时或恢复行为，并设置可接受的性能下限。

两个目标入口下都使用下方三种 `experience_category`。优化目标是查询与验收维度，异构类别是场景与机制维度；同一经验页可以被两个目标入口引用，但必须分别给出指标、阈值和回退条件，不复制或无证据改写结论。统一格式见 [[deployment-objective-knowledge-framework]]。

当前有证据支持建立的经验知识只分为三类：

| 字段值 | 中文分类 | 收录边界 | 当前经验 |
|---|---|---|---|
| `homogeneous-baseline` | 同构基线 | 无已知异构设备，用于建立正常部署对照 | 标准 32 卡基线 |
| `local-heterogeneity` | 局部异构 | 异常集中在单个局部区域，核心动作是限制污染或隔离 | 单张慢卡局部隔离 |
| `distributed-heterogeneity` | 分布式异构 | 异常跨节点、亲和组或副本分布，核心动作是均衡或对称映射 | 两张跨亲和组慢卡、四张均匀慢卡 |

分类回答“这条经验主要处理哪种部署场景”：没有稳定设备快慢差异的是同构场景；异构影响能够限制在一个可控局部范围的是局部异构；异常跨越多个独立拓扑区域的是分布式异构。Score 推导、验证计划和证据页不是部署经验，不设置 `experience_category`。通信、显存、Batch、资源降级和跨场景决策在当前材料中尚未形成独立经验类别；以后只有出现通过审查的实际经验时才扩充，不预建空分类。

### Objective-first knowledge format

每个优化目标下的三类知识使用以下字段：

- 同构基线：场景定义 → 资源规模部署经验 → `PP/TP/DP/MBN` 部署经验 → 场景案例。
- 局部异构：场景定义 → 对 `TP group`、`DP replica`、`PP stage` 的影响 → 并行策略。隔离对策和场景案例并入并行策略，不另设并列章节。
- 分布式异构：场景定义 → 分布式异构影响 → 并行策略。均衡与对称对策和场景案例并入并行策略，不另设并列章节。

其中“并行策略”不是参数清单。它必须回答如何处理前一节列出的异构影响，并按来源实际支持的组合维度分别阐述部署经验，优先使用 `TP`、`TP/PP`、`DP`、`PP/MBN` 等小节，再列场景案例和当前 `PP/TP/DP/MBN` 实例；不为填满模板编造没有证据的维度。

其中“资源规模部署经验”也不是只写“共 N 张卡”。先说明何时使用全部资源、必须保留什么少卡反事实、减卡后如何保持有效拓扑和整除约束，最后再列当前总卡数与 `active_gpu` 实例。

优化目标总览只保存该目标下跨实例可复用的总体经验和三类场景规则。具体卡数、慢卡位置、参数元组和案例证据状态统一放在对应“场景案例”中，并使用具体案例名称链接唯一经验卡；不得在总体规则中插入“当前实例”或“当前经验范围”。

场景案例仍必须满足正式经验的证据契约，补齐目标指标、护栏、观测、验收阈值、失效边界和回退动作。当前没有稳定性直接 Evaluation 的页面不得因进入“稳定优先型”入口而升级状态。

对应文件结构固定为：

```text
concepts/
├── deployment-objective-knowledge-framework.md
├── latency-first-experience-summary.md
├── homogeneous-baseline/
│   └── <同构基线具体经验卡>
├── local-heterogeneity/
│   └── <局部异构具体经验卡>
├── distributed-heterogeneity/
│   └── <分布式异构具体经验卡>
└── <其他支撑知识按需保留在根目录>
```

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
- `homogeneous-baseline`：同构硬件条件下的部署基线经验
- `local-heterogeneity`：局部异构或局部慢卡隔离经验
- `distributed-heterogeneity`：跨节点、亲和组或副本的分布式异构经验
- `distribution-imbalanced`：分布式异构中各副本慢卡结构或预测执行时间不一致
- `distribution-symmetric`：分布式异构中各副本慢卡结构近似一致
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

| 状态 | Wiki 表达 | 在线推理权限 |
|---|---|---|
| `active` | 已通过来源、历史结果、仿真或审核准入的正式经验 | 条件与边界匹配时直接输出策略，无需新 Evaluation |
| `superseded` | 历史经验，保留演化关系 | 不作为默认建议 |
| `unverified` / `partially_supported` | 假设或初步证据 | 只输出候选和补库计划，不直接部署 |
| `supported` | 可生成正式更新提案 | 仍需审核、dry-run 与显式写入 |
| `refuted` / `mixed` | 被反驳或需要拆边界 | 不直接推广，保留反证和条件分支 |

## Direct Inference Contract

新场景只有同时满足以下条件，才能进入免 Evaluation 的直接推理路径：

1. 命中状态为 `active` 的唯一经验，且不存在未解决冲突。
2. 优化目标和 `experience_category` 一致。
3. 总卡数、每节点卡数、拓扑边界、慢卡数量/位置/速度范围与经验硬条件匹配。
4. 模型显存、batch、rank/group/stage 映射能力和必要的搜索约束匹配。
5. 参数换算没有超出经验记录的比例、阈值、上下界或允许变换。

直接推理输出必须包含主策略、`PP/TP/DP/MBN`、可执行映射、命中经验、置信度、适用边界和回退动作。任一硬条件缺失、越界、多经验冲突或只命中非 active 卡时，停止直接部署，改为生成仿真、Evaluation 或人工审核任务；结果用于经验准入或边界扩展，而不是成为每次部署的固定步骤。

## Update Policy

1. 先比较来源日期、哈希、验证状态和直接 Evaluation 证据。
2. 新信息与现有页面冲突时，不静默覆盖；同时陈述两个结论及各自条件。
3. 真正冲突时设置 `contested: true`，并在 `contradictions` 中填写页面 slug。
4. 新结论先进入假设和仿真层；经证据支持或知识库所有者明确确认成熟、完成人工审核、直接推理契约和正式写入门禁后，才能成为 active 经验。
5. 每次更新同步维护 `index.md` 和追加式 `log.md`。
6. 正式写入前保存或记录候选审查结果；`EVIDENCE_ONLY` 和 `KEEP_FOR_VALIDATION` 不得混入 active 部署动作。
7. 每张正式经验页必须且只能选择一个当前登记的 `experience_category`；分类变化属于知识边界变化，需要同步更新页面、索引和日志。
