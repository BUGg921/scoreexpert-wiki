# Wiki Schema

## Domain

本 Wiki 覆盖 ScoreExpert 在 GPU 集群上的部署经验：场景条件、PP/TP/DP/MBN 候选、证据、适用边界、反例、来源可信度，以及尚待仿真或 Evaluation 验证的假设。

## Conventions

- 文件名使用小写英文、连字符、不留空格，例如 `deployment-topic.md`。
- `concepts/` 中的部署经验必须放入与 `experience_category` 同名的一级子目录；支撑知识可以保留在 `concepts/` 根目录。
- 当前经验库使用“总经验库 → 优化目标总体经验 → raw 场景来源”的结构，不为每个 `experience_category` 创建重复分类页。总经验库永久保留延迟优先、稳定优先及各自三类场景的完整框架；目标总览保存可召回的数值策略和原因，raw 保存实验场景、Score 推导、映射和结论边界。
- 每个知识页必须以 YAML frontmatter 开头，并满足下方字段契约。
- 每个知识页至少包含 2 个指向其他知识页的 `[[wikilinks]]`。
- 每个新知识页都必须加入 `index.md`，每次操作都必须追加到 `log.md`。
- 更新知识页时必须更新 `updated` 日期；原始来源只读，不在 `raw/` 内直接修订。
- Evolve 仿真完成后只在 `DAGBuilder_Evolve/outputs/` 根目录保留带场景名和时间戳的 `*_scenario_analysis.md` 待审草稿，不保留成功运行的场景子目录。仿真完成后不得自动写入 `raw/` 或更新 `concepts/`；只有知识库所有者手动修改、审核并明确授权后，才把该平铺文件的当前版本导入不可变 raw 快照。
- `concepts/` 的经验更新必须以用户审核后的 raw 快照为唯一文本来源，不得直接从未审核草稿、`deployment_experience.json` 或 `final_report.json` 生成正式经验。
- 综合 3 个及以上来源时，在关键段落末尾追加 `^[raw/articles/source-file.md]` 来源标记。
- 若以后因独立治理需要重新建立具体经验页，其正文使用 `1. 场景描述` 和 `2. 具体的并行策略`；当前五个成熟场景不创建重复经验页，直接由目标总览与 raw 来源共同承载。
- 每条“并行策略”先写一条可判定的“适用规则”，再写资源使用并按 `PP`、`TP`、`DP`、`MBN` 分项给出变量、公式、整数约束、拓扑关系和最大/最小可行值，不写某次实验的固定参数数字。适用规则只使用输入场景已经提供的慢卡数量、rank、物理位置、节点慢卡向量、亲和组慢卡向量和速度倍率，用于判断选择哪条策略；优化目标由所在总览确定，不在规则内重复。raw 边界、模型/workload、显存、网络、映射能力和参数整数可行性属于命中策略后的部署校验，不写入适用规则。满卡写成 `active_gpu=N`，留卡则必须写出可计算的选择规则；固定 PP/TP/DP/MBN 数值只保留在 raw。目标总览只能抽取来源原因能够直接支持的关系，例如 `active_gpu=N`、`PP×TP×DP=N`、`TP:DP=2:1` 或“约束内最大 MBN”，不能把实例中 TP 恰好等于节点规模改写成固定规则，也不能借变量化扩大 raw 的适用边界。
- “场景定义”使用输入完成同构、局部异构或分布式异构分类；“适用规则”再用精确的慢卡数量与节点/亲和组分布选择该类内部的具体策略；随后只写资源使用以及 `PP`、`TP`、`DP`、`MBN` 的取值或求解规则。具体 rank 分组、TP group、PP stage、DP replica、layer 分配、bubble、skew 和运行验收保留在 raw 来源。
- 正式经验总览和经验页不提评分策略、评分权重、打分公式或 score 选择过程。“原因”只解释算力利用、显存、通信域、同步等待、流水线气泡、replica skew 和调度等部署机制；评分代码与候选排序证据只保留在 raw 来源和审核层，不进入经验正文。
- 卡数、节点规模和拓扑必须写入 raw 场景来源，并与 `PP×TP×DP=active_gpu`、完整 group/replica/stage 约束绑定。资源改变后先重新分类并重建拓扑；目标总览明确给出卡数换算规则时，可以按比例和约束求解新参数，不能随意删除 rank 或沿用原实例参数。
- 来源存在显式“经验总结”“结论”“建议”或“最佳实践”时，在“具体的并行策略”中忠实保留其结论、限定词和因果关系，不另建第三个一级章节。Wiki 新增推理必须明确标注，不能冒充来源结论。
- 不规定经验条数或来源标题。显式结论使用“来源明确经验”；没有总结段落但存在分散决策时使用“来源分散归纳”；完全没有部署结论时使用“Wiki 推导假设”并默认保持 `unverified`。同一来源可组合使用，但三类内容必须分开。
- 来源强调的比例、阈值、上下界和不等式必须作为定量经验保留；固定实例留在 raw，目标总览用已定义变量表达来源支持的关系。不得把关系弱化成“较平衡”“较大”，也不得把单一实例擅自升级成跨资源规模结论。
- 当前目标总览中的成熟经验只有在对应 raw 来源的硬条件和量化边界匹配，或命中已明确准入的卡数换算规则时，才能直接生成部署策略；未命中或越界时只能生成候选与补库计划。
- 经验成熟度与来源附件完整度分开管理。知识库所有者明确确认某条经验成熟，可作为人工审核准入依据；仍需保留缺失的原始指标说明、适用边界、直接推理契约和审核日期，但不得仅因附件不完整把成熟经验自动降级。
- 参数组合是特定条件下的候选，不得省略拓扑、慢卡分布、模型约束或搜索空间边界。
- 来源提取与正式经验写入之间必须有候选审查层。每条候选按“来源可追溯、触发条件、部署动作、非 score 机制、预期观测、失效边界、新增价值、证据状态”判定为经验、证据、待验证或拒绝；纯 score 解释不得单独成为正式经验。
- 筛选不得删除来源明确结论。未通过经验门槛的来源结论继续保留在来源整理或证据层，并记录降级/拒绝理由。
- 并行策略以资源使用、`PP`、`TP`、`DP`、`MBN` 五项变量化关系为合并键：五项全部相同的场景合并为一条并行策略，不因慢卡数量、位置或作用机制不同而重复参数；合并后的“适用规则”用“或”并列各个已准入输入模式，不能把多个来源扩写成未经准入的更大范围。这些差异分别保留在同一编号的“原因”和“场景案例”中。任一项关系不同则拆成独立策略，并按最能区分它的参数特点命名，而不是只用场景编号或慢卡数量命名。
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
status: active | superseded | unverified | partially_supported | supported | refuted | mixed
optimization_priority: latency-first | stability-first
admitted_by: <审核主体；active 必填>
admitted_at: YYYY-MM-DD # active 必填
```

`status`、`optimization_priority`、`admitted_by` 和 `admitted_at` 只用于知识库检索与治理，不在正文重复。`sources` 和 `confidence` 分别保存准入来源与置信度；来源附件缺口保留在来源层或审核日志，不混入场景描述。

正文只允许以下两个一级章节；所需证据和直接推理字段通过二级标题或列表并入其中：

```markdown
## 1. 场景描述
## 2. 具体的并行策略
```

第二章的三级标题固定为：

```markdown
### 部署策略
### 部署经验
### 失效条件与回退
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
| `distributed-heterogeneity` | 分布式异构 | 异常跨节点、亲和组或副本分布，核心动作是均衡、对称映射或限制同步扩散 | 两张跨亲和组慢卡、四张均匀慢卡、五张 2/1/1/1 非对称慢卡 |

