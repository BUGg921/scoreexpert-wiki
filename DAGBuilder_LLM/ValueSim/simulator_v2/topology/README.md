# 物理拓扑配置

`topology_128g.py` 是可直接编辑的 128 卡示例。文件按下面的物理层级展开：

```text
4 个亲合组
└─ 每个亲合组 2 台 Server
   └─ 每台 Server 16 张卡
```

因此默认共有 8 台 Server、128 张卡。`affinity_groups` 明确列出每台
Server 对应的全局 Rank；`domains` 再定义 TP、DP、EP 等通信域。

## 设置慢卡

在 `device_overrides` 中按全局 Rank 配置实际计算速度：

```python
"device_overrides": {
    17: {
        "compute_tflops": 180.0,
        "status": "slow",
        "note": "人工注入慢卡",
    },
},
```

慢卡只影响采用数值计算模型的节点，不改变通信节点或 profiling 填充值。

## 设置慢链路

链路可按卡、Server 或亲合组设置。带宽单位是 Gbit/s，延迟单位是秒。

```python
"link_overrides": [
    {
        "scope": "device",
        "endpoints": [0, 4],
        "status": "slow",
        "bandwidth_gbps": 80.0,
        "latency_s": 120e-6,
        "bidirectional": True,
        "note": "Rank 0 与 Rank 4 之间的慢链路",
    },
    {
        "scope": "server",
        "endpoints": [0, 1],
        "status": "slow",
        "bandwidth_gbps": 200.0,
        "bidirectional": True,
    },
],
```

匹配优先级是“卡间链路 > Server 间链路 > 亲合组间链路 > 默认网络参数”。
若只填写带宽或延迟，未填写的字段继承该通信算法的默认链路参数。

## 设置故障链路

```python
{
    "scope": "affinity",
    "endpoints": [0, 1],
    "status": "down",
    "bidirectional": True,
    "note": "亲合组 0 到 1 的链路故障",
}
```

当数值仿真的通信路径使用故障链路时，运行会立即终止，并报告具体 Rank、
覆盖范围和备注，不会静默绕行。若需要模拟路由绕行，应在后续配置中显式
描述备用路径。

`scope="server"` 允许 `[0, 0]`，用于覆盖 Server 0 内部的所有卡间链路；
`scope="affinity"` 同理。`scope="device"` 的两个 Rank 必须不同。
