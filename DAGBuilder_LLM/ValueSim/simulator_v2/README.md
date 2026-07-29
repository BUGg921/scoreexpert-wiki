# ValueSim simulator_v2

`simulator_v2` 是独立的 DAG 时间填充器。它把物理拓扑、配置、DP/PP/EP
数值模型、profiling 填充和输出报告分开，并保持输入 DAG 的节点与边不变。

## 目录

```text
simulator_v2/
├─ topology/       # 亲合组、Server、卡、通信域和异常链路
├─ config/         # 配置加载、校验和 30B 示例
├─ simulators/     # DP、PP、EP、Compute、profiling
├─ tests/          # 单元测试和 30B 集成回归
├─ output/         # 每轮独立输出目录
├─ engine.py       # 来源选择、时间填充和最长路径
└─ __main__.py     # 命令行入口
```

## 快速执行

在仓库根目录运行：

```powershell
python -m ValueSim.simulator_v2 `
  --dag outputs\dag_30b_coarse_20260710_112015\dag.json `
  --config ValueSim\simulator_v2\config\config_30b.py `
  --run-name 30b_baseline
```

输出位于 `ValueSim/simulator_v2/output/30b_baseline/`。已有同名目录时拒绝
覆盖；省略 `--run-name` 会使用时间戳。

## 拓扑配置

30B 配置直接读取 `topology/topology_128g.py`。该文件明确展开：

- 128 张卡、8 台 Server、4 个亲合组；
- 每台 Server 16 张卡；
- 每个亲合组 2 台 Server、32 张卡；
- DP_CP 第一域 `[0,4,8,...,124]`；
- DP_EP 第一域 `[0,32,64,96]`。

`device_overrides` 可按全局 Rank 设置慢卡的实际算力；`link_overrides` 可按
卡、Server 或亲合组设置慢链路和故障链路。具体示例、优先级和故障行为见
[`topology/README.md`](topology/README.md)。

慢卡只影响数值计算节点。慢链路只影响实际经过对应通信边的数值通信轮次。
若路径经过 `status="down"` 的链路，运行会终止并报告端点；不会静默绕行。

## 数据来源

```python
"simulation_flags": {
    "dp": 1,
    "pp": 1,
    "ep": 1,
    "tp": 0,
    "compute": 0,
    "optimizer": 0,
    "other": 0,
}
```

`1` 表示数值仿真，`0` 表示按 `profile_key` 精确读取 profiling。覆盖优先级为
`node_id > op_name > 类别默认值`。置零节点若缺少或重复 profiling，程序会在
仿真前一次列出全部问题，不做模糊匹配或比例拟合。

## 网络与算子配置

默认网络参数位于 `config/config_30b.py`，包含 HCCS、RoCE、HBM 的带宽、
利用率和静态延迟。链路按实际端点选择：

- 同一 Server：`hccs_intra_server`
- 同一亲合组、不同 Server：`hccs_inter_server`
- 不同亲合组：`roce`

每个数值通信算子必须声明 `payload_scope`：

| 取值 | 含义 |
| --- | --- |
| `full_tensor` | 完整集合通信张量 |
| `local_shard` | 当前 Rank 的本地分片 |
| `replicated` | 每个 Rank 都持有的完整输入 |
| `per_rank_send` | 每个 Rank 的 AllToAll 或 P2P 发送量 |

数据量可由 `payload_bytes`、`payload_elements × dtype_bytes` 或 DAG 节点提供。
`bucket_count` 表示均分 bucket；掌握真实分桶时可提供
`bucket_sizes_bytes=[...]`，其总和必须严格等于逻辑 payload。

DP/EP 支持 Ring、NHR、分层 Ring+NHR；EP AllToAll 支持 pairwise 和
hierarchical-pairwise；PP 按对应 TP lane 做相邻 stage P2P；Compute 按参与
Rank 中最慢卡计算。

## 输出

每轮生成：

- `weighted_dag.json`：写入耗时与明细后的 DAG
- `node_timings.json`：逐节点来源、数据量、步数和误差
- `topology.json`：物理层级、卡、通信域和异常覆盖
- `resolved_config.json`：本轮完整配置快照
- `run_manifest.json`：输入路径、时间及文件哈希
- `summary.json`、`summary.md`：来源统计、最长路径和关键节点

## 测试

```powershell
python -m unittest discover -s ValueSim\simulator_v2\tests -v
python -m unittest ValueSim.simulation.test_dp_step_time_v2
python OverlapOPT\validate_overlap_opt.py
```

常见错误包括：profiling 精确键缺失、通信域未完整覆盖 Rank、数值算子缺少
payload 口径、故障链路被使用，以及输出目录已存在。
