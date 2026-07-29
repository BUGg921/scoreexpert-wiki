# DAG 生成 -> 规则检查 -> 数值仿真流程 PASS

- 源配置: `/Users/cookie/Documents/DAGBuilder_LLM/config/config.py`
- 规则文件: `/Users/cookie/Documents/DAGBuilder_LLM/RuleCheck/rules/default_rules.json`
- 下一步动作: `ready_for_overlap_opt`

## 步骤

- DagGenerator: pass - 已生成 DAG HTML 和 JSON 产物。
- RuleCheck: pass - 已检查 DAG 语义有效性。
- ValueSim: pass - 已为 DAG 节点填充计算和通信耗时字段。

## 产物

- dag_html: `outputs/run_dag_rulecheck_current/dag.html`
- dag_json: `outputs/run_dag_rulecheck_current/dag.json`
- node_timing_table_json: `outputs/run_dag_rulecheck_current/node_timing_table.json`
- rule_check_json: `outputs/run_dag_rulecheck_current/rule_report.json`
- rule_check_md: `outputs/run_dag_rulecheck_current/rule_report.md`
- weighted_dag_json: `outputs/run_dag_rulecheck_current/weighted_dag.json`

## RuleCheck 汇总

- 错误: 0
- 警告: 0
- 可读性提示: 0
