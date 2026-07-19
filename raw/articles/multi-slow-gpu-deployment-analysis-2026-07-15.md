---
source_url:
source_path: /Users/cookie/Documents/clc/DAG_build/多张慢卡场景部署策略分析.md
ingested: 2026-07-15
sha256: fff1b4381672c268d4dc3619cb49fd64240cae990592c814e0364420dcc53744
original_sha256: 4dddd1033716ef8d7a76802eb8f75bbf91cce299c968bc785faa0ff10bb8ae67
---

# 原始来源：多张慢卡场景部署策略分析

> 这是从 `/Users/cookie/Documents/clc/DAG_build/多张慢卡场景部署策略分析.md` 于 2026-07-15 导入的不可变文本快照。原文件 SHA-256：`4dddd1033716ef8d7a76802eb8f75bbf91cce299c968bc785faa0ff10bb8ae67`。

````markdown
## <span style="color:red;">任务</span>

基于实验场景、Evaluation 得到的最优解，以及演化后的打分策略 Python 代码，分析各评分项如何共同导向当前最优并行策略，并进一步总结两张慢卡和四张慢卡场景下可复用的实际部署经验。

本文严格区分两类结论：

1. **评分公式能够直接表达的偏好**：由代码中的奖励项、惩罚项和约束项定量推导；
2. **结合慢卡分布和 Evaluation 结果得到的部署解释**：用于解释为什么该公式命中的策略在当前硬件场景下有效。

> <span style="color:orange;">重要说明：</span>当前只提供了一份 `score_strategy`。该代码没有读取慢卡数量、慢卡位置或设备计算速度，因此两张慢卡和四张慢卡在评分阶段得到完全相同的策略分数。本文分别分析两个场景，但不会把公式没有显式表达的慢卡规律误写成公式本身已经学到的规律。

---

## 实验场景

共 32 张 GPU 卡：

- 每 8 张卡位于一个节点内；
- 每两个节点、共 16 张卡属于一个亲和组；
- 节点内带宽最高；
- 亲和组内跨节点带宽较高；
- 跨亲和组带宽最低。

### <span style="color:orange;">慢卡设置</span>

#### 两张慢卡场景

两张慢卡分别位于两个亲和组，使两个亲和组中都存在慢卡。

#### 四张慢卡场景

本文按照“慢卡继续分散”的实验逻辑进行解释，即四个节点各有一张慢卡，每个亲和组内有两张慢卡。

> 如果实际四张慢卡的位置不是“一节点一张”，则评分公式的数值分析不变，但后文关于 TP group 和 DP replica 均衡性的部署解释需要按实际卡号映射调整。

### 模型配置与复算条件

为复现当前实验中的评分关系，数值表采用：

```text
num_layers = 32
global_batch_size = 8
total_devices = 32
```

候选策略满足：

```text
PP × TP × DP ≤ 32
```

当前 Evaluation 对应的最优策略为：

```text
PP = 1
TP = 8
DP = 4
micro-batch number = 1
```

---

# <span style="color:red;">一、打分策略代码</span>

```python
def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    total_devices = int(topo_cfg.get("num_gpus", topo_cfg.get("num_devices", 1)))
    active = pp * tp * dp

    # pipeline bubble fraction (1F1B schedule approximation)
    bubble = float(pp - 1) / max(1.0, float(mbn + pp - 1))

    # derive per-microbatch size for memory pressure
    gbs = float(model_cfg.get("global_batch_size", 1))
    microbatch_size = gbs / max(1.0, float(dp * mbn))

    score = 1000.0

    # balance latency risk through pipeline bubble
    score -= 300.0 * bubble

    # penalize idle devices without making utilization the only objective
    score -= 2.0 * max(0, total_devices - active)

    # keep memory pressure visible through the microbatch_size
    score -= 0.04 * microbatch_size

    # tensor-parallel communication grows with the number of microbatches
    score -= 0.15 * tp * mbn

    # mild reward for using tensor and data parallelism when other costs are acceptable
    score += 1.0 * tp + 0.2 * dp

    # prefer even layer distribution across pipeline stages (small imbalance)
    num_layers = int(model_cfg.get("num_layers", 0))
    if num_layers > 0:
        remainder = num_layers % pp
        if remainder != 0:
            imbalance_ratio = float(remainder) / float(num_layers)
            score -= 50.0 * imbalance_ratio

    return float(score)
```

