---
source_url:
source_path: /Users/cookie/Documents/wiki/DAGBuilder_Evolve/outputs/s4-two-same-affinity-review_20260730_180425_scenario_analysis.md
ingested: 2026-07-30
sha256: 3855dc4ae0121b2c8b8fd920195b6ae554871960cc9b97b5b17de80de91fee96
original_sha256: 6c51c78dca3adb1f55e022aa15d60120ca977eebd502db9c4f1dfe649590aa65
---

# s4_two_same_affinity_32g仿真与部署策略分析

## 实验场景

共 32 张 GPU：4个节点，每节点8卡，每两个节点组成一个16卡亲和组。
共有2张慢卡，具体为Rank 7=156 TFLOPS（0.50×）、Rank 15=156 TFLOPS（0.50×）。

### 模型配置与复算条件

```text
model = LLaMA-7B
num_layers = 32
global_batch_size = 128
sequence_length = 2048
device_memory = 16.0 GB
total_devices = 32
PP × TP × DP ≤ total_devices
search_coverage = 75/873 (8.59%)
```

## 最优解

```text
PP = 16
TP = 1
DP = 2
micro-batch number = 64
schedule = 1f1b
DP communication = allreduce
active GPUs = 32
simulated critical-path latency = 3.867548 s
formula candidate score = 955.618847
formula candidate rank = 3
```

这里的“最优”仅指已实际仿真的候选中最长路径最低，不代表873个结构候选已经穷举。

| 排名 | 已仿真策略 | 时延 (s) | 显存估算 (GB/卡) |
| ---: | --- | ---: | ---: |
| 1 | `PP16/TP1/DP2/MBN64/1F1B/AllReduce` | 3.867548 | 5.570 |
| 2 | `PP16/TP1/DP2/MBN64/1F1B/RS+AG` | 3.867548 | 5.570 |
| 3 | `PP8/TP1/DP4/MBN32/1F1B/RS+AG` | 3.926769 | 11.140 |
| 4 | `PP8/TP1/DP4/MBN32/1F1B/AllReduce` | 3.926769 | 11.140 |
| 5 | `PP8/TP2/DP2/MBN64/1F1B/RS+AG` | 3.936714 | 5.570 |

## 打分策略代码

该代码来自`pipeline_efficiency`岛第5代程序`3857cae3bd6a083f`，归因方式为`direct_evaluation_nomination`。

```python
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    pp = int(strategy['pp'])
    tp = int(strategy['tp'])
    dp = int(strategy['dp'])
    mb = int(strategy['micro_batch_num'])
    schedule = strategy['schedule']
    active_gpus = int(strategy['active_gpus'])
    cards_per_server = int(topology_cfg['cards_per_server'])
    compute_eff = float(workload_cfg['compute_efficiency'])

    # 气泡比例
    bubble_ratio = float(pp - 1) / float(mb + pp - 1) if (mb + pp - 1) > 0 else 0.0

    # 计算时间近似：每层计算量与算力，但这里用 active_gpus 和 compute_eff 粗略估计
    # 假设单 GPU 计算时间与模型大小成正比，与 active_gpus 和 compute_eff 成反比
    # 但为了简化，用 active_gpus 作为分母
    compute_time_approx = 1000.0 / (active_gpus * compute_eff)  # 基础计算时间

    # 气泡时间 = 气泡比例 * (计算时间 + 通信时间)，但通信时间难估，主要考虑气泡
    # 气泡惩罚
    bubble_penalty = 500.0 * bubble_ratio

    # 微批数量：微批越多，气泡越小，但每个微批计算时间变短，通信次数增加。
    # 这里用 mb 的平方根来奖励，边际递减
    mb_bonus = 20.0 * (mb ** 0.5)

    # 调度方式：1f1b 减少内存，可能减少气泡，加分
    schedule_bonus = 50.0 if schedule == '1f1b' else 0.0

    # TP 通信开销：TP 越大，allreduce 通信量越大，且跨机更严重
    # 用 active_gpus 和 cards_per_server 判断是否跨机
    cross_node = 1.0 if active_gpus > cards_per_server else 0.0
    # TP 通信量大致与 tp 成正比，跨机时延迟更高
    tp_penalty = -30.0 * tp * (1.0 + 2.0 * cross_node)

    # DP 通信：如果使用 rs_ag 比 allreduce 更优，加分
    dp_comm = strategy.get('dp_communication', '')
    dp_bonus = 25.0 if dp_comm == 'rs_ag' else 0.0

    # 综合得分：基础分 1000，减去气泡惩罚，加上微批奖励和调度奖励，考虑 TP 和 DP 影响
    # 并考虑计算时间影响（计算时间短更好）
    score = 1000.0 - bubble_penalty + mb_bonus + schedule_bonus + tp_penalty + dp_bonus - compute_time_approx

    return score
```

## 经验总结

### <span style="color:blue;">(1) 并行策略</span>

