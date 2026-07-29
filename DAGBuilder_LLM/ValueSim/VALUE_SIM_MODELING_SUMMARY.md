# ValueSim 数值仿真建模方式总结

本文档总结当前 `ValueSim` 对 DAG 图中各类节点的建模方式，以及每个节点 `duration_s` 的计算来源。当前实现以解析 DAG 节点的 `task_kind` 为入口，只给已有 DAG 节点补充时间和载荷字段，不改变 DAG 拓扑。

## 总体流程

入口是 `ValueSim/simulation/simulate_dag.py`。

ValueSim 输入：

- `dag.json`：由 DagGenerator 生成，包含 `nodes` 和 `edges`。
- `config.py`：提供模型参数、并行配置、网络带宽/延迟、ValueSim 参数。

ValueSim 输出：

- `weighted_dag.json`：在原 DAG 节点上增加数值仿真字段。
- `node_timing_table.json`：按节点展开的 timing 表。

每个节点会增加：

- `duration_s`：该节点估算耗时，单位秒。
- `flops`：该节点对应计算量。通信节点为 0。
- `payload_bytes`：该节点通信或 TP 内部通信载荷。
- `value_sim_detail`：具体模型细节，例如带宽、延迟、TP 切分、collective 步骤等。

ValueSim 会检查节点数和边数是否保持不变。如果仿真过程改变了 DAG 拓扑，会直接报错。

## 节点类型分发

当前根据 `task_kind` 选择不同模型：

| task_kind | 建模方式 |
|---|---|
| `control` | 零耗时节点 |
| `forward` | Transformer layer 前向计算 + TP 通信 |
| `backward` | Transformer layer 反向计算 + TP 通信 |
| `pp_forward_send` / `pp_backward_send` / `pp_forward_recv` / `pp_backward_recv` | PP 点到点通信 |
| `dp_allreduce` / `zero01_g_ar` | DP AllReduce |
| `dp_reducescatter` / `reduce_scatter` / `zero01_g_rs` | DP ReduceScatter |
| `dp_allgather` / `allgather` / `zero01_p_ag` | DP AllGather |

如果遇到未支持的 `task_kind`，ValueSim 会报错。

## Control 节点

`control` 节点用于 DAG 起点、终点或控制依赖，不代表真实计算或通信。

计算方式：

```text
duration_s = 0
flops = 0
payload_bytes = 0
```

## Forward / Backward 计算节点

前向和反向节点使用 `estimate_tp_compute(...)` 建模。它把一个 layer 视作 TP supernode：本地计算会按 TP 切分，同时额外加入 TP 内部 collective 通信时间。

### 计算量

如果配置中显式提供 `value_sim_config.layer_forward_flops`，则直接使用该值。否则按 Transformer layer 估算：

```text
tokens = microbatch_size * seq_len
attention_flops = 8 * tokens * hidden_size * hidden_size
mlp_flops = 4 * tokens * hidden_size * ffn_hidden_size
forward_flops = attention_flops + mlp_flops
```

反向计算量使用倍率：

```text
backward_flops = forward_flops * backward_flop_multiplier
```

默认 `backward_flop_multiplier = 2.0`。

### TP 切分后的本地计算时间

如果 `tp_compute_sharding_enabled = True`：

```text
sharded_flops = flops / tp_size
```

否则：

```text
sharded_flops = flops
```

本地计算时间：

```text
effective_flops = device_peak_flops * compute_efficiency
local_compute_s = sharded_flops / effective_flops
```

### TP 内部通信

如果 `tp_comm_enabled = True`，当前只支持 ring 模型。

TP 通信 payload 使用完整 activation：

```text
tp_activation_bytes = microbatch_size * seq_len * hidden_size * precision_bytes(tp)
```

每个 TP rank 的本地 payload：

```text
local_payload_bytes = full_activation_bytes / tp_size
```

每个 collective 的 ring 步数：

```text
steps_per_collective = 2 * (tp_size - 1)
```

每个 collective 的 wire bytes：

```text
wire_bytes_per_collective = 2 * local_payload_bytes * (tp_size - 1) / tp_size
```

每个 collective 的通信时间：

```text
duration_per_collective =
    steps_per_collective * latency_s
  + wire_bytes_per_collective / effective_bandwidth_bytes_per_s
```

总 TP 通信时间：

```text
tp_comm_s = duration_per_collective * collective_count
```

其中：

- forward 节点默认使用 `tp_forward_collectives_per_layer`。
- backward 节点默认使用 `tp_backward_collectives_per_layer`。

如果 TP domain 跨 affinity group，则使用 `tp_cross_affinity_link_type`，默认可能走 RoCE；否则使用 `tp_intra_affinity_link_type`，通常走 HCCS/innode。

### Forward / Backward 最终 duration

TP 通信可以按配置做部分 overlap：

```text
tp_comm_non_overlapped_s = tp_comm_s * (1 - tp_comm_overlap_ratio)
duration_s = local_compute_s + tp_comm_non_overlapped_s
```

当前默认 `tp_comm_overlap_ratio` 来自 `value_sim_config`。

## PP 通信节点

PP 通信节点包括：

