---
name: dag-generator-config-contract
description: DagGenerator Python config 输入契约。
---

# DagGenerator Config 

config 描述要生成什么 DAG，而不是 DAG 产物本身。默认模板是 `config/config.py`。

Python config 必须暴露以下任意一个对象：

- `CONFIG`
- `DAG_GENERATOR_CONFIG`
- `get_config()`

## 必需字段

- `dag_id`
- `model_para`
- `parallelism_config`
- `network_config`
- `value_sim_config`
- `search_config`
- `immutable_config_sections`
- `domains`
- `strategies`
- `color_theme`
- `outputs`

## 固定字段

`model_para` 和 `network_config` 是固定输入。自动搜索不应修改它们。

## 可搜索字段

`parallelism_config` 是主要搜索空间，包括：

- `dp_size`
- `tp_size`
- `pp_size`
- `global_batch_size`
- `microbatch_num`
- `microbatch_size`
- `pp_strategy`
- `dp_strategy`
- `dp_allreduce_granularity`

当前版本不直接搜索 `microbatch_size`。两阶段搜索会根据候选 DP 自动计算：

```text
local_minibatch_size = global_batch_size / dp_size
microbatch_size = local_minibatch_size / microbatch_num
```

## 输出位置

默认使用：

```python
"outputs": {
    "base_dir": "D:\\CodeProgram\\codex\\DAGBuilder\\DagGenerator\\outputs",
    "name_template": "pp{pp_size}_{pp_strategy}_dp{dp_size}_{dp_strategy_short}",
    "html_filename": "dag.html",
    "json_filename": "dag.json",
}
```

两阶段搜索也默认写入 `outputs.base_dir`。
