---
source_url:
source_path: /Users/cookie/Documents/clc/DAG_build/32卡基线_score_strategy_分析.md
ingested: 2026-07-13
sha256: eb5f2486a2181478da50d40837221d6a6f43068e955be7ad8529f86bd00bccf7
original_sha256: a445f9654b5cf16e30cb4a4d0b0b20bcc336bade358442630d57f593540bc88c
---

# 原始来源：32 卡基线 score strategy 分析

> 这是从 `/Users/cookie/Documents/clc/DAG_build/32卡基线_score_strategy_分析.md` 于 2026-07-13 导入的不可变快照。原文件 SHA-256：`a445f9654b5cf16e30cb4a4d0b0b20bcc336bade358442630d57f593540bc88c`。

````markdown
# 32 卡基线场景 score strategy 分析

## 任务

基于用户给出的 32 卡拓扑和 scoring function，解释该 score 为什么会得到当前评分最优解，并沉淀可复用部署经验、适用边界和下一步仿真建议。

## 实验场景

```text
总 GPU = 32
每节点 = 8 卡
每亲和组 = 16 卡 = 2 个节点
节点内带宽最高
亲和组内带宽较高
跨亲和组带宽较低
慢卡信息 = 未提供，本文按同构 32 卡场景分析
```

## 分析假设

用户没有给出完整搜索空间和 `micro` 的定义。为了让推导可复查，本文采用以下口径：

```text
active = pp * tp * dp
active <= 32
tp <= 8 作为拓扑硬约束
mbn >= 1
bubble = (pp - 1) / (mbn + pp - 1), pp > 1；pp=1 时 bubble=0
```

关键说明：

- score 本身没有 `tp_cross` 项，因此如果不把 `tp <= 8` 当作搜索约束，跨节点 TP 候选可能被错误保留。
- `micro` 和 `mbn` 在公式中是两个变量。本文不假设它们是同一个量；候选表中的关键分数主要展示除 `micro` 外的决策项。若 `micro` 由 batch、DP、MBN 派生，需要用实际定义重算精确总分。

## 最优解

在 `tp <= 8`、满 32 卡优先、常见因子候选下，该 score 直接导向：

```text
PP = 1
TP = 8
DP = 4
MBN = 1
active = 32
```

这是给定 score 和上述搜索约束下的评分最优；真实硬件最优仍需要 Evaluation 或实测验证。

# 一、当前 score

```python
score = 1000.0
score -= 50.0 * bubble
score -= 2.0 * max(0, total - active)
score += 10.0 * micro / (micro + 10.0)
score += 1.0 * tp + 0.2 * dp
score -= 0.9 * abs(tp - dp)
score -= 0.5 * (mbn - 1) * (mbn - 1)
```

## 1. 该 score 的主要结构

一句话概括：

```text
强烈避免 pipeline bubble 和大 MBN；倾向满卡；在 PP=1、MBN=1 后，通过 TP/DP 耦合项在节点内 TP 和跨节点 DP 之间选一个不过度失衡的满卡形状。
```

评分项拆解：

| 项 | 代码 | 强度 | score 直接含义 |
| --- | --- | --- | --- |
| Pipeline bubble | `-50 * bubble` | 主导项 | 只要没有 PP 补偿收益，`PP=1` 很自然 |
| 空闲 GPU | `-2 * idle` | 中等 | 倾向用满 32 卡，但不是绝对硬约束 |
| micro reward | `+10*micro/(micro+10)` | 饱和奖励 | 奖励 `micro`，但上限不足 10 分 |
| TP/DP throughput | `+tp + 0.2*dp` | 中等 | 偏好更多 TP，轻微奖励 DP |
| TP/DP balance | `-0.9*abs(tp-dp)` | 中等 | 压制极端 TP-only 或 DP-only |
| MBN | `-0.5*(mbn-1)^2` | 强单调惩罚 | 直接把 `MBN` 推向 1 |

## 2. 最优解推导：围绕 score 主导项回答“为什么”

### 为什么优先 `PP=1`

`PP` 只通过 bubble 被惩罚，没有任何直接奖励或 overlap 奖励：

```text
score -= 50 * bubble
```

当 `PP=1` 时：

```text
bubble = 0
```

当 `PP>1` 且 `MBN=1` 时：

```text
bubble = (pp - 1) / pp
```

例如：

| PP | MBN | bubble | bubble penalty |
| -: | --: | -----: | -------------: |
| 1 | 1 | 0 | 0 |
| 2 | 1 | 0.500 | -25.0 |
| 4 | 1 | 0.750 | -37.5 |
| 8 | 1 | 0.875 | -43.75 |

由于没有深 PP 的补偿项，`PP=1` 是该 score 的第一层结构偏好。

### 为什么 `MBN=1`

`MBN` 有二次惩罚：

```text
score -= 0.5 * (mbn - 1)^2
```