- `pp_forward_send`
- `pp_forward_recv`
- `pp_backward_send`
- `pp_backward_recv`

这些节点当前统一用 `estimate_pp_p2p(...)` 建模。

PP payload 使用 TP 切分后的 activation：

```text
pp_activation_bytes =
    microbatch_size * seq_len * hidden_size * precision_bytes(pp) / tp_size
```

通信链路由 `value_sim_config.pp_link_type` 决定：

- `roce`：使用 RoCE 带宽、RoCE 静态延迟。
- `hccs` / `innode`：使用 HCCS/节点内带宽、节点内静态延迟。

duration 计算：

```text
effective_bandwidth = bandwidth_gbps * 1e9 / 8 * utilization_ratio
duration_s = latency_s + payload_bytes / effective_bandwidth
```

当前 `validate_value_sim_config(...)` 中要求 Ascend profile 下 `pp_link_type = roce`，除非后续显式重新设计。

## DP 通信节点

DP 节点的 payload 通常来自当前 PP stage 的梯度大小。

### DP payload

如果 DAG 节点显式带有 `payload_bytes` 或 `bucket_bytes`，优先使用节点上的值。若配置中未声明这些值已经 TP 切分，则还会除以 `tp_size`。

否则，如果节点有 `pp_stage_id`，按 stage 内层数计算梯度大小：

```text
stage_gradient_bytes =
    num_layers_in_stage * layer_param_bytes / tp_size
```

单层参数量估算：

```text
attention_params = 4 * hidden_size * hidden_size
mlp_params = 2 * hidden_size * ffn_hidden_size
layer_param_count = attention_params + mlp_params
layer_param_bytes = layer_param_count * precision_bytes(dp)
```

如果没有 stage 信息，则退化为单层参数大小或配置中的 `dp_bucket_size_bytes`。

## DP ReduceScatter / AllGather

`dp_reducescatter` 和 `dp_allgather` 使用同一个 layered collective 模型，只是 `direction` 不同。

当前 collective 输入包括：

- `domain_size = dp_size`
- `ranks_per_node`
- `affinity_group_size`
- HCCS 有效带宽
- RoCE 有效带宽
- 节点内静态延迟
- RoCE 静态延迟

模型把 DP domain 分成三层：

```text
n1 = min(ranks_per_node, domain_size)
n2 = min(affinity_group_size, ceil(domain_size / n1))
n3 = ceil(domain_size / (n1 * n2))
```

每个 rank 的基本数据量：

```text
per_rank_bytes = total_data_size / domain_size
```

三层步骤数：

```text
layer1_steps = n1 - 1
layer2_steps = ceil(log2(n2))
layer3_steps = ceil(log2(n3))
```

每一步的数据量按 `per_rank_bytes * 2^step` 估算：

```text
step_time = latency_s + step_bytes / bandwidth
```

总时间：

```text
duration_s =
    sum(intra_node_steps)
  + sum(affinity_group_steps)
  + sum(inter_node_roce_steps)
```

`value_sim_detail.steps` 会记录每一层、每一步的 payload、传输时间、静态延迟和 step duration。

## DP AllReduce

`dp_allreduce` 支持两类模式。

### hierarchical / decomposed 路径

当 `allreduce_mode = decomposed`，或者 `dp_collective_model = hierarchical` 时，AllReduce 被估算为：

```text
duration_s = ReduceScatter(payload).duration_s + AllGather(payload).duration_s
```

这不会改变 DAG 拓扑，只是在 `dp_allreduce` 节点内部把时间分解为 RS + AG。

### simple ring 路径

如果没有使用 hierarchical 模型，AllReduce 会使用 ring alpha-beta 估算：

```text
steps = 2 * (dp_size - 1)
wire_bytes = 2 * payload_bytes * (dp_size - 1) / dp_size
duration_s = steps * latency_s + wire_bytes / effective_bandwidth
```

当前 simple ring 路径使用 HCCS 带宽和节点内静态延迟。

## 输出字段含义

`weighted_dag.json` 中每个节点会保留原始 DAG 字段，并增加：

```text
duration_s
flops
payload_bytes
value_sim_detail
```

`node_timing_table.json` 每行包含：

```text
node_id
label
task_kind
duration_s
flops
payload_bytes
resource
value_sim_detail
```

其中 `resource` 来自 DAG 节点的 `stream_type`，用于后续 Evaluation 或 OverlapOPT 判断资源串行和关键路径。

## 当前模型假设与限制

- ValueSim 不修改节点和边，只给节点加权。
- Forward / Backward 是 layer 粒度节点，不是算子级节点。
- TP 通信被合并进 compute 节点内部，不展开成独立 DAG 节点。
- PP send/recv 当前使用同样的点到点通信模型。
- DP stage-level 节点可能是 monolithic，也可能由 DagGenerator 直接生成 ReduceScatter + AllGather 节点。
- AllReduce 的 hierarchical 分解只发生在 duration 估算内部，不会自动拆 DAG 节点。
- 当前只支持已列出的 `task_kind`，新节点类型需要显式增加模型分发逻辑。
- 当前模型主要是解析式估算，不是基于真实 profiler trace 的逐算子仿真。

