---
source_url:
source_path: /Users/cookie/Documents/wiki/DAGBuilder_Evolve/outputs/s3-two-same-node-review_20260730_180416_scenario_analysis.md
ingested: 2026-07-30
sha256: f8fcbe3b8dc9108fe103439ceac3bd4d6a3061a49b674fb520ccc8fd00910793
original_sha256: 50ca32efb423a838f0ae1ab3a51177543861e5b374254941898862f8da68f510
---

# s3_two_same_node_32g仿真与部署策略分析

## 实验场景

共 32 张 GPU：4个节点，每节点8卡，每两个节点组成一个16卡亲和组。
共有2张慢卡，具体为Rank 6=156 TFLOPS（0.50×）、Rank 7=156 TFLOPS（0.50×）。

### 模型配置与复算条件

```text
model = LLaMA-7B
num_layers = 32
global_batch_size = 128
sequence_length = 2048
device_memory = 16.0 GB
total_devices = 32
PP × TP × DP ≤ total_devices
search_coverage = 71/873 (8.13%)
```

## 最优解

```text
PP = 4
TP = 8
DP = 1
micro-batch number = 8
schedule = 1f1b
DP communication = rs_ag
active GPUs = 32
simulated critical-path latency = 3.828020 s
formula candidate score = -4.179287
formula candidate rank = 19
```


| 排名 | 已仿真策略 | 时延 (s) | 显存估算 (GB/卡) |
| ---: | --- | ---: | ---: |
| 1 | `PP4/TP8/DP1/MBN8/1F1B/RS+AG` | 3.828020 | 6.812 |
| 2 | `PP2/TP8/DP2/MBN4/1F1B/RS+AG` | 3.947308 | 13.623 |
| 3 | `PP2/TP8/DP2/MBN4/1F1B/AllReduce` | 3.947308 | 13.623 |
| 4 | `PP8/TP4/DP1/MBN64/1F1B/RS+AG` | 4.003622 | 3.053 |
| 5 | `PP4/TP8/DP1/MBN16/1F1B/RS+AG` | 4.043060 | 4.664 |

## 打分策略代码

该代码来自`pipeline_efficiency`岛第10代程序`a62a3ce524040d8a`，归因方式为`direct_evaluation_nomination`。

```python
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    pp = int(strategy['pp'])
    tp = int(strategy['tp'])
    dp = int(strategy['dp'])
    mb = int(strategy['micro_batch_num'])
    active = int(strategy['active_gpus'])
    schedule = strategy.get('schedule', '1f1b')
    dp_comm = strategy.get('dp_communication', 'none')
    server_cards = int(topology_cfg['cards_per_server'])
    total_devices = int(topology_cfg['total_devices'])
    affinity_groups = int(topology_cfg.get('affinity_group_count', 1))
    global_batch = int(workload_cfg['global_batch_size'])
    seq_len = int(workload_cfg['sequence_length'])
    hidden_size = int(model_cfg['hidden_size'])
    num_layers = int(model_cfg['num_layers'])
    ffn_hidden_size = int(model_cfg['ffn_hidden_size'])
    dtype_bytes = int(model_cfg['dtype_bytes'])
    gradient_dtype_bytes = int(model_cfg['gradient_dtype_bytes'])
    compute_efficiency = float(workload_cfg['compute_efficiency'])
    activation_multiplier = float(workload_cfg['activation_multiplier'])
    optimizer_state_multiplier = float(workload_cfg['optimizer_state_multiplier'])
    backward_flop_multiplier = float(workload_cfg['backward_flop_multiplier'])
    if active > total_devices:
        return -1e9
    if pp * tp * dp != active:
        return -1e9
    compute_time_per_micro = (num_layers * hidden_size * ffn_hidden_size * seq_len * dtype_bytes) / (active * compute_efficiency * 1e12)
    compute_time = compute_time_per_micro * mb
    tp_comm_time = 0.0
    if tp > 1:
        tp_bytes = hidden_size * hidden_size * dtype_bytes * 2
        tp_bw = 100e9
        tp_comm_time = (tp_bytes / tp_bw) * ((tp - 1) / tp)
    dp_comm_time = 0.0
    if dp > 1:
        total_params = num_layers * hidden_size * ffn_hidden_size
        dp_bytes = total_params * gradient_dtype_bytes * (1 + optimizer_state_multiplier)
        dp_bw = 50e9
        dp_comm_time = (dp_bytes / dp_bw) * 2 * ((dp - 1) / dp)
    bubble_ratio = 0.0
    if pp > 1:
        if schedule == '1f1b':
            bubble_ratio = (pp - 1) / (mb + pp - 1)
        elif schedule == 'gpipe':
            bubble_ratio = (pp - 1) / mb
    tp_cross_node = 0
    if server_cards > 0:
        tp_per_server = min(tp, server_cards)
        tp_cross_node = max(0, tp - tp_per_server)
    dp_cross_group = 0
    if affinity_groups > 0:
        groups_used = min(dp, affinity_groups)
        dp_per_group = dp // groups_used if groups_used > 0 else dp
        dp_cross_group = max(0, dp - dp_per_group)
    tp_cross_penalty = tp_cross_node * 0.05 * compute_time
    dp_cross_penalty = dp_cross_group * 0.1 * compute_time
    latency_estimate = compute_time + tp_comm_time + dp_comm_time + bubble_ratio * compute_time + tp_cross_penalty + dp_cross_penalty
    return -latency_estimate
```