当 `PP=1` 后，`bubble=0`，增大 `MBN` 不再降低 pipeline bubble，只剩下二次惩罚。

| MBN | MBN penalty |
| --: | ----------: |
| 1 | 0 |
| 2 | -0.5 |
| 4 | -4.5 |
| 8 | -24.5 |
| 16 | -112.5 |

因此 `MBN=1` 不是搜索边界偶然，而是该公式明确偏好的最优点。

### 为什么要满 32 卡

空闲 GPU 惩罚为：

```text
score -= 2 * (32 - active)
```

这使少卡候选必须用更好的 TP/DP 项补回 idle loss。当前 score 的 TP/DP 项幅度通常不足以补偿大量闲卡。例如 `PP=1,TP=8,DP=2` 只用 16 卡，会先被扣：

```text
idle penalty = -2 * 16 = -32
```

而满卡候选 `PP=1,TP=8,DP=4` 不承担该项。因此该 score 在当前场景下优先使用满 32 卡。

### 为什么是 `TP=8,DP=4`，而不是其它满卡组合

固定 `PP=1`、`MBN=1`、`active=32` 后，核心只剩下：

```text
TP/DP term = tp + 0.2 * dp - 0.9 * abs(tp - dp)
```

在 `tp <= 8` 的拓扑约束下，满卡候选主要是：

| PP | TP | DP | 关键 score 项：`tp + 0.2dp - 0.9abs(tp-dp)` | 结论 |
| -: | -: | -: | -------------------------------------------: | --- |
| 1 | 1 | 32 | -20.5 | DP 过大，失衡惩罚极重 |
| 1 | 2 | 16 | -7.4 | DP 仍过大 |
| 1 | 4 | 8 | 2.0 | 可行但 TP 偏小 |
| 1 | 8 | 4 | 5.2 | 最优 |

代数上：

```text
tp >= dp:
tp + 0.2dp - 0.9(tp-dp) = 0.1tp + 1.1dp

tp < dp:
tp + 0.2dp - 0.9(dp-tp) = 1.9tp - 0.7dp
```

这说明该项不是单纯奖励 TP，也不是单纯奖励 DP，而是在压制 `DP >> TP` 的同时，偏好节点内较高 TP。结合 `tp <= 8` 和 `tp*dp=32`，它落到：

```text
TP=8, DP=4
```

### 为什么不是深 PP 候选

即使深 PP 也可以满 32 卡，它会立刻承担 bubble 惩罚。关键反例：

| PP | TP | DP | MBN | 关键项 | 不含 micro 的关键增量 |
| -: | -: | -: | --: | --- | --------------------: |
| 1 | 8 | 4 | 1 | 无 bubble，TP/DP term=5.2 | 5.2 |
| 2 | 4 | 4 | 4 | bubble 降到 0.2，但 MBN penalty=-4.5 | -9.7 |
| 2 | 8 | 2 | 4 | TP/DP term=3.0，bubble 与 MBN 仍扣分 | -11.5 |
| 4 | 4 | 2 | 4 | bubble=3/6，TP/DP term=2.6 | -26.4 |

深 PP 若用小 MBN，bubble 太大；若提高 MBN，二次 MBN 惩罚又上升。该 score 没有 overlap bonus，因此深 PP 很难胜过 `PP=1`。

## 3. 当前场景解释：score 之外还需要哪些拓扑或 Evaluation 证据

拓扑解释：

```text
TP=8:
  正好落在单节点 8 卡高速通信域内，避免 TP 跨节点。

DP=4:
  用 4 个节点/副本补齐 32 卡，DP 通信跨节点但频率通常低于 TP layer 内通信。

PP=1:
  避免 pipeline bubble、stage imbalance 和跨阶段 activation 传输。

MBN=1:
  没有 pipeline 时，大 MBN 没有填 bubble 的价值，反而被 score 二次惩罚。
```

这些拓扑解释需要 Evaluation 验证。该 score 本身没有显式建模：

```text
TP 跨节点惩罚；
DP all-reduce 的真实拓扑；
亲和组内和跨亲和组带宽差异；
模型显存是否允许 PP=1；
micro 的真实定义。
```

## 公式能证明什么，不能证明什么

能证明：

```text
1. 在 tp<=8、PP/TP/DP 满卡因子候选下，PP=1,TP=8,DP=4,MBN=1 是 score 最优。
2. PP=1 来自 bubble 只有惩罚、没有补偿奖励。
3. MBN=1 来自二次惩罚中心点。
4. TP=8,DP=4 来自满卡约束、tp<=8 和 TP/DP 耦合项。
```

不能证明：

```text
1. TP=8 是任何拓扑下的通用最优。
2. 如果允许 TP 跨节点，score 能自动规避跨节点 TP。
3. PP=1 在显存不足或模型很深时仍可行。
4. micro 与 mbn 的关系。
5. DP=4 的真实 all-reduce 开销是否被低估。
```

