# ScoreExpert Search Report

- Status: `pass`
- Run root: `outputs/scoreexpert_search_20260618_125218`
- Strategy count: 322
- DeepSeek enabled: `False`
- OverlapOPT: `disabled`
- Initial score matrix: `outputs/scoreexpert_search_20260618_125218/initialization/initial_score_matrix.md`
- Evaluation cache: `outputs/scoreexpert_search_20260618_125218/evaluation_cache.json`
- Latency trend chart: `outputs/scoreexpert_search_20260618_125218/island_best_latency_trend.png`
- Replacement chart: `outputs/scoreexpert_search_20260618_125218/island_replacement_events.png`

## Initialization

- Nomination Top-N: 64
- Union candidates: 142
- Cache misses evaluated: 142

| Island | Rank | Strategy | Score | Score rank | Total latency (s) |
|---|---:|---|---:|---:|---:|
| `memory_safe` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1023.860000 | 43 | 2.343845636 |
| `memory_safe` | 2 | PP=2, MBN=8, TP=8, DP=2 | 1024.360000 | 34 | 2.591522803 |
| `memory_safe` | 3 | PP=2, MBN=4, TP=8, DP=2 | 1023.720000 | 45 | 2.610345723 |
| `memory_safe` | 4 | PP=4, MBN=16, TP=8, DP=1 | 1025.360000 | 24 | 2.721872544 |
| `topology_affinity` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1000.800000 | 50 | 2.343845636 |
| `topology_affinity` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1000.800000 | 51 | 2.773925636 |
| `topology_affinity` | 3 | PP=2, MBN=32, TP=4, DP=4 | 1000.487500 | 57 | 2.774894514 |
| `topology_affinity` | 4 | PP=1, MBN=16, TP=8, DP=4 | 1000.800000 | 52 | 3.634085636 |
| `pipeline_efficiency` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1003.200000 | 29 | 2.343845636 |
| `pipeline_efficiency` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1003.200000 | 30 | 2.773925636 |
| `pipeline_efficiency` | 3 | PP=1, MBN=4, TP=16, DP=2 | 1005.600000 | 10 | 2.794008142 |
| `pipeline_efficiency` | 4 | PP=1, MBN=16, TP=8, DP=4 | 1003.200000 | 31 | 3.634085636 |
| `balanced_generalist` | 1 | PP=8, MBN=64, TP=2, DP=2 | 972.782535 | 57 | 2.223170486 |
| `balanced_generalist` | 2 | PP=1, MBN=4, TP=8, DP=4 | 1008.480000 | 12 | 2.343845636 |
| `balanced_generalist` | 3 | PP=4, MBN=32, TP=2, DP=4 | 977.045714 | 47 | 2.349294034 |
| `balanced_generalist` | 4 | PP=4, MBN=32, TP=4, DP=2 | 978.605714 | 46 | 2.455220585 |

## Evolution Rounds

### Round 1

- Nomination Top-N: 32
- Union candidates: 84
- Cache misses evaluated: 0
- Cycle directory: `outputs/scoreexpert_search_20260618_125218/round_01`

Evolution:
- `memory_safe`: `skipped`, mode=`bootstrap`, parents=`v0`
- `topology_affinity`: `skipped`, mode=`bootstrap`, parents=`v0`
- `pipeline_efficiency`: `skipped`, mode=`bootstrap`, parents=`v0`
- `balanced_generalist`: `skipped`, mode=`bootstrap`, parents=`v0`

| Island | Rank | Strategy | Score | Score rank | Total latency (s) |
|---|---:|---|---:|---:|---:|
| `memory_safe` | 1 | PP=4, MBN=16, TP=8, DP=1 | 1025.360000 | 24 | 2.721872544 |
| `memory_safe` | 2 | PP=1, MBN=4, TP=16, DP=2 | 1047.220000 | 13 | 2.794008142 |
| `memory_safe` | 3 | PP=4, MBN=8, TP=8, DP=1 | 1024.720000 | 28 | 2.860143506 |
| `memory_safe` | 4 | PP=2, MBN=16, TP=8, DP=2 | 1024.680000 | 30 | 2.904671343 |
| `topology_affinity` |  | no valid leaders |  |  |  |
| `pipeline_efficiency` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1003.200000 | 29 | 2.343845636 |
| `pipeline_efficiency` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1003.200000 | 30 | 2.773925636 |
| `pipeline_efficiency` | 3 | PP=1, MBN=4, TP=16, DP=2 | 1005.600000 | 10 | 2.794008142 |
| `pipeline_efficiency` | 4 | PP=1, MBN=16, TP=8, DP=4 | 1003.200000 | 31 | 3.634085636 |
| `balanced_generalist` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1008.480000 | 12 | 2.343845636 |
| `balanced_generalist` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1008.640000 | 11 | 2.773925636 |
| `balanced_generalist` | 3 | PP=2, MBN=32, TP=4, DP=4 | 995.669091 | 31 | 2.774894514 |
| `balanced_generalist` | 4 | PP=1, MBN=4, TP=16, DP=2 | 1015.760000 | 5 | 2.794008142 |