将其写成数学形式：

\[
\begin{aligned}
Score = 1000
&-300\cdot Bubble \\
&-2\cdot Idle \\
&-0.04\cdot MicroBatchSize \\
&-0.15\cdot TP\cdot MBN \\
&+1.0\cdot TP \\
&+0.2\cdot DP \\
&-50\cdot LayerImbalance
\end{aligned}
\]

它表达的总体偏好是：

> **强烈避免流水线气泡，优先使用满 32 张卡；在没有 PP 时倾向较小的 MBN，并在 TP 奖励、DP 奖励、TP×MBN 通信惩罚之间选择一个满卡组合。**

---

# <span style="color:red;">二、各评分项的定量作用</span>

## 1. Pipeline Bubble 是权重最大的惩罚项

```python
bubble = (pp - 1) / (mbn + pp - 1)
score -= 300.0 * bubble
```

当 `mbn=1` 时：

\[
Bubble=\frac{PP-1}{PP}
\]

| PP | MBN | Bubble | Bubble penalty |
| -: | --: | -----: | -------------: |
| 1 | 1 | 0.0000 | 0.00 |
| 2 | 1 | 0.5000 | -150.00 |
| 4 | 1 | 0.7500 | -225.00 |
| 8 | 1 | 0.8750 | -262.50 |
| 16 | 1 | 0.9375 | -281.25 |
| 32 | 1 | 0.9688 | -290.63 |

这说明该公式对深 PP 极其敏感。

例如，从 `PP=1` 增加到 `PP=2`，仅 Bubble 一项就损失 150 分。相比之下：

- TP 从 1 增加到 8，最大只有约 7 分的直接奖励；
- DP 从 1 增加到 4，只有 0.6 分的直接奖励；
- 少用一张 GPU 只损失 2 分。

因此：

> **只要 PP=1 在显存上可行，该公式首先会消灭 PP，而不是通过增加 MBN 去维持深流水线。**

---

## 2. Idle penalty 负责推动满卡

```python
active = pp * tp * dp
score -= 2.0 * max(0, total_devices - active)
```

每空闲一张 GPU 扣 2 分。

以 `PP=1、TP=8、MBN=1` 为例：

| DP | Active GPUs | Idle GPUs | Idle penalty |
| -: | ----------: | --------: | -----------: |
| 1 | 8 | 24 | -48 |
| 2 | 16 | 16 | -32 |
| 4 | 32 | 0 | 0 |

固定 `PP=1、TP=8` 时，从 `DP=2` 增加到 `DP=4`：

- Idle penalty 改善 32 分；
- DP reward 增加 0.4 分；
- microbatch memory penalty 改善约 0.08 分。

总分提高约：

\[
32+0.4+0.08=32.48
\]

因此：

```text
PP=1, TP=8
        ↓
为了使用满32张卡
        ↓
DP=4
```

这里 `DP=4` 主要是由**满卡约束**推出的，而不是因为 `+0.2×DP` 本身足够强。

---

## 3. MBN 在 PP=1 时是单调不利变量

当前最优策略中：

```text
PP = 1
```

因此无论 MBN 取多少：

```python
bubble = 0
```

MBN 不再具有降低流水线气泡的价值，只剩下两项作用：

```python
score -= 0.04 * gbs / (dp * mbn)
score -= 0.15 * tp * mbn
```

在 `TP=8、DP=4、GBS=8` 时：

\[
Score_{MBN相关}=-1.2\cdot MBN-\frac{0.08}{MBN}
\]

第一项随 MBN 线性恶化，第二项虽然随 MBN 增大而减小，但权重非常小。

