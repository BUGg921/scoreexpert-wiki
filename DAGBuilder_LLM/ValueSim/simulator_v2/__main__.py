from __future__ import annotations

import argparse
from pathlib import Path

from .engine import run_simulation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run modular ValueSim v2 on an existing DAG")
    parser.add_argument("--dag", required=True, type=Path, help="Input DAG JSON")
    parser.add_argument("--config", required=True, type=Path, help="Python simulator_v2 config")
    parser.add_argument("--run-name", help="Output subdirectory name; defaults to a timestamp")
    parser.add_argument("--output-root", type=Path, help="Override ValueSim/simulator_v2/output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_simulation(
        args.dag,
        args.config,
        run_name=args.run_name,
        output_root=args.output_root,
    )
    print(f"Wrote {result['output_dir']}")
    print(f"longest_path_s={result['summary']['longest_path']['duration_s']:.9f}")


if __name__ == "__main__":
    main()
