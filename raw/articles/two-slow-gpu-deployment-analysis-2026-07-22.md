---
source_url:
source_path: /Users/cookie/Documents/wiki/两张慢卡场景部署策略分析.md
ingested: 2026-07-22
sha256: 0fcee0bf07f0d843740432732281b40750acf28729de87c050a21d9d04138f32
original_sha256: 4ff91e0c507b2f9636b92d37d595b052f03a474dcfb3aab0ffb4c64e60213119
---

## <span style="color:red;">任务</span>

基于实验场景、Evaluation 最优解和演化后的打分策略 Python 代码，总结两张慢卡跨亲和组场景的部署策略，并将并行策略与参数选择原因分开表述。

## 实验场景

共 32 张 GPU 卡：每节点 8 卡，每两个节点组成一个 16 卡亲和组。两张慢卡分别位于两个亲和组，并落在两个不同节点中。

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
- **映射**：两张慢卡分别落入两个 TP group；四个 replica 中形成两个含慢卡 replica 和两个正常 replica。

### <span style="color:blue;">(2) 原因</span>

#### PP=1 的原因

两张慢卡已经跨亲和组分布，深 PP 容易形成多个慢 stage，不能再像单慢卡场景一样只隔离一个局部异常。`-300×bubble` 又是当前公式中权重最大的惩罚项，因此取消流水线更有利。

#### TP=8 的原因

`PP=1,MBN=1` 时，TP 的净评分系数为正，公式倾向较大的 TP。`TP=8` 与单节点 8 卡规模一致，可把高频 TP 通信限制在节点内。

#### DP=4 的原因

`PP=1,TP=8` 后，设置 `DP=4` 才能使用全部 32 卡。四个节点形成四个 replica，但其中两个含慢卡、两个不含慢卡，因此部署时需要关注快 replica 等待慢 replica 的现象。

#### MBN=1 的原因

`PP=1` 时 bubble 恒为 0，增大 MBN 不再有填充流水线的收益，反而会增加 `TP×MBN` 通信惩罚，因此选择最小值 1。

#### 从隔离切换到均衡的原因

单慢卡时可以通过一个 stage 做局部隔离；两张慢卡跨越两个独立拓扑区域后，逐点隔离会把多个慢点串入长流水线。当前方案转而采用规整的节点内 TP 和节点间 DP，并控制不同 replica 的执行时间差。

### <span style="color:blue;">(3) 结论边界</span>

该策略要求两张慢卡跨亲和组、模型能够在 `TP=8` 下部署，并允许按节点构造完整 TP group。若两张慢卡集中在同一节点、速度倍率差异很大或显存要求必须增加 PP，需要作为新的场景重新推理。

当前打分代码不读取慢卡数量、位置和速度；慢卡映射与均衡原因来自 Evaluation 结果和拓扑解释，而不是评分公式直接感知异构。