分类回答“这条经验主要处理哪种部署场景”：没有稳定设备快慢差异的是同构场景；异构影响能够限制在一个可控局部范围的是局部异构；异常跨越多个独立拓扑区域的是分布式异构。Score 推导、验证计划和证据页不是部署经验，不设置 `experience_category`。通信、显存、Batch、资源降级和跨场景决策在当前材料中尚未形成独立经验类别；以后只有出现通过审查的实际经验时才扩充，不预建空分类。

### Objective-first knowledge format

每个优化目标下的三类知识使用以下字段：

- 同构基线：场景定义 → 并行策略 → 原因 → 场景案例。
- 局部异构：场景定义 → 并行策略 → 原因 → 场景案例。
- 分布式异构：场景定义 → 并行策略 → 原因 → 场景案例。

三类知识严格分工：“场景定义”保存用于同构、局部异构或分布式异构分类的输入特征；每条“并行策略”先用慢卡数量、节点/亲和组慢卡向量和速度倍率写“适用规则”，再写资源使用以及 `PP`、`TP`、`DP`、`MBN` 的变量化关系，固定参数数字只留在 raw。raw 边界、模型/workload、显存、网络、映射能力、参数可行性、rank 映射、group/stage/replica 构造、layer/计算量分配和运行验收都在选中策略后另行校验，不混入适用规则。“原因”解释资源使用和四个参数的选择机制。同一大类内五项策略关系完全相同的场景共用一个策略编号，合并后的适用规则保留各个已准入输入分支；任一策略关系不同则按参数特点拆分。变量化只用于表达经验关系，不代表自动准入其他卡数或拓扑。

