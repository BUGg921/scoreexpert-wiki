from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT / "configs"
OUTPUT_DIR = PROJECT / "outputs"


def scenario_configs() -> dict[str, Path]:
    configs: dict[str, Path] = {}
    for path in sorted(CONFIG_DIR.glob("scenario_s*_32g.py")):
        token = path.name.removeprefix("scenario_s").split("_", 1)[0]
        if token.isdigit():
            configs[f"s{int(token)}"] = path
    return configs


def write_manifest(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_one(
    scenario_id: str,
    config_path: Path,
    batch_name: str,
    rounds: int | None,
    mock: bool,
) -> dict[str, Any]:
    run_name = f"{batch_name}_{scenario_id}"
    run_dir = OUTPUT_DIR / run_name
    if (run_dir / "final_report.json").exists():
        return {
            "scenario_id": scenario_id,
            "status": "skipped_complete",
            "run_dir": str(run_dir),
        }
    command = [
        sys.executable,
        "-m",
        "dagbuilder_evolve",
        "--scenario",
        str(config_path),
        "--run-name",
        run_name,
    ]
    if rounds is not None:
        command.extend(["--rounds", str(rounds)])
    if mock:
        command.append("--mock")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT)
    completed = subprocess.run(
        command,
        cwd=PROJECT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log_path = OUTPUT_DIR / batch_name / "logs" / f"{scenario_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(completed.stdout, encoding="utf-8")
    return {
        "scenario_id": scenario_id,
        "status": "completed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "run_dir": str(run_dir),
        "log_path": str(log_path),
        "output": completed.stdout[-2000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run multiple DAGBuilder_Evolve scenarios with native reports."
    )
    parser.add_argument("scenario_ids", nargs="+", help="For example: s0 s1 s3")
    parser.add_argument(
        "--batch-name",
        default=f"evolve_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    available = scenario_configs()
    requested = [value.lower() for value in args.scenario_ids]
    missing = [value for value in requested if value not in available]
    if missing:
        print(
            "Missing scenario definitions: "
            + ", ".join(missing)
            + ". Available: "
            + ", ".join(sorted(available)),
            file=sys.stderr,
        )
        return 2
    if args.jobs < 1:
        raise ValueError("--jobs must be at least 1")

    manifest_path = OUTPUT_DIR / args.batch_name / "manifest.json"
    manifest: dict[str, Any] = {
        "batch_name": args.batch_name,
        "requested": requested,
        "jobs": args.jobs,
        "rounds": args.rounds,
        "mock": args.mock,
        "results": {},
    }
    write_manifest(manifest_path, manifest)
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(
                run_one,
                scenario_id,
                available[scenario_id],
                args.batch_name,
                args.rounds,
                args.mock,
            ): scenario_id
            for scenario_id in requested
        }
        for future in as_completed(futures):
            scenario_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "scenario_id": scenario_id,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            manifest["results"][scenario_id] = result
            write_manifest(manifest_path, manifest)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    failed = [
        item
        for item in manifest["results"].values()
        if item["status"] == "failed"
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
