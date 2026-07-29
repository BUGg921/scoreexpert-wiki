from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TimingResult:
    duration_s: float
    source: str
    category: str
    algorithm: str
    collective: str | None = None
    domain: str | None = None
    rank_group: tuple[int, ...] = ()
    payload_scope: str | None = None
    logical_payload_bytes: float = 0.0
    local_payload_bytes: float = 0.0
    wire_bytes_per_rank: float = 0.0
    logical_steps: int = 0
    bucket_count: int = 1
    transfer_time_s: float = 0.0
    latency_time_s: float = 0.0
    local_copy_time_s: float = 0.0
    reduction_time_s: float = 0.0
    flops: float = 0.0
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        numeric = (
            self.duration_s,
            self.logical_payload_bytes,
            self.local_payload_bytes,
            self.wire_bytes_per_rank,
            self.transfer_time_s,
            self.latency_time_s,
            self.local_copy_time_s,
            self.reduction_time_s,
            self.flops,
        )
        if any(value < 0 for value in numeric):
            raise ValueError("TimingResult numeric fields must be non-negative")
        if self.logical_steps < 0 or self.bucket_count <= 0:
            raise ValueError("TimingResult steps/bucket_count is invalid")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rank_group"] = list(self.rank_group)
        return data


def operation_key(node: dict[str, Any]) -> str:
    return str(node.get("op_name") or node.get("node_id") or "")


def operation_config(config: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    operations = config["algorithms"].get("operations", {})
    for key in (str(node.get("node_id") or ""), str(node.get("op_name") or "")):
        if key and key in operations:
            return operations[key]
    task_kind = str(node.get("task_kind") or "")
    task_defaults = config["algorithms"].get("task_kinds", {})
    if task_kind in task_defaults:
        return task_defaults[task_kind]
    raise ValueError(f"No numerical algorithm configuration for node {node.get('node_id')}")


def resolve_payload(
    node: dict[str, Any],
    spec: dict[str, Any],
    domain_size: int,
    collective: str,
) -> tuple[float, float, str]:
    scope = str(spec.get("payload_scope") or node.get("payload_scope") or "")
    if not scope:
        raise ValueError(f"Node {node.get('node_id')} must declare payload_scope")
    if "payload_bytes" in spec:
        base = float(spec["payload_bytes"])
    elif "payload_elements" in spec:
        base = float(spec["payload_elements"]) * float(spec["dtype_bytes"])
    elif node.get("payload_bytes") is not None:
        base = float(node["payload_bytes"])
    elif node.get("payload_elements") is not None:
        dtype_bytes = spec.get("dtype_bytes") or node.get("dtype_bytes")
        if dtype_bytes is None:
            raise ValueError(f"Node {node.get('node_id')} has payload_elements but no dtype_bytes")
        base = float(node["payload_elements"]) * float(dtype_bytes)
    else:
        raise ValueError(f"Node {node.get('node_id')} has no payload input")
    if base < 0:
        raise ValueError("payload bytes must be non-negative")

    if scope == "full_tensor":
        logical = base
        local = base if collective == "all_reduce" else base / domain_size
    elif scope == "local_shard":
        local = base
        logical = base * domain_size
    elif scope == "replicated":
        logical = base
        local = base
    elif scope == "per_rank_send":
        local = base
        logical = base * domain_size
    else:
        raise ValueError(f"Unsupported payload_scope: {scope}")
    return logical, local, scope
