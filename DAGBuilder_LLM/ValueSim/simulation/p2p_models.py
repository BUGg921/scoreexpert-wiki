from __future__ import annotations

from typing import Any

try:
    from .collective_models import TimingResult, effective_bandwidth_bytes_per_s
except ImportError:  # pragma: no cover - supports direct script execution.
    from collective_models import TimingResult, effective_bandwidth_bytes_per_s


def estimate_pp_p2p(config: dict[str, Any], payload_bytes: float) -> TimingResult:
    network = config["network_config"]
    value_sim = config.get("value_sim_config", {})
    link_type = value_sim.get("pp_link_type", "hccs")
    if link_type == "roce":
        bandwidth_gbps = float(network["roce_bandwidth_gbps"])
        efficiency = float(network["bandwidth_utilization_ratio"])
        latency_s = float(network["roce_static_delay_s"])
    elif link_type in {"hccs", "innode"}:
        bandwidth_gbps = float(network["hccs_bandwidth_gbps"])
        efficiency = float(network["hccs_bandwidth_utilization_ratio"])
        latency_s = float(network["npu_innode_static_delay_s"])
    else:
        raise ValueError(f"Unsupported pp_link_type: {link_type}")
    bandwidth = effective_bandwidth_bytes_per_s(bandwidth_gbps, efficiency)
    duration = latency_s + payload_bytes / bandwidth
    return TimingResult(
        duration_s=duration,
        payload_bytes=payload_bytes,
        detail={"link_type": link_type, "latency_s": latency_s, "effective_bandwidth_bytes_per_s": bandwidth},
    )
