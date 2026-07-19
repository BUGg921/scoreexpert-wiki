---
source_url:
source_path: /Users/cookie/Documents/clc/DAG_build/Scoring strategy analysis.md
ingested: 2026-07-14
sha256: 62dbc843380418bbaacbbc6762c1cecddf37308218f3471a2e60a2f743c8bef7
original_sha256: 466feeb3687d200c4ef4c1e4e0125ca0754f9ab4da5bcf2bd83548287349f1f5
embedded_source_sha256: 92a30f5ebc82fcae67e4461ccb368bda23821e26458df8bdf5b8781b7c77366b
normalization: crlf-to-lf-and-final-newline
---

# 原始来源：Scoring strategy analysis

> 这是从 `/Users/cookie/Documents/clc/DAG_build/Scoring strategy analysis.md` 于 2026-07-14 导入的不可变文本快照。原文件 SHA-256：`466feeb3687d200c4ef4c1e4e0125ca0754f9ab4da5bcf2bd83548287349f1f5`。原文件使用 CRLF 且末尾无换行；快照正文统一为 LF 并补充末尾换行。

````markdown
## <span style="color:red;">任务</span>
基于实验场景，最优解，以及打分策略python代码，进行经验总结

人工跟ChatGPT对话总结的思路是：看打分策略代码中各项得分的变化，分析出为何可以从当前打分策略得到当前的最优解，从而总结出在当前实验场景下的部署策略。

## 实验场景
共32 张 GPU 卡。每 8 张卡在一个节点内（即一个服务器内），16 张卡（每两个节点）属于一个亲和组。

节点内的带宽最高，亲和组内的带宽较高，跨亲和组的带宽较低。

## 最优解
PP = 1, 
TP = 8, 
DP = 4, 
microbath number = 1


## 打分策略代码

```python
program_id = "v10"

...

score = 1000.0
# Penalize pipeline bubble to keep pipeline depth moderate
score -= 50.0 * bubble
# Penalize idle GPUs to encourage full utilization
score -= 2.0 * max(0, total - active)
# Reward efficient micro-batch size that lowers per-GPU overhead
score += 10.0 * micro / (micro + 10.0)
# Reward throughput scaling from tensor and data parallelism
score += 1.0 * tp + 0.2 * dp
# Balance TP and DP to avoid extreme communication asymmetry
score -= 0.9 * abs(tp - dp)
# Strongly penalize large micro-batch numbers that cause memory risk and high latency
score -= 0.5 * (mbn - 1) * (mbn - 1)
```



## 经验总结
### <span style="color:blue;">(1) 满卡优先</span>   
score：
```python
-2.0 * max(0, total - active)
```
与目标最小化latency相符合

当前场景下，通信还没慢到成为主瓶颈，因此：idle 的损失 > 通信优化收益 → 满卡优先

<span style="color:green;">
下一步可以用仿真器分析出什么样的情况下，ideal 的损失 ＜ 通信优化收益的，此时可能就不是满卡优先了。
</span>

### <span style="color:blue;">(2) TP与DP必须接近平衡：TP≈DP 或 TP:DP=2:1 附近</span>   
score：
```python
    -0.9 * abs(tp - dp) + 1.0 * tp + 0.2 * dp
```
忽略 PP 和 microbatch，我们只看 TP/DP。我们近似优化：

$$
score(tp,dp) = -0.9|tp-dp| + 1.0 * tp + 0.2 * dp
$$


#### 情况1：TP ≥ DP

$$
\begin{aligned}
score &= tp+0.2dp-0.9(tp-dp) \\
&= tp+0.2dp-0.9tp+0.9dp \\
&= 0.1tp+1.1dp
\end{aligned}
$$

此时，dp 的边际收益(1.1) > tp(0.1)。这说明，系统其实更“奖励 DP 的数量”，但同时又不允许 TP 太小。

#### 情况2：TP < DP
$$
\begin{aligned}
score &= tp+0.2dp-0.9(dp-tp) \\
&= tp+0.2dp-0.9dp+0.9tp \\
&= 1.9tp-0.7dp
\end{aligned}
$$

此时，DP 是强惩罚项。

基于上述，score 在强迫系统进入一个“平衡点”：
- TP 不能太大（否则 |tp-dp| 惩罚）
- DP 不能太大（否则 TP<DP 区域被惩罚）
- TP 又比 DP 更“贵”（权重1.0 vs 0.2）

因此，最优区间满足
$$
TP ≳ DP
$$
因此，最优的 TP 与 DP 配比应接近平衡，略微倾向于 TP 略大于 DP，即 TP:DP 略大于 1:1。考虑到 TP ≤ 8，可以选择 TP:DP = 2:1。

此外，给定 PP=1 和 TP ≤ 8，只优化 TP 和 DP，可以尝试的组合有：
<table align="center">
    <thead>
        <tr>
            <th>TP</th>
            <th>DP</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>1</td>
            <td>32</td>
        </tr>
        <tr>
            <td>2</td>
            <td>16</td>
        </tr>
        <tr>
            <td>4</td>
            <td>8</td>
        </tr>
        <tr>
            <td>8</td>
            <td>4</td>
        </tr>
    </tbody>
</table>

不同组合下的score值 $-0.9 * abs(tp - dp) + 1.0 * tp + 0.2 * dp$ 为
<table align="center">
    <thead>
        <tr>
            <th>tp</th>
            <th>dp</th>
            <th>score</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>1</td>
            <td>32</td>
            <td>-20.5</td>
        </tr>
        <tr>
            <td>2</td>
            <td>16</td>
            <td>-7.4</td>
        </tr>
        <tr>
            <td>4</td>
            <td>8</td>
            <td>2.0</td>
        </tr>
        <tr>
            <td>8</td>
            <td>4</td>
            <td>⭐ 5.2</td>
        </tr>
    </tbody>
</table>

最优解：TP = 8, DP = 4。

也能看到 TP:DP = 2:1 的组合在 score 上表现较好，符合前面分析的最优区间，即略微倾向于 TP 略大于 DP。

### <span style="color:blue;">(3) PP倾向于1</span>   
score：
```python
score -= 50.0 * bubble
```
上述score会惩罚bubble，即pipeline stages 大于 1 的情况。
因此，score 对 PP 的建模是“单边惩罚”，没有对 PP 为 1 的情况提供额外奖励。

从而，系统倾向于将 PP 设置为 1，以避免 pipeline bubble 带来的惩罚。

### <span style="color:blue;">(4) microbatch number = 1</span>   
score：
```python
-0.5 * (mbn - 1) * (mbn - 1)
```

| mbn  | penalty | 
| ---  | ------- | 
| 1   | ⭐0       | 
| 2   | -0.5    | 
| 3   | -2.0    |
| 4   | -4.5    |
| 8   | -24.5   | 

可以看到，最优点永远在 mbn = 1。说明在当前score设计下，microbatch 的最优选择倾向于较小的值，是 1 。
````
