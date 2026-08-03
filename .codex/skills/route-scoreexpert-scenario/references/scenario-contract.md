# ScoreExpert 场景输入与路由契约

## 目录

1. 场景输入
2. 路由状态
3. 路由输出

## 1. 场景输入

先把自然语言整理为下列结构；未知值写 `unknown`，不得猜测：

```yaml
optimization_priority: latency-first | stability-first
topology:
  total_gpus: <int>
  node_count: <int>
  gpus_per_node: <int | list[int]>
  affinity_groups: <node/rank membership>
  rank_to_node: <mapping>
  network_boundaries: <intra-node/inter-node/inter-affinity links>
heterogeneity:
  slow_gpus:
    - rank: <int>
      node: <int>
      affinity_group: <int>
      speed_ratio: <float>
model:
  name: <string>
  num_layers: <int>
  parameter_count: <number | unknown>
workload:
  global_batch_size: <int>
  sequence_length: <int>
memory:
  capacity_gb_per_gpu: <float>
mapping_capabilities:
  rank_reorder: <bool | unknown>
  stage_layer_rebalance: <bool | unknown>
search:
  active_gpu_counts: <list[int]>
  pp_values: <list[int]>
  tp_values: <list[int]>
  dp_values: <list[int]>
  mbn_values: <list[int]>
  schedules: <list[string]>
  dp_communications: <list[string]>
campaign:
  max_followup_rounds: <int | null>
  scenarios_per_round: <int | null>
  max_total_scenarios: <int | null>
  max_wall_time_s: <number | null>
```

直接匹配至少需要：优化目标、总卡数、节点与每节点卡数、亲和组、慢卡数量/Rank/节点/倍率、模型层数、GBS、Seq、显存和映射能力。仿真还必须有搜索空间以及至少一个 campaign 硬上限。用户明确只要求当前一个场景时，可将其解析为 `max_total_scenarios=1`、`max_followup_rounds=0`、`scenarios_per_round=1`。

## 2. 路由状态

| 状态 | 判定 | 动作 |
| --- | --- | --- |
| `DIRECT_MATCH` | DeepWiki 召回且本地唯一成熟经验完整匹配 | 直接返回策略 |
| `DIRECT_MATCH_LOCAL_RECOVERY` | DeepWiki 未召回或索引陈旧，但本地唯一成熟经验完整匹配 | 直接返回，并标记索引差异 |
| `PENDING_REVIEW` | 正式库未命中，但存在同一完整场景的有效平铺待审报告 | 返回报告并等待审核，不重复仿真 |
| `MISS` | 输入完整，本地没有成熟候选 | 进入有界仿真 |
| `AMBIGUOUS_MATCH` | 输入完整，但存在两个以上可能候选或边界无法唯一判定 | 进入对照仿真 |
| `OUT_OF_BOUND` | 命中场景类型但越过卡数、拓扑、速度、模型、显存或搜索边界 | 进入边界仿真 |
| `CONFLICT` | 本地成熟来源给出不兼容策略 | 保留冲突，进入判别仿真/Evaluation |
| `STALE_RECALL` | DeepWiki 给出本地已不存在、未成熟或已变更的候选 | 以本地为准，通常进入仿真或人工修复 |
| `INSUFFICIENT_INPUT` | 缺少无法合法配置或硬匹配的字段 | 列出缺口并停止 |
| `RECALL_UNAVAILABLE` | DeepWiki 工具不可用 | 可做本地预判，但不得声称完成 DeepWiki 路由 |

“模糊”不等于“缺字段”：完整输入的多候选模糊可以仿真；决定性输入缺失必须先补齐。

## 3. 路由输出

```yaml
normalized_scene: <完整结构>
deepwiki:
  status: hit | miss | ambiguous | stale | unavailable
  candidates: <concept/raw paths>
local_adjudication:
  matched_active_sources: <paths>
  rejected_candidates: <path + reason>
  missing_fields: <list>
route_state: <one enum above>
action: direct_return | return_pending_report | request_input | simulate | resolve_conflict | repair_recall
result:
  pp: <int | null>
  tp: <int | null>
  dp: <int | null>
  mbn: <int | null>
  active_gpus: <int | null>
  mapping: <text | null>
  source_or_report: <paths>
boundaries: <list>
next_gate: none | provide_fields | review_report | approve_admission | commit_push_reindex
```
