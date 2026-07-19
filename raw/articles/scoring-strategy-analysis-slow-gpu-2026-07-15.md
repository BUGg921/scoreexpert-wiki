---
source_url:
source_path: /Users/cookie/Documents/clc/DAG_build/Scoring strategy analysis_快慢卡.md
ingested: 2026-07-15
sha256: d1b1d5fd32beb4b104ed7fe9265515dc0b49228d026fb30f722f008781eee182
original_sha256: 9aca21dad5d3d0ade1b19e2d7f43623272a68cdca4f81db8a6bf5ff27f1d5c0e
---

# 原始来源：Scoring strategy analysis_快慢卡

> 这是从 `/Users/cookie/Documents/clc/DAG_build/Scoring strategy analysis_快慢卡.md` 于 2026-07-15 导入的不可变文本快照。原文件 SHA-256：`9aca21dad5d3d0ade1b19e2d7f43623272a68cdca4f81db8a6bf5ff27f1d5c0e`。

````markdown
## <span style="color:red;">任务</span>
基于实验场景，最优解，以及打分策略python代码，进行经验总结

人工跟ChatGPT对话总结的思路是：看打分策略代码中各项得分的变化，分析出为何可以从当前打分策略得到当前的最优解，从而总结出在当前实验场景下的部署策略。

## 实验场景
共32 张 GPU 卡。每 8 张卡在一个节点内（即一个服务器内），16 张卡（每两个节点）属于一个亲和组。

节点内的带宽最高，亲和组内的带宽较高，跨亲和组的带宽较低。

### <span style="color:orange;">慢卡设置</span>

设置了一张慢卡（第7张卡），慢卡相比其他正常卡计算速度慢一倍

## 最优解
PP = 16, 
TP = 2, 
DP = 1, 
micro-batch number = 64

<span style="color:red;">
是否micro-batch number的最大值设成了 64，所以后续两个最优策略都搜到了 64，但其实这个值还可以更大，只是可能就不合理了
</span>


# <span style="color:red;">一、打分策略代码一</span>

策略一的主要结构是：

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

它表达的偏好是：

> **TP 越大越亏，DP 越大越亏，PP 可以接受，只要 mbn 足够大。**

---

## 1. 为什么 DP=1？

策略一里 DP 的惩罚是：

```python
dp_overhead = max(0, dp - 1)
score -= 12.0 * dp_overhead
```

所以：

| DP | DP penalty |
| -: | ---------: |
|  1 |          0 |
|  2 |        -12 |
|  4 |        -36 |
|  8 |        -84 |

这说明策略一非常不喜欢多副本 DP。

在快慢卡场景下，这个设定也有直觉：**DP 是同步副本，如果某个 replica 里有慢卡，会拖慢整个 DP 同步。**

所以搜索器会把 DP 压到：

```text
DP = 1
```

---

## 2. 为什么不是 TP=8, PP=4？

在 32 卡、DP=1 的情况下，要用满 GPU，需要：

```text
PP × TP = 32
```

可选组合主要是：

| PP | TP | DP |
| -: | -: | -: |
| 32 |  1 |  1 |
| 16 |  2 |  1 |
|  8 |  4 |  1 |
|  4 |  8 |  1 |

假设 `mbn=64`，并且先忽略各方案共有的 memory 项、idle 项、cross-node 项，只看最关键的：

```python
-6.0 * tp
-55.0 * bubble
```

其中：

```python
bubble = (pp - 1) / (mbn + pp - 1)
```

计算如下：

| PP | TP |        bubble | TP penalty | bubble penalty |       合计惩罚 |
| -: | -: | ------------: | ---------: | -------------: | ---------: |
| 32 |  1 | 31/95 = 0.326 |         -6 |         -17.95 |     -23.95 |
| 16 |  2 | 15/79 = 0.190 |        -12 |         -10.44 | **-22.44** |
|  8 |  4 |  7/71 = 0.099 |        -24 |          -5.42 |     -29.42 |
|  4 |  8 |  3/67 = 0.045 |        -48 |          -2.46 |     -50.46 |

所以策略一会选：

```text
PP=16, TP=2
```

原因很清楚：

