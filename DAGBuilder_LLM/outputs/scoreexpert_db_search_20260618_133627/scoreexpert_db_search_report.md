# ScoreExpert DB Search Report

- Status: `pass`
- Run root: `outputs/scoreexpert_db_search_20260618_133627`
- Database entries: 322
- DeepSeek enabled: `True`
- Rounds run: 1
- Stop reason: `max_rounds`
- Stop on target gap: `False`
- Stop on patience: `False`
- Database best: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Best found: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Latency chart: `outputs/scoreexpert_db_search_20260618_133627/latency_trend.png`
- Score chart: `outputs/scoreexpert_db_search_20260618_133627/score_trend.png`
- Replacement chart: `outputs/scoreexpert_db_search_20260618_133627/island_replacement_events.png`
- LLM usage CSV: `outputs/scoreexpert_db_search_20260618_133627/llm_usage_by_round.csv`

## LLM Usage

| Round | Calls | Failures | Input Tokens | Output Tokens | Total Tokens | Elapsed s | Estimated Cost |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 0 | 9316 | 31448 | 40764 | 405.114 | 0.03141222 |
| 1 | 4 | 0 | 29221 | 40990 | 70211 | 520.828 | 0.04837243 |

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
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 14, "score": 1003.2, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "pipeline_efficiency", "program_id": "v0"}, "islands": {"memory_safe": {"best_program_id": "v0", "ranking_quality": 544.5746838122918, "spearman": 0.6044362196691762, "top_k_avg_latency_s": 7.0344755700625, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1048.84, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 137, "score": 1009.92, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "topology_affinity": {"best_program_id": "v1", "ranking_quality": -35.440216822942496, "spearman": 0.03452420588175851, "top_k_avg_latency_s": 9.022521336375, "bad_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 1, "micro_batch_num": 1}, "score_rank": 6, "score": 1000.0, "total_latency_s": 7.537446331, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp1_dp1_tp8_mb1_naive_ar"}], "missed_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 111, "score": 970.0, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag"}]}, "pipeline_efficiency": {"best_program_id": "v0", "ranking_quality": 150.87500963682666, "spearman": 0.19208064274350478, "top_k_avg_latency_s": 5.470187905125, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 32}, "score_rank": 11, "score": 1005.6, "total_latency_s": 9.24216721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb32_rs_ag"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 282, "score": 657.704225, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "balanced_generalist": {"best_program_id": "v0", "ranking_quality": 199.86441802695845, "spearman": 0.36631342874784917, "top_k_avg_latency_s": 28.52092762125, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 64}, "score_rank": 1, "score": 1016.36, "total_latency_s": 16.61496721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 16, "tp": 1, "dp": 2, "micro_batch_num": 64}, "score_rank": 148, "score": 944.397975, "total_latency_s": 2.283072818, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp16_dp2_tp1_mb64_rs_ag"}]}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.10185185185185186, 'avg_recent_program_similarity': 0.24582106557121666}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v0` | 544.574684 | 0.604436 | 7.034476 | 2.330167 |
| `topology_affinity` | `v1` | -35.440217 | 0.034524 | 9.022521 | 2.909849 |
| `pipeline_efficiency` | `v0` | 150.875010 | 0.192081 | 5.470188 | 2.000179 |
| `balanced_generalist` | `v0` | 199.864418 | 0.366313 | 28.520928 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v2`, parents=`v0, v1`
- `topology_affinity`: `pass`, program=`v2`, parents=`v1, v0`
- `pipeline_efficiency`: `pass`, program=`v2`, parents=`v0, v1`
- `balanced_generalist`: `pass`, program=`v2`, parents=`v0, v1`

Experience events:
- `add` `global_experience`: global_experience: PP=1, TP=8, DP=1, MB=2, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- `add` `island_interpretation`: island_interpretation: PP=1, TP=8, DP=4, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