局部异构的“场景定义”必须说明：异常性能差异是否稳定可识别，异常 rank/速度/物理位置是否已知，所有异常是否位于同一节点或另一个由 raw 明确准入的单一物理局部范围，以及该范围之外是否仍无固定快慢结构。group/stage/replica 是否真正收敛属于 raw 映射与验收细节，不写入并行策略；无法收敛不改变输入的物理异构分类。慢卡数量不能单独作为局部异构的判定标准。

卡数、节点规模和拓扑是场景匹配条件。资源变化后先重新判定场景并重建完整并行拓扑；若成熟策略明确允许按比例换算，且能够求得满足模型与通信边界的完整整数拓扑，则可直接生成新参数，否则按新场景补库。减卡不能通过随意删除 rank 或照搬原实例参数完成。

优化目标总览保存该目标下的三类场景规则。三类分支在“并行策略”中写变量化参数关系，在“场景案例”中概括场景边界并链接唯一 raw 来源；具体参数数字、卡数、慢卡位置、rank 映射、Score 代码和结论边界在 raw 中维护。不得设置“当前经验范围”。

“原因”只解释对应数值策略成立的机制，不重复场景定义或来源内容；存在成熟并行策略时，必须与“并行策略”按编号一一对应，例如“并行策略 1”对应“原因 1”，同一策略内部的条件分支在对应原因条目内分别解释。“场景案例”概括场景条件、参数结果并链接 raw 来源，不重复原因。当前没有稳定性直接 Evaluation 的页面不得因进入“稳定优先型”入口而填入数值策略。

对应文件结构固定为：

```text
concepts/
├── deployment-objective-knowledge-framework.md
└── latency-first-experience-summary.md

raw/articles/
├── homogeneous-32gpu-deployment-analysis-2026-07-22.md
├── single-slow-gpu-deployment-analysis-2026-07-22.md
├── two-slow-gpu-deployment-analysis-2026-07-22.md
├── four-slow-gpu-deployment-analysis-2026-07-22.md
└── five-slow-gpu-2-1-1-1-evolve-analysis-reviewed-2026-08-03.md
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

上表状态写入正式经验页的 `status` frontmatter。`active` 页同时记录 `admitted_by` 和 `admitted_at`；正文不再设置“状态”“准入依据”或“准入记录”。

## Direct Inference Contract

新场景只有同时满足以下条件，才能进入免 Evaluation 的直接推理路径：

1. 命中目标总览中的唯一成熟场景规则，且不存在未解决冲突。
2. 优化目标和 `experience_category` 一致。
3. 总卡数、每节点卡数、拓扑边界、慢卡数量/位置/速度范围与对应 raw 来源匹配；资源规模不同时，必须命中目标总览明确准入的换算规则，并求得满足 `PP×TP×DP=active_gpu`、比例和完整拓扑约束的整数参数。
4. 模型显存、batch、rank/group/stage 映射能力和必要的搜索约束匹配。
5. 参数换算没有超出经验记录的比例、阈值、上下界或允许变换。

直接推理输出必须包含主策略、资源使用、`PP/TP/DP/MBN`、可执行映射、命中场景来源、适用边界和回退动作。任一硬条件缺失、越界或多场景冲突时，停止直接部署，改为生成仿真、Evaluation 或人工补库任务；结果用于边界扩展，而不是成为每次部署的固定步骤。

## Update Policy

1. 仿真结束后先向知识库所有者交付待审草稿并停止；未经明确审核授权，不创建 raw、不更新 concepts。
2. 获得授权后重新读取审核后文件，比较来源日期、哈希、验证状态和直接 Evaluation 证据，再创建不可变 raw 快照。
3. 只根据该 raw 提取候选并更新 concepts；新信息与现有页面冲突时，不静默覆盖，同时陈述两个结论及各自条件。
4. 真正冲突时设置 `contested: true`，并在 `contradictions` 中填写页面 slug。
5. 新结论先进入假设和仿真层；经证据支持或知识库所有者明确确认成熟、完成人工审核、直接推理契约和正式写入门禁后，才能成为 active 经验。
6. 每次更新同步维护 `index.md` 和追加式 `log.md`。
7. 正式写入前保存或记录候选审查结果；`EVIDENCE_ONLY` 和 `KEEP_FOR_VALIDATION` 不得混入 active 部署动作。
8. 每张正式经验页必须且只能选择一个当前登记的 `experience_category`；分类变化属于知识边界变化，需要同步更新页面、索引和日志。