* `TP=8, PP=4` 虽然 bubble 小，但 TP 惩罚太大；
* `TP=1, PP=32` 虽然 TP 惩罚小，但 PP 太深，bubble 惩罚又变大；
* `TP=2, PP=16` 是二者之间的折中点。

也就是说：

> **TP=2 是“低 TP 成本”和“不过深 PP bubble”之间的平衡点。**

---

## 3. 为什么 mbn=64？

策略一里 mbn 同时有三个作用。

### 第一，它降低 bubble：

```python
bubble = (pp - 1) / (mbn + pp - 1)
```

mbn 越大，bubble 越小。

以 PP=16 为例：

| mbn |        bubble |
| --: | ------------: |
|   8 | 15/23 = 0.652 |
|  16 | 15/31 = 0.484 |
|  32 | 15/47 = 0.319 |
|  64 | 15/79 = 0.190 |

---

### 第二，它降低 microbatch_size：

```python
microbatch_size = global_bs / (dp * mbn)
score -= 0.4 * microbatch_size
```

mbn 越大，单个 microbatch 越小，memory penalty 越小。

---

### 第三，它还有线性正奖励：

```python
score += 0.3 * mbn
```

所以 mbn 越大，分数越高。

因此在策略一里：

> **mbn 是单调有利变量。**

<span style="color:orange;">如果候选集合最大是 64，那么它就会选 64；如果允许 128，它很可能继续选 128。</span>

所以：

```text
mbn = 64
```

本质上是搜索空间上界导致的结果。

---

# <span style="color:red;">二、打分策略代码二</span>

策略二是：

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

它和策略一非常像，但是 DP 的处理方式稍微不同。

---

## 1. 为什么 DP=1？

策略二直接惩罚：

```python
score -= 7.0 * dp
```

所以：

| DP | DP penalty |
| -: | ---------: |
|  1 |         -7 |
|  2 |        -14 |
|  4 |        -28 |
|  8 |        -56 |

DP 仍然是纯成本项，没有任何正收益项。

因此最优自然会选择最小 DP：

```text
DP = 1
```

---

## 2. 为什么还是 TP=2, PP=16？

同样看 32 卡、DP=1、mbn=64 的情况：

| PP | TP | bubble | TP penalty | bubble penalty | DP penalty |       合计惩罚 |
| -: | -: | -----: | ---------: | -------------: | ---------: | ---------: |
| 32 |  1 |  0.326 |         -6 |         -16.32 |         -7 |     -29.32 |
| 16 |  2 |  0.190 |        -12 |          -9.49 |         -7 | **-28.49** |
|  8 |  4 |  0.099 |        -24 |          -4.93 |         -7 |     -35.93 |
|  4 |  8 |  0.045 |        -48 |          -2.24 |         -7 |     -57.24 |

策略二同样选：

```text
PP=16, TP=2
```

原因和策略一一样：

* TP=8 的 TP penalty 太大；
* TP=1 的 PP bubble 太大；
* TP=2 是折中点。

---

## 3. 策略二为什么也选 mbn=64？

因为策略二也有：

```python
score += 0.3 * mbn
```

同时：

```python
bubble = (pp - 1) / (mbn + pp - 1)
microbatch_size = global_bs / (dp * mbn)
```

所以 mbn 增大时：

* bubble 下降；
* memory penalty 下降；
* 线性 reward 上升。

因此 mbn 仍然是单调有利的。

所以：

```text
mbn = 64
```

也是边界解。

---

# <span style="color:red;">三、为什么这个策略适合快慢卡场景？</span>

快慢卡的关键问题是 **straggler effect**。

如果有一张卡慢一倍，那么同步组越大，它拖慢的范围越大。

---

## 1. 大 TP 会放大慢卡影响

例如：

```text
TP = 8
```

如果慢卡在这个 TP group 里，那么这个 8 卡 tensor-parallel group 都要等慢卡。

所以慢卡影响范围是：

```text
1 张慢卡 → 拖慢 8 张卡
```

---

## 2. 小 TP 会缩小慢卡污染范围

如果：

```text
TP = 2
```

慢卡最多只拖慢一个 2 卡 TP group。

