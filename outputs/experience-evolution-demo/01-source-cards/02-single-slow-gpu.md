# 场景源文档 2：单张慢卡

## 1. 来源

- Raw：`raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md`
- 原始标题：`Scoring strategy analysis_快慢卡`
- 证据类型：两套 score 推导与拓扑解释；无可核验的 Evaluation 原始指标。

## 2. 实验场景

- 32 张 GPU；每节点 8 卡，每亲和组 16 卡。
- 第 7 张卡约为正常卡的 `0.5×` 计算速度。
- 只有这一张局部慢卡。

## 3. 来源给出的最优解

两套 score 均得到：

```text
PP=16, TP=2, DP=1, MBN=64
```

`MBN=64` 是候选搜索上界。

## 4. Score 策略

策略一关键项：

```python
score -= 6.0 * tp
score -= 55.0 * bubble
score -= 12.0 * dp_overhead
score -= 35.0 * tp_cross
score -= 0.4 * microbatch_size
score -= 15.0 * pp_imbalance
score -= 5.0 * idle_gpus
score += 0.3 * mbn
```

策略二关键项：

```python
score -= 50.0 * bubble
score -= 6.0 * tp
score -= 7.0 * dp
score += 0.3 * mbn
score -= 0.2 * microbatch_size
score -= 40.0 * tp_cross
score -= 10.0 * pp_imbalance
score -= 5.0 * idle_gpus
```

## 5. 为什么 Score 会打出该策略

1. TP 在两套公式中都是成本，促使同步组缩小；在当前因子对中 `TP=2` 与 PP bubble 达到折中。
2. DP 被直接惩罚或通过 `dp_overhead` 惩罚，因此选择 `DP=1`。
3. `TP=2,DP=1` 要使用满 32 卡时得到 `PP=16`。
4. 增大 MBN 一方面降低深 PP bubble，另一方面得到 `+0.3×MBN` 的线性奖励，因此搜索推到上界 64。
5. 公式没有直接读取 GPU 7 或 `0.5×` 速度；“隔离慢卡”的解释来自拓扑推理，不是 score 直接感知慢卡。

## 6. 来源明确总结

- 小 TP 缩小慢卡同步污染范围。
- `DP=1` 避免多副本 straggler 同步。
- 高 PP 使用满卡，并将局部慢卡限制在少数 stage。
- 大 MBN 填充深 pipeline；64 是 score 与搜索边界共同形成的结果，不是物理常数。

## 7. 进入审查队列的候选

| ID | 候选 | 初始角色 |
|---|---|---|
| S1 | 一张局部慢卡时，用小 TP、高 PP 和 stage rebalance 做隔离型 Evaluation | 经验候选 |
| S2 | 所有单慢卡场景固定使用 `16/2/1/64` | 待拒绝的过度外推 |
| S3 | MBN 越大越好 | 待拒绝的边界伪规律 |
| S4 | 两套 score 通过 TP/DP 成本、bubble 与 MBN 奖励形成当前排名 | 证据候选 |
| S5 | 慢卡 stage 少分层可缓解瓶颈 | 待验证候选 |

## 8. 证据边界

- 没有 stage/layer 的具体分配和 profile。
- 没有 latency、throughput、显存、stage time 及重复波动。
- `MBN=64` 必须和 16、32 等对照，不能直接进入通用经验。
- 本文件是统一模板整理，不替代 raw 来源。

