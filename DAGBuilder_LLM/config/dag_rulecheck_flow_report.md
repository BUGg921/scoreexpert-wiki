# DAG 生成 -> 规则检查 -> 数值仿真流程 FAIL

- 源配置: `config/config.py`
- 规则文件: `RuleCheck/rules/default_rules.json`
- 下一步动作: `fix_dag_generator_or_config`

## 步骤

- DagGenerator: fail - Invalid parallel domains: pp_size * dp_size * tp_size must equal num_gpus (2 * 4 * 4 != 16).

## 产物

