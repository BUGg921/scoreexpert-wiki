# 场景源文档 4：四张慢卡

## 1. 来源

- Raw：`raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md`
- 证据类型：与两慢卡相同的 score 复算、来源报告的 Evaluation 胜者与拓扑解释；缺少 Evaluation 原始表。

## 2. 实验场景

- 32 张 GPU；4 节点，每节点 8 卡。
- 按来源假设，四张慢卡“一节点一张”，每个亲和组两张。
- 四张慢卡的速度倍率应近似，才能把“数量对称”当作“性能对称”的近似。

## 3. 来源给出的最优解

```text
PP=1, TP=8, DP=4, MBN=1
Score=1007.520
Evaluation：来源称当前组合最优，但未给出原始指标
```

## 4. Score 策略

与两张慢卡场景完全相同：

```python
score -= 300.0 * bubble
score -= 2.0 * idle_gpus
score -= 0.04 * microbatch_size
score -= 0.15 * tp * mbn
score += 1.0 * tp + 0.2 * dp
score -= 50.0 * layer_imbalance_ratio
```

## 5. 为什么 Score 会打出该策略

- 决策链仍是“强 bubble 惩罚 → `PP=1` → `MBN=1` → 小 MBN 下奖励较大 TP → 满卡得到 `DP=4`”。
- score 没有慢卡变量，所以两张慢卡与四张慢卡的所有候选分数完全相同。
- 因此 score 只能解释参数排名，不能解释“一节点一慢卡为什么更均衡”。

## 6. 来源明确总结

- 四张慢卡均匀覆盖节点时，优先追求 DP replica 结构对称，而不是把慢卡放进多个 PP stage。
- 每节点组成一个 `TP=8` group，四个 group 组成 `DP=4`。
- 设置 `PP=1,MBN=1`，避免多个慢 stage 和无意义的 microbatch 切分。
- 该方案不能恢复绝对性能，只可能降低 replica 间的 straggler skew。

## 7. 进入审查队列的候选

| ID | 候选 | 初始角色 |
|---|---|---|
| F1 | 一节点一张、速度相近时，使每个 DP replica 含相同慢卡结构 | 经验候选 |
| F2 | 只要有四张慢卡就固定使用 `1/8/4/1` | 待拒绝的过度外推 |
| F3 | 四慢卡和两慢卡 score 相同 | 证据候选 |
| F4 | 四个副本一样慢就一定更快 | 待拒绝；混淆均衡与绝对性能 |
| F5 | 比较均匀和非均匀映射的 `replica skew` | 验证候选 |

## 8. 证据边界

- 如果四张慢卡并非一节点一张，经验机制需要重做，score 数值仍不变。
- 没有慢卡 ID、倍率、原始 replica time 和位置扰动结果。
- “skew 更低”是待测机制，不是现有数值已证明的事实。
- 本文件是从合并 raw 来源中整理出的独立场景卡，不修改 raw。

