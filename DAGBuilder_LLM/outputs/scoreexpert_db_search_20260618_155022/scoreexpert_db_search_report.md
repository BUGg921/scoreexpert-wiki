# ScoreExpert DB Search Report

- Status: `pass`
- Run root: `outputs/scoreexpert_db_search_20260618_155022`
- Database entries: 322
- DeepSeek enabled: `True`
- Rounds run: 1
- Stop reason: `max_rounds`
- Stop on target gap: `False`
- Stop on patience: `False`
- Database best: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Best found: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Latency chart: `outputs/scoreexpert_db_search_20260618_155022/latency_trend.png`
- Score chart: `outputs/scoreexpert_db_search_20260618_155022/score_trend.png`
- Replacement chart: `outputs/scoreexpert_db_search_20260618_155022/island_replacement_events.png`
- LLM usage CSV: `outputs/scoreexpert_db_search_20260618_155022/llm_usage_by_round.csv`
- Island API timing CSV: `outputs/scoreexpert_db_search_20260618_155022/island_api_timing.csv`

## LLM Usage

| Round | Calls | Failures | Input Tokens | Output Tokens | Total Tokens | Elapsed s | Estimated Cost |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 0 | 9316 | 45677 | 54993 | 822.344 | 0.04379146 |
| 1 | 4 | 0 | 29383 | 45964 | 75347 | 899.591 | 0.05277027 |

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
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 14, "score": 1007.52, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "balanced_generalist", "program_id": "v0"}, "islands": {"memory_safe": {"best_program_id": "v0", "ranking_quality": 544.5746838122918, "spearman": 0.6044362196691762, "top_k_avg_latency_s": 7.0344755700625, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1048.84, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 137, "score": 1009.92, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "topology_affinity": {"best_program_id": "v1", "ranking_quality": 323.3729387745967, "spearman": 0.3902483916063206, "top_k_avg_latency_s": 8.4215590025, "bad_cases": [{"strategy": {"pp": 1, "tp": 8, "dp": 1, "micro_batch_num": 1}, "score_rank": 2, "score": 1000.0, "total_latency_s": 7.537446331, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp1_dp1_tp8_mb1_naive_ar"}], "missed_cases": [{"strategy": {"pp": 4, "tp": 2, "dp": 4, "micro_batch_num": 32}, "score_rank": 114, "score": 975.037143, "total_latency_s": 2.264867954, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp4_dp4_tp2_mb32_rs_ag"}]}, "pipeline_efficiency": {"best_program_id": "v1", "ranking_quality": 201.71651419124248, "spearman": 0.2591749387350947, "top_k_avg_latency_s": 6.5811631406875, "bad_cases": [{"strategy": {"pp": 8, "tp": 1, "dp": 1, "micro_batch_num": 64}, "score_rank": 6, "score": 1031.004225, "total_latency_s": 7.843371128, "pp_strategy": "gpipe", "dp_strategy": "naive_allreduce_after_backward", "dag_id": "gpipe_pp8_dp1_tp1_mb64_naive_ar"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 236, "score": 731.304225, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "balanced_generalist": {"best_program_id": "v0", "ranking_quality": 199.86441802695845, "spearman": 0.36631342874784917, "top_k_avg_latency_s": 28.52092762125, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 64}, "score_rank": 1, "score": 1016.36, "total_latency_s": 16.61496721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 16, "tp": 1, "dp": 2, "micro_batch_num": 64}, "score_rank": 148, "score": 944.397975, "total_latency_s": 2.283072818, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp16_dp2_tp1_mb64_rs_ag"}]}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.041666666666666664, 'avg_recent_program_similarity': 0.26421347812316737}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v0` | 544.574684 | 0.604436 | 7.034476 | 2.330167 |
| `topology_affinity` | `v1` | 323.372939 | 0.390248 | 8.421559 | 2.099767 |
| `pipeline_efficiency` | `v1` | 201.716514 | 0.259175 | 6.581163 | 2.345143 |
| `balanced_generalist` | `v0` | 199.864418 | 0.366313 | 28.520928 | 2.000179 |

Evolution:
- `memory_safe`: `pass`, program=`v2`, parents=`v1, v0`
- `topology_affinity`: `pass`, program=`v2`, parents=`v1, v0`
- `pipeline_efficiency`: `pass`, program=`v2`, parents=`v0, v1`
- `balanced_generalist`: `pass`, program=`v2`, parents=`v0, v1`

Experience events:
- `add` `global_experience`: global_experience: PP=8, TP=1, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- `add` `global_experience`: global_experience: PP=4, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
