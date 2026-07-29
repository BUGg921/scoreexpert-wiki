# ScoreExpert DB Search Report

- Status: `pass`
- Run root: `outputs/scoreexpert_db_search_20260615_084549`
- Database entries: 322
- DeepSeek enabled: `True`
- Rounds run: 10
- Stop reason: `max_rounds`
- Stop on target gap: `False`
- Stop on patience: `False`
- Database best: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Best found: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Latency chart: `outputs/scoreexpert_db_search_20260615_084549/latency_trend.png`
- Score chart: `outputs/scoreexpert_db_search_20260615_084549/score_trend.png`
- Replacement chart: `outputs/scoreexpert_db_search_20260615_084549/island_replacement_events.png`
- LLM usage CSV: `outputs/scoreexpert_db_search_20260615_084549/llm_usage_by_round.csv`

## LLM Usage

| Round | Calls | Failures | Input Tokens | Output Tokens | Total Tokens | Elapsed s | Estimated Cost |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 0 | 9316 | 28720 | 38036 | 325.515 | 0.00000000 |
| 1 | 4 | 0 | 27922 | 44238 | 72160 | 489.308 | 0.00000000 |
| 2 | 4 | 0 | 28311 | 35082 | 63393 | 441.953 | 0.00000000 |
| 3 | 4 | 0 | 27810 | 30700 | 58510 | 373.006 | 0.00000000 |
| 4 | 4 | 0 | 24964 | 33433 | 58397 | 407.284 | 0.00000000 |
| 5 | 4 | 0 | 25111 | 42186 | 67297 | 506.276 | 0.00000000 |
| 6 | 4 | 0 | 24458 | 37125 | 61583 | 557.542 | 0.00000000 |
| 7 | 4 | 0 | 24518 | 28891 | 53409 | 338.957 | 0.00000000 |
| 8 | 4 | 1 | 17134 | 21929 | 39063 | 267.623 | 0.00000000 |
| 9 | 4 | 0 | 24224 | 33805 | 58029 | 408.084 | 0.00000000 |
| 10 | 4 | 0 | 23973 | 28478 | 52451 | 330.301 | 0.00000000 |

## Second Seed Initialization

- `memory_safe`: `pass`, program=`v1`, reason=``
- `topology_affinity`: `pass`, program=`v1`, reason=``
- `pipeline_efficiency`: `pass`, program=`v1`, reason=``
- `balanced_generalist`: `pass`, program=`v1`, reason=``

## Rounds