| MBN | Microbatch size | Memory penalty | TP×MBN penalty | Total score |
| --: | --------------: | -------------: | --------------: | ----------: |
| 1 | 2.000 | -0.080 | -1.20 | **1007.520** |
| 2 | 1.000 | -0.040 | -2.40 | 1006.360 |
| 4 | 0.500 | -0.020 | -4.80 | 1003.980 |
| 8 | 0.250 | -0.010 | -9.60 | 999.190 |
| 16 | 0.125 | -0.005 | -19.20 | 989.595 |
| 32 | 0.0625 | -0.0025 | -38.40 | 970.398 |
| 64 | 0.03125 | -0.00125 | -76.80 | 931.999 |

所以：

> **PP=1 一旦确定，MBN=1 就是该公式明确偏好的最优点，而不是搜索空间下界偶然造成的结果。**

这与原先“一张慢卡时使用高 PP、高 MBN 填流水线”的策略完全相反。

---

## 4. TP 奖励与 TP×MBN 惩罚共同决定 TP 偏好

相关代码为：

```python
score -= 0.15 * tp * mbn
score += 1.0 * tp
```

合并后：

\[
TP\ Term=TP\cdot(1-0.15\cdot MBN)
\]

不同 MBN 下，每增加 1 个 TP 对分数的净影响为：

| MBN | 每增加1个TP的净分数 |
| --: | ------------------: |
| 1 | +0.85 |
| 2 | +0.70 |
| 4 | +0.40 |
| 6 | +0.10 |
| 8 | -0.20 |
| 16 | -1.40 |
| 64 | -8.60 |

这说明：

- 当 MBN 较小时，公式奖励 TP；
- 当 MBN 大于约 6.67 时，TP 由收益项变成成本项；
- 因此该公式会形成“**小 MBN + 较大 TP**”或“**大 MBN + 较小 TP**”的耦合偏好。

当前最优解选择 `MBN=1`，所以 TP 的净系数为：

\[
1-0.15=0.85>0
\]

TP 越大越有利，直到受设备总数与候选范围限制。

---

## 5. 为什么是 TP=8，而不是 TP=1、DP=32？

在 `PP=1、MBN=1` 且使用满 32 张卡时：

```text
TP × DP = 32
```

主要候选为：

| PP | TP | DP | MBN | Score |
| -: | -: | -: | --: | ----: |
| 1 | 1 | 32 | 1 | 1007.240 |
| 1 | 2 | 16 | 1 | 1004.880 |
| 1 | 4 | 8 | 1 | 1004.960 |
| 1 | 8 | 4 | 1 | **1007.520** |

`TP=8, DP=4` 相比 `TP=1, DP=32` 的差值可以逐项展开：

| 变化项 | 分数变化 |
| ------ | -------: |
| TP reward：8 相比 1 | +7.00 |
| TP×MBN penalty 增量 | -1.05 |
| DP reward：4 相比 32 | -5.60 |
| Memory penalty 变化 | -0.07 |
| 总变化 | **+0.28** |

所以最终：

```text
Score(1,8,4,1) - Score(1,1,32,1) = 0.28
```

该公式确实选择：

```text
PP=1, TP=8, DP=4, MBN=1
```

但需要注意：

> **TP=8 只领先 TP=1 约 0.28 分，属于较弱偏好；PP=1 和 MBN=1 才是由大权重评分项强力决定的。**

进一步把 GBS 记为 \(B\)，两者分差为：

\[
\Delta Score=0.35-0.00875B
\]

因此当：

\[
B<40
\]

`TP=8,DP=4` 更高；当 GBS 大于 40 且 `DP=32` 是合法候选时，评分排序可能翻转。

这说明当前 TP/DP 比例对 GBS 和候选空间较敏感。

---

## 6. 为什么不是高 PP 方案？

即使通过增大 MBN 降低 Bubble，高 PP 方案仍然难以追上 `PP=1`。

在相同复算条件下，各类满卡 PP 方案能够达到的较高分数为：

