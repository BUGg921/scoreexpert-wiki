---
source_url:
source_path: /Users/cookie/Documents/wiki/DAGBuilder_Evolve/outputs/s7-five-slow-2-1-1-1_20260730_144533_scenario_analysis.md
ingested: 2026-07-30
sha256: 9bae6f7f494d867a70dc66f242b6e0300d2cfd9391669e88fe524f8ffd8eeef0
original_sha256: a30208dc9de489eee963bfb99665c8b3a3a7e25264f5d3795e827b78f21d9a9b
---

# s7_five_slow_32g仿真与部署策略分析


## 实验场景

共 32 张 GPU：4个节点，每节点8卡，每两个节点组成一个16卡亲和组。
共有5张慢卡，具体为Rank 6=156 TFLOPS（0.50×）、Rank 7=156 TFLOPS（0.50×）、Rank 15=156 TFLOPS（0.50×）、Rank 23=156 TFLOPS（0.50×）、Rank 31=156 TFLOPS（0.50×）。

### 模型配置与复算条件

```text
model = LLaMA-7B
num_layers = 32
global_batch_size = 128
sequence_length = 2048
device_memory = 16.0 GB
total_devices = 32
PP × TP × DP ≤ total_devices
search_coverage = 65/873 (7.45%)
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
simulated critical-path latency = 4.146778 s
formula candidate score = -857.527882
formula candidate rank = 5
```

这里的“最优”仅指已实际仿真的候选中最长路径最低，不代表873个结构候选已经穷举。

| 排名 | 已仿真策略 | 时延 (s) | 显存估算 (GB/卡) |
| ---: | --- | ---: | ---: |
| 1 | `PP16/TP1/DP2/MBN64/1F1B/AllReduce` | 4.146778 | 5.570 |
| 2 | `PP16/TP1/DP2/MBN64/GPIPE/AllReduce` | 4.146778 | 9.328 |
| 3 | `PP16/TP1/DP2/MBN64/1F1B/RS+AG` | 4.146778 | 5.570 |
| 4 | `PP16/TP1/DP2/MBN64/GPIPE/RS+AG` | 4.146778 | 9.328 |
| 5 | `PP16/TP2/DP1/MBN64/1F1B/RS+AG` | 4.164339 | 3.053 |

## 打分策略代码

该代码来自`memory_safe`岛第4代程序`390b14fcfe45eafb`，归因方式为`direct_evaluation_nomination`。

```python
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mb = int(strategy["micro_batch_num"])
    active = int(strategy["active_gpus"])
    server_cards = int(topology_cfg["cards_per_server"])
    affinity_groups = int(topology_cfg["affinity_group_count"])
    global_bs = int(workload_cfg["global_batch_size"])
    seq_len = int(workload_cfg["sequence_length"])
    hidden = int(model_cfg["hidden_size"])
    ffn = int(model_cfg["ffn_hidden_size"])
    layers = int(model_cfg["num_layers"])
    dtype = int(model_cfg["dtype_bytes"])
    compute_eff = float(workload_cfg["compute_efficiency"])
    backward_flop_multiplier = float(workload_cfg["backward_flop_multiplier"])
    activation_multiplier = float(workload_cfg["activation_multiplier"])
    optimizer_state_multiplier = float(workload_cfg["optimizer_state_multiplier"])

    # Memory estimation
    param_per_layer = 8.0 * hidden * hidden + 4.0 * hidden * ffn
    total_params = layers * param_per_layer
    param_mem = total_params * dtype / (tp * pp)
    grad_mem = param_mem
    opt_mem = optimizer_state_multiplier * param_mem
    activation_mem = pp * mb * seq_len * hidden * activation_multiplier * dtype
    total_mem = param_mem + grad_mem + opt_mem + activation_mem
    mem_limit = 80.0 * 1024**3  # 80 GB
    if total_mem > mem_limit:
        return -1000.0 + total_mem / 1e9  # penalize, worse for higher memory

    # Latency estimation
    flops_per_layer = 12.0 * hidden * hidden * hidden
    total_flops_per_micro = layers * flops_per_layer * (1.0 + backward_flop_multiplier)
    compute_time_per_micro = total_flops_per_micro / (tp * compute_eff)
    bubble = (pp - 1.0) / (mb + pp - 1.0) if (mb + pp - 1) > 0 else 0.0
    total_compute_time = compute_time_per_micro * mb / (1.0 - bubble) if bubble < 1.0 else float('inf')

    # Communication penalties
    tp_comm_volume = 8 * layers * global_bs * seq_len * hidden * dtype / tp
    tp_comm_per_gpu = tp_comm_volume * (tp - 1) / tp
    cross_server = 1.0 if active > server_cards else 0.0
    cross_affinity_penalty = 0.0
    if cross_server:
        if tp > server_cards:
            cross_affinity_penalty = (tp - server_cards) * tp_comm_per_gpu
        else:
            cross_affinity_penalty = tp_comm_per_gpu * 0.3
    dp_comm_cost = 0.0
    if dp > 1:
        grad_size = layers * hidden * hidden * dtype * 4
        dp_comm_cost = grad_size * (dp - 1) / dp
    if strategy["dp_communication"] == "rs_ag":
        dp_comm_cost *= 0.5

    # Score components (higher score = lower latency, we want to nominate low-latency strategies)
    base_score = 1000.0
    # Encourage more parallelism (tp, dp) as they reduce compute time; but pp also helps but adds bubble
    tp_benefit = 20.0 * tp
    dp_benefit = 5.0 * dp
    # Bubble penalty: penalize high pipeline bubble
    bubble_penalty = -200.0 * bubble
    # Communication penalties: penalize high communication costs
    tp_comm_penalty = -0.01 * tp_comm_per_gpu
    cross_affinity_penalty_scaled = -0.01 * cross_affinity_penalty
    dp_comm_penalty = -0.01 * dp_comm_cost
    # Compute time penalty: penalize high compute time (lower is better)
    compute_time_penalty = -10.0 * total_compute_time

    score = base_score + tp_benefit + dp_benefit + bubble_penalty + tp_comm_penalty + cross_affinity_penalty_scaled + dp_comm_penalty + compute_time_penalty
    return score
```

