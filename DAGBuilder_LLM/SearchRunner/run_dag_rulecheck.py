from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_RULES = ROOT / "RuleCheck" / "rules" / "default_rules.json"

sys.path.insert(0, str(ROOT / "DagGenerator"))
sys.path.insert(0, str(ROOT / "RuleCheck"))
sys.path.insert(0, str(ROOT))

from check_dag import RuleChecker, default_report_paths, load_json, render_markdown  # noqa: E402
from generate_dag import build_dag, load_config, output_paths_from_config, render_html, write_json  # noqa: E402
from ValueSim.simulator_v2.adapter import simulate_dag, write_json as write_value_json  # noqa: E402


def run_flow(
    *,
    config_path: Path,
    rules_path: Path,
    html_output: Path | None = None,
    dag_json_output: Path | None = None,
    rule_report_json: Path | None = None,
    rule_report_md: Path | None = None,
    weighted_dag_output: Path | None = None,
    timing_output: Path | None = None,
    skip_valuesim: bool = False,
    flow_report_json: Path | None = None,
    flow_report_md: Path | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {}

    try:
        config = load_config(config_path)
        html_path, dag_json_path = output_paths_from_config(
            config,
            html_override=html_output,
            json_override=dag_json_output,
        )
        dag = build_dag(config, config_path, html_path, dag_json_path)
        render_html(dag, html_path)
        write_json(dag, dag_json_path)
        artifacts["dag_html"] = str(html_path.as_posix())
        artifacts["dag_json"] = str(dag_json_path.as_posix())
        steps.append(
            {
                "name": "DagGenerator",
                "status": "pass",
                "message": "已生成 DAG HTML 和 JSON 产物。",
                "outputs": {"html": artifacts["dag_html"], "json": artifacts["dag_json"]},
            }
        )
    except Exception as exc:  # noqa: BLE001
        report = build_flow_report(
            config_path=config_path,
            rules_path=rules_path,
            status="fail",
            steps=[
                {
                    "name": "DagGenerator",
                    "status": "fail",
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                }
            ],
            artifacts=artifacts,
            rule_check_summary=None,
            next_action="fix_dag_generator_or_config",
        )
        return write_flow_reports(report, flow_report_json, flow_report_md, fallback_dir=config_path.parent, write_reports=write_reports)

    try:
        rules = load_json(rules_path)
        checker = RuleChecker(dag, rules, dag_json_path)
        rule_report = checker.run()
        default_json, default_md = default_report_paths(dag_json_path)
        rule_json_path = rule_report_json or default_json
        rule_md_path = rule_report_md or default_md
        rule_report["outputs"] = {
            "json": str(rule_json_path.as_posix()),
            "markdown": str(rule_md_path.as_posix()),
        }
        if write_reports:
            rule_json_path.parent.mkdir(parents=True, exist_ok=True)
            rule_md_path.parent.mkdir(parents=True, exist_ok=True)
            rule_json_path.write_text(json.dumps(rule_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            rule_md_path.write_text(render_markdown(rule_report), encoding="utf-8")
            artifacts["rule_check_json"] = str(rule_json_path.as_posix())
            artifacts["rule_check_md"] = str(rule_md_path.as_posix())
        steps.append(
            {
                "name": "RuleCheck",
                "status": rule_report["status"],
                "message": "已检查 DAG 语义有效性。",
                "summary": rule_report["summary"],
                "outputs": rule_report["outputs"],
            }
        )

        status = "fail" if rule_report["summary"]["errors"] else "pass"
        if status == "fail" or skip_valuesim:
            report = build_flow_report(
                config_path=config_path,
                rules_path=rules_path,
                status=status,
                steps=steps,
                artifacts=artifacts,
                rule_check_summary=rule_report["summary"],
                next_action="feedback_to_dag_generator" if status == "fail" else "ready_for_value_sim",
            )
            return write_flow_reports(report, flow_report_json, flow_report_md, fallback_dir=dag_json_path.parent, write_reports=write_reports)

        try:
            weighted_path = weighted_dag_output or dag_json_path.with_name("weighted_dag.json")
            timing_path = timing_output or dag_json_path.with_name("node_timing_table.json")
            weighted_dag, timing_rows = simulate_dag(dag, config)
            write_value_json(weighted_path, weighted_dag)
            write_value_json(timing_path, timing_rows)
            artifacts["weighted_dag_json"] = str(weighted_path.as_posix())
            artifacts["node_timing_table_json"] = str(timing_path.as_posix())
            steps.append(
                {
                    "name": "ValueSim",
                    "status": "pass",
                    "message": "已为 DAG 节点填充计算和通信耗时字段。",
                    "summary": {
                        "nodes": len(weighted_dag["nodes"]),
                        "edges": len(weighted_dag["edges"]),
                        "topology_unchanged": weighted_dag["value_sim_v2"]["topology_unchanged"],
                        "simulator": "simulator_v2",
                    },
                    "outputs": {
                        "weighted_dag": artifacts["weighted_dag_json"],
                        "node_timing_table": artifacts["node_timing_table_json"],
                    },
                }
            )
        except Exception as exc:  # noqa: BLE001
            steps.append(
                {
                    "name": "ValueSim",
                    "status": "fail",
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
            report = build_flow_report(
                config_path=config_path,
                rules_path=rules_path,
                status="fail",
                steps=steps,
                artifacts=artifacts,
                rule_check_summary=rule_report["summary"],
                next_action="fix_valuesim_config_or_node_model",
            )
            return write_flow_reports(report, flow_report_json, flow_report_md, fallback_dir=dag_json_path.parent, write_reports=write_reports)

        report = build_flow_report(
            config_path=config_path,
            rules_path=rules_path,
            status="pass",
            steps=steps,
            artifacts=artifacts,
            rule_check_summary=rule_report["summary"],
            next_action="ready_for_overlap_opt",
        )
        return write_flow_reports(report, flow_report_json, flow_report_md, fallback_dir=dag_json_path.parent, write_reports=write_reports)
    except Exception as exc:  # noqa: BLE001
        steps.append(
            {
                "name": "RuleCheck",
                "status": "fail",
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        fallback_dir = Path(artifacts["dag_json"]).parent if "dag_json" in artifacts else config_path.parent
        report = build_flow_report(
            config_path=config_path,
            rules_path=rules_path,
            status="fail",
            steps=steps,
            artifacts=artifacts,
            rule_check_summary=None,
            next_action="fix_rulecheck_or_dag_schema",
        )
        return write_flow_reports(report, flow_report_json, flow_report_md, fallback_dir=fallback_dir, write_reports=write_reports)


def build_flow_report(
    *,
    config_path: Path,
    rules_path: Path,
    status: str,
    steps: list[dict[str, Any]],
    artifacts: dict[str, str],
    rule_check_summary: dict[str, Any] | None,
    next_action: str,
) -> dict[str, Any]:
    return {
        "flow_id": "dag_generator_rulecheck_valuesim",
        "status": status,
        "source_config": str(config_path.as_posix()),
        "rules": str(rules_path.as_posix()),
        "steps": steps,
        "artifacts": artifacts,
        "rule_check_summary": rule_check_summary,
        "next_action": next_action,
        "contract": {
            "pass": "DAG 已完成规则检查和耗时填充，可供后续 OverlapOPT 使用。",
            "fail": "使用 RuleCheck 发现的问题反馈给 DagGenerator，重新生成后再运行流程。",
        },
    }


def write_flow_reports(
    report: dict[str, Any],
    flow_report_json: Path | None,
    flow_report_md: Path | None,
    *,
    fallback_dir: Path,
    write_reports: bool = True,
) -> dict[str, Any]:
    json_path = flow_report_json or fallback_dir / "dag_rulecheck_flow_report.json"
    md_path = flow_report_md or fallback_dir / "dag_rulecheck_flow_report.md"
    report["outputs"] = {
        "json": str(json_path.as_posix()),
        "markdown": str(md_path.as_posix()),
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    if write_reports:
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(render_flow_markdown(report), encoding="utf-8")
    return report


def render_flow_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# DAG 生成 -> 规则检查 -> 数值仿真流程 {report['status'].upper()}",
        "",
        f"- 源配置: `{report['source_config']}`",
        f"- 规则文件: `{report['rules']}`",
        f"- 下一步动作: `{report['next_action']}`",
        "",
        "## 步骤",
        "",
    ]
    for step in report["steps"]:
        lines.append(f"- {step['name']}: {step['status']} - {step['message']}")
    lines.extend(["", "## 产物", ""])
    for key, value in sorted(report["artifacts"].items()):
        lines.append(f"- {key}: `{value}`")
    if report.get("rule_check_summary") is not None:
        summary = report["rule_check_summary"]
        lines.extend(
            [
                "",
                "## RuleCheck 汇总",
                "",
                f"- 错误: {summary['errors']}",
                f"- 警告: {summary['warnings']}",
                f"- 可读性提示: {summary['readability']}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DagGenerator, RuleCheck, and ValueSim.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--html-output", type=Path)
    parser.add_argument("--dag-json-output", type=Path)
    parser.add_argument("--rule-report-json", type=Path)
    parser.add_argument("--rule-report-md", type=Path)
    parser.add_argument("--weighted-dag-output", type=Path)
    parser.add_argument("--timing-output", type=Path)
    parser.add_argument("--skip-valuesim", action="store_true")
    parser.add_argument("--flow-report-json", type=Path)
    parser.add_argument("--flow-report-md", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_flow(
        config_path=args.config,
        rules_path=args.rules,
        html_output=args.html_output,
        dag_json_output=args.dag_json_output,
        rule_report_json=args.rule_report_json,
        rule_report_md=args.rule_report_md,
        weighted_dag_output=args.weighted_dag_output,
        timing_output=args.timing_output,
        skip_valuesim=args.skip_valuesim,
        flow_report_json=args.flow_report_json,
        flow_report_md=args.flow_report_md,
    )
    print(f"Flow status: {report['status']}")
    print(f"Wrote {report['outputs']['json']}")
    print(f"Wrote {report['outputs']['markdown']}")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
