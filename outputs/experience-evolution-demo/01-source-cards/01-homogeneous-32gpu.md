# 场景源文档 1：正常 32 卡

## 1. 来源

- Raw：`raw/articles/scoring-strategy-analysis-2026-07-14.md`
- 原始标题：`Scoring strategy analysis`
- 证据类型：score 推导；无直接 Evaluation 指标。

## 2. 实验场景

- 32 张正常 GPU；每节点 8 卡，共 4 节点。
- 每两个节点构成一个 16 卡亲和组。
- 节点内带宽最高，亲和组内跨节点次之，跨亲和组最低。
- 候选受 `PP×TP×DP=32` 和 `TP≤8` 约束。

## 3. 来源给出的最优解

```text
PP=1, TP=8, DP=4, MBN=1
```

## 4. Score 策略

```python
score = 1000.0
score -= 50.0 * bubble
score -= 2.0 * max(0, total - active)
score += 10.0 * micro / (micro + 10.0)
score += 1.0 * tp + 0.2 * dp
score -= 0.9 * abs(tp - dp)
score -= 0.5 * (mbn - 1) * (mbn - 1)
```

## 5. 为什么 Score 会打出该策略

1. `-2×idle` 促使候选使用满 32 卡。
2. 固定 `PP=1`、满卡、`TP≤8` 后，TP/DP 项在列出的因子对中给 `TP=8,DP=4` 最高分：`5.2`。
3. `-50×bubble` 只有 PP 惩罚，没有 PP 收益，因此偏向 `PP=1`。
4. `-0.5×(MBN-1)²` 在 `MBN=1` 取最大值 0，因此偏向 `MBN=1`。
5. `micro` 的定义缺失，不能复算完整总分；上述解释只覆盖来源能证明的决策项。

## 6. 来源明确总结

- 满卡优先。
- TP 与 DP 接近平衡并略偏向 TP；在当前约束和候选中实例为 `TP:DP=2:1`，即 `8:4`。
- PP 倾向于 1。
- MBN 倾向于 1。

## 7. 进入审查队列的候选

| ID | 候选 | 初始角色 |
|---|---|---|
| N1 | 严格匹配该场景时，以 `1/8/4/1` 作为第一轮 Evaluation 基线 | 经验候选 |
| N2 | 正常场景永远满卡 | 待拒绝的过度外推 |
| N3 | `TP:DP=2:1` 是通用最优比例 | 待拒绝的过度外推 |
| N4 | bubble、idle、TP/DP、MBN 项解释了当前 score 排名 | 证据候选 |

## 8. 证据边界

- 没有 latency、throughput、显存和通信实测。
- 没有可执行 rank/group mapping。
- `TP=8` 对齐单节点是拓扑解释，不是 score 代码直接读取拓扑后的结论。
- 本文件是统一模板整理，不替代 raw 来源。