## 经验总结

### <span style="color:blue;">(1) 并行策略</span>

1. 当异常设备跨多个节点或亲和组、无法通过一个局部执行单元完成隔离，且`保留满卡与数据并行的收益 > replica等待和DP通信成本`时，优先采用满卡方案。参数按以下规则求解：先取能够限制异常同步扩散的最小已验证`TP=1`；再保留本轮仿真有收益的`DP=2`；在满卡约束下由`PP=active_gpu/(TP×DP)=32/(1×2)=16`反推PP；最后取显存、气泡和调度边界内已验证的`MBN=64`。

### <span style="color:blue;">(2) 原因</span>

1. **分布式异构参数求解与映射原因**：
   - **TP**：`TP=1`把TP同步范围限制在单卡、消除TP集合通信；慢卡不会通过跨节点TP集合通信进一步放大等待。
   - **DP**：`DP=2`与PP、TP共同使用32/32张卡。当前映射中副本0含1张慢卡、副本1含4张慢卡；该不对称结构需要以副本关键路径和真实训练尾延迟为护栏，必要时优先重映射慢卡。
   - **PP/MBN**：32层模型可被16个stage整除；当前气泡近似为`18.99%`，派生micro-batch size为`1.000`。`MBN=64`只是在当前显存、气泡和搜索边界内与该PP深度配套的已验证值。
   - **仿真观测**：关键路径中compute=96.9%、dp=2.9%、pp=0.1%；慢卡影响5/32个TP group、4/16个PP stage和2/2个DP replica。
   - **公式与仿真分工**：公式把`PP32/TP1/DP1/MBN64/1F1B/RS+AG`排在第1，高于最终候选的第5；但其仿真时延为`4.506442 s`，比最终候选慢`8.67%`。因此公式负责提名，不能直接替代数值仿真结论。
   - **等价最优**：相对误差`1e-6`内存在4个等价最优：`PP16/TP1/DP2/MBN64/1F1B/AllReduce`、`PP16/TP1/DP2/MBN64/GPIPE/AllReduce`、`PP16/TP1/DP2/MBN64/1F1B/RS+AG`、`PP16/TP1/DP2/MBN64/GPIPE/RS+AG`。当前数值模型不能据此区分调度和DP通信实现，真实部署需用训练Evaluation选择。

### <span style="color:blue;">(3) 结论边界</span>

该经验仅适用于本报告的32卡拓扑、LLaMA-7B、GBS=128、Seq=2048、16.0GB/卡和当前慢卡Rank/速度。

本轮只实际评估65/873个候选；结论是当前已仿真候选最优。缺少真实训练P50/P99、吞吐、显存峰值和运行方差，因此经验状态保持`KEEP_FOR_VALIDATION`。

相对误差`1e-6`内存在4个等价最优：`PP16/TP1/DP2/MBN64/1F1B/AllReduce`、`PP16/TP1/DP2/MBN64/GPIPE/AllReduce`、`PP16/TP1/DP2/MBN64/1F1B/RS+AG`、`PP16/TP1/DP2/MBN64/GPIPE/RS+AG`。当前数值模型不能据此区分调度和DP通信实现，真实部署需用训练Evaluation选择。若慢卡Rank、速度、模型、batch、显存、网络或Rank映射变化，应作为新场景重新仿真。
