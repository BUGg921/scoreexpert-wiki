from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from dagbuilder_evolve.config import ScenarioConfig
from dagbuilder_evolve.database import ProgramDatabase
from dagbuilder_evolve.reporting import build_final_report
from dagbuilder_evolve.strategy import enumerate_strategies


OUTPUTS = PROJECT / "outputs"


def refresh_report(run_dir: Path) -> dict:
    config = ScenarioConfig.from_dict(
        json.loads((run_dir / "scenario.json").read_text(encoding="utf-8")),
        source=run_dir / "scenario.json",
    )
    database = ProgramDatabase.from_dict(
        json.loads(
            (run_dir / "program_database.json").read_text(encoding="utf-8")
        ),
        int(config.evolution["island_capacity"]),
        int(config.evolution["global_archive_size"]),
    )
    results = json.loads(
        (run_dir / "simulation_results.json").read_text(encoding="utf-8")
    )
    return build_final_report(
        config,
        run_dir,
        database,
        enumerate_strategies(config),
        results,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh native reports and summarize a scenario batch."
    )
    parser.add_argument("batch_name")
    parser.add_argument("--refresh-reports", action="store_true")
    args = parser.parse_args()
    batch_dir = OUTPUTS / args.batch_name
    manifest = json.loads(
        (batch_dir / "manifest.json").read_text(encoding="utf-8")
    )
    rows = []
    for scenario_id in manifest["requested"]:
        result = manifest["results"].get(scenario_id)
        if not result or result.get("status") not in {
            "completed",
            "skipped_complete",
        }:
            rows.append(
                f"| {scenario_id.upper()} | 未完成 | — | — | — | — |"
            )
            continue
        run_dir = Path(result["run_dir"])
        if args.refresh_reports:
            report = refresh_report(run_dir)
        else:
            report = json.loads(
                (run_dir / "final_report.json").read_text(encoding="utf-8")
            )
        best = report["best"]
        strategy = best["strategy"]
        evidence = report["best_score_program"]
        relative = run_dir.relative_to(batch_dir.parent)
        rows.append(
            f"| {scenario_id.upper()} | `{strategy['signature']}` | "
            f"{best['latency_s']:.6f} | "
            f"{report['evaluated_strategy_count']}/{report['total_strategy_count']} | "
            f"{evidence['island']} G{evidence['generation']} rank="
            f"{evidence['candidate_rank']} | "
            f"[报告](../{relative.as_posix()}/scenario_analysis.md) |"
        )
    lines = [
        f"# {args.batch_name} 仿真汇总",
        "",
        "| 场景 | 当前已仿真最优 | 时延 (s) | 覆盖 | 关联公式 | 报告 |",
        "| --- | --- | ---: | ---: | --- | --- |",
        *rows,
        "",
        "所有最优均指实际数值仿真候选中的最低最长路径，不代表873个候选的穷举全局最优。",
        "打分公式负责候选提名；具体部署策略由RuleCheck、显存和数值仿真共同确定。",
    ]
    (batch_dir / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(batch_dir / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
