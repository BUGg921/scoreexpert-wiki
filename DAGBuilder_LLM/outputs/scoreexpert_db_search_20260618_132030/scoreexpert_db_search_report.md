# ScoreExpert DB Search Report

- Status: `pass`
- Run root: `outputs/scoreexpert_db_search_20260618_132030`
- Database entries: 322
- DeepSeek enabled: `True`
- Rounds run: 1
- Stop reason: `max_rounds`
- Stop on target gap: `False`
- Stop on patience: `False`
- Database best: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Best found: {'strategy': {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}, 'total_latency_s': 2.000179116, 'pp_strategy': '1f1b', 'dp_strategy': 'reduce_scatter_allgather_after_backward'}
- Latency chart: `outputs/scoreexpert_db_search_20260618_132030/latency_trend.png`
- Score chart: `outputs/scoreexpert_db_search_20260618_132030/score_trend.png`
- Replacement chart: `outputs/scoreexpert_db_search_20260618_132030/island_replacement_events.png`
- LLM usage CSV: `outputs/scoreexpert_db_search_20260618_132030/llm_usage_by_round.csv`

## LLM Usage

| Round | Calls | Failures | Input Tokens | Output Tokens | Total Tokens | Elapsed s | Estimated Cost |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 4 | 0 | 0 | 0 | 0.000 | 0.00000000 |
| 1 | 4 | 4 | 0 | 0 | 0 | 0.000 | 0.00000000 |

## Second Seed Initialization

- `memory_safe`: `fail`, program=``, reason=`<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1028)>`
- `topology_affinity`: `fail`, program=``, reason=`<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1028)>`
- `pipeline_efficiency`: `fail`, program=``, reason=`<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1028)>`
- `balanced_generalist`: `fail`, program=``, reason=`<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1028)>`

## Rounds

### Round 1

- Strategy: `all_database_strategies`
- Evaluation status: `pass`
- Latency: `2.000179116`
- Evaluation feedback summary: `{"mode": "full_database_ranking", "database_size": 322, "top_k": 16, "best_candidate_found_by_scoring": {"strategy": {"pp": 1, "tp": 8, "dp": 4, "micro_batch_num": 1}, "score_rank": 14, "score": 1003.2, "total_latency_s": 2.000179116, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp4_tp8_mb1_rs_ag", "island": "pipeline_efficiency", "program_id": "v0"}, "islands": {"memory_safe": {"best_program_id": "v0", "ranking_quality": 544.5746838122918, "spearman": 0.6044362196691762, "top_k_avg_latency_s": 7.0344755700625, "bad_cases": [{"strategy": {"pp": 2, "tp": 16, "dp": 1, "micro_batch_num": 64}, "score_rank": 1, "score": 1048.84, "total_latency_s": 9.381758378, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp2_dp1_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 137, "score": 1009.92, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "topology_affinity": {"best_program_id": "v0", "ranking_quality": -1080.5616127094795, "spearman": 0.11423894871267805, "top_k_avg_latency_s": 234.0877415036875, "bad_cases": [{"strategy": {"pp": 1, "tp": 1, "dp": 32, "micro_batch_num": 1}, "score_rank": 1, "score": 1006.4, "total_latency_s": 193.238499198, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp32_tp1_mb1_rs_ag"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 152, "score": 999.30625, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "pipeline_efficiency": {"best_program_id": "v0", "ranking_quality": 150.87500963682666, "spearman": 0.19208064274350478, "top_k_avg_latency_s": 5.470187905125, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 32}, "score_rank": 11, "score": 1005.6, "total_latency_s": 9.24216721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb32_rs_ag"}], "missed_cases": [{"strategy": {"pp": 8, "tp": 2, "dp": 2, "micro_batch_num": 64}, "score_rank": 282, "score": 657.704225, "total_latency_s": 2.198843034, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp8_dp2_tp2_mb64_rs_ag"}]}, "balanced_generalist": {"best_program_id": "v0", "ranking_quality": 199.86441802695845, "spearman": 0.36631342874784917, "top_k_avg_latency_s": 28.52092762125, "bad_cases": [{"strategy": {"pp": 1, "tp": 16, "dp": 2, "micro_batch_num": 64}, "score_rank": 1, "score": 1016.36, "total_latency_s": 16.61496721, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp1_dp2_tp16_mb64_rs_ag"}], "missed_cases": [{"strategy": {"pp": 16, "tp": 1, "dp": 2, "micro_batch_num": 64}, "score_rank": 148, "score": 944.397975, "total_latency_s": 2.283072818, "pp_strategy": "1f1b", "dp_strategy": "reduce_scatter_allgather_after_backward", "dag_id": "1f1b_pp16_dp2_tp1_mb64_rs_ag"}]}}}`
- Diversity: `{'avg_top_strategy_overlap': 0.08333333333333333, 'avg_recent_program_similarity': 0.35121285049655393}`
- Adjustment: `{'type': 'none', 'reason': 'full database ranking feedback'}`
- Next strategy: `all_database_strategies`

| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |
|---|---|---:|---:|---:|---:|
| `memory_safe` | `v0` | 544.574684 | 0.604436 | 7.034476 | 2.330167 |
| `topology_affinity` | `v0` | -1080.561613 | 0.114239 | 234.087742 | 2.524591 |
| `pipeline_efficiency` | `v0` | 150.875010 | 0.192081 | 5.470188 | 2.000179 |
| `balanced_generalist` | `v0` | 199.864418 | 0.366313 | 28.520928 | 2.000179 |

Evolution:
- `memory_safe`: `fail`, program=``, parents=`v0`
- `topology_affinity`: `fail`, program=``, parents=`v0`
- `pipeline_efficiency`: `fail`, program=``, parents=`v0`
- `balanced_generalist`: `fail`, program=``, parents=`v0`

Adaptive context:
- `memory_safe` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `topology_affinity` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `pipeline_efficiency` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
- `balanced_generalist` guidance: ['Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.', 'Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.']
