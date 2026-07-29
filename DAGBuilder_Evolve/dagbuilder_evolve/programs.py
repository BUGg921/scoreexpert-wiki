from __future__ import annotations

import ast
import hashlib
import math
import multiprocessing as mp
import queue
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import ScenarioConfig
from .evaluator import estimate_memory_gb
from .strategy import Strategy


ISLANDS = ("memory_safe", "topology_affinity", "pipeline_efficiency", "balanced_generalist")
FORBIDDEN_NODES = (
    ast.Import, ast.ImportFrom, ast.ClassDef, ast.AsyncFunctionDef, ast.For, ast.AsyncFor,
    ast.While, ast.With, ast.AsyncWith, ast.Try, ast.Raise, ast.Global, ast.Nonlocal,
    ast.Lambda, ast.Delete,
)
FORBIDDEN_CALLS = {
    "open", "eval", "exec", "compile", "__import__", "globals", "locals", "vars",
    "input", "breakpoint", "getattr", "setattr", "delattr",
}
SAFE_BUILTINS = {
    "abs": abs, "bool": bool, "float": float, "int": int, "len": len, "max": max,
    "min": min, "round": round, "sum": sum,
}


SEED_SOURCES = {
    "memory_safe": """
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mb = int(strategy["micro_batch_num"])
    local_batch = float(workload_cfg["global_batch_size"]) / dp
    return 900.0 + 18.0 * tp + 12.0 * pp + 0.2 * mb - 2.0 * local_batch
""".strip(),
    "topology_affinity": """
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    tp = int(strategy["tp"])
    active = int(strategy["active_gpus"])
    server_cards = int(topology_cfg["cards_per_server"])
    cross = 1.0 if active > server_cards else 0.0
    return 1000.0 + 30.0 * tp - 90.0 * cross - 3.0 * int(strategy["pp"])
""".strip(),
    "pipeline_efficiency": """
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    pp = int(strategy["pp"])
    mb = int(strategy["micro_batch_num"])
    bubble = float(pp - 1) / float(mb + pp - 1)
    schedule_bonus = 35.0 if strategy["schedule"] == "1f1b" else 0.0
    return 1000.0 - 500.0 * bubble + schedule_bonus + 0.5 * mb
""".strip(),
    "balanced_generalist": """
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mb = int(strategy["micro_batch_num"])
    bubble = float(pp - 1) / float(mb + pp - 1)
    comm_bonus = 18.0 if strategy["dp_communication"] == "rs_ag" else 0.0
    return 1000.0 + 14.0 * tp + 5.0 * dp - 220.0 * bubble + comm_bonus
""".strip(),
}


def validate_source(source: str) -> int:
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if len(tree.body) != 1 or len(functions) != 1 or functions[0].name != "score_strategy":
        raise ValueError("Program must contain only score_strategy")
    args = [arg.arg for arg in functions[0].args.args]
    if args != ["strategy", "model_cfg", "topology_cfg", "workload_cfg"]:
        raise ValueError("score_strategy must use the required four arguments")
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            raise ValueError(f"Forbidden syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError("Dunder names are forbidden")
        if isinstance(node, ast.Attribute) and (node.attr.startswith("_") or node.attr != "get"):
            raise ValueError(f"Forbidden attribute: {node.attr}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            raise ValueError(f"Forbidden call: {node.func.id}")
    return sum(1 for _ in ast.walk(tree))


def _score_worker(
    source: str,
    strategies: list[dict[str, Any]],
    model: dict[str, Any],
    topology: dict[str, Any],
    workload: dict[str, Any],
    output: mp.Queue,
) -> None:
    try:
        namespace: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
        exec(compile(source, "<evolved_program>", "exec"), namespace, namespace)
        scorer = namespace["score_strategy"]
        scores = []
        for strategy in strategies:
            value = scorer(strategy, model, topology, workload)
            score = float(value)
            if not math.isfinite(score):
                raise ValueError("Program returned a non-finite score")
            scores.append(score)
        output.put({"scores": scores})
    except Exception as exc:
        output.put({"error_type": type(exc).__name__, "error": str(exc)})


def score_program(
    source: str,
    strategies: list[Strategy],
    config: ScenarioConfig,
    timeout_s: float,
) -> tuple[list[tuple[Strategy, float]], int]:
    complexity = validate_source(source)
    topology_view = {
        "total_devices": int(config.topology["total_devices"]),
        "cards_per_server": max(
            len(server["ranks"])
            for affinity in config.topology["affinity_groups"]
            for server in affinity["servers"]
        ),
        "affinity_group_count": len(config.topology["affinity_groups"]),
    }
    payloads = [strategy.to_dict() for strategy in strategies]
    context = mp.get_context("spawn")
    output = context.Queue()
    process = context.Process(
        target=_score_worker,
        args=(source, payloads, config.model, topology_view, config.workload, output),
    )
    process.start()
    process.join(timeout_s)
    if process.is_alive():
        process.terminate()
        process.join()
        raise TimeoutError(f"Program exceeded {timeout_s} seconds")
    try:
        response = output.get_nowait()
    except queue.Empty as exc:
        raise RuntimeError("Program worker exited without a result") from exc
    if "error" in response:
        raise RuntimeError(f"{response['error_type']}: {response['error']}")
    return sorted(zip(strategies, response["scores"]), key=lambda item: (-item[1], item[0].signature)), complexity


@dataclass
class ProgramRecord:
    program_id: str
    island: str
    source: str
    generation: int
    parents: list[str] = field(default_factory=list)
    inspirations: list[str] = field(default_factory=list)
    origin: str = "seed"
    complexity: int = 0
    nominated: list[str] = field(default_factory=list)
    nominated_scores: dict[str, float] = field(default_factory=dict)
    nominated_ranks: dict[str, int] = field(default_factory=dict)
    evaluated_nominations: list[str] = field(default_factory=list)
    evaluated_nomination_scores: dict[str, float] = field(default_factory=dict)
    evaluated_nomination_ranks: dict[str, int] = field(default_factory=dict)
    best_latency_s: float | None = None
    top3_mean_latency_s: float | None = None
    failures: int = 0
    combined_score: float = 0.0
    cell: str = ""
    error: str | None = None

    @classmethod
    def create(
        cls, island: str, source: str, generation: int, *, parents: list[str] | None = None,
        inspirations: list[str] | None = None, origin: str = "child",
    ) -> "ProgramRecord":
        digest = hashlib.sha256(f"{island}:{generation}:{source}".encode("utf-8")).hexdigest()[:16]
        return cls(digest, island, source, generation, parents or [], inspirations or [], origin)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def feasible_strategies(strategies: list[Strategy], config: ScenarioConfig) -> list[Strategy]:
    return [strategy for strategy in strategies if not estimate_memory_gb(strategy, config)["oom"]]