影响范围变成：

```text
1 张慢卡 → 拖慢 2 张卡
```

所以快慢卡场景下，降低 TP 是合理的。

---

## 3. PP=16 可以把慢卡隔离到局部 stage

在：

```text
PP=16, TP=2, DP=1
```

下：

```text
32 GPUs = 16 pipeline stages × 2 GPUs per stage
```

慢卡只影响其中一个 stage。

如果系统支持 layer rebalancing，还可以给慢卡所在 stage 分配更少层数。

所以这个配置的直觉是：

> **用小 TP 限制同步污染范围，用高 PP 把慢卡隔离到局部 pipeline stage。**

---

# <span style="color:red;">四、两个策略的共同点</span>

两个策略虽然权重略有不同，但共同结构非常明显。

---

## 共同点 1：TP 是成本，不是收益

两个策略都有：

```python
score -= 6.0 * tp
```

所以 TP 越大越亏。

这和之前的正常同构场景不同。之前你是奖励 TP：

```python
score += 1.0 * tp
```

现在变成惩罚 TP，说明系统已经从：

```text
同构场景：利用 TP 提升计算并行
```

切换成：

```text
异构场景：限制 TP 防止慢卡拖累同步组
```

---

## 共同点 2：DP 是成本，不是扩展收益

策略一：

```python
score -= 12.0 * max(0, dp - 1)
```

策略二：

```python
score -= 7.0 * dp
```

因此两个策略都压制 DP。

这反映了快慢卡场景下的一个经验：

> **DP 副本越多，同步等待和 straggler 风险越大。**

所以最终得到：

```text
DP = 1
```

---

## 共同点 3：PP bubble 被大 mbn 稀释

两个策略都使用类似：

```python
bubble = (pp - 1) / (mbn + pp - 1)
```

这意味着：

> PP 本身不是绝对不能用，只要 mbn 足够大，PP bubble 就可以被压低。

因此 PP=16 虽然很深，但在 mbn=64 时 bubble 约为：

```text
15 / 79 ≈ 0.19
```

乘上 50 或 55 后，惩罚约为 9.5 到 10.4，仍然可以接受。

---

## 共同点 4：mbn 被设计成单调有利变量

两个策略都有：

```python
score += 0.3 * mbn
```

同时 mbn 还会降低 bubble 和 microbatch_size。

所以 mbn 变大有三重好处：

```text
mbn ↑ → bubble ↓
mbn ↑ → microbatch_size ↓
mbn ↑ → score reward ↑
```

因此只要搜索空间允许，mbn 就会冲到最大值。

所以：

```text
mbn=64
```

不是自然物理最优，而是 score 诱导出来的边界解。

---

## 共同点 5：满卡仍然被偏好

两个策略都有：

```python
score -= 5.0 * max(0, total_gpus - active)
```

所以系统仍然倾向使用满 32 卡。

在 DP=1、TP=2 的情况下，要用满卡，只能：

```text
PP = 32 / (TP × DP) = 32 / 2 = 16
```

这就是为什么：

```text
TP=2, DP=1
```

会自然推出：

```text
PP=16
```

---

# <span style="color:red;">五、最终总结</span>

这两个策略共同学到的是：

> **在快慢卡场景下，不要用大 TP 和大 DP 去扩大同步组；应该用小 TP 限制慢卡污染范围，用 DP=1 避免多副本同步等待，用高 PP 使用满 32 卡，并用大 mbn 填充深 pipeline。**

所以最优解：

```text
PP=16, TP=2, DP=1, mbn=64
```

可以理解为：

```text
小 TP：缩小慢卡同步污染范围
低 DP：避免多副本 straggler 同步
高 PP：用 pipeline 吃满 32 卡并隔离慢卡
大 mbn：隐藏 PP bubble
```

不过需要注意：这两个 score 仍然没有直接写入“第 7 张卡慢一倍”这样的设备级变量。它们是通过 **惩罚 TP/DP、鼓励 PP+mbn** 间接表达快慢卡场景偏好的。如果要更真实，最好进一步加入：

```text
TP group 内慢卡 straggler penalty
pipeline stage time imbalance penalty
慢卡所在 stage 的 layer rebalance penalty
大 mbn 的 latency / kernel overhead penalty
```