# 二、部署经验更新

## 场景描述

- 当前场景：`32卡 / 8卡每节点 / 16卡每亲和组 / 无慢卡信息 / score 无 tp_cross 项 / tp<=8 作为搜索硬约束`。
- 与旧场景的差异：这是同构 32 卡基线场景，可作为后续单慢卡、多慢卡和慢网络场景的对照点。
- 适用边界：适用于模型显存允许 `PP=1`、`TP=8` 不跨节点、`MBN=1` 不违反 batch 或吞吐要求的情况。

## 部署经验

1. 在 `32卡/8卡每节点/同构或未建模异构/TP硬限制在节点内` 的场景下，把 `PP=1,TP=8,DP=4,MBN=1` 作为第一候选；它的共同评分决策链是：`bubble` 消灭 PP，`MBN` 二次惩罚压到 1，满卡项要求 `tp*dp=32`，TP/DP 耦合项在 `tp<=8` 下选择 `8:4`。
2. 如果 `PP=1,TP=8,DP=4,MBN=1` 在 Evaluation 中失败，优先检查三个条件：`TP=8` 是否真的只在节点内、模型是否能在 `PP=1` 下放入显存、`DP=4` 跨节点 all-reduce 是否成为瓶颈。
3. 如果后续场景加入慢卡或慢网络，不要直接沿用该策略；要把 `PP=16,TP=2,DP=1`、`PP=4,TP=8,DP=1`、允许闲卡或降低 DP 的候选加入 Top-K 比较。

## 证据

- score 直接证据：`PP=1` 无 bubble；`MBN=1` 无二次惩罚；`TP=8,DP=4` 的 TP/DP term 为 `5.2`，高于 `TP=4,DP=8` 的 `2.0`。
- Evaluation 或拓扑证据：`TP=8` 正好匹配单节点 8 卡高速域；`DP=4` 用跨节点副本补齐 32 卡。
- 与旧经验的关系：作为正常 32 卡基线，后续异构场景要判断是保留该结构，还是被慢卡隔离、慢网络局部性、显存瓶颈覆盖。
- 反例候选：`PP=1,TP=4,DP=8,MBN=1`、`PP=2,TP=4,DP=4,MBN=4`、`PP=1,TP=8,DP=2,MBN=1`。
- 仍缺证据：真实 `micro` 定义、显存可行性、DP all-reduce latency、跨亲和组带宽对 DP 的影响。

# 三、经验缺口与下一步仿真建议

- 当前已覆盖的经验单元：
  - 慢卡数量：0 或未建模；
  - 拓扑：32 卡、8 卡每节点、16 卡每亲和组；
  - 并行形态：`PP=1`、节点内 `TP=8`、跨节点 `DP=4`、`MBN=1`；
  - score 形态：bubble 惩罚、idle 惩罚、TP/DP 耦合、MBN 二次惩罚。

- 仍缺的关键经验：
  - `micro` 的实际定义和取值范围；
  - `TP=8` 是否始终能映射在单节点内；
  - `DP=4` 在亲和组内/跨亲和组 all-reduce 的真实成本；
  - 模型显存是否允许 `PP=1`；
  - 当出现慢卡、慢网络或层数不均衡时，是否会从 `PP=1` 翻转到深 PP 或低 DP。

- 优先仿真的场景：
  1. **显存边界仿真**：固定 32 卡拓扑，增加模型规模直到 `PP=1` 接近 OOM，验证 `PP=1,TP=8,DP=4` 何时被 `PP=2/4` 覆盖。
  2. **DP 跨域成本仿真**：比较 `DP=4` 的跨节点/跨亲和组 all-reduce latency，验证该 score 是否低估 DP 通信。
  3. **TP 跨节点反例仿真**：允许 `TP=16/32` 进入候选，验证缺少 `tp_cross` 项是否会产生危险高分候选。
  4. **MBN 扫描仿真**：测试 `MBN={1,2,4,8}`，验证二次 MBN 惩罚是否与真实 latency 一致。
  5. **单慢卡插入仿真**：在第 7 张卡半速时比较 `PP=1,TP=8,DP=4,MBN=1` 与小 TP/深 PP 候选，验证同构基线何时被异构瓶颈覆盖。

# 四、边界条件与仍需验证

该 score 的最大边界是没有显式拓扑跨域项。`TP=8,DP=4` 的结论依赖 `tp<=8` 搜索约束，而不是 score 自动学到节点内带宽最高。若实际搜索器允许 `TP>8`，应补充 `tp_cross` 惩罚或硬过滤。

另一个边界是 `micro` 未定义。当前推导把 `micro` 和 `mbn` 分开处理；若 `micro` 实际由 `DP`、`MBN` 或 global batch 派生，必须在候选表中加入该项后重新计算精确分数。
````