### Round 2

- Nomination Top-N: 32
- Union candidates: 84
- Cache misses evaluated: 0
- Cycle directory: `outputs/scoreexpert_search_20260618_125218/round_02`

Evolution:
- `memory_safe`: `skipped`, mode=`bootstrap`, parents=`v0`
- `topology_affinity`: `skipped`, mode=`bootstrap`, parents=`v0`
- `pipeline_efficiency`: `skipped`, mode=`bootstrap`, parents=`v0`
- `balanced_generalist`: `skipped`, mode=`bootstrap`, parents=`v0`

| Island | Rank | Strategy | Score | Score rank | Total latency (s) |
|---|---:|---|---:|---:|---:|
| `memory_safe` | 1 | PP=4, MBN=16, TP=8, DP=1 | 1025.360000 | 24 | 2.721872544 |
| `memory_safe` | 2 | PP=1, MBN=4, TP=16, DP=2 | 1047.220000 | 13 | 2.794008142 |
| `memory_safe` | 3 | PP=4, MBN=8, TP=8, DP=1 | 1024.720000 | 28 | 2.860143506 |
| `memory_safe` | 4 | PP=2, MBN=16, TP=8, DP=2 | 1024.680000 | 30 | 2.904671343 |
| `topology_affinity` |  | no valid leaders |  |  |  |
| `pipeline_efficiency` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1003.200000 | 29 | 2.343845636 |
| `pipeline_efficiency` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1003.200000 | 30 | 2.773925636 |
| `pipeline_efficiency` | 3 | PP=1, MBN=4, TP=16, DP=2 | 1005.600000 | 10 | 2.794008142 |
| `pipeline_efficiency` | 4 | PP=1, MBN=16, TP=8, DP=4 | 1003.200000 | 31 | 3.634085636 |
| `balanced_generalist` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1008.480000 | 12 | 2.343845636 |
| `balanced_generalist` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1008.640000 | 11 | 2.773925636 |
| `balanced_generalist` | 3 | PP=2, MBN=32, TP=4, DP=4 | 995.669091 | 31 | 2.774894514 |
| `balanced_generalist` | 4 | PP=1, MBN=4, TP=16, DP=2 | 1015.760000 | 5 | 2.794008142 |

### Round 3

- Nomination Top-N: 32
- Union candidates: 84
- Cache misses evaluated: 0
- Cycle directory: `outputs/scoreexpert_search_20260618_125218/round_03`

Evolution:
- `memory_safe`: `skipped`, mode=`bootstrap`, parents=`v0`
- `topology_affinity`: `skipped`, mode=`bootstrap`, parents=`v0`
- `pipeline_efficiency`: `skipped`, mode=`bootstrap`, parents=`v0`
- `balanced_generalist`: `skipped`, mode=`bootstrap`, parents=`v0`

| Island | Rank | Strategy | Score | Score rank | Total latency (s) |
|---|---:|---|---:|---:|---:|
| `memory_safe` | 1 | PP=4, MBN=16, TP=8, DP=1 | 1025.360000 | 24 | 2.721872544 |
| `memory_safe` | 2 | PP=1, MBN=4, TP=16, DP=2 | 1047.220000 | 13 | 2.794008142 |
| `memory_safe` | 3 | PP=4, MBN=8, TP=8, DP=1 | 1024.720000 | 28 | 2.860143506 |
| `memory_safe` | 4 | PP=2, MBN=16, TP=8, DP=2 | 1024.680000 | 30 | 2.904671343 |
| `topology_affinity` |  | no valid leaders |  |  |  |
| `pipeline_efficiency` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1003.200000 | 29 | 2.343845636 |
| `pipeline_efficiency` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1003.200000 | 30 | 2.773925636 |
| `pipeline_efficiency` | 3 | PP=1, MBN=4, TP=16, DP=2 | 1005.600000 | 10 | 2.794008142 |
| `pipeline_efficiency` | 4 | PP=1, MBN=16, TP=8, DP=4 | 1003.200000 | 31 | 3.634085636 |
| `balanced_generalist` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1008.480000 | 12 | 2.343845636 |
| `balanced_generalist` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1008.640000 | 11 | 2.773925636 |
| `balanced_generalist` | 3 | PP=2, MBN=32, TP=4, DP=4 | 995.669091 | 31 | 2.774894514 |
| `balanced_generalist` | 4 | PP=1, MBN=4, TP=16, DP=2 | 1015.760000 | 5 | 2.794008142 |

