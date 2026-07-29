from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    repository_root: Path
    output_root: Path
    model: dict[str, Any]
    workload: dict[str, Any]
    memory: dict[str, Any]
    topology: dict[str, Any]
    network: dict[str, Any]
    search: dict[str, Any]
    evolution: dict[str, Any]
    deepseek: dict[str, Any]

    @classmethod
    def from_dict(cls, value: dict[str, Any], *, source: Path) -> "ScenarioConfig":
        required = {
            "name", "repository_root", "output_root", "model", "workload", "memory",
            "topology", "network", "search", "evolution", "deepseek",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ValueError(f"Scenario is missing sections: {missing}")
        data = copy.deepcopy(value)
        for key in ("repository_root", "output_root"):
            path = Path(data[key])
            if not path.is_absolute():
                path = (source.parent / path).resolve()
            data[key] = path
        if not data["repository_root"].exists():
            raise FileNotFoundError(data["repository_root"])
        total = int(data["topology"]["total_devices"])
        if total <= 0:
            raise ValueError("topology.total_devices must be positive")
        all_ranks: list[int] = []
        for affinity in data["topology"]["affinity_groups"]:
            for server in affinity["servers"]:
                all_ranks.extend(int(rank) for rank in server["ranks"])
        if sorted(all_ranks) != list(range(total)):
            raise ValueError("Physical topology must cover every rank exactly once")
        if int(data["model"]["num_layers"]) <= 0 or int(data["workload"]["global_batch_size"]) <= 0:
            raise ValueError("Model layers and global batch size must be positive")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        value = {
            key: copy.deepcopy(getattr(self, key))
            for key in (
                "name", "repository_root", "output_root", "model", "workload", "memory",
                "topology", "network", "search", "evolution", "deepseek",
            )
        }
        value["repository_root"] = str(value["repository_root"])
        value["output_root"] = str(value["output_root"])
        return value

    def fingerprint(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def load_scenario(path: Path) -> ScenarioConfig:
    path = path.resolve()
    spec = importlib.util.spec_from_file_location(f"dagbuilder_evolve_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load scenario: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = module.get_config() if hasattr(module, "get_config") else module.CONFIG
    return ScenarioConfig.from_dict(value, source=path)