| PP | TP | DP | 较优 MBN | Score | 与最优差距 |
| -: | -: | -: | -------: | ----: | ---------: |
| 1 | 8 | 4 | 1 | **1007.520** | 0.000 |
| 2 | 4 | 4 | 16 | 977.548 | -29.972 |
| 2 | 8 | 2 | 16 | 971.543 | -35.977 |
| 4 | 2 | 4 | 64 | 970.166 | -37.354 |

以 `PP=2,TP=4,DP=4,MBN=16` 为例：

- MBN=16 已将 Bubble 降到约 0.0588；
- 但 Bubble penalty 仍为约 -17.65；
- TP×MBN penalty 为 -9.60；
- 两项合计已损失约 27.25 分。

因此：

> **该公式不是简单地排斥 PP，而是认为“为了降低 PP Bubble 而增加 MBN”也会引入 TP×MBN 成本，最终无 PP 方案更优。**

---

## 7. Layer imbalance 在当前最优解中不起决定作用

```python
remainder = num_layers % pp
score -= 50.0 * remainder / num_layers
```

当前：

```text
num_layers = 32
PP = 1
```

所以：

```text
32 % 1 = 0
```

Layer imbalance penalty 为 0。

而且常见候选 `PP=2、4、8、16、32` 都能整除 32 层，因此该项在当前候选集合中基本不参与排序。

这是一项**安全约束项**，而不是当前最优策略的核心驱动力。

---

# <span style="color:red;">三、两张慢卡场景分析</span>

## 1. 最优策略

```text
PP = 1
TP = 8
DP = 4
MBN = 1
```

其评分项分解为：

| Scoring term | Value |
| ------------ | ----: |
| Base score | +1000.000 |
| Bubble penalty | 0.000 |
| Idle GPU penalty | 0.000 |
| Microbatch-size penalty | -0.080 |
| TP×MBN penalty | -1.200 |
| TP reward | +8.000 |
| DP reward | +0.800 |
| Layer imbalance penalty | 0.000 |
| **Final score** | **1007.520** |

---

## 2. 公式为什么选择这个策略？

决策路径可以写成：

```text
-300×Bubble
    ↓
优先令 PP=1
    ↓
PP=1 后，MBN 不再降低 Bubble
    ↓
-0.15×TP×MBN 使 MBN=1
    ↓
MBN=1 时 TP 的净系数为 +0.85
    ↓
提高 TP 有利
    ↓
TP=8 与单节点8卡规模对齐
    ↓
为了使用满32张卡，DP=4
```

其中只有前四步是评分公式可以直接证明的。

“TP=8 与单节点对齐”是硬件部署解释，因为代码中没有读取：

```text
gpus_per_node
intra-node bandwidth
affinity-group bandwidth
TP group mapping
```

所以公式只是数值上选到了 8，并没有显式判断 TP 是否跨节点。

---

## 3. 两张慢卡下的实际映射

`PP=1,TP=8,DP=4` 可以映射为：

```text
Node 0：8卡 TP group，DP replica 0
Node 1：8卡 TP group，DP replica 1
Node 2：8卡 TP group，DP replica 2
Node 3：8卡 TP group，DP replica 3
```

若两张慢卡分别位于两个亲和组，并分别落在两个节点中，则：

```text
4个TP group中：
2个包含慢卡
2个全部为快卡
```

含慢卡的 TP group 会被慢卡同步拖慢，而 DP 又需要等待所有 replica 完成，因此：

```text
慢 replica 完成时间
        ↓
决定整个 DP step 的完成时间
        ↓
两个纯快卡 replica 会出现等待
```

这说明两张慢卡场景仍然存在明显的 **DP replica imbalance**。

---

## 4. 为什么仍然不使用 PP 隔离两张慢卡？

从实际部署角度看，两张慢卡已经分散到两个亲和组，异构性不再局限于单一区域。

如果采用深 PP：

- 两张慢卡可能形成两个慢 stage；
- 每个 microbatch 都必须经过所有 stage；
- 最慢 stage 决定流水线吞吐；
- 为降低 Bubble 还需要增大 MBN；
- 当前公式又对 `TP×MBN` 施加线性惩罚。

因此，深 PP 不再是“隔离一个局部异常”，而更像是：