### Round 1

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 14, "score": 1003.2, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "pipeline_efficiency", "program_id": "v0"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v1", "ranking_quality": 90.82438958314998, "spearman": 0.18159767632398932, "top_k_avg_latency_s": 13.1895226801875, "bad_cases": [{"strategy": {"pp": 2, "tp": 2, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 999.34375, "total_latency_s": 15.260686921, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp2_dp1_tp2_mb64_naive_ar"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 1}, "score_rank": 109, "score": 997.78, "total_latency_s": 2.09976721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb1_rs_ag"}]}, "pipeline_efficiency": {"best_program_id": "v0", "ranking_quality": 150.87500963682666, "spearman": 0.19208064274350478, "top_k_avg_latency_s": 5.470187905125, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 32}, "score_rank": 11, "score": 1005.6, "total_latency_s": 9.24216721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb32_rs_ag"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 282, "score": 657.704225, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "balanced_generalist": {"best_program_id": "v0", "ranking_quality": 199.86441802695845, "spearman": 0.36631342874784917, "top_k_avg_latency_s": 28.52092762125, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 64}, "score_rank": 1, "score": 1016.36, "total_latency_s": 16.61496721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 16, "tp": 1, "dp": 2, "micro_batch_num": 64}, "score_rank": 148, "score": 944.397975, "total_latency_s": 2.283072818, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp16_dp2_tp1_mb64_rs_ag"}]}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.041666666666666664, 'avg_recent_program_similarity': 0.2868604161854221}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v1` | 90.824390 | 0.181598 | 13.189523 | 7.869590 |
| `pipeline_efficiency` | `v0` | 150.875010 | 0.192081 | 5.470188 | 2.000179 |
| `balanced_generalist` | `v0` | 199.864418 | 0.366313 | 28.520928 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v2`, parents=`v1, v0`
- `topology_affinity`: `pass`, program=`v2`, parents=`v1, v0`
- `pipeline_efficiency`: `pass`, program=`v2`, parents=`v1, v0`
- `balanced_generalist`: `pass`, program=`v2`, parents=`v0, v1`

Experience events:
- `add` `island_interpretation`: island_interpretation: PP=1, TP=8, DP=4, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- `add` `island_interpretation`: island_interpretation: PP=1, TP=16, DP=2, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- `add` `global_experience`: global_experience: PP=2, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- `add` `global_experience`: global_experience: PP=1, TP=4, DP=1, MB=1, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 2

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 6, "score": 1008.98, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "balanced_generalist", "program_id": "v2"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v2", "ranking_quality": 283.43118541503145, "spearman": 0.36433213963180183, "top_k_avg_latency_s": 11.2289575903125, "bad_cases": [{"strategy": {"pp": 1, "tp": 4, "dp": 1, "micro_batch_num": 1}, "score_rank": 1, "score": 999.3, "total_latency_s": 14.796854127, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp1_dp1_tp4_mb1_naive_ar"}], "missed_cases": [{"strategy": {"pp": 16, "tp": 1, "dp": 2, "micro_batch_num": 64}, "score_rank": 123, "score": 996.95625, "total_latency_s": 2.283072818, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp16_dp2_tp1_mb64_rs_ag"}]}, "pipeline_efficiency": {"best_program_id": "v2", "ranking_quality": 248.60770527781878, "spearman": 0.30807733542938565, "top_k_avg_latency_s": 7.062979572625, "bad_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 1, "micro_batch_num": 1}, "score_rank": 3, "score": 1012.9, "total_latency_s": 7.537446331, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp1_dp1_tp8_mb1_naive_ar"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 148, "score": 902.004225, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "balanced_generalist": {"best_program_id": "v2", "ranking_quality": 394.5056070215236, "spearman": 0.6750914066111089, "top_k_avg_latency_s": 52.655208524125, "bad_cases": [{"strategy": {"pp": 1, "tp": 1, "dp": 32, "micro_batch_num": 1}, "score_rank": 9, "score": 1007.86, "total_latency_s": 193.238499198, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp32_tp1_mb1_rs_ag"}], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.037037037037037035, 'avg_recent_program_similarity': 0.28307115891809653}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v2` | 283.431185 | 0.364332 | 11.228958 | 7.441515 |
| `pipeline_efficiency` | `v2` | 248.607705 | 0.308077 | 7.062980 | 2.099767 |
| `balanced_generalist` | `v2` | 394.505607 | 0.675091 | 52.655209 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v3`, parents=`v1, v2`
- `topology_affinity`: `pass`, program=`v3`, parents=`v2, v1`
- `pipeline_efficiency`: `pass`, program=`v3`, parents=`v1, v2`
- `balanced_generalist`: `pass`, program=`v3`, parents=`v0, v1`

Experience events:
- `add` `global_experience`: global_experience: PP=1, TP=4, DP=1, MB=2, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- `add` `global_experience`: global_experience: PP=1, TP=8, DP=1, MB=1, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 3

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 6, "score": 1008.98, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "balanced_generalist", "program_id": "v2"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v3", "ranking_quality": 340.32880684610774, "spearman": 0.40554092470337066, "top_k_avg_latency_s": 8.1058945521875, "bad_cases": [{"strategy": {"pp": 1, "tp": 2, "dp": 2, "micro_batch_num": 1}, "score_rank": 1, "score": 999.2, "total_latency_s": 14.587997811, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp2_mb1_rs_ag"}], "missed_cases": [{"strategy": {"pp": 16, "tp": 2, "dp": 1, "micro_batch_num": 64}, "score_rank": 167, "score": 992.65625, "total_latency_s": 2.345143222, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp16_dp1_tp2_mb64_naive_ar"}]}, "pipeline_efficiency": {"best_program_id": "v2", "ranking_quality": 248.60770527781878, "spearman": 0.30807733542938565, "top_k_avg_latency_s": 7.062979572625, "bad_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 1, "micro_batch_num": 1}, "score_rank": 3, "score": 1012.9, "total_latency_s": 7.537446331, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp1_dp1_tp8_mb1_naive_ar"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 148, "score": 902.004225, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "balanced_generalist": {"best_program_id": "v2", "ranking_quality": 394.5056070215236, "spearman": 0.6750914066111089, "top_k_avg_latency_s": 52.655208524125, "bad_cases": [{"strategy": {"pp": 1, "tp": 1, "dp": 32, "micro_batch_num": 1}, "score_rank": 9, "score": 1007.86, "total_latency_s": 193.238499198, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp32_tp1_mb1_rs_ag"}], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.018518518518518517, 'avg_recent_program_similarity': 0.28484455515812174}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v3` | 340.328807 | 0.405541 | 8.105895 | 2.724008 |
| `pipeline_efficiency` | `v2` | 248.607705 | 0.308077 | 7.062980 | 2.099767 |
| `balanced_generalist` | `v2` | 394.505607 | 0.675091 | 52.655209 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v4`, parents=`v1, v2`
- `topology_affinity`: `pass`, program=`v4`, parents=`v3, v1`
- `pipeline_efficiency`: `pass`, program=`v4`, parents=`v1, v3`
- `balanced_generalist`: `pass`, program=`v4`, parents=`v3, v2`

Experience events:
- `add` `global_experience`: global_experience: PP=1, TP=2, DP=2, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- `add` `global_experience`: global_experience: PP=1, TP=2, DP=2, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- `add` `island_interpretation`: island_interpretation: PP=16, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 4

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 11, "score": 1480.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "pipeline_efficiency", "program_id": "v4"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v4", "ranking_quality": 564.0169668781047, "spearman": 0.5957307391114244, "top_k_avg_latency_s": 4.382653086, "bad_cases": [{"strategy": {"pp": 2, "tp": 4, "dp": 1, "micro_batch_num": 16}, "score_rank": 2, "score": 1003.675, "total_latency_s": 8.231504198, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp2_dp1_tp4_mb16_naive_ar"}], "missed_cases": []}, "pipeline_efficiency": {"best_program_id": "v4", "ranking_quality": 650.4918669273267, "spearman": 0.6717403831369846, "top_k_avg_latency_s": 3.540929423, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1539.300699, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "balanced_generalist": {"best_program_id": "v4", "ranking_quality": 684.3398160341229, "spearman": 0.7117996810505318, "top_k_avg_latency_s": 4.025666835, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 32}, "score_rank": 12, "score": 1000.28, "total_latency_s": 9.24216721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb32_rs_ag"}], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.0, 'avg_recent_program_similarity': 0.2744239438526755}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v4` | 564.016967 | 0.595731 | 4.382653 | 2.198843 |
| `pipeline_efficiency` | `v4` | 650.491867 | 0.671740 | 3.540929 | 2.000179 |
| `balanced_generalist` | `v4` | 684.339816 | 0.711800 | 4.025667 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v5`, parents=`v1, v2`
- `topology_affinity`: `pass`, program=`v5`, parents=`v4, v2`
- `pipeline_efficiency`: `pass`, program=`v5`, parents=`v1, v2`
- `balanced_generalist`: `pass`, program=`v5`, parents=`v3, v1`

Experience events:
- `add` `global_experience`: global_experience: PP=2, TP=4, DP=1, MB=16, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- `add` `global_experience`: global_experience: PP=2, TP=4, DP=1, MB=8, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 5

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 5, "score": 1002.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "topology_affinity", "program_id": "v5"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v5", "ranking_quality": 651.8875700071206, "spearman": 0.6715047815895357, "top_k_avg_latency_s": 3.56376145125, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 16, "score": 999.975, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "pipeline_efficiency": {"best_program_id": "v4", "ranking_quality": 650.4918669273267, "spearman": 0.6717403831369846, "top_k_avg_latency_s": 3.540929423, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1539.300699, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "balanced_generalist": {"best_program_id": "v4", "ranking_quality": 684.3398160341229, "spearman": 0.7117996810505318, "top_k_avg_latency_s": 4.025666835, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 32}, "score_rank": 12, "score": 1000.28, "total_latency_s": 9.24216721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb32_rs_ag"}], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.1111111111111111, 'avg_recent_program_similarity': 0.2687012190131335}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v5` | 651.887570 | 0.671505 | 3.563761 | 2.000179 |
| `pipeline_efficiency` | `v4` | 650.491867 | 0.671740 | 3.540929 | 2.000179 |
| `balanced_generalist` | `v4` | 684.339816 | 0.711800 | 4.025667 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v6`, parents=`v5, v4`
- `topology_affinity`: `pass`, program=`v6`, parents=`v5, v4`
- `pipeline_efficiency`: `pass`, program=`v6`, parents=`v1, v4`
- `balanced_generalist`: `pass`, program=`v6`, parents=`v3, v4`

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 6

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 5, "score": 1002.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "topology_affinity", "program_id": "v5"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v5", "ranking_quality": 651.8875700071206, "spearman": 0.6715047815895357, "top_k_avg_latency_s": 3.56376145125, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 16, "score": 999.975, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "pipeline_efficiency": {"best_program_id": "v4", "ranking_quality": 650.4918669273267, "spearman": 0.6717403831369846, "top_k_avg_latency_s": 3.540929423, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1539.300699, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "balanced_generalist": {"best_program_id": "v4", "ranking_quality": 684.3398160341229, "spearman": 0.7117996810505318, "top_k_avg_latency_s": 4.025666835, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 32}, "score_rank": 12, "score": 1000.28, "total_latency_s": 9.24216721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb32_rs_ag"}], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.1111111111111111, 'avg_recent_program_similarity': 0.27892160701409313}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v5` | 651.887570 | 0.671505 | 3.563761 | 2.000179 |
| `pipeline_efficiency` | `v4` | 650.491867 | 0.671740 | 3.540929 | 2.000179 |
| `balanced_generalist` | `v4` | 684.339816 | 0.711800 | 4.025667 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v7`, parents=`v5, v0`
- `topology_affinity`: `pass`, program=`v7`, parents=`v6, v4`
- `pipeline_efficiency`: `pass`, program=`v7`, parents=`v1, v5`
- `balanced_generalist`: `pass`, program=`v7`, parents=`v3, v4`

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 7

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 5, "score": 1002.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "topology_affinity", "program_id": "v5"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v5", "ranking_quality": 651.8875700071206, "spearman": 0.6715047815895357, "top_k_avg_latency_s": 3.56376145125, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 16, "score": 999.975, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "pipeline_efficiency": {"best_program_id": "v4", "ranking_quality": 650.4918669273267, "spearman": 0.6717403831369846, "top_k_avg_latency_s": 3.540929423, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1539.300699, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "balanced_generalist": {"best_program_id": "v7", "ranking_quality": 728.1334055050334, "spearman": 0.7393918459646227, "top_k_avg_latency_s": 3.051961395, "bad_cases": [], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.07142857142857142, 'avg_recent_program_similarity': 0.27819375244153044}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v5` | 651.887570 | 0.671505 | 3.563761 | 2.000179 |
| `pipeline_efficiency` | `v4` | 650.491867 | 0.671740 | 3.540929 | 2.000179 |
| `balanced_generalist` | `v7` | 728.133406 | 0.739392 | 3.051961 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v8`, parents=`v5, v6`
- `topology_affinity`: `pass`, program=`v8`, parents=`v7, v1`
- `pipeline_efficiency`: `pass`, program=`v8`, parents=`v1, v7`
- `balanced_generalist`: `pass`, program=`v8`, parents=`v7, v6`

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 8

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 5, "score": 1002.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "topology_affinity", "program_id": "v5"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v5", "ranking_quality": 651.8875700071206, "spearman": 0.6715047815895357, "top_k_avg_latency_s": 3.56376145125, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 16, "score": 999.975, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "pipeline_efficiency": {"best_program_id": "v4", "ranking_quality": 650.4918669273267, "spearman": 0.6717403831369846, "top_k_avg_latency_s": 3.540929423, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1539.300699, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "balanced_generalist": {"best_program_id": "v8", "ranking_quality": 775.7830951262063, "spearman": 0.773910443836298, "top_k_avg_latency_s": 2.8257227854374998, "bad_cases": [], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.07142857142857142, 'avg_recent_program_similarity': 0.27834072923686204}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v5` | 651.887570 | 0.671505 | 3.563761 | 2.000179 |
| `pipeline_efficiency` | `v4` | 650.491867 | 0.671740 | 3.540929 | 2.000179 |
| `balanced_generalist` | `v8` | 775.783095 | 0.773910 | 2.825723 | 2.000179 |

