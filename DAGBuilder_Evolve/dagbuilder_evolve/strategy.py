from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Strategy:
    pp: int
    tp: int
    dp: int
    micro_batch_num: int
    schedule: str
    dp_communication: str

    @property
    def active_gpus(self) -> int:
        return self.pp * self.tp * self.dp

    @property
    def signature(self) -> str:
        short = "ar" if self.dp_communication == "allreduce" else "rsag"
        return f"pp{self.pp}_tp{self.tp}_dp{self.dp}_mb{self.micro_batch_num}_{self.schedule}_{short}"

    @property
    def cache_key(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"active_gpus": self.active_gpus, "signature": self.signature}


def enumerate_strategies(config: Any) -> list[Strategy]:
    model = config.model
    workload = config.workload
    search = config.search
    total = int(config.topology["total_devices"])
    allowed_active = set(int(value) for value in search.get("active_gpu_counts", [total]))
    result: dict[str, Strategy] = {}
    for pp in search["pp_values"]:
        pp = int(pp)
        if int(model["num_layers"]) % pp:
            continue
        for tp in search["tp_values"]:
            tp = int(tp)
            if int(model["hidden_size"]) % tp:
                continue
            for dp in search["dp_values"]:
                dp = int(dp)
                active = pp * tp * dp
                if active > total or active not in allowed_active:
                    continue
                if int(workload["global_batch_size"]) % dp:
                    continue
                for microbatches in search["micro_batch_num_values"]:
                    microbatches = int(microbatches)
                    if int(workload["global_batch_size"]) % (dp * microbatches):
                        continue
                    schedules = ["1f1b"] if pp == 1 else search["schedules"]
                    dp_options = ["rs_ag"] if dp == 1 else search["dp_communications"]
                    for schedule in schedules:
                        for dp_comm in dp_options:
                            item = Strategy(pp, tp, dp, microbatches, schedule, dp_comm)
                            result[item.signature] = item
    return [result[key] for key in sorted(result)]


def rank_mapping(strategy: Strategy) -> list[dict[str, int]]:
    mapping = []
    for pp_stage in range(strategy.pp):
        for dp_rank in range(strategy.dp):
            for tp_rank in range(strategy.tp):
                global_rank = ((pp_stage * strategy.dp) + dp_rank) * strategy.tp + tp_rank
                mapping.append(
                    {
                        "global_rank": global_rank,
                        "pp_stage": pp_stage,
                        "dp_rank": dp_rank,
                        "tp_rank": tp_rank,
                    }
                )
    ranks = [item["global_rank"] for item in mapping]
    if ranks != list(range(strategy.active_gpus)):
        raise AssertionError("PP-major rank mapping is not contiguous")
    return mapping


def communication_groups(strategy: Strategy) -> dict[str, list[list[int]]]:
    mapping = rank_mapping(strategy)
    tp_groups = [
        [item["global_rank"] for item in mapping if item["pp_stage"] == pp and item["dp_rank"] == dp]
        for pp in range(strategy.pp)
        for dp in range(strategy.dp)
    ]
    dp_groups = [
        [item["global_rank"] for item in mapping if item["pp_stage"] == pp and item["tp_rank"] == tp]
        for pp in range(strategy.pp)
        for tp in range(strategy.tp)
    ]
    pp_groups = [
        [item["global_rank"] for item in mapping if item["dp_rank"] == dp and item["tp_rank"] == tp]
        for dp in range(strategy.dp)
        for tp in range(strategy.tp)
    ]
    return {"tp": tp_groups, "dp": dp_groups, "pp": pp_groups}

