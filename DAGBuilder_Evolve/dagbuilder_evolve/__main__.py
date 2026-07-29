from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .config import load_scenario
from .engine import EvolutionEngine


def main() -> int:
    parser = argparse.ArgumentParser(description="DAGBuilder simulation-driven strategy evolution")
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--run-name")
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--mock", action="store_true", help="Use deterministic Mock instead of DeepSeek")
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    config = load_scenario(args.scenario)
    run_name = args.run_name or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = config.output_root / run_name
    if run_dir.exists() and args.resume is None:
        raise FileExistsError(f"Run directory exists: {run_dir}")
    engine = EvolutionEngine(config, run_dir, mock=args.mock, resume=args.resume)
    report = engine.run(args.rounds)
    best = report["best"]
    print(f"Run directory: {run_dir}")
    print(f"Evaluated: {report['evaluated_strategy_count']}/{report['total_strategy_count']}")
    print(f"Current search best: {best['strategy']['signature']} = {best['latency_s']:.6f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

