# ScoreExpert DB Search Report

- Status: `pass`
- Run root: `outputs/scoreexpert_db_search_20260613_173814`
- Database entries: 322
- DeepSeek enabled: `True`
- Rounds run: 3
- Stop reason: `target_gap_reached`
- Database best: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Best found: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Latency chart: `outputs/scoreexpert_db_search_20260613_173814/latency_trend.png`
- Score chart: `outputs/scoreexpert_db_search_20260613_173814/score_trend.png`
- Replacement chart: `outputs/scoreexpert_db_search_20260613_173814/island_replacement_events.png`

## Second Seed Initialization

- `memory_safe`: `pass`, program=`v1`, reason=``
- `topology_affinity`: `pass`, program=`v1`, reason=``
- `pipeline_efficiency`: `pass`, program=`v1`, reason=``
- `balanced_generalist`: `pass`, program=`v1`, reason=``

## Rounds

### Round 1

- Strategy: `{'pp': 1, 'tp': 1, 'dp': 1, 'micro_batch_num': 1}`
- Evaluation status: `invalid`
- Latency: `None`
- Adjustment: `{'type': 'repair_illegal', 'changed': 'tp', 'reason': 'strategy_not_found_in_database', 'target': {'pp': 1, 'tp': 8, 'dp': 1, 'micro_batch_num': 1}}`
- Next strategy: `{'pp': 1, 'tp': 8, 'dp': 1, 'micro_batch_num': 1}`

| Island | Best Program | Score |
|---|---|---:|
| `memory_safe` | `v0` | 993.260000 |
| `topology_affinity` | `v1` | 1000.500000 |
| `pipeline_efficiency` | `v0` | 1001.100000 |
| `balanced_generalist` | `v0` | 934.080000 |

Evolution:
- `memory_safe`: `pass`, program=`v2`, parents=`v0, v1`
- `topology_affinity`: `pass`, program=`v2`, parents=`v0, v1`
- `pipeline_efficiency`: `pass`, program=`v2`, parents=`v0, v1`
- `balanced_generalist`: `pass`, program=`v2`, parents=`v0, v1`

Adaptive context:
- `memory_safe` guidance: ['Avoid scoring invalid or database-missing strategy shapes too highly.']
- `topology_affinity` guidance: ['Avoid scoring invalid or database-missing strategy shapes too highly.']
- `pipeline_efficiency` guidance: ['Avoid scoring invalid or database-missing strategy shapes too highly.']
- `balanced_generalist` guidance: ['Avoid scoring invalid or database-missing strategy shapes too highly.']

### Round 2

- Strategy: `{'pp': 1, 'tp': 8, 'dp': 1, 'micro_batch_num': 1}`
- Evaluation status: `pass`
- Latency: `7.537446331`
- Adjustment: `{'type': 'latency_guided', 'changed': 'dp', 'target': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'next': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}}`
- Next strategy: `{'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}`

| Island | Best Program | Score |
|---|---|---:|
| `memory_safe` | `v0` | 1014.260000 |
| `topology_affinity` | `v1` | 1000.500000 |
| `pipeline_efficiency` | `v0` | 1003.200000 |
| `balanced_generalist` | `v0` | 955.080000 |

Evolution:
- `memory_safe`: `pass`, program=`v3`, parents=`v2, v0`
- `topology_affinity`: `pass`, program=`v3`, parents=`v2, v0`
- `pipeline_efficiency`: `pass`, program=`v3`, parents=`v2, v0`
- `balanced_generalist`: `pass`, program=`v3`, parents=`v0, v2`

Adaptive context:
- `memory_safe` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']
- `topology_affinity` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']
- `pipeline_efficiency` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']
- `balanced_generalist` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']

### Round 3

- Strategy: `{'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Adjustment: `{'type': 'latency_guided', 'changed': 'multi_parameter_jump_to_database_candidate', 'target': {'pp': 1, 'tp': 16, 'dp': 2, 'micro_batch_num': 1}, 'next': {'pp': 1, 'tp': 16, 'dp': 2, 'micro_batch_num': 1}}`
- Next strategy: `{'pp': 1, 'tp': 16, 'dp': 2, 'micro_batch_num': 1}`

| Island | Best Program | Score |
|---|---|---:|
| `memory_safe` | `v2` | 1027.031250 |
| `topology_affinity` | `v3` | 1007.000000 |
| `pipeline_efficiency` | `v0` | 1003.200000 |
| `balanced_generalist` | `v0` | 1007.520000 |

Evolution:
- `memory_safe`: `pass`, program=`v4`, parents=`v3, v1`
- `topology_affinity`: `pass`, program=`v4`, parents=`v3, v1`
- `pipeline_efficiency`: `pass`, program=`v4`, parents=`v2, v0`
- `balanced_generalist`: `pass`, program=`v4`, parents=`v2, v0`

Adaptive context:
- `memory_safe` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']
- `topology_affinity` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']
- `pipeline_efficiency` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']
- `balanced_generalist` guidance: ['Prefer strategy shapes that reduce database total_latency_s while preserving the island core direction.']
