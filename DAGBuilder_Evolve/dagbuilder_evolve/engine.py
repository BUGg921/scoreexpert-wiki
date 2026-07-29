from __future__ import annotations

import ast
import json
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .config import ScenarioConfig
from .database import ProgramDatabase
from .evaluator import StrategyEvaluator
from .llm import DeepSeekEvolutionClient, MockEvolutionClient
from .programs import (
    ISLANDS, SEED_SOURCES, ProgramRecord, feasible_strategies, score_program,
)
from .reporting import build_final_report, write_json
from .strategy import Strategy, enumerate_strategies


class EvolutionEngine:
    def __init__(
        self,
        config: ScenarioConfig,
        run_dir: Path,
        *,
        mock: bool = False,
        resume: Path | None = None,
    ) -> None:
        self.config = config
        self.run_dir = run_dir.resolve()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.catalog = enumerate_strategies(config)
        self.feasible = feasible_strategies(self.catalog, config)
        self.strategy_by_signature = {item.signature: item for item in self.catalog}
        self.evaluator = StrategyEvaluator(config, self.run_dir)
        self.rng = random.Random(int(config.evolution["random_seed"]))
        self.database = ProgramDatabase(
            int(config.evolution["island_capacity"]),
            int(config.evolution["global_archive_size"]),
        )
        self.results: dict[str, dict[str, Any]] = {}
        self.current_generation = 0
        self.lineage: list[dict[str, Any]] = []
        self.convergence: list[dict[str, Any]] = []
        self.client = MockEvolutionClient() if mock else DeepSeekEvolutionClient(config)
        if resume is not None:
            self._restore(resume)
        else:
            self._write_static_outputs()

    def _write_static_outputs(self) -> None:
        write_json(self.run_dir / "scenario.json", self.config.to_dict())
        write_json(self.run_dir / "strategy_catalog.json", [item.to_dict() for item in self.catalog])
        write_json(
            self.run_dir / "search_space_summary.json",
            {
                "structurally_legal": len(self.catalog),
                "memory_feasible": len(self.feasible),
                "memory_rejected": len(self.catalog) - len(self.feasible),
            },
        )

    def _score_records(self, records: list[ProgramRecord]) -> dict[str, list[tuple[Strategy, float]]]:
        rankings: dict[str, list[tuple[Strategy, float]]] = {}
        for record in records:
            if record.error:
                continue
            try:
                ranking, complexity = score_program(
                    record.source,
                    self.feasible,
                    self.config,
                    float(self.config.evolution["program_timeout_s"]),
                )
                record.complexity = complexity
                record.nominated = [strategy.signature for strategy, _ in ranking[:8]]
                record.nominated_scores = {
                    strategy.signature: float(score) for strategy, score in ranking[:8]
                }
                record.nominated_ranks = {
                    strategy.signature: rank
                    for rank, (strategy, _) in enumerate(ranking[:8], start=1)
                }
                rankings[record.program_id] = ranking
            except Exception as exc:
                record.error = f"{type(exc).__name__}: {exc}"
        return rankings

    def _evaluate_unseen(
        self, rankings: dict[str, list[tuple[Strategy, float]]]
    ) -> dict[str, list[dict[str, Any]]]:
        limit = int(self.config.search["nominations_per_program"])
        selected: dict[str, Strategy] = {}
        selected_by_program: dict[str, list[dict[str, Any]]] = {}
        for program_id, ranking in rankings.items():
            unseen: list[dict[str, Any]] = []
            for rank, (strategy, score) in enumerate(ranking, start=1):
                if strategy.signature in self.results:
                    continue
                cached = self.evaluator.cached(strategy)
                if cached is not None:
                    self.results[strategy.signature] = cached
                    continue
                unseen.append(
                    {
                        "strategy": strategy,
                        "score": float(score),
                        "rank": rank,
                    }
                )
                if len(unseen) == limit:
                    break
            selected_by_program[program_id] = unseen
            for item in unseen:
                strategy = item["strategy"]
                selected[strategy.signature] = strategy
        for signature in sorted(selected):
            result = self.evaluator.evaluate(selected[signature])
            self.results[signature] = result
        return selected_by_program

    def _load_cached_nominations(self, records: list[ProgramRecord]) -> None:
        for record in records:
            for signature in record.nominated:
                if signature in self.results:
                    continue
                cached = self.evaluator.cached(self.strategy_by_signature[signature])
                if cached is not None:
                    self.results[signature] = cached

    def _finalize_records(self, records: list[ProgramRecord]) -> None:
        self._load_cached_nominations(records)
        for record in records:
            attributed_signatures = list(
                dict.fromkeys(record.evaluated_nominations + record.nominated)
            )
            nominated_results = [
                self.results[signature]
                for signature in attributed_signatures
                if signature in self.results
            ]
            passed = sorted(
                (item for item in nominated_results if item.get("status") == "pass"),
                key=lambda item: item["latency_s"],
            )
            record.failures = len(nominated_results) - len(passed)
            if passed:
                record.best_latency_s = float(passed[0]["latency_s"])
                top3 = passed[:3]
                record.top3_mean_latency_s = sum(item["latency_s"] for item in top3) / len(top3)
                record.combined_score = 1.0 / (1.0 + record.best_latency_s)
            self.database.add(record)

    def _evaluate_program_batch(self, records: list[ProgramRecord]) -> None:
        rankings = self._score_records(records)
        selected_by_program = self._evaluate_unseen(rankings)
        for record in records:
            selected = selected_by_program.get(record.program_id, [])
            record.evaluated_nominations = [
                item["strategy"].signature for item in selected
            ]
            record.evaluated_nomination_scores = {
                item["strategy"].signature: float(item["score"]) for item in selected
            }
            record.evaluated_nomination_ranks = {
                item["strategy"].signature: int(item["rank"]) for item in selected
            }
        self._finalize_records(records)

    def _feedback(self, parent: ProgramRecord) -> dict[str, Any]:
        rows = []
        attributed_signatures = list(
            dict.fromkeys(parent.evaluated_nominations + parent.nominated)
        )
        for signature in attributed_signatures:
            result = self.results.get(signature)
            if result:
                rows.append(
                    {
                        "strategy": result["strategy"],
                        "status": result["status"],
                        "latency_s": result.get("latency_s"),
                        "error": result.get("error"),
                        "critical_path_category_s": result.get("critical_path_category_s"),
                    }
                )
        global_best = min(
            (item for item in self.results.values() if item.get("status") == "pass"),
            key=lambda item: item["latency_s"],
            default=None,
        )
        compact_best = None
        if global_best:
            compact_best = {
                "strategy": global_best["strategy"],
                "latency_s": global_best["latency_s"],
                "critical_path_category_s": global_best.get("critical_path_category_s", {}),
            }
        return {
            "parent_attributed_simulation": rows,
            "current_search_best": compact_best,
            "coverage": len(self.results) / len(self.catalog),
        }

    def _initialize(self) -> None:
        records = [
            ProgramRecord.create(island, SEED_SOURCES[island], 0, origin="seed")
            for island in ISLANDS
        ]
        self._evaluate_program_batch(records)
        self._save_round(0, records, [])

    def _save_round(
        self,
        generation: int,
        records: list[ProgramRecord],
        migrated: list[str],
    ) -> None:
        best = min(
            (item for item in self.results.values() if item.get("status") == "pass"),
            key=lambda item: item["latency_s"],
            default=None,
        )
        convergence = {
            "generation": generation,
            "evaluated": len(self.results),
            "best_latency_s": best.get("latency_s") if best else None,
            "best_strategy": best.get("strategy") if best else None,
        }
        self.convergence.append(convergence)
        round_dir = self.run_dir / "rounds" / f"round_{generation:02d}"
        write_json(round_dir / "programs.json", [item.to_dict() for item in records])
        write_json(round_dir / "island_rankings.json", {
            island: [
                self.database.records[item].to_dict()
                for item in sorted(
                    self.database.populations[island],
                    key=lambda key: (
                        self.database.records[key].best_latency_s is None,
                        self.database.records[key].best_latency_s or float("inf"),
                    ),
                )
            ]
            for island in ISLANDS
        })
        write_json(round_dir / "map_elites.json", self.database.grids)
        write_json(round_dir / "migration.json", migrated)
        write_json(round_dir / "summary.json", convergence)
        self._checkpoint(generation)

    def _checkpoint(self, generation: int) -> None:
        payload = {
            "generation": generation,
            "scenario_fingerprint": self.config.fingerprint(),
            "rng_state": repr(self.rng.getstate()),
            "database": self.database.to_dict(),
            "results": self.results,
            "lineage": self.lineage,
            "convergence": self.convergence,
        }
        write_json(self.run_dir / "checkpoints" / f"checkpoint_{generation:02d}.json", payload)
        write_json(self.run_dir / "checkpoint_latest.json", payload)

    def _restore(self, path: Path) -> None:
        value = json.loads(path.read_text(encoding="utf-8"))
        if value["scenario_fingerprint"] != self.config.fingerprint():
            raise ValueError("Checkpoint scenario does not match current scenario")
        self.current_generation = int(value["generation"])
        self.rng.setstate(ast.literal_eval(value["rng_state"]))
        self.database = ProgramDatabase.from_dict(
            value["database"],
            int(self.config.evolution["island_capacity"]),
            int(self.config.evolution["global_archive_size"]),
        )
        self.results = dict(value["results"])
        self.lineage = list(value["lineage"])
        self.convergence = list(value["convergence"])

    def run(self, rounds: int | None = None) -> dict[str, Any]:
        target = int(rounds if rounds is not None else self.config.evolution["rounds"])
        if not self.database.records:
            self._initialize()
        start = self.current_generation + 1
        for generation in range(start, target + 1):
            children: list[ProgramRecord] = []
            requests = []
            for island in ISLANDS:
                parent, inspirations = self.database.sample(island, self.rng)
                requests.append((island, parent, inspirations, self._feedback(parent)))
            with ThreadPoolExecutor(max_workers=len(ISLANDS)) as executor:
                futures = [
                    executor.submit(
                        self.client.evolve,
                        island,
                        parent,
                        inspirations,
                        feedback,
                        generation,
                    )
                    for island, parent, inspirations, feedback in requests
                ]
                responses = []
                for request, future in zip(requests, futures):
                    try:
                        responses.append((request, future.result(), None))
                    except Exception as exc:
                        responses.append((request, None, exc))
            for (island, parent, inspirations, _), evolved_source, error in responses:
                try:
                    if error is not None:
                        raise error
                    source = str(evolved_source)
                except Exception as exc:
                    source = parent.source + f"\n# generation {generation} evolution failed"
                    child = ProgramRecord.create(
                        island, source, generation, parents=[parent.program_id],
                        inspirations=[item.program_id for item in inspirations],
                    )
                    child.error = f"{type(exc).__name__}: {exc}"
                else:
                    child = ProgramRecord.create(
                        island, source, generation, parents=[parent.program_id],
                        inspirations=[item.program_id for item in inspirations],
                    )
                children.append(child)
                self.lineage.append(
                    {
                        "generation": generation, "island": island,
                        "parent": parent.program_id, "child": child.program_id,
                        "inspirations": child.inspirations,
                    }
                )
            self._evaluate_program_batch(children)
            migrated = []
            if generation in {int(value) for value in self.config.evolution["migration_rounds"]}:
                migrated = self.database.migrate_ring(generation)
            self.current_generation = generation
            self._save_round(generation, children, migrated)
        for path in sorted(self.evaluator.cache_dir.glob("*.json")):
            cached = json.loads(path.read_text(encoding="utf-8"))
            signature = str(cached.get("strategy", {}).get("signature") or "")
            if signature:
                self.results.setdefault(signature, cached)
        write_json(self.run_dir / "program_database.json", self.database.to_dict())
        write_json(self.run_dir / "lineage.json", self.lineage)
        write_json(self.run_dir / "convergence.json", self.convergence)
        write_json(self.run_dir / "simulation_results.json", self.results)
        return build_final_report(
            self.config, self.run_dir, self.database, self.catalog, self.results
        )