### Round 4

- Nomination Top-N: 32
- Union candidates: 84
- Cache misses evaluated: 0
- Cycle directory: `outputs/scoreexpert_search_20260618_125218/round_04`

Evolution:
- `memory_safe`: `skipped`, mode=`bootstrap`, parents=`v0`
- `topology_affinity`: `skipped`, mode=`bootstrap`, parents=`v0`
- `pipeline_efficiency`: `skipped`, mode=`bootstrap`, parents=`v0`
- `balanced_generalist`: `skipped`, mode=`bootstrap`, parents=`v0`

| Island | Rank | Strategy | Score | Score rank | Total latency (s) |
|---|---:|---|---:|---:|---:|
| `memory_safe` | 1 | PP=4, MBN=16, TP=8, DP=1 | 1025.360000 | 24 | 2.721872544 |
| `memory_safe` | 2 | PP=1, MBN=4, TP=16, DP=2 | 1047.220000 | 13 | 2.794008142 |
| `memory_safe` | 3 | PP=4, MBN=8, TP=8, DP=1 | 1024.720000 | 28 | 2.860143506 |
| `memory_safe` | 4 | PP=2, MBN=16, TP=8, DP=2 | 1024.680000 | 30 | 2.904671343 |
| `topology_affinity` |  | no valid leaders |  |  |  |
| `pipeline_efficiency` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1003.200000 | 29 | 2.343845636 |
| `pipeline_efficiency` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1003.200000 | 30 | 2.773925636 |
| `pipeline_efficiency` | 3 | PP=1, MBN=4, TP=16, DP=2 | 1005.600000 | 10 | 2.794008142 |
| `pipeline_efficiency` | 4 | PP=1, MBN=16, TP=8, DP=4 | 1003.200000 | 31 | 3.634085636 |
| `balanced_generalist` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1008.480000 | 12 | 2.343845636 |
| `balanced_generalist` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1008.640000 | 11 | 2.773925636 |
| `balanced_generalist` | 3 | PP=2, MBN=32, TP=4, DP=4 | 995.669091 | 31 | 2.774894514 |
| `balanced_generalist` | 4 | PP=1, MBN=4, TP=16, DP=2 | 1015.760000 | 5 | 2.794008142 |

### Round 5

- Nomination Top-N: 32
- Union candidates: 84
- Cache misses evaluated: 0
- Cycle directory: `outputs/scoreexpert_search_20260618_125218/round_05`

Evolution:
- `memory_safe`: `skipped`, mode=`bootstrap`, parents=`v0`
- `topology_affinity`: `skipped`, mode=`bootstrap`, parents=`v0`
- `pipeline_efficiency`: `skipped`, mode=`bootstrap`, parents=`v0`
- `balanced_generalist`: `skipped`, mode=`bootstrap`, parents=`v0`

| Island | Rank | Strategy | Score | Score rank | Total latency (s) |
|---|---:|---|---:|---:|---:|
| `memory_safe` | 1 | PP=4, MBN=16, TP=8, DP=1 | 1025.360000 | 24 | 2.721872544 |
| `memory_safe` | 2 | PP=1, MBN=4, TP=16, DP=2 | 1047.220000 | 13 | 2.794008142 |
| `memory_safe` | 3 | PP=4, MBN=8, TP=8, DP=1 | 1024.720000 | 28 | 2.860143506 |
| `memory_safe` | 4 | PP=2, MBN=16, TP=8, DP=2 | 1024.680000 | 30 | 2.904671343 |
| `topology_affinity` |  | no valid leaders |  |  |  |
| `pipeline_efficiency` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1003.200000 | 29 | 2.343845636 |
| `pipeline_efficiency` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1003.200000 | 30 | 2.773925636 |
| `pipeline_efficiency` | 3 | PP=1, MBN=4, TP=16, DP=2 | 1005.600000 | 10 | 2.794008142 |
| `pipeline_efficiency` | 4 | PP=1, MBN=16, TP=8, DP=4 | 1003.200000 | 31 | 3.634085636 |
| `balanced_generalist` | 1 | PP=1, MBN=4, TP=8, DP=4 | 1008.480000 | 12 | 2.343845636 |
| `balanced_generalist` | 2 | PP=1, MBN=8, TP=8, DP=4 | 1008.640000 | 11 | 2.773925636 |
| `balanced_generalist` | 3 | PP=2, MBN=32, TP=4, DP=4 | 995.669091 | 31 | 2.774894514 |
| `balanced_generalist` | 4 | PP=1, MBN=4, TP=16, DP=2 | 1015.760000 | 5 | 2.794008142 |