```text
构造一条包含多个慢点的长流水线
```

在当前 Evaluation 中，无 PP 的规整 TP/DP 方案更有效。

---

## 5. 两张慢卡场景得到的部署经验

> **当少量慢卡已经跨亲和组分散时，不应机械地继续增加 PP 试图逐卡隔离；若模型能够在单个 TP group 中放下，应优先取消深流水线，将 TP 限制在节点内，再用 DP 扩展到其他节点。**

具体经验为：

```text
PP=1：消除多慢stage和流水线气泡
TP=8：节点内完成高频TP同步
DP=4：用四个节点组成四个模型副本
MBN=1：没有流水线时避免额外microbatch通信开销
```

但两张慢卡分布不均衡时，还应额外关注：

```text
不同DP replica的迭代时间差
快replica等待慢replica的比例
慢卡是否集中污染少数TP group
```

这些信息当前评分公式没有建模。

---

# <span style="color:red;">四、四张慢卡场景分析</span>

## 1. 评分阶段的最优策略

由于当前打分代码没有读取慢卡数量和位置，在模型配置、拓扑规模和候选集合不变时，四张慢卡场景中每个候选策略的 score 与两张慢卡场景完全相同。

因此评分侧仍然选择：

```text
PP = 1
TP = 8
DP = 4
MBN = 1
Score = 1007.520
```

不能从这份代码推出：

```text
2张慢卡 → 一套打分逻辑
4张慢卡 → 另一套打分逻辑
```

真实变化只会出现在后续 Evaluation 的计算时间、同步等待时间和总延迟中。

---

## 2. 四张慢卡均匀分布时的实际映射

若四个节点各有一张慢卡，则 `TP=8,DP=4` 下：

```text
4个TP group中：
每个TP group都包含1张慢卡
```

这会产生两方面影响。

### 第一，所有 TP group 都被慢卡限制

每个 8 卡 TP group 都执行同步算子。一张慢卡变慢后，同组其他 7 张快卡需要等待。

因此：

```text
1张慢卡 × 4个节点
        ↓
4个TP group全部受到影响
```

从单个 replica 的绝对性能看，这比只有两个 group 含慢卡更差。

### 第二，DP replica 之间反而更均衡

两张慢卡场景中：

```text
2个慢replica + 2个快replica
```

四张慢卡均匀分布后：

```text
4个速度近似一致的慢replica
```

虽然每个 replica 都更慢，但 replica 间的时间方差降低，DP 同步中的额外 straggler skew 可能减小。

可以写成：

```text
两张慢卡：平均速度较高，但副本不均衡
四张慢卡：平均速度较低，但副本更均衡
```

因此：

> **四张慢卡均匀分散时，TP=8、DP=4 的价值不在于消除慢卡影响，而在于把异构性均匀复制到每个 DP replica，使所有副本具有相近的执行速度。**

---

## 3. 为什么 PP=1 在四张慢卡时更容易成立？

如果改用高 PP，四张慢卡很可能对应多个慢 stage。

流水线吞吐近似由最慢 stage 决定：

\[
T_{pipeline}\approx \max_i T_{stage_i}
\]

当四张慢卡分散在多个 stage 时：

- 慢 stage 数量增加；
- stage 均衡更难；
- 任一慢 stage 都会限制稳态吞吐；
- 多个慢 stage 还可能扩大 Bubble 和排空时间；
- 为填充流水线增加 MBN，又会触发当前公式的 `TP×MBN` 惩罚。

因此四张慢卡下，高 PP 的“局部隔离收益”进一步降低。

当前最优策略表达的是：

> **与其把四张慢卡放进多个流水线阶段，不如取消 PP，将每个节点构造成结构相同的 8 卡 TP replica，再通过 DP 做规则化扩展。**

---

## 4. 四张慢卡场景得到的部署经验

> **当慢卡已经均匀覆盖所有节点时，应优先追求 replica 间的对称性，而不是试图把所有慢卡隔离到少数 PP stage。**

具体部署经验为：