## 经验总结

### <span style="color:blue;">(1) 并行策略</span>

1. 当异常设备能够收敛到一个局部执行单元，且`保留异常卡并局部隔离的算力收益 > 深流水线与重映射成本`时，优先采用满卡方案。参数按以下规则求解：先取能够限制异常同步扩散的最小已验证`TP=8`；再保留本轮仿真有收益的`DP=1`；在满卡约束下由`PP=active_gpu/(TP×DP)=32/(8×1)=4`反推PP；最后取显存、气泡和调度边界内已验证的`MBN=8`。

### <span style="color:blue;">(2) 原因</span>

1. **局部异构参数求解与映射原因**：
   - **TP**：`TP=8`把TP同步范围限制在单节点8卡边界内；慢卡不会通过跨节点TP集合通信进一步放大等待。
   - **DP**：`DP=1`与PP、TP共同使用32/32张卡。当前映射中副本0含2张慢卡；该不对称结构需要以副本关键路径和真实训练尾延迟为护栏，必要时优先重映射慢卡。
   - **PP/MBN**：32层模型可被4个stage整除；当前气泡近似为`27.27%`，派生micro-batch size为`16.000`。`MBN=8`只是在当前显存、气泡和搜索边界内与该PP深度配套的已验证值。
   - **仿真观测**：关键路径中compute=92.1%、tp=7.9%；慢卡影响1/4个TP group、1/4个PP stage和1/1个DP replica。
   - **公式与仿真分工**：公式把`PP4/TP8/DP1/MBN4/1F1B/RS+AG`排在第1，高于最终候选的第19；但其仿真时延为`4.388789 s`，比最终候选慢`14.65%`。因此公式负责提名，不能直接替代数值仿真结论。
   - **等价最优**：相对误差`1e-6`内存在1个等价最优：`PP4/TP8/DP1/MBN8/1F1B/RS+AG`。当前数值模型不能据此区分调度和DP通信实现，真实部署需用训练Evaluation选择。

### <span style="color:blue;">(3) 结论边界</span>

该经验仅适用于本报告的32卡拓扑、LLaMA-7B、GBS=128、Seq=2048、16.0GB/卡和当前慢卡Rank/速度。

本轮只实际评估71/873个候选；结论是当前已仿真候选最优。缺少真实训练P50/P99、吞吐、显存峰值和运行方差，因此经验状态保持`KEEP_FOR_VALIDATION`。

相对误差`1e-6`内存在1个等价最优：`PP4/TP8/DP1/MBN8/1F1B/RS+AG`。当前数值模型不能据此区分调度和DP通信实现，真实部署需用训练Evaluation选择。若慢卡Rank、速度、模型、batch、显存、网络或Rank映射变化，应作为新场景重新仿真。

## 未仿真的场景

从经验库目标总览读取的已总结场景为：标准 32 卡同构基线（成熟经验）、单慢卡局部隔离（成熟经验）、两慢卡非对称均衡（成熟经验）、四慢卡对称副本（成熟经验）、五慢卡 2/1/1/1 待验证证据（KEEP_FOR_VALIDATION）。本轮另有待人工审核的2张慢卡，按节点2/0/0/0分布。缺口计算以经验库已总结场景和本轮结果为准，不读取用户口头清单，也不把仅存在的配置文件算作已仿真。

尚未形成完整对照的场景包括：

1. **双慢卡拓扑差集**：经验库当前仍缺少同亲和组不同节点场景。同一节点还应继续区分同TP group与不同TP group；已由经验库覆盖的分支不重复建议。
2. **慢卡数量差集**：建议补充3、6、7、8张慢卡。其中3张观察奇数慢卡造成的副本不对称，6张观察2/2/1/1过渡分布，7张观察2/2/2/1近对称边界，8张构造每节点2张的高密度对称对照。
3. **同数量不同分布**：对3张及以上慢卡分别比较集中、同亲和组分散、跨亲和组不对称和跨节点近似对称映射，避免把慢卡数量本身误当成部署经验。

## 下一步仿真建议

1. **P0—补齐双慢卡拓扑对照**：优先仿真同亲和组不同节点；保持慢卡数量不变，可以直接识别节点边界、亲和边界和replica映射对策略的影响。
2. **P1—补齐3张慢卡**：3张采用1/1/1/0或2/1/0/0分布，观察奇数不对称场景。
3. **P2—提高慢卡密度到6和8张**：分别采用2/2/1/1和2/2/2/2分布，检查深PP隔离、DP副本均衡和满卡收益在高密度异构下是否仍成立。
4. **P3—补7张近对称边界**：采用2/2/2/1分布，验证只差一张慢卡时对称映射经验是否失效。

上述对照统一保持：慢卡倍率保持当前值，不在下一批中改变；模型、batch、显存和网络参数保持不变。先改变拓扑位置和慢卡数量，不在同一批同时改变慢卡速度。
