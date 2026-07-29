# 32卡固定半速慢卡七场景完整仿真

- 运行目录：`/Users/cookie/Documents/wiki/DAGBuilder_LLM/outputs/scoreexpert_32g_7scenes_v2_20260726_210942`
- 结果身份：`KEEP_FOR_VALIDATION`，未写入正式经验库
- 每个场景均使用完整链：ScoreExpert → DagGenerator → RuleCheck → simulator_v2 → Evaluation
- 拓扑：4 个 8 卡服务器，2 个亲和组，每组 2 个服务器
- EP：禁用
- 产物策略：每场景保留 Top 10 完整 DAG 目录及旧经验反事实；其余候选保留 evaluation cache，可按同一脚本恢复

| 场景 | 慢卡 Rank | PP | TP | DP | MBN | latency (s) | 场景文件 |
|---|---|---:|---:|---:|---:|---:|---|
| `s0_homogeneous` | `无` | 16 | 2 | 1 | 64 | 2.324650160 | [报告](s0_homogeneous/s0_homogeneous.md) |
| `s1_single_slow` | `7` | 32 | 1 | 1 | 64 | 3.720621768 | [报告](s1_single_slow/s1_single_slow.md) |
| `s3_two_same_node` | `6,7` | 16 | 2 | 1 | 64 | 3.729096448 | [报告](s3_two_same_node/s3_two_same_node.md) |
| `s4_two_same_affinity` | `7,15` | 16 | 2 | 1 | 64 | 3.875337256 | [报告](s4_two_same_affinity/s4_two_same_affinity.md) |
| `s5_two_cross_affinity` | `7,23` | 2 | 8 | 2 | 4 | 3.960645539 | [报告](s5_two_cross_affinity/s5_two_cross_affinity.md) |
| `s6_four_symmetric` | `7,15,23,31` | 16 | 2 | 1 | 64 | 4.169283550 | [报告](s6_four_symmetric/s6_four_symmetric.md) |
| `s7_five_2111` | `6,7,15,23,31` | 16 | 2 | 1 | 64 | 4.169283550 | [报告](s7_five_2111/s7_five_2111.md) |

旧经验元组 `PP1/TP8/DP4/MBN1` 另做硬约束外反事实仿真；若 ScoreExpert 判定 `memory_hard_overflow`，其 latency 仅用于分析，不参与最优排名。

旧的 `simulator_v2/experiments/run_32g_scenarios.py` 简化结果不参与本次排名；本目录结果应作为新的仿真候选来源。
