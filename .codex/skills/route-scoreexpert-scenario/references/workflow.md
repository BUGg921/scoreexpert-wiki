# DeepWiki 召回到 Evolve 补库工作流

## 目录

1. 结构化场景
2. DeepWiki 召回
3. 本地硬裁决
4. 路由动作
5. 仿真与总结
6. 审核准入与索引刷新

## 1. 结构化场景

按 `scenario-contract.md` 记录所有输入。先复算：

- `total_gpus = Σ(gpus_per_node)`；
- 每个 Rank 只能属于一个节点和一个亲和组；
- 慢卡 Rank、节点和亲和组一致；
- 候选必须满足 `PP×TP×DP=active_gpu≤total_gpus`；
- TP group、PP stage、DP replica 必须能构造完整整数映射；
- 模型层数、GBS、MBN、显存和搜索上下界不能互相矛盾。

约束不成立时返回 `INSUFFICIENT_INPUT` 或明确的输入错误，不查询出一个“近似答案”掩盖问题。

## 2. DeepWiki 召回

先调用 `read_wiki_structure` 确认 `BUGg921/scoreexpert-wiki` 可访问，再用 `ask_question`。问题中嵌入完整场景，并要求只返回候选路径和匹配理由：

```text
给定以下 ScoreExpert 场景，请在成熟经验中召回候选，不要自行补造参数：
<normalized scene>

按优化目标、同构/局部异构/分布式异构、总卡数、节点/亲和组、慢卡 Rank/位置/倍率、模型/显存/映射能力和搜索边界逐项比较。
返回：候选总览路径、raw 来源、成熟状态、匹配字段、缺失/越界字段、是否唯一。若不能确认，写 ambiguous 或 miss。
```

DeepWiki 输出只进入候选集合。不要直接采用它生成的 PP/TP/DP/MBN，也不要把公开索引的状态当成本地成熟状态。

## 3. 本地硬裁决

固定读取顺序：

1. `SCHEMA.md` 的 Direct Inference Contract；
2. `index.md`；
3. 对应优化目标总览；
4. 候选链接的每个 raw 来源；
5. `git status --short --branch` 和最近 `log.md`；
6. `DAGBuilder_Evolve/outputs/*_scenario_analysis.md` 中是否已有同一完整场景的待审报告；
7. 必要时用 `rg` 查同一场景的冲突来源。

逐项核对成熟状态、优化目标、场景分类、总卡数、节点、亲和组、慢卡向量、速度倍率、模型、GBS、Seq、显存、映射能力、参数换算和搜索边界。只有一个成熟来源全部通过时才允许直接推理。

DeepWiki 与本地不一致时，本地获胜：

- DeepWiki miss、本地唯一命中：`DIRECT_MATCH_LOCAL_RECOVERY`；
- DeepWiki hit、本地候选未成熟或不存在：`STALE_RECALL`；
- DeepWiki 多候选、本地可唯一排除：按本地结果路由；
- 本地自身有冲突：`CONFLICT`。

如果正式库未命中，但一个或多个结构有效的平铺报告与场景的拓扑、慢卡Rank/倍率、模型、负载、显存和搜索边界完全一致，返回 `PENDING_REVIEW` 并列出这些报告。不得把报告当成熟经验，也不得为了获得新时间戳重复仿真。

## 4. 路由动作

### 直接返回

`DIRECT_MATCH` 和 `DIRECT_MATCH_LOCAL_RECOVERY` 必须返回：

- 命中的目标总览和唯一 raw；
- `PP/TP/DP/MBN`、`active_gpu` 和 `PP×TP×DP` 复算；
- TP group、PP stage、DP replica 与慢卡映射；
- 适用边界、失效条件和具体回退；
- DeepWiki 与本地索引是否一致。

不得运行 Evolve，也不要求新的真实 Evaluation。

### 已有待审报告

`PENDING_REVIEW` 返回匹配报告、仿真参数、覆盖率、证据缺口和 `review_report` 门禁。存在多份同场景报告时全部列出，优先让所有者选择或编辑，不擅自认定其中一份成熟。

### 仿真

`MISS`、完整输入的 `AMBIGUOUS_MATCH`、`OUT_OF_BOUND`、`CONFLICT` 或需实验判别的 `STALE_RECALL` 在没有精确待审报告时进入 Evolve。优先使用单变量对照；冲突场景至少覆盖冲突策略及能区分机制的邻居。

`INSUFFICIENT_INPUT` 只列一次最小缺口并停止。`RECALL_UNAVAILABLE` 可输出本地预判，但需明确没有完成用户要求的 DeepWiki 召回。

## 5. 仿真与总结

严格调用 `scoreexpert-scenario-analysis` 的两阶段流水线：

1. 新建唯一场景配置，复制完整输入和 campaign 硬上限；
2. 运行正式 Evolve，不用 mock；
3. 在 `awaiting_codex_summary` 读取同一 run 的公式、Top-K、单变量邻居、Rank mapping、关键路径、覆盖率和 Evaluation 状态；
4. 亲自写场景专属经验 JSON；
5. finalize 并只保留平铺 `*_scenario_analysis.md`；
6. 返回 `当前已仿真候选最优`、覆盖率和证据边界。

这一阶段的最终路由状态是 `PENDING_REVIEW`，不是已命中经验。

## 6. 审核准入与索引刷新

收到所有者对明确报告的“审核通过”后：

1. 重新读取报告当前版本并计算原文件 SHA-256；
2. 原样导入新的不可变 `raw/articles/` 快照；
3. 运行候选审查，记录 `ACCEPT_EXPERIENCE`、`EVIDENCE_ONLY`、`KEEP_FOR_VALIDATION` 或 `REJECT`；
4. 只从新 raw 更新对应优化目标和场景类别；
5. 更新 `index.md`、追加 `log.md`，运行 Wiki lint 和 `git diff --check`；
6. 未经用户明确 Git 授权，不提交或推送；
7. 未推送或 DeepWiki 未重新索引时，标记 `commit_push_reindex`，不要声称公开 DeepWiki 已能召回新经验。

准入后的下一次相同场景应先重新走 DeepWiki 召回和本地裁决；本地已经成熟但 DeepWiki 尚未刷新时使用 `DIRECT_MATCH_LOCAL_RECOVERY`，不能重复仿真。
