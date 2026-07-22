---
source_url:
source_path: /Users/cookie/Documents/wiki/Scoring strategy analysis.md
ingested: 2026-07-22
sha256: a1c00cad5c902ad603035c7f1d64495fe2c11cd32b787cca63f41256d0d96044
original_sha256: ad45f7d7394d3ce6d608e2cb191d7850f83591633593765273eb08741843bc7c
---

## <span style="color:red;">任务</span>

基于实验场景、最优解和打分策略 Python 代码，总结标准 32 卡同构场景的部署策略，并将并行策略与参数选择原因分开表述。

## 实验场景

共 32 张正常 GPU 卡。每 8 张卡位于一个节点内，每两个节点、共 16 张卡属于一个亲和组。

- 节点内带宽最高；
- 亲和组内跨节点带宽较高；
- 跨亲和组带宽较低；
- 当前没有已知慢卡或稳定的设备性能差异；
- 候选满足 `PP × TP × DP = 32`，且 `TP ≤ 8`。

## 最优解

```text
PP = 1
TP = 8
DP = 4
micro-batch number = 1
TP:DP = 2:1
```

## 打分策略代码

```python
score = 1000.0
score -= 50.0 * bubble
score -= 2.0 * max(0, total - active)
score += 10.0 * micro / (micro + 10.0)
score += 1.0 * tp + 0.2 * dp
score -= 0.9 * abs(tp - dp)
score -= 0.5 * (mbn - 1) * (mbn - 1)
```

## 经验总结

### <span style="color:blue;">(1) 并行策略</span>

- **PP**：设置 `PP=1`。
- **TP**：设置 `TP=8`，每个节点构造一个完整的 8 卡 TP group。
- **DP**：设置 `DP=4`，四个节点分别形成一个 DP replica。
- **TP/DP**：当前 32 卡实例使用 `TP:DP=2:1`，即 `8:4`。
- **MBN**：设置 `MBN=1`。
- **资源使用**：使用全部 32 张 GPU，不跨节点拆分 TP group。

### <span style="color:blue;">(2) 原因</span>

#### PP=1 的原因

`-50 × bubble` 只惩罚流水线气泡，没有为增加 PP 提供收益。显存允许无流水线部署时，`PP=1` 可以消除 pipeline stage 和 bubble。

#### TP=8 的原因

在 `PP=1`、满 32 卡且 `TP≤8` 的候选中，TP/DP 评分项给 `TP=8,DP=4` 的分数最高。部署时 `TP=8` 又与单节点 8 卡规模一致，可把高频 TP 同步限制在节点内。

#### DP=4 的原因

`TP=8` 后需要四个完整 replica 才能使用全部 32 卡，因此取 `DP=4`。四个 replica 的结构一致，不会因设备性能形成固定快慢组。

#### MBN=1 的原因

`-0.5 × (MBN-1)²` 在 `MBN=1` 时惩罚为 0；同时 `PP=1` 不需要增加微批来填充流水线。

#### 满卡的原因

每空闲一张 GPU 都会受到 idle penalty。当前场景的最优结果表明，增加算力的收益大于当前评分模型中的通信成本，因此使用全部 32 卡。

### <span style="color:blue;">(3) 结论边界</span>

`PP=1,TP=8,DP=4,MBN=1` 与 32 卡、每节点 8 卡和当前候选空间绑定。资源数量或每节点卡数改变后，需要重新构造完整的 TP group、DP replica 和 PP stage，不能直接沿用该数值组合。
