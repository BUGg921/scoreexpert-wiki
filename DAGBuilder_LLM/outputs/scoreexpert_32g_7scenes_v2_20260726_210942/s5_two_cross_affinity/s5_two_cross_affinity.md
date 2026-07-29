# s5_two_cross_affinity：两张慢卡跨亲和组

- 经验候选判定：`KEEP_FOR_VALIDATION`
- 优化目标：`latency-first`
- 场景分类：`distributed-heterogeneity`
- 仿真链：`ScoreExpert 全空间枚举/打分 → DagGenerator → RuleCheck → ValueSim simulator_v2 → Evaluation 最长路径`
- OverlapOPT：禁用；按未重叠的 baseline latency 排名
- EP：禁用
- 完整候选产物保留：Top 10；其余 46 个候选仅保留 evaluation cache，可按相同配置重跑恢复

## 场景设置

- 资源：32 卡，4 个服务器 × 8 卡；2 个亲和组，每组 2 个服务器
- 慢卡 Rank：`7, 23`
- 正常/慢卡算力：`312.000` / `156.000` TFLOPS，固定倍率 `0.5×`
- 模型：32 层，hidden=4096，FFN=11008，seq=2048，global batch=128.0
- 搜索约束：`PP×TP×DP=32`，`TP∈{1,2,4,8}`，不允许 idle GPU，`MBN∈{1,2,4,8,16,32,64}`
- Rank mapping：`pp_major_huawei`；PP stage 均匀分层

## 搜索与评估结果

- 枚举策略：106
- ScoreExpert 四岛均可评分：106
- Score 硬约束通过并进入完整 DAG 评估：56
- 完整链通过：56
- 失败/跳过：50

## 当前最优候选

- `PP=2, TP=8, DP=2, MBN=4`
- Evaluation 最长路径 latency：`3.960645539 s`
- DAG：534 个节点，1301 条边
- 完整候选目录：`/Users/cookie/Documents/wiki/DAGBuilder_LLM/outputs/scoreexpert_32g_7scenes_v2_20260726_210942/s5_two_cross_affinity/evaluations/eval_pp2_mbn4_tp8_dp2`
- 受慢卡影响的 TP group：2 个

## Top 10

| 排名 | PP | TP | DP | MBN | latency (s) | RuleCheck | simulator_v2 |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 2 | 8 | 2 | 4 | 3.960645539 | `pass` | `pass` |
| 2 | 16 | 2 | 1 | 64 | 3.995510901 | `pass` | `pass` |
| 3 | 8 | 4 | 1 | 32 | 4.165316202 | `pass` | `pass` |
| 4 | 4 | 4 | 2 | 16 | 4.169451831 | `pass` | `pass` |
| 5 | 2 | 8 | 2 | 8 | 4.175685539 | `pass` | `pass` |
| 6 | 8 | 4 | 1 | 64 | 4.176787690 | `pass` | `pass` |
| 7 | 4 | 4 | 2 | 8 | 4.192746245 | `pass` | `pass` |
| 8 | 32 | 1 | 1 | 64 | 4.200330900 | `pass` | `pass` |
| 9 | 1 | 8 | 4 | 4 | 4.238720099 | `pass` | `pass` |
| 10 | 4 | 4 | 2 | 32 | 4.296044624 | `pass` | `pass` |

## 硬约束外反事实

下列策略可以完成 DAG 数值仿真，但被 ScoreExpert 硬约束排除，不参与最优排名。

| 策略 | simulator_v2 + Evaluation | latency (s) | 排除原因 |
|---|---|---:|---|
| `PP=1, TP=8, DP=4, MBN=1` | `pass` | 3.916160099 | `memory_hard_overflow` |

## 证据边界

- 本结果是完整软件仿真链产生的候选，不是真实 32 卡集群 Evaluation；因此暂不写入正式 active 经验。
- ScoreExpert 分数只用于保留打分证据；本次对所有 Score 硬约束通过的策略都运行完整 DAG 评估，最终按 Evaluation latency 排名。
- 当前搜索只支持均匀 PP 分层和固定 rank-major 映射，尚不能针对慢卡自动减层或交换 rank；这会限制单慢卡深 PP 策略的可发现范围。
- 慢卡仅改变计算吞吐，未模拟慢卡通信链路、抖动、故障、显存差异或不同慢速倍率。
- `MBN=64` 若成为最优，只能解释为当前搜索上界候选，不能解释为物理必然最优。
