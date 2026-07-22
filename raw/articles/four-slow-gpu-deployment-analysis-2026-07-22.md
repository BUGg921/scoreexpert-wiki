---
source_url:
source_path: /Users/cookie/Documents/wiki/四张慢卡场景部署策略分析.md
ingested: 2026-07-22
sha256: f0d3c1f371343c98ca42fa5132973ff3ad004f9c9ed2057b6b3159ad00a56098
original_sha256: ef6e7375a4b454d1f05923a77af66a28365c84a2238f30509b6c2545d061c526
---

## <span style="color:red;">任务</span>

基于实验场景、Evaluation 最优解和演化后的打分策略 Python 代码，总结四张慢卡均匀分布场景的部署策略，并将并行策略与参数选择原因分开表述。

## 实验场景

共 32 张 GPU 卡：每节点 8 卡，每两个节点组成一个 16 卡亲和组。四张速度接近的慢卡均匀分布，四个节点各有一张慢卡，每个亲和组内有两张慢卡。

### 模型配置与复算条件

```text
num_layers = 32
global_batch_size = 8
total_devices = 32
PP × TP × DP ≤ 32
```

## 最优解

```text
PP = 1
TP = 8
DP = 4
micro-batch number = 1
TP:DP = 2:1
Score = 1007.520
```

## 打分策略代码

```python
def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    total_devices = int(topo_cfg.get("num_gpus", topo_cfg.get("num_devices", 1)))
    active = pp * tp * dp

    bubble = float(pp - 1) / max(1.0, float(mbn + pp - 1))
    gbs = float(model_cfg.get("global_batch_size", 1))
    microbatch_size = gbs / max(1.0, float(dp * mbn))

    score = 1000.0
    score -= 300.0 * bubble
    score -= 2.0 * max(0, total_devices - active)
    score -= 0.04 * microbatch_size
    score -= 0.15 * tp * mbn
    score += 1.0 * tp + 0.2 * dp

    num_layers = int(model_cfg.get("num_layers", 0))
    if num_layers > 0:
        remainder = num_layers % pp
        if remainder != 0:
            score -= 50.0 * float(remainder) / float(num_layers)

    return float(score)
```

## 经验总结

### <span style="color:blue;">(1) 并行策略</span>

- **PP**：设置 `PP=1`。
- **TP**：设置 `TP=8`，每个节点构造一个 8 卡 TP group。
- **DP**：设置 `DP=4`，四个节点分别形成一个 DP replica。
- **TP/DP**：当前实例使用 `TP:DP=2:1`，即 `8:4`。
- **MBN**：设置 `MBN=1`。
- **映射**：每个 TP group 放置一张速度接近的慢卡，使四个 DP replica 具有相同的慢卡数量和近似一致的位置结构。

### <span style="color:blue;">(2) 原因</span>

#### PP=1 的原因

四张慢卡分布在四个节点后，高 PP 很可能形成多个慢 stage，最慢 stage 仍会决定流水线吞吐。取消 PP 可以避免多个慢 stage、pipeline bubble 和排空开销。

#### TP=8 的原因

`PP=1,MBN=1` 时评分公式倾向较大的 TP。`TP=8` 与单节点规模一致，使每个节点形成一个完整 TP group，避免高频 TP 通信跨节点。

#### DP=4 的原因

`DP=4` 使用四个节点构造四个 replica。每个 replica 都包含一张速度接近的慢卡，虽然绝对计算速度都会下降，但副本结构更对称，可减少额外的 replica skew。

#### MBN=1 的原因

`PP=1` 下没有流水线需要填充。增大 MBN 只会增加 `TP×MBN` 成本，因此采用 `MBN=1`。

#### 对称映射的原因

四张慢卡无法被收敛为一个局部异常。把慢卡数量、速度和位置尽可能均匀地复制到四个 replica，可以把不规则的硬件异构转化为四个结构相近的副本，减少快组等待慢组的额外差异。

### <span style="color:blue;">(3) 结论边界</span>

该策略要求四张慢卡一节点一张且速度倍率接近。若慢卡集中在部分节点、速度差异明显或实际位置不是对称分布，需要按预计执行时间重新映射，不能只按慢卡数量平均分配。

当前打分代码不读取慢卡数量、位置和速度，因此两慢卡与四慢卡候选的 score 完全相同。四慢卡的对称部署原因来自 Evaluation 结果和拓扑解释；该策略只能降低副本间失衡，不能恢复慢卡造成的绝对性能损失。
