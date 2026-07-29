from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .report import render_markdown
    from .rules import apply_overlap_rules
except ImportError:  # pragma: no cover - supports direct script execution.
    from report import render_markdown
    from rules import apply_overlap_rules


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def run_overlap_opt(
    weighted_dag_path: Path,
    overlapped_dag_output: Path | None = None,
    report_json_output: Path | None = None,
    report_md_output: Path | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    weighted_dag = load_json(weighted_dag_path)
    overlapped_dag, report = apply_overlap_rules(weighted_dag)

    output_dir = weighted_dag_path.parent
    overlapped_path = overlapped_dag_output or output_dir / "overlapped_weighted_dag.json"
    report_json_path = report_json_output or output_dir / "overlap_report.json"
    report_md_path = report_md_output or output_dir / "overlap_report.md"

    report["outputs"] = {
        "overlapped_weighted_dag": str(overlapped_path.as_posix()),
        "json": str(report_json_path.as_posix()),
        "markdown": str(report_md_path.as_posix()),
    }
    write_json(overlapped_path, overlapped_dag)
    if write_reports:
        write_json(report_json_path, report)
        report_md_path.parent.mkdir(parents=True, exist_ok=True)
        report_md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OverlapOPT on a weighted DAG.")
    parser.add_argument("--weighted-dag", required=True, type=Path)
    parser.add_argument("--overlapped-dag-output", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_overlap_opt(
        weighted_dag_path=args.weighted_dag,
        overlapped_dag_output=args.overlapped_dag_output,
        report_json_output=args.report_json,
        report_md_output=args.report_md,
    )
    print(f"OverlapOPT status: {report['status']}")
    print(f"Overlapped DAG: {report['outputs']['overlapped_weighted_dag']}")
    print(f"Report: {report['outputs']['json']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
