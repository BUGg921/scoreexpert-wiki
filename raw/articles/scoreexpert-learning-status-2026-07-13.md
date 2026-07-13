---
source_url:
source_path: /Users/cookie/Documents/clc/DAG_build/scoreexpert_kb/data/learning_status.md
ingested: 2026-07-13
sha256: 249bdba0703609e74e1fbebd8db7fe4cf4a7062cf118799f8ec073208252975d
original_sha256: a1c1042104003c5a59f8f79c8505c8627aa44cfcb5d5d1ac167b87a3e204dff2
---

# 原始来源：ScoreExpert 学习状态

> 这是从 `/Users/cookie/Documents/clc/DAG_build/scoreexpert_kb/data/learning_status.md` 于 2026-07-13 导入的不可变快照。原文件 SHA-256：`a1c1042104003c5a59f8f79c8505c8627aa44cfcb5d5d1ac167b87a3e204dff2`。

````markdown
# ScoreExpert 经验学习状态

> 此文件由 `scripts/generate_learning_report.py` 生成。猜测保存在 `hypotheses.json`，不会直接写入正式经验。

## 状态概览

- 假设：5（unverified=5）
- 仿真：11（ready=11）

## 假设

### `hyp_four_slow_rank_mapping_symmetry`：四慢卡物理对称只有在逻辑rank mapping对称时才能降低replica skew

- 状态：`unverified`
- 可证伪声明：固定PP=1/TP=8/DP=4、物理慢卡位置和其他输入时，在speed_ratio=0.5与0.25下，对称rank mapping的dp_replica_skew_pct都应至少比不对称mapping低10%；否则该假设被挑战。
- 结果：支持 0 / 反驳 0 / 不确定 0
- 成立后动作：生成add提案：四慢卡部署经验必须把逻辑rank mapping对称作为必要条件，并要求观测DP replica skew。
- 仿真：
  - `sim_four_slow_rank_mapping_ratio050`：`ready` / outcome=`-` / 隔离物理慢卡数量不变，只验证逻辑rank mapping是否降低replica skew。
  - `sim_four_slow_rank_mapping_ratio025`：`ready` / outcome=`-` / 验证慢卡更慢时，对称rank mapping的收益是否扩大。

### `hyp_four_slow_symmetric_strategy_balance`：四节点各一张慢卡时对称均衡策略优于高DP和深PP

- 状态：`unverified`
- 可证伪声明：固定四张慢卡每节点一张、对称rank mapping和其余输入时，在speed_ratio=0.5与0.25两个场景中，基线候选latency都应至少比高DP和深PP候选低3%；否则该假设被挑战或需要按速度倍率拆分。
- 结果：支持 0 / 反驳 0 / 不确定 0
- 成立后动作：生成add提案：新增四慢卡对称分布经验，以TP=8/DP=4为第一Evaluation候选，并写明速度倍率与rank mapping边界。
- 仿真：
  - `sim_four_slow_symmetric_strategy_ratio050`：`ready` / outcome=`-` / 验证半速四慢卡对称分布下，均衡策略是否比高DP和深PP更稳。
  - `sim_four_slow_symmetric_strategy_ratio025`：`ready` / outcome=`-` / 验证极慢四卡时均衡策略是否仍成立，或出现隔离/闲卡翻转。

### `hyp_high_dp_score_false_positive`：高DP候选因未建模replica skew和跨亲和组同步而被score高估

- 状态：`unverified`
- 可证伪声明：固定两张半速慢卡和global batch后，在正常与降速跨亲和组网络中，基线候选都应比DP=32候选至少快3%，且网络更慢时差距扩大。
- 结果：支持 0 / 反驳 0 / 不确定 0
- 成立后动作：生成refine提案：给高DP经验增加dp_replica_skew和跨亲和组all-reduce硬边界，并把DP=32标为score风险候选。
- 仿真：
  - `sim_high_dp_cross_affinity_normal_network`：`ready` / outcome=`-` / 判断DP=32的高score是否能经受真实同步成本。
  - `sim_high_dp_cross_affinity_slow_network`：`ready` / outcome=`-` / 验证跨亲和组网络变慢时高DP候选的劣势是否扩大。

### `hyp_single_slow_ratio_switch_boundary`：单慢卡速度倍率决定同构策略与隔离策略的翻转边界

- 状态：`unverified`
- 可证伪声明：固定拓扑、慢卡位置、模型和候选后，speed_ratio=0.8时基线候选应更快；speed_ratio=0.5和0.25时隔离候选应至少快3%。若不出现这种方向变化，该假设被挑战。
- 结果：支持 0 / 反驳 0 / 不确定 0
- 成立后动作：生成refine提案：把两条现有经验改写为按slow_gpus.speed_ratio分段的条件规则，并记录实测翻转区间。
- 仿真：
  - `sim_single_slow_ratio_050`：`ready` / outcome=`-` / 复验当前半速慢卡种子经验是否有真实Evaluation支撑。
  - `sim_single_slow_ratio_080`：`ready` / outcome=`-` / 验证轻微慢卡是否不足以抵消深PP隔离成本。
  - `sim_single_slow_ratio_025`：`ready` / outcome=`-` / 验证极慢单卡下隔离收益是否继续增强。

### `hyp_two_slow_topology_symmetry`：两张慢卡的拓扑对称性决定优先均衡还是优先隔离

- 状态：`unverified`
- 可证伪声明：固定慢卡数量、速度、模型和网络带宽后，跨亲和组对称放置时基线候选应至少快3%；同亲和组集中放置时隔离候选应至少快3%。若两个场景赢家不随对称性改变，该假设被挑战。
- 结果：支持 0 / 反驳 0 / 不确定 0
- 成立后动作：生成add或merge提案：新增两慢卡条件经验，以拓扑对称性和rank mapping作为部署分支，而不是只按慢卡数量选策略。
- 仿真：
  - `sim_two_slow_cross_affinity_symmetric`：`ready` / outcome=`-` / 验证对称分散异构是否使均衡策略优于深PP隔离。
  - `sim_two_slow_same_affinity_asymmetric`：`ready` / outcome=`-` / 验证慢卡集中造成的拓扑不对称是否提高局部隔离收益。

## 状态迁移规则

```text
无结果 -> unverified
1 个支持 -> partially_supported
至少 2 个独立支持且无反驳 -> supported
1 个反驳 -> challenged
至少 2 个反驳且无支持 -> refuted
同时存在支持和反驳 -> mixed，并拆分适用边界
只有小于最小效应阈值的结果 -> inconclusive
```

`supported` 只允许生成正式经验更新提案，仍然不能自动合并 `experiences.json`。
````