```text
每个节点放置相同数量的慢卡
每个节点内部组成一个TP=8 group
四个节点组成DP=4
禁用不必要的PP
使用MBN=1避免额外切分开销
```

这种部署相当于把：

```text
硬件异构
```

转化成：

```text
四个结构相同、性能接近的副本
```

它不能恢复慢卡造成的绝对性能损失，但可以减少副本之间的同步等待差异。

---

# <span style="color:red;">五、两张慢卡与四张慢卡的横向对比</span>

| 对比维度 | 两张慢卡 | 四张慢卡均匀分布 |
| -------- | -------- | ---------------- |
| 评分公式是否感知慢卡数量 | 否 | 否 |
| 评分侧最优策略 | PP=1, TP=8, DP=4, MBN=1 | PP=1, TP=8, DP=4, MBN=1 |
| 含慢卡的TP group数量 | 约2个 | 4个 |
| 纯快卡TP group数量 | 约2个 | 0个 |
| DP replica速度分布 | 快慢不均 | 整体较慢但更均匀 |
| 主要问题 | 快replica等待慢replica | 所有replica绝对计算变慢 |
| PP隔离收益 | 已明显下降 | 进一步下降 |
| 主要部署目标 | 减少replica间失衡 | 保持四个replica对称 |

两者的共同策略都是：

```text
无PP + 节点内TP + 节点间DP + 最小MBN
```

但实际含义不同：

```text
两张慢卡：该策略主要避免把多个局部慢点串进深流水线
四张慢卡：该策略主要把慢卡均匀摊入所有DP replica
```

---

# <span style="color:red;">六、该公式真正学到的经验</span>

从评分项本身可以严格推出以下经验。

## 共同点 1：如果 PP=1 可行，就优先消除 Pipeline Bubble

```python
score -= 300.0 * bubble
```

权重 300 远大于其他项，是公式最主要的决策因素。

部署经验：

> **在模型显存允许、单个 TP group 能承载模型时，不应为了隔离分散慢卡而盲目引入深 PP。**

---

## 共同点 2：PP 和 MBN 必须联合考虑

PP 增大后，需要 MBN 增大来降低 Bubble；但当前公式同时惩罚：

```python
-0.15 * TP * MBN
```

因此：

```text
PP增加
  ↓
需要更大MBN填流水线
  ↓
TP×MBN通信惩罚增加
```

部署经验：

> **只有当 PP 带来的显存或慢卡隔离收益足以覆盖 Bubble 与多 microbatch 通信成本时，才应启用 PP。**

---

## 共同点 3：没有 PP 时，不要无意义地增大 MBN

当前公式中 MBN 没有独立奖励项。

当 `PP=1` 时，增加 MBN：

- 不会降低 Bubble；
- 只会轻微降低 microbatch-size penalty；
- 会线性增加 TP×MBN penalty。

部署经验：

> **无流水线训练应从 MBN=1 起步，除非显存、梯度累积或通信重叠明确要求更大的 MBN。**

---

## 共同点 4：优先使用满卡，但满卡不是唯一目标

每空闲一张卡扣 2 分，而 PP=2 的 Bubble penalty 可以达到 150 分。

这意味着公式允许：

```text
为了避免极差的PP结构，牺牲少量利用率
```

但当前 `PP=1,TP=8,DP=4` 恰好能够同时做到：

```text
无Bubble + 满32卡
```

因此成为明显优选。

---

## 共同点 5：TP=8 是“弱命中”，不是强鲁棒规律

当前最优仅比 `TP=1,DP=32` 高 0.28 分。

所以更准确的结论是：

> **该公式强烈学到了 PP=1 和 MBN=1，但只轻度偏好 TP=8、DP=4。**

TP=8 是否能够稳定迁移到其他模型和 GBS，需要依赖：

- TP 候选上限；
- DP 候选范围；
- Global Batch Size；
- TP 是否跨节点；
- 节点内 TP 通信实测；
- 慢卡在 TP group 中的同步拖累。

---

# <span style="color:red;">七、当前公式没有学到的慢卡信息</span>