Evolution:
- `memory_safe`: `fail`, program=``, parents=`v5, v0`
- `topology_affinity`: `pass`, program=`v9`, parents=`v8, v4`
- `pipeline_efficiency`: `pass`, program=`v9`, parents=`v1, v8`
- `balanced_generalist`: `pass`, program=`v9`, parents=`v8, v3`

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 9

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 5, "score": 1002.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "topology_affinity", "program_id": "v5"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v5", "ranking_quality": 651.8875700071206, "spearman": 0.6715047815895357, "top_k_avg_latency_s": 3.56376145125, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 16, "score": 999.975, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "pipeline_efficiency": {"best_program_id": "v4", "ranking_quality": 650.4918669273267, "spearman": 0.6717403831369846, "top_k_avg_latency_s": 3.540929423, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1539.300699, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "balanced_generalist": {"best_program_id": "v8", "ranking_quality": 775.7830951262063, "spearman": 0.773910443836298, "top_k_avg_latency_s": 2.8257227854374998, "bad_cases": [], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.07142857142857142, 'avg_recent_program_similarity': 0.2859479638177459}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v5` | 651.887570 | 0.671505 | 3.563761 | 2.000179 |
| `pipeline_efficiency` | `v4` | 650.491867 | 0.671740 | 3.540929 | 2.000179 |
| `balanced_generalist` | `v8` | 775.783095 | 0.773910 | 2.825723 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v9`, parents=`v5, v4`
- `topology_affinity`: `pass`, program=`v10`, parents=`v8, v0`
- `pipeline_efficiency`: `pass`, program=`v10`, parents=`v1, v5`
- `balanced_generalist`: `pass`, program=`v10`, parents=`v8, v0`

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

### Round 10

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 5, "score": 1002.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "topology_affinity", "program_id": "v5"}, "islands": {"memory_safe": {"best_program_id": "v1", "ranking_quality": 556.0818218893594, "spearman": 0.5785587065715572, "top_k_avg_latency_s": 3.522138624875, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1048.671875, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 121, "score": 1040.3125, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "topology_affinity": {"best_program_id": "v5", "ranking_quality": 651.8875700071206, "spearman": 0.6715047815895357, "top_k_avg_latency_s": 3.56376145125, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 16, "score": 999.975, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "pipeline_efficiency": {"best_program_id": "v4", "ranking_quality": 650.4918669273267, "spearman": 0.6717403831369846, "top_k_avg_latency_s": 3.540929423, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1539.300699, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": []}, "balanced_generalist": {"best_program_id": "v10", "ranking_quality": 884.4635885312761, "spearman": 0.8948810134792825, "top_k_avg_latency_s": 2.43925898075, "bad_cases": [], "missed_cases": []}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.018518518518518517, 'avg_recent_program_similarity': 0.2831998168397617}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v1` | 556.081822 | 0.578559 | 3.522139 | 2.198843 |
| `topology_affinity` | `v5` | 651.887570 | 0.671505 | 3.563761 | 2.000179 |
| `pipeline_efficiency` | `v4` | 650.491867 | 0.671740 | 3.540929 | 2.000179 |
| `balanced_generalist` | `v10` | 884.463589 | 0.894881 | 2.439259 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v10`, parents=`v5, v6`
- `topology_affinity`: `pass`, program=`v11`, parents=`v8, v1`
- `pipeline_efficiency`: `pass`, program=`v11`, parents=`v1, v0`
- `balanced_generalist`: `pass`, program=`v11`, parents=`v10, v0`

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']

Replacements:
- `memory_safe` from `pipeline_efficiency, balanced_generalist`
- `pipeline_efficiency` from `balanced_generalist, memory_safe`
