---
source_url:
source_path: /Users/cookie/Documents/wiki/Scoring strategy analysis_快慢卡.md
ingested: 2026-07-22
sha256: b6b2e92d3a0bfa4ccb8edbb9c44a4207b78962f4669d20d1cf5b8f493f96022c
original_sha256: 477cd8b811e688ee04a083e0851b96a49f77e6d2921d4d7002ce2ba2499fccd0
---

## <span style="color:red;">任务</span>

基于实验场景、最优解和两套打分策略 Python 代码，总结单张慢卡场景的部署策略，并将并行策略与参数选择原因分开表述。

## 实验场景

共 32 张 GPU 卡。每 8 张卡位于一个节点内，每两个节点、共 16 张卡属于一个亲和组。

### <span style="color:orange;">慢卡设置</span>

第 7 张卡为慢卡，计算速度约为正常卡的 `0.5×`。异构影响集中在一个可识别的局部范围内。

## 最优解

```text
PP = 16
TP = 2
DP = 1
micro-batch number = 64
TP:DP = 2:1
```

`MBN=64` 是当前搜索空间上界，不表示微批数越大在真实系统中一定越好。

## 打分策略代码

### 策略一

```python
score = 1000.0
score -= 6.0 * tp
score -= 55.0 * bubble
score -= 12.0 * dp_overhead
score -= 35.0 * tp_cross
score -= 0.4 * microbatch_size
score -= 15.0 * pp_imbalance
score -= 5.0 * idle_gpus
score += 0.3 * mbn
```

### 策略二

```python
score = 1000.0
score -= 50.0 * bubble
score -= 6.0 * tp
score -= 7.0 * dp
score += 0.3 * mbn
score -= 0.2 * microbatch_size
score -= 40.0 * tp_cross
score -= 10.0 * pp_imbalance
score -= 5.0 * idle_gpus
```

## 经验总结

### <span style="color:blue;">(1) 并行策略</span>

- **PP**：设置 `PP=16`，构造 16 个双卡 stage。
- **TP**：设置 `TP=2`，将慢卡放入一个 2 卡 TP group。
- **DP**：设置 `DP=1`，只构造一个 replica。
- **TP/DP**：当前实例使用 `TP:DP=2:1`。
- **MBN**：当前搜索空间内设置 `MBN=64`。
- **映射**：减少慢卡所在 stage 的层数或计算量，使该 stage 的预计执行时间接近其他 stage。
- **资源使用**：通过 `PP=16 × TP=2 × DP=1` 使用全部 32 张 GPU。

### <span style="color:blue;">(2) 原因</span>

#### TP=2 的原因

慢卡会使同一 TP group 内的正常卡等待。较小的 `TP=2` 把同步等待限制在一个双卡 group 内；在当前因子组合中，它也是 TP 成本与 PP bubble 之间的折中点。

#### PP=16 的原因

`TP=2,DP=1` 下使用全部 32 卡需要 `PP=16`。深 PP 将慢卡限制在一个 stage，配合减少该 stage 的层数或计算量，可以削弱局部慢卡对整条流水线周期的影响。

#### DP=1 的原因

两套公式都把 DP 当作成本。单张慢卡若只落入部分 DP replica，会形成纯快 replica 等待慢 replica；`DP=1` 避免这种跨副本 straggler 同步。

#### MBN=64 的原因

增大 MBN 会降低深 PP 的 bubble、减小单个 microbatch，并获得 `+0.3×MBN` 奖励，所以搜索结果被推到候选上界 64。该数值是当前评分公式与搜索边界共同产生的结果。

#### 满卡与 stage 重平衡的原因

idle penalty 推动方案使用全部 32 卡。但仅把慢卡放进某个 stage 不足以完成隔离；如果不减少慢卡 stage 的负载，它仍可能成为整条流水线的瓶颈。

### <span style="color:blue;">(3) 结论边界</span>

该策略适用于一张约半速慢卡且能够调整 stage/layer 映射的 32 卡场景。慢卡数量、位置、速度倍率或模型分层约束改变后，需要重新判断异构是否仍可局部隔离；`MBN=64` 也必须受显存、延迟和调度开销约束。