这样搜索结果会更接近真实系统运行性能。


# <span style="color:red;">六、不同快慢卡数量性能对比</span>

<span style="color:blue;">
问题：
如果另外一个亲和组多一张慢卡，也就是有2张慢卡，分别在2个亲和组里面，此时最优解变回了 PP=1, TP=8, DP=4, mbn=1，为什么？
</span>

这个现象非常有意思，说明你的系统发生了第二次“策略相变”。

先说核心结论：

> **一张慢卡时，系统倾向于“隔离慢卡”，所以选 PP=16, TP=2, DP=1, mbn=64；
> 两张慢卡分别落在两个亲和组后，慢卡不再是局部异常，而变成了全局分布式异构，此时“隔离策略”失效，系统重新偏向 PP=1, TP=8, DP=4, mbn=1 这种同步型满卡方案。**

---

# 1. 一张慢卡时，为什么 PP-heavy 有利？

一张慢卡只在一个亲和组里时，它是一个**局部异常点**。

这时系统最自然的想法是：

> 把慢卡影响限制在尽可能小的范围内。

所以会倾向于：

```text
TP=2
```

因为 TP=2 时，慢卡最多拖慢一个 2 卡 TP group。

同时为了用满 32 张卡：

```text
PP × TP × DP = 32
```

如果：

```text
TP=2, DP=1
```

那就必须：

```text
PP=16
```

所以一张慢卡时的策略是：

```text
PP=16, TP=2, DP=1
```

它的含义是：

> **用小 TP 缩小慢卡同步污染范围，用高 PP 把慢卡隔离到局部 pipeline stage。**

这就是“隔离慢卡”的策略。

---

# 2. 两张慢卡分别在两个亲和组时，为什么隔离策略失效？

现在慢卡不再是一个局部异常，而是分布到了两个亲和组里。

也就是说，原来系统面对的是：

```text
一个亲和组有慢卡，另一个亲和组基本正常
```

现在变成：

```text
两个亲和组都有慢卡
```

这会改变最优策略。

---

## 2.1 PP=16 会出现多个慢 pipeline stage

在：

```text
PP=16, TP=2, DP=1
```

下，32 张卡被切成：

```text
16 个 pipeline stage × 每个 stage 2 张 GPU
```

如果两张慢卡分别落在两个亲和组里，那么它们很可能对应到两个不同的 pipeline stage。

于是原来只有：

```text
1 个慢 stage
```

现在变成：

```text
2 个慢 stage
```

而 pipeline 的问题是：

> **每个 microbatch 都必须顺序经过所有 stage。**

所以只要 pipeline 里有慢 stage，它就会影响整条流水线。

一张慢卡时，PP=16 还能把慢卡隔离成一个局部 bottleneck；但两张慢卡分布到两个亲和组后，pipeline 里出现多个 bottleneck，隔离收益明显下降。

---

## 2.2 深 PP 的收益被慢 stage 抵消

PP=16 的代价包括：

```text
pipeline bubble
stage imbalance
activation transfer
microbatch scheduling complexity
```

一张慢卡时，系统愿意承担这些代价，因为它换来了“慢卡隔离”。

但两张慢卡时，隔离不再干净：

```text
PP=16 不再是隔离一个坏点
而是构造了一条包含多个慢点的长流水线
```

于是 PP=16 的收益下降，而成本仍然存在。

这时系统就会重新偏向：

```text
PP=1
```

因为：

```text
PP=1 没有 pipeline bubble
PP=1 没有 stage imbalance
PP=1 不需要大量 microbatch 填流水线
```

---

# 3. 为什么会回到 TP=8？

当 PP 被压回 1 后，要用满 32 张卡，就需要：

```text
TP × DP = 32
```

同时你的拓扑是：

```text
每个节点 8 张卡
```

所以最自然的 TP 选择就是：

```text
TP=8
```

原因是：

> **TP=8 正好限制在单节点内，不跨节点。**

这点非常重要。

```text
TP=8 <= gpus_per_node=8
```

所以不会触发跨节点 TP 通信。