虽然该 program 可以命中两张和四张慢卡场景的最优组合，但代码中没有以下变量：

```text
slow_gpu_count
slow_gpu_ids
per_gpu_compute_speed
TP group中的最慢卡速度
DP replica的最大/平均计算时间
PP stage的预测执行时间
节点内/亲和组内/跨亲和组通信带宽
TP/DP/PP的实际rank映射
```

因此不能直接得出：

> “该公式通过识别两张或四张慢卡而选择了 TP=8、DP=4。”

更准确的表述是：

> **该公式通过强惩罚 Bubble、轻度鼓励 TP/DP、惩罚空闲 GPU 和 TP×MBN，选择了 PP=1、TP=8、DP=4、MBN=1；这一结构恰好在当前慢卡分布下获得了最佳 Evaluation 延迟。**

这可能是一条真实有效的部署规律，也可能包含一部分候选空间与参数配置带来的偶然命中，需要通过慢卡位置扰动实验进一步验证。

---

# <span style="color:red;">八、建议增加的定量评分项</span>

为了让评分公式真正区分两张和四张慢卡，建议加入以下项。

## 1. TP group straggler penalty

对每个 TP group 估计：

\[
P_{TP-straggler}=\sum_g\left(\max_{r\in g}T_r-\operatorname{avg}_{r\in g}T_r\right)
\]

用于表示组内快卡等待最慢卡的代价。

---

## 2. DP replica imbalance penalty

\[
P_{DP-skew}=\frac{\max_j T_{replica_j}-\operatorname{avg}_j T_{replica_j}}
{\operatorname{avg}_j T_{replica_j}}
\]

该项能够明确区分：

```text
两张慢卡：2个慢replica + 2个快replica
四张慢卡：4个速度相近的慢replica
```

---

## 3. PP slowest-stage penalty

\[
P_{PP-stage}=\frac{\max_iT_{stage_i}}
{\operatorname{avg}_iT_{stage_i}}-1
\]

用于判断 PP 是否真的隔离了慢卡，还是制造了一个或多个流水线瓶颈。

---

## 4. Topology crossing penalty

分别统计：

```text
TP跨节点次数
TP跨亲和组次数
DP跨亲和组通信量
PP跨亲和组激活通信量
```

这样 `TP=8` 才能被明确解释为“节点内 TP”，而不只是一个数值为 8 的候选。

---

# <span style="color:red;">九、最终总结</span>

当前评分策略的核心结构为：

```text
强Bubble惩罚
    +
空闲GPU惩罚
    +
小MBN下的TP奖励
    +
轻量DP奖励
    +
TP×MBN通信惩罚
```

它导向：

```text
PP=1, TP=8, DP=4, MBN=1
```

评分层面的决策过程是：

```text
PP=1：消除权重最大的Bubble惩罚
MBN=1：PP=1后，大MBN只会增加TP×MBN成本
TP=8：MBN=1时TP净收益为正
DP=4：与TP=8共同使用满32张卡
```

两张慢卡场景的部署经验是：

> **慢卡已经跨亲和组分散时，深 PP 很可能形成多个慢 stage；更适合取消流水线，在节点内执行 TP，并通过 DP 扩展，但要警惕快慢 replica 之间的同步等待。**

四张慢卡均匀分布场景的部署经验是：

> **当每个节点都包含慢卡时，应优先构造结构一致的 TP group 和 DP replica，将异构性均匀化；虽然所有副本都会变慢，但可以减少副本间的 straggler skew。**

最终可以将这两个场景概括为：

```text
两张慢卡：避免“多个慢点串入深流水线”
四张慢卡：利用“每个副本相同的慢卡配置”保持同步均衡
共同策略：PP=1 + 节点内TP=8 + 节点间DP=4 + MBN=1
```

但必须保留一个结论边界：

> **这份公式强烈学到了“无 PP、低 MBN”，但没有显式学到慢卡数量与位置；TP=8、DP=4 的慢卡部署经验主要来自 Evaluation 与拓扑映射，而不是评分代码中的设备异构建模。**
````
