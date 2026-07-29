# ScoreExpert Experience Bank

This file stores reusable scoring-search experience for ScoreExpert only.

> 当前四个打分程序能够直接支持的部署经验，统一整理在
> [基于打分策略的部署经验](islands/programs/deployment_experience.md)。
> 下方条目是搜索轮次产生的候选观察，其中的低时延或高时延结论属于
> Evaluation 反馈，不等同于打分公式本身能够直接推出的经验。

## Global Experience

## Island Interpretations


### Global Experience: global_experience: PP=2, TP=16, DP=1, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=2, TP=16, DP=1, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=memory_safe, latency=9.381758378, score_rank=1, score=1048.84
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 2, 'tp': 16, 'dp': 1, 'micro_batch_num': 64}
- source_islands: ['memory_safe']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=1, TP=16, DP=2, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=1, TP=16, DP=2, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=memory_safe, latency=16.61496721, score_rank=3, score=1048.42
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 16, 'dp': 2, 'micro_batch_num': 64}
- source_islands: ['memory_safe']
- confidence: 0.6
- last_seen_round: 1


### Island Interpretations: island_interpretation: PP=8, TP=2, DP=2, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: island_interpretation: PP=8, TP=2, DP=2, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=memory_safe, latency=2.198843034, score_rank=137, score=1009.92
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 8, 'tp': 2, 'dp': 2, 'micro_batch_num': 64}
- source_islands: ['memory_safe']
- confidence: 0.6
- last_seen_round: 1


### Island Interpretations: island_interpretation: PP=4, TP=2, DP=4, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: island_interpretation: PP=4, TP=2, DP=4, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=memory_safe, latency=2.264867954, score_rank=154, score=1007.92
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 4, 'tp': 2, 'dp': 4, 'micro_batch_num': 32}
- source_islands: ['memory_safe']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=1, TP=1, DP=32, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=1, TP=1, DP=32, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=topology_affinity, latency=193.238499198, score_rank=1, score=1006.4
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 1, 'dp': 32, 'micro_batch_num': 1}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=1, TP=1, DP=32, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=1, TP=1, DP=32, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=topology_affinity, latency=193.238499198, score_rank=2, score=1006.4
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 1, 'dp': 32, 'micro_batch_num': 2}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=1, TP=16, DP=2, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=1, TP=16, DP=2, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=pipeline_efficiency, latency=9.24216721, score_rank=11, score=1005.6
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 16, 'dp': 2, 'micro_batch_num': 32}
- source_islands: ['pipeline_efficiency']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=1, TP=16, DP=1, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=1, TP=16, DP=1, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=pipeline_efficiency, latency=11.101397982, score_rank=12, score=1005.6
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 16, 'dp': 1, 'micro_batch_num': 32}
- source_islands: ['pipeline_efficiency']
- confidence: 0.6
- last_seen_round: 1


### Island Interpretations: island_interpretation: PP=16, TP=1, DP=2, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: island_interpretation: PP=16, TP=1, DP=2, MB=64, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=balanced_generalist, latency=2.283072818, score_rank=148, score=944.397975
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 16, 'tp': 1, 'dp': 2, 'micro_batch_num': 64}
- source_islands: ['balanced_generalist']
- confidence: 0.6
- last_seen_round: 1


### Island Interpretations: island_interpretation: PP=8, TP=2, DP=2, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: island_interpretation: PP=8, TP=2, DP=2, MB=32, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=balanced_generalist, latency=2.341963184, score_rank=120, score=948.473846
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 8, 'tp': 2, 'dp': 2, 'micro_batch_num': 32}
- source_islands: ['balanced_generalist']
- confidence: 0.6
- last_seen_round: 1

### Island Interpretations: island_interpretation: PP=1, TP=8, DP=4, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: island_interpretation: PP=1, TP=8, DP=4, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=memory_safe, latency=2.000179116, score_rank=121, score=1040.3125
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 1}
- source_islands: ['memory_safe']
- confidence: 0.6
- last_seen_round: 1