因此 TP=8 是一个非常自然的拓扑对齐点：

```text
节点内做 TP
节点间做 DP
```

这就是经典的同构/近似同构场景部署经验：

```text
intra-node TP
inter-node DP
```

---

# 4. 为什么 DP=4？

因为：

```text
PP=1
TP=8
total_gpus=32
```

所以：

```text
DP = 32 / TP = 4
```

也就是：

```text
DP=4
```

这对应 4 个 8 卡 TP group。

直观上就是：

```text
4 个节点 / 4 个 TP group / 4 个 DP replica
```

这是一种非常规整的拓扑映射。

---

# 5. 为什么 mbn=1？

当：

```text
PP=1
```

时，pipeline 不存在，所以：

```text
bubble = 0
```

这时 microbatch 不再需要承担“填充流水线”的作用。

也就是说，mbn 从：

```text
pipeline filler
```

退化成：

```text
纯粹的 batch 切分 / gradient accumulation 参数
```

如果系统里有任何现实开销项，例如：

```text
microbatch scheduling overhead
kernel launch overhead
latency overhead
activation buffer overhead
```

那么 mbn 就会自然回到最小值：

```text
mbn=1
```

所以：

> **PP=1 时，mbn=1 是非常合理的默认解。**

---

# 6. 一张慢卡 vs 两张慢卡的本质区别

可以用一句话概括：

> **一张慢卡时，问题是“局部异常”，适合隔离；两张慢卡分布到两个亲和组后，问题变成“全局异构”，隔离收益下降，均衡同步方案反而更稳。**

---

更具体地说：

| 场景             | 最优倾向        | 原因                   |
| -------------- | ----------- | -------------------- |
| 1 张慢卡，集中在一个亲和组 | PP-heavy    | 可以把慢卡隔离到局部 stage     |
| 2 张慢卡，分别在两个亲和组 | TP/DP-heavy | 两个亲和组都慢，PP 隔离不再有效    |
| 慢卡很少且局部化       | 小 TP + 高 PP | 限制污染范围               |
| 慢卡分布式存在        | 大 TP + DP   | 拓扑对齐、减少 pipeline 复杂度 |

---

# 7. 为什么这可以理解为“从隔离到均衡”的切换？

一张慢卡时：

```text
目标 = isolate
```

所以系统选择：

```text
小 TP + 高 PP
```

两张慢卡分布在两个亲和组时：

```text
目标 = balance
```

所以系统选择：

```text
节点内 TP=8 + 跨节点 DP=4
```

这两个策略的思想不同：

| 策略                | 思想   |
| ----------------- | ---- |
| PP=16, TP=2, DP=1 | 隔离慢卡 |
| PP=1, TP=8, DP=4  | 均衡拓扑 |

---

# 8. 更直观的解释

一张慢卡时，PP=16 像是：

```text
把坏点切出来，单独放进一个小 stage
```

两张慢卡分别在两个亲和组时，PP=16 变成：

```text
整条流水线里有多个坏点
```

这时每个 microbatch 都要经过这些坏点，流水线的好处下降。

于是系统宁愿回到：

```text
不做 pipeline
直接用节点内 TP + 节点间 DP
```

也就是：

```text
PP=1, TP=8, DP=4
```

---

# 9. 最终总结

这个现象说明你的搜索器可能学到了一个很重要的部署经验：

> **当异构性是局部的，使用 PP 隔离慢卡；当异构性在多个亲和组中分布，使用 TP/DP 进行拓扑均衡，避免深 pipeline 被多个慢 stage 拖累。**

所以这次最优解变回：

```text
PP=1, TP=8, DP=4, mbn=1
```

可以解释为：

```text
两张慢卡分散在两个亲和组
        ↓
PP 隔离收益下降
        ↓
深 pipeline 出现多个慢 stage
        ↓
mbn=64 的填流水线收益不足以抵消复杂度
        ↓
系统回到无 pipeline 结构
        ↓
节点内 TP=8，跨节点 DP=4
        ↓
mbn=1
```

一句话：

> **一张慢卡时，最优策略是“隔离”；两张慢卡跨亲和组分布时，最优策略变成“均衡”。**
````