1. 当异常设备跨多个节点或亲和组、无法通过一个局部执行单元完成隔离，且`保留满卡与数据并行的收益 > replica等待和DP通信成本`时，优先采用满卡方案。参数按以下规则求解：先取能够限制异常同步扩散的最小已验证`TP=1`；再保留本轮仿真有收益的`DP=2`；在满卡约束下由`PP=active_gpu/(TP×DP)=32/(1×2)=16`反推PP；最后取显存、气泡和调度边界内已验证的`MBN=64`。

### <span style="color:blue;">(2) 原因</span>

1. **分布式异构参数求解与映射原因**：
   - **TP**：`TP=1`把TP同步范围限制在单卡、消除TP集合通信；慢卡不会通过跨节点TP集合通信进一步放大等待。
   - **DP**：`DP=2`与PP、TP共同使用32/32张卡。当前映射中副本1含2张慢卡；该不对称结构需要以副本关键路径和真实训练尾延迟为护栏，必要时优先重映射慢卡。
   - **PP/MBN**：32层模型可被16个stage整除；当前气泡近似为`18.99%`，派生micro-batch size为`1.000`。`MBN=64`只是在当前显存、气泡和搜索边界内与该PP深度配套的已验证值。
   - **仿真观测**：关键路径中compute=96.8%、dp=3.1%、pp=0.1%；慢卡影响2/32个TP group、2/16个PP stage和1/2个DP replica。
   - **公式与仿真分工**：公式把`PP8/TP1/DP2/MBN64/1F1B/RS+AG`排在第2，高于最终候选的第3；但其仿真时延为`7.610919 s`，比最终候选慢`96.79%`。因此公式负责提名，不能直接替代数值仿真结论。
   - **等价最优**：相对误差`1e-6`内存在2个等价最优：`PP16/TP1/DP2/MBN64/1F1B/AllReduce`、`PP16/TP1/DP2/MBN64/1F1B/RS+AG`。当前数值模型不能据此区分调度和DP通信实现，真实部署需用训练Evaluation选择。

### <span style="color:blue;">(3) 结论边界</span>

该经验仅适用于本报告的32卡拓扑、LLaMA-7B、GBS=128、Seq=2048、16.0GB/卡和当前慢卡Rank/速度。

本轮只实际评估75/873个候选；结论是当前已仿真候选最优。缺少真实训练P50/P99、吞吐、显存峰值和运行方差，因此经验状态保持`KEEP_FOR_VALIDATION`。

相对误差`1e-6`内存在2个等价最优：`PP16/TP1/DP2/MBN64/1F1B/AllReduce`、`PP16/TP1/DP2/MBN64/1F1B/RS+AG`。当前数值模型不能据此区分调度和DP通信实现，真实部署需用训练Evaluation选择。若慢卡Rank、速度、模型、batch、显存、网络或Rank映射变化，应作为新场景重新仿真。

## 未仿真的场景

从经验库目标总览读取的已总结场景为：标准 32 卡同构基线（成熟经验）、单慢卡局部隔离（成熟经验）、两慢卡非对称均衡（成熟经验）、四慢卡对称副本（成熟经验）、五慢卡 2/1/1/1 待验证证据（KEEP_FOR_VALIDATION）。本轮另有待人工审核的2张慢卡，按节点1/1/0/0分布。缺口计算以经验库已总结场景和本轮结果为准，不读取用户口头清单，也不把仅存在的配置文件算作已仿真。

尚未形成完整对照的场景包括：

1. **双慢卡拓扑差集**：经验库当前仍缺少同一节点场景。同一节点还应继续区分同TP group与不同TP group；已由经验库覆盖的分支不重复建议。
2. **慢卡数量差集**：建议补充3、6、7、8张慢卡。其中3张观察奇数慢卡造成的副本不对称，6张观察2/2/1/1过渡分布，7张观察2/2/2/1近对称边界，8张构造每节点2张的高密度对称对照。
3. **同数量不同分布**：对3张及以上慢卡分别比较集中、同亲和组分散、跨亲和组不对称和跨节点近似对称映射，避免把慢卡数量本身误当成部署经验。

## 下一步仿真建议

1. **P0—补齐双慢卡拓扑对照**：优先仿真同一节点；保持慢卡数量不变，可以直接识别节点边界、亲和边界和replica映射对策略的影响。
2. **P1—补齐3张慢卡**：3张采用1/1/1/0或2/1/0/0分布，观察奇数不对称场景。
3. **P2—提高慢卡密度到6和8张**：分别采用2/2/1/1和2/2/2/2分布，检查深PP隔离、DP副本均衡和满卡收益在高密度异构下是否仍成立。
4. **P3—补7张近对称边界**：采用2/2/2/1分布，验证只差一张慢卡时对称映射经验是否失效。

上述对照统一保持：慢卡倍率保持当前值，不在下一批中改变；模型、batch、显存和网络参数保持不变。先改变拓扑位置和慢卡数量，不在同一批同时改变慢卡速度。