### Island Interpretations: island_interpretation: PP=1, TP=16, DP=2, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: island_interpretation: PP=1, TP=16, DP=2, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=memory_safe, latency=2.09976721, score_rank=159, score=1037.65625
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 1, 'tp': 16, 'dp': 2, 'micro_batch_num': 1}
- source_islands: ['memory_safe']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=2, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=2, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=1, island=topology_affinity, latency=15.260686921, score_rank=1, score=999.34375
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 2, 'tp': 2, 'dp': 1, 'micro_batch_num': 64}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=1, TP=4, DP=1, MB=1, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=1, TP=4, DP=1, MB=1, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=1, island=topology_affinity, latency=14.796854127, score_rank=2, score=999.28
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 4, 'dp': 1, 'micro_batch_num': 1}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 1

### Global Experience: global_experience: PP=1, TP=4, DP=1, MB=2, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=1, TP=4, DP=1, MB=2, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=2, island=topology_affinity, latency=14.842934127, score_rank=2, score=999.3
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 4, 'dp': 1, 'micro_batch_num': 2}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 2


### Global Experience: global_experience: PP=1, TP=8, DP=1, MB=1, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=1, TP=8, DP=1, MB=1, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=2, island=pipeline_efficiency, latency=7.537446331, score_rank=3, score=1012.9
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 8, 'dp': 1, 'micro_batch_num': 1}
- source_islands: ['pipeline_efficiency']
- confidence: 0.6
- last_seen_round: 2

### Global Experience: global_experience: PP=1, TP=2, DP=2, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=1, TP=2, DP=2, MB=1, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=3, island=topology_affinity, latency=14.587997811, score_rank=1, score=999.2
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 2, 'dp': 2, 'micro_batch_num': 1}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 3


### Global Experience: global_experience: PP=1, TP=2, DP=2, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: global_experience: PP=1, TP=2, DP=2, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=3, island=topology_affinity, latency=14.603357811, score_rank=2, score=999.2
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 2, 'dp': 2, 'micro_batch_num': 2}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 3


### Island Interpretations: island_interpretation: PP=16, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: island_interpretation: PP=16, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=3, island=topology_affinity, latency=2.345143222, score_rank=167, score=992.65625
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 16, 'tp': 2, 'dp': 1, 'micro_batch_num': 64}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 3

### Global Experience: global_experience: PP=2, TP=4, DP=1, MB=16, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=2, TP=4, DP=1, MB=16, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=4, island=topology_affinity, latency=8.231504198, score_rank=2, score=1003.675
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 2, 'tp': 4, 'dp': 1, 'micro_batch_num': 16}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 4


### Global Experience: global_experience: PP=2, TP=4, DP=1, MB=8, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=2, TP=4, DP=1, MB=8, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=4, island=topology_affinity, latency=8.511501333, score_rank=16, score=1003.05
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 2, 'tp': 4, 'dp': 1, 'micro_batch_num': 8}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 4

### Global Experience: global_experience: PP=1, TP=8, DP=1, MB=2, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=1, TP=8, DP=1, MB=2, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=1, island=topology_affinity, latency=7.644966331, score_rank=7, score=1000.0
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 1, 'tp': 8, 'dp': 1, 'micro_batch_num': 2}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 1


### Island Interpretations: island_interpretation: PP=1, TP=8, DP=4, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- description: island_interpretation: PP=1, TP=8, DP=4, MB=2, pp_strategy=1f1b, dp_strategy=reduce_scatter_allgather_after_backward
- evidence: round=1, island=topology_affinity, latency=2.107699116, score_rank=112, score=970.0
- recommendation: Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.
- applies_to: {'pp': 1, 'tp': 8, 'dp': 4, 'micro_batch_num': 2}
- source_islands: ['topology_affinity']
- confidence: 0.6
- last_seen_round: 1

### Global Experience: global_experience: PP=8, TP=1, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=8, TP=1, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=1, island=pipeline_efficiency, latency=7.843371128, score_rank=6, score=1031.004225
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 8, 'tp': 1, 'dp': 1, 'micro_batch_num': 64}
- source_islands: ['pipeline_efficiency']
- confidence: 0.6
- last_seen_round: 1


### Global Experience: global_experience: PP=4, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- description: global_experience: PP=4, TP=2, DP=1, MB=64, pp_strategy=gpipe, dp_strategy=naive_allreduce_after_backward
- evidence: round=1, island=pipeline_efficiency, latency=7.869589906, score_rank=9, score=1018.21194
- recommendation: High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.
- applies_to: {'pp': 4, 'tp': 2, 'dp': 1, 'micro_batch_num': 64}
- source_islands: ['pipeline_efficiency']
- confidence: 0.6
- last_seen_round: 1
