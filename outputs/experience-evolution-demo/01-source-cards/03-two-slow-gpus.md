# 场景源文档 3：两张慢卡

## 1. 来源

- Raw 1：`raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md`
- Raw 2：`raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md`
- 证据类型：score 复算、来源报告的 Evaluation 胜者与拓扑解释；缺少 Evaluation 原始表。

## 2. 实验场景

- 32 张 GPU；每节点 8 卡，每亲和组 16 卡。
- 两张慢卡分别位于两个亲和组，并落在两个节点中。
- 多慢卡来源的复算条件为 `num_layers=32`、`GBS=8`、`total_devices=32`。

## 3. 来源给出的最优解

```text
PP=1, TP=8, DP=4, MBN=1
Evaluation：来源称当前组合最优，但未给出原始指标
```

## 4. Score 策略

```python
bubble = (pp - 1) / (mbn + pp - 1)
microbatch_size = gbs / (dp * mbn)
score = 1000.0
score -= 300.0 * bubble
score -= 2.0 * max(0, total_devices - active)
score -= 0.04 * microbatch_size
score -= 0.15 * tp * mbn
score += 1.0 * tp + 0.2 * dp
score -= 50.0 * layer_imbalance_ratio
```

## 5. 为什么 Score 会打出该策略

1. `-300×bubble` 是大权重项，首先把 PP 推到 1。
2. `PP=1` 后 MBN 不再降低 bubble，`-0.15×TP×MBN` 使 `MBN=1` 最优。
3. `MBN=1` 时 TP 的净系数为 `1-0.15=0.85`，因此偏向较大 TP。
4. `TP=8` 后，为消除 idle penalty 并使用满 32 卡，得到 `DP=4`。
5. 当前分数为 `1007.520`；只比 `PP=1,TP=1,DP=32,MBN=1` 高 `0.28`，所以 `8/4` 是弱偏好。

## 6. 来源明确总结

- 两张慢卡跨亲和组后，深 PP 可能形成多个慢 stage，单慢卡隔离收益下降。
- 模型能在节点内 TP group 放下时，优先取消深流水线，在节点内做 `TP=8`，跨节点做 `DP=4`。
- `PP=1` 时从 `MBN=1` 起步。
- 两个慢 replica 和两个快 replica 会造成 DP skew，必须观察快副本等待慢副本的比例。

## 7. 进入审查队列的候选

| ID | 候选 | 初始角色 |
|---|---|---|
| T1 | 两慢卡跨亲和组时，从局部隔离切换到无 PP、节点内 TP、节点间 DP | 经验候选 |
| T2 | 任何两张慢卡都使用 `1/8/4/1` | 待拒绝的过度外推 |
| T3 | `PP=1` 与 `MBN=1` 是 score 的强偏好 | 证据候选 |
| T4 | `TP=8,DP=4` 是 score 的稳定强规律 | 待拒绝；当前只领先 0.28 |
| T5 | 用 replica skew 验证快慢副本等待 | 验证候选 |

## 8. 证据边界

- score 不读取慢卡数量、ID、位置或速度。
- 来源未给慢卡 ID、倍率、Evaluation 延迟、吞吐和波动。
- 两张慢卡集中在同一节点时不满足本场景。
- 本文件是从两份 raw 中整理出的独立场景卡，不新增第四份 raw 快照。

