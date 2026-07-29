# 基于打分策略的部署经验

本文只根据本目录四个当前生效的 `score_strategy` 总结部署经验。候选的仿真时延、慢卡放置效果和最终 Evaluation 排名不反向冒充打分策略的结论。

## 1. 打分策略表达了什么

| 打分岛 | 主要评分项 | 可以直接总结的部署倾向 |
| --- | --- | --- |
| `memory_safe` | `-0.08×micro + 3×TP + 0.5×PP` | 优先增大 TP 以降低参数分片压力；通过增大 DP 或 MBN 降低派生 micro-batch；在其他项相同时轻微偏向更大的 PP。 |
| `topology_affinity` | TP 跨节点 `-1000`、TP 不能整除单节点卡数 `-100`、`+0.2×DP`、流水线气泡惩罚 | TP 通信域应限制在单节点内，并优先选能整除每节点卡数的 TP；拓扑条件相同时轻微偏向更大的 DP，并避免过大的流水线气泡。 |
| `pipeline_efficiency` | `-500×bubble`、派生 micro-batch 小于2时强惩罚、`+0.8×PP + 0.3×TP` | PP 增大时必须同步增大 MBN 压低气泡；派生 micro-batch 应至少为2；满足前两项后才轻微增加 PP/TP。 |
| `balanced_generalist` | `-300×bubble`、空闲卡 `-2/卡`、`-0.04×micro`、`+TP +0.2×DP` | 优先使用更多卡、控制流水线气泡和单次 micro-batch 压力，再在可接受范围内增加 TP/DP。 |

对应源程序：

- [`memory_safe.py`](memory_safe.py)
- [`topology_affinity.py`](topology_affinity.py)
- [`pipeline_efficiency.py`](pipeline_efficiency.py)
- [`balanced_generalist.py`](balanced_generalist.py)

## 2. 可复用部署经验

1. **先满足显存和并行度硬约束，再比较分数。** 打分函数只是候选排序器；`PP×TP×DP`、显存容量和 batch 可整除性仍由搜索空间与 Evaluation 校验。尤其是 `memory_safe` 当前没有读取真实显存估算值，不能仅凭名称判定候选一定不会 OOM。

2. **TP 优先保持在单节点内。** 对每节点8卡的拓扑，优先比较 `TP∈{1,2,4,8}`；避免 `TP>8`，也避免不能整除8的TP值。这条经验直接来自 `topology_affinity` 的两级惩罚。

3. **显存压力高时优先增加 TP，并用 DP 或 MBN 降低派生 micro-batch。** `memory_safe` 对 TP 的奖励最强，同时对 `global_batch_size/(DP×MBN)` 施加惩罚。因此显存导向搜索会偏向较大的 TP，以及能够降低单次 micro-batch 的 DP/MBN 组合。

4. **深流水线必须配高 MBN。** 两个流水线相关打分器都按 `(PP-1)/(MBN+PP-1)` 或近似形式惩罚气泡。增加 PP 之前，应确认 MBN 足以抵消气泡；否则小 PP 更容易得高分。

5. **派生 micro-batch 不应小于2。** `pipeline_efficiency` 对小于1的候选施加极大惩罚，对 `[1,2)` 的候选额外扣300分。高 MBN 不是越大越好，必须同时检查 `global_batch_size/(DP×MBN)`。

6. **尽量使用全部GPU，但不能让满卡奖励掩盖通信成本。** `balanced_generalist` 每空闲一张卡扣2分，因此倾向满卡；但是当前公式没有显式计算真实 TP/DP/PP 通信时延，满卡候选仍必须经过数值仿真。

7. **DP只受到轻微正向奖励，不能据此推出“大DP一定更好”。** 当前打分函数没有把慢卡拖尾和真实 DP 集合通信成本写入公式。DP 增大只能作为候选生成偏好，不能直接升级为部署结论。

## 3. 当前打分策略不能总结的经验

四个函数都没有使用 `profile_cfg`，因此看不到：

- 慢卡 Rank、慢卡数量和速度比例；
- 慢卡位于同节点、同亲和组或跨亲和组；
- 固定 Rank 映射后慢卡落入哪个 TP/DP/PP 通信域；
- 具体网络带宽、拥塞和最终关键路径时延。

同时，四个函数没有读取调度方式和 DP 通信算法，因此不能从这些分数推出 `1F1B` 优于 `GPipe`，也不能推出 `RS+AG` 优于 `AllReduce`。

所以：

- “TP限制在节点内”“深PP配高MBN”“显存压力下增加TP”属于**打分策略经验**；
- “把两张慢卡聚到同一个TP2组”“单慢卡使用PP32”“跨亲和组双慢卡使用PP2/TP8/DP2”属于**仿真或Evaluation经验**，不是当前分数直接推出的结论；
- S0–S13虽然慢卡分布不同，但在这四个打分函数中得到的结构分数相同。场景之间最终策略不同，来自后续 DAG、RuleCheck 和 simulator_v2，而不是评分函数看懂了慢卡分布。

## 4. 使用口径

后续报告中的部署经验按以下顺序组织：

1. 先写打分策略支持的通用部署规则；
2. 再写该规则在当前候选上的具体体现；
3. 用 RuleCheck、显存检查和 simulator_v2 验证候选是否可部署；
4. 慢卡位置、Rank重排、调度方式和通信算法只写成仿真证据，不归因给当前打分函数；
5. 未经过真实训练 P50/P99、吞吐和稳定性 Evaluation 的结论保持 `KEEP_FOR_VALIDATION`。

本目录当前程序的分数与负时延 Spearman 相关性分别约为：`memory_safe=0.604`、`balanced_generalist=0.366`、`pipeline_efficiency=0.192`、`topology_affinity=0.114`。因此它们适合产生有方向差异的候选，不足以单独替代最终性能评估。
