from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Device:
    rank: int
    server_id: int
    affinity_group_id: int
    compute_tflops: float
    status: str = "normal"
    note: str = ""


@dataclass(frozen=True)
class LinkProfile:
    kind: str
    bandwidth_bytes_s: float
    latency_s: float
    physical_kind: str = ""
    status: str = "normal"
    override_scope: str = "default"
    override_endpoints: tuple[int, int] | None = None
    note: str = ""


class LinkUnavailableError(RuntimeError):
    """Raised when a numerical communication path uses a failed link."""


class Topology:
    """Resolved physical devices, links, communication groups, and fault overrides."""

    _SCOPE_PRIORITY = {"affinity": 1, "server": 2, "device": 3}

    def __init__(self, topology_config: dict[str, Any], network_config: dict[str, Any]) -> None:
        self._topology_config = topology_config
        self._network_config = network_config
        self._unit_bits = float(network_config.get("bandwidth_unit_bits", 1e9))
        if self._unit_bits <= 0:
            raise ValueError("network.bandwidth_unit_bits must be positive")
        self._links = self._build_link_profiles(network_config)
        self.devices = self._build_devices(topology_config)
        self.total_devices = len(self.devices)
        self.server_count = len({device.server_id for device in self.devices})
        self.affinity_group_count = len({device.affinity_group_id for device in self.devices})
        server_sizes = {
            sum(device.server_id == server_id for device in self.devices)
            for server_id in {device.server_id for device in self.devices}
        }
        affinity_server_counts = {
            len({device.server_id for device in self.devices if device.affinity_group_id == affinity_id})
            for affinity_id in {device.affinity_group_id for device in self.devices}
        }
        self.devices_per_server = next(iter(server_sizes)) if len(server_sizes) == 1 else 0
        self.servers_per_affinity_group = (
            next(iter(affinity_server_counts)) if len(affinity_server_counts) == 1 else 0
        )
        self._link_overrides = self._build_link_overrides(topology_config.get("link_overrides", []))

        self.domains: dict[str, tuple[tuple[int, ...], ...]] = {}
        for name, domain_config in topology_config.get("domains", {}).items():
            self.domains[str(name)] = self._build_domain(str(name), domain_config)

    @staticmethod
    def _rate_bytes_s(config: dict[str, Any], unit_bits: float) -> float:
        bandwidth = float(config["bandwidth_gbps"])
        efficiency = float(config.get("efficiency", 1.0))
        latency = float(config.get("latency_s", 0.0))
        if bandwidth <= 0 or not 0 < efficiency <= 1 or latency < 0:
            raise ValueError("Network bandwidth/efficiency/latency is invalid")
        return bandwidth * unit_bits / 8.0 * efficiency

    def _build_link_profiles(self, network: dict[str, Any]) -> dict[str, LinkProfile]:
        profiles: dict[str, LinkProfile] = {}
        for kind, config in network.items():
            if kind == "bandwidth_unit_bits" or not isinstance(config, dict) or "bandwidth_gbps" not in config:
                continue
            profiles[kind] = LinkProfile(
                kind=kind,
                physical_kind=kind,
                bandwidth_bytes_s=self._rate_bytes_s(config, self._unit_bits),
                latency_s=float(config.get("latency_s", 0.0)),
            )
        required = {"hccs_intra_server", "hccs_inter_server", "roce", "hbm"}
        missing = sorted(required - profiles.keys())
        if missing:
            raise ValueError(f"Missing required network profiles: {missing}")
        return profiles

    @staticmethod
    def _normalize_device_overrides(config: dict[str, Any]) -> dict[int, dict[str, Any]]:
        normalized: dict[int, dict[str, Any]] = {}
        for rank, value in config.get("device_compute_tflops", {}).items():
            normalized[int(rank)] = {"compute_tflops": float(value), "status": "slow"}
        for rank, value in config.get("device_overrides", {}).items():
            item = dict(value)
            normalized[int(rank)] = {**normalized.get(int(rank), {}), **item}
        return normalized

    def _build_devices(self, config: dict[str, Any]) -> tuple[Device, ...]:
        default_tflops = float(config["default_compute_tflops"])
        if default_tflops <= 0:
            raise ValueError("default_compute_tflops must be positive")
        overrides = self._normalize_device_overrides(config)
        placements: list[tuple[int, int, int]] = []

        if config.get("affinity_groups") is not None:
            affinity_ids: set[int] = set()
            server_ids: set[int] = set()
            ranks_seen: set[int] = set()
            for affinity in config["affinity_groups"]:
                affinity_id = int(affinity["affinity_group_id"])
                if affinity_id in affinity_ids:
                    raise ValueError(f"Duplicate affinity_group_id: {affinity_id}")
                affinity_ids.add(affinity_id)
                for server in affinity.get("servers", []):
                    server_id = int(server["server_id"])
                    if server_id in server_ids:
                        raise ValueError(f"Duplicate server_id: {server_id}")
                    server_ids.add(server_id)
                    ranks = [int(rank) for rank in server.get("ranks", [])]
                    if not ranks:
                        raise ValueError(f"Server {server_id} must contain at least one rank")
                    duplicate = sorted(ranks_seen.intersection(ranks))
                    if duplicate:
                        raise ValueError(f"Ranks appear in more than one server: {duplicate}")
                    if len(set(ranks)) != len(ranks):
                        raise ValueError(f"Server {server_id} contains duplicate ranks")
                    ranks_seen.update(ranks)
                    placements.extend((rank, server_id, affinity_id) for rank in ranks)
            if not placements:
                raise ValueError("Explicit topology must contain at least one server and rank")
            expected = set(range(len(placements)))
            if ranks_seen != expected:
                raise ValueError("Explicit topology ranks must be contiguous and cover 0..N-1 exactly once")
            configured_total = config.get("total_devices")
            if configured_total is not None and int(configured_total) != len(placements):
                raise ValueError("total_devices does not match the explicit affinity-group hierarchy")
        else:
            total = int(config["total_devices"])
            per_server = int(config["devices_per_server"])
            servers_per_affinity = int(config["servers_per_affinity_group"])
            if total <= 0 or per_server <= 0 or servers_per_affinity <= 0:
                raise ValueError("Topology dimensions must be positive")
            if total % per_server:
                raise ValueError("total_devices must be divisible by devices_per_server")
            server_count = total // per_server
            if server_count % servers_per_affinity:
                raise ValueError("server_count must be divisible by servers_per_affinity_group")
            placements = [
                (rank, rank // per_server, (rank // per_server) // servers_per_affinity)
                for rank in range(total)
            ]

        ranks = {rank for rank, _, _ in placements}
        invalid = sorted(set(overrides) - ranks)
        if invalid:
            raise ValueError(f"Device overrides contain invalid ranks: {invalid}")
        devices: list[Device] = []
        for rank, server_id, affinity_id in sorted(placements):
            override = overrides.get(rank, {})
            compute_tflops = float(override.get("compute_tflops", default_tflops))
            status = str(override.get("status", "normal")).lower()
            if compute_tflops <= 0:
                raise ValueError(f"Device {rank} compute_tflops must be positive")
            if status not in {"normal", "slow"}:
                raise ValueError(f"Device {rank} status must be normal or slow")
            devices.append(
                Device(
                    rank=rank,
                    server_id=server_id,
                    affinity_group_id=affinity_id,
                    compute_tflops=compute_tflops,
                    status=status,
                    note=str(override.get("note", "")),
                )
            )
        return tuple(devices)

    def _build_link_overrides(self, raw_overrides: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
        valid_ids = {
            "device": {device.rank for device in self.devices},
            "server": {device.server_id for device in self.devices},
            "affinity": {device.affinity_group_id for device in self.devices},
        }
        normalized: list[dict[str, Any]] = []
        seen: set[tuple[str, int, int, bool]] = set()
        for index, raw in enumerate(raw_overrides):
            item = dict(raw)
            scope = str(item.get("scope", "")).lower()
            if scope not in self._SCOPE_PRIORITY:
                raise ValueError(f"link_overrides[{index}].scope must be device, server, or affinity")
            endpoints = tuple(int(value) for value in item.get("endpoints", ()))
            if len(endpoints) != 2:
                raise ValueError(f"link_overrides[{index}].endpoints must contain two IDs")
            invalid = [value for value in endpoints if value not in valid_ids[scope]]
            if invalid:
                raise ValueError(f"link_overrides[{index}] contains invalid {scope} IDs: {invalid}")
            if scope == "device" and endpoints[0] == endpoints[1]:
                raise ValueError("A device link override must contain two different ranks")
            status = str(item.get("status", "slow")).lower()
            if status not in {"slow", "down"}:
                raise ValueError(f"link_overrides[{index}].status must be slow or down")
            bandwidth = item.get("bandwidth_gbps")
            latency = item.get("latency_s")
            if status == "slow" and bandwidth is None and latency is None:
                raise ValueError("A slow link override must provide bandwidth_gbps and/or latency_s")
            if bandwidth is not None and float(bandwidth) <= 0:
                raise ValueError("A link override bandwidth_gbps must be positive")
            if latency is not None and float(latency) < 0:
                raise ValueError("A link override latency_s must be non-negative")
            bidirectional = bool(item.get("bidirectional", True))
            key_endpoints = tuple(sorted(endpoints)) if bidirectional else endpoints
            key = (scope, key_endpoints[0], key_endpoints[1], bidirectional)
            if key in seen:
                raise ValueError(f"Duplicate link override for {scope} endpoints {key_endpoints}")
            seen.add(key)
            normalized.append(
                {
                    "scope": scope,
                    "endpoints": endpoints,
                    "status": status,
                    "bandwidth_gbps": float(bandwidth) if bandwidth is not None else None,
                    "efficiency": float(item.get("efficiency", 1.0)),
                    "latency_s": float(latency) if latency is not None else None,
                    "bidirectional": bidirectional,
                    "note": str(item.get("note", "")),
                }
            )
        return tuple(normalized)

    def _validate_group(self, domain: str, group: Iterable[int], size: int) -> tuple[int, ...]:
        ranks = tuple(int(rank) for rank in group)
        if len(ranks) != size:
            raise ValueError(f"Domain {domain} group has {len(ranks)} ranks, expected {size}")
        if len(set(ranks)) != len(ranks):
            raise ValueError(f"Domain {domain} group contains duplicate ranks: {ranks}")
        invalid = [rank for rank in ranks if rank < 0 or rank >= self.total_devices]
        if invalid:
            raise ValueError(f"Domain {domain} group contains out-of-range ranks: {invalid}")
        return ranks

    def _build_domain(self, name: str, config: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
        size = int(config["size"])
        if size <= 0 or self.total_devices % size:
            raise ValueError(f"Domain {name} size must be positive and divide total_devices")
        if "groups" in config:
            groups = tuple(self._validate_group(name, group, size) for group in config["groups"])
        else:
            stride = int(config.get("stride", 1))
            if stride <= 0:
                raise ValueError(f"Domain {name} stride must be positive")
            used: set[int] = set()
            built: list[tuple[int, ...]] = []
            for start in range(self.total_devices):
                if start in used:
                    continue
                group = tuple(start + index * stride for index in range(size))
                if group[-1] >= self.total_devices:
                    raise ValueError(
                        f"Domain {name} size={size}, stride={stride} cannot fully partition {self.total_devices} ranks"
                    )
                validated = self._validate_group(name, group, size)
                if used.intersection(validated):
                    raise ValueError(f"Domain {name} auto-generated overlapping groups")
                used.update(validated)
                built.append(validated)
            groups = tuple(built)
        flattened = [rank for group in groups for rank in group]
        if sorted(flattened) != list(range(self.total_devices)):
            raise ValueError(f"Domain {name} groups must cover every rank exactly once")
        return groups

    def device(self, rank: int) -> Device:
        if rank < 0 or rank >= self.total_devices:
            raise ValueError(f"Invalid global rank: {rank}")
        return self.devices[rank]

    def link_kind(self, source_rank: int, target_rank: int) -> str:
        source = self.device(source_rank)
        target = self.device(target_rank)
        if source.server_id == target.server_id:
            return "hccs_intra_server"
        if source.affinity_group_id == target.affinity_group_id:
            return "hccs_inter_server"
        return "roce"

    @staticmethod
    def _endpoints_match(actual: tuple[int, int], expected: tuple[int, int], bidirectional: bool) -> bool:
        return actual == expected or (bidirectional and actual == (expected[1], expected[0]))

    def _matching_override(self, source_rank: int, target_rank: int) -> dict[str, Any] | None:
        source = self.device(source_rank)
        target = self.device(target_rank)
        actual = {
            "device": (source.rank, target.rank),
            "server": (source.server_id, target.server_id),
            "affinity": (source.affinity_group_id, target.affinity_group_id),
        }
        matches = [
            item
            for item in self._link_overrides
            if self._endpoints_match(actual[item["scope"]], item["endpoints"], item["bidirectional"])
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: self._SCOPE_PRIORITY[item["scope"]])

    def link(self, source_rank: int, target_rank: int, default_profile_kind: str | None = None) -> LinkProfile:
        physical_kind = self.link_kind(source_rank, target_rank)
        base = self.link_profile(default_profile_kind or physical_kind)
        override = self._matching_override(source_rank, target_rank)
        if override is None:
            return LinkProfile(
                kind=base.kind,
                physical_kind=physical_kind,
                bandwidth_bytes_s=base.bandwidth_bytes_s,
                latency_s=base.latency_s,
            )
        if override["status"] == "down":
            note = f" ({override['note']})" if override["note"] else ""
            raise LinkUnavailableError(
                f"Communication link {source_rank}->{target_rank} is down via "
                f"{override['scope']} endpoints {override['endpoints']}{note}"
            )
        bandwidth = base.bandwidth_bytes_s
        if override["bandwidth_gbps"] is not None:
            bandwidth = (
                override["bandwidth_gbps"] * self._unit_bits / 8.0 * float(override["efficiency"])
            )
        return LinkProfile(
            kind=base.kind,
            physical_kind=physical_kind,
            bandwidth_bytes_s=bandwidth,
            latency_s=base.latency_s if override["latency_s"] is None else override["latency_s"],
            status=override["status"],
            override_scope=override["scope"],
            override_endpoints=override["endpoints"],
            note=override["note"],
        )

    def critical_link(
        self,
        ranks: tuple[int, ...],
        physical_kind: str | None = None,
        payload_bytes: float = 0.0,
        default_profile_kind: str | None = None,
    ) -> LinkProfile:
        candidates: list[LinkProfile] = []
        for source in ranks:
            for target in ranks:
                if source == target:
                    continue
                if physical_kind is not None and self.link_kind(source, target) != physical_kind:
                    continue
                candidates.append(self.link(source, target, default_profile_kind))
        if not candidates:
            return self.link_profile(default_profile_kind or physical_kind or "hccs_intra_server")
        return max(
            candidates,
            key=lambda profile: profile.latency_s + payload_bytes / profile.bandwidth_bytes_s,
        )

    def critical_link_for_pairs(
        self,
        pairs: Iterable[tuple[int, int]],
        payload_bytes: float = 0.0,
        default_profile_kind: str | None = None,
    ) -> LinkProfile:
        candidates = [
            self.link(source, target, default_profile_kind)
            for source, target in pairs
            if source != target
        ]
        if not candidates:
            return self.link_profile(default_profile_kind or "hccs_intra_server")
        return max(
            candidates,
            key=lambda profile: profile.latency_s + payload_bytes / profile.bandwidth_bytes_s,
        )

    def link_profile(self, kind: str) -> LinkProfile:
        if kind not in self._links:
            raise ValueError(f"Unknown link kind: {kind}")
        return self._links[kind]

    def group(self, domain: str, index: int = 0) -> tuple[int, ...]:
        if domain not in self.domains:
            raise ValueError(f"Unknown communication domain: {domain}")
        groups = self.domains[domain]
        if index < 0 or index >= len(groups):
            raise ValueError(f"Domain {domain} group index {index} is out of range")
        return groups[index]

    def group_for_rank(self, domain: str, rank: int) -> tuple[int, ...]:
        for group in self.domains.get(domain, ()):
            if rank in group:
                return group
        raise ValueError(f"Rank {rank} is not assigned to domain {domain}")

    def resolve_group(self, domain: str, node: dict[str, Any]) -> tuple[int, ...]:
        explicit = node.get("ranks") or node.get("rank_group")
        if explicit is not None:
            if domain not in self.domains:
                raise ValueError(f"Unknown communication domain: {domain}")
            expected_size = len(self.domains[domain][0])
            return self._validate_group(domain, explicit, expected_size)
        for key in ("global_rank", "rank"):
            if node.get(key) is not None:
                return self.group_for_rank(domain, int(node[key]))
        return self.group(domain, int(node.get("domain_group_index") or 0))

    def _hierarchy_dict(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for affinity_id in sorted({device.affinity_group_id for device in self.devices}):
            servers: list[dict[str, Any]] = []
            server_ids = sorted(
                {device.server_id for device in self.devices if device.affinity_group_id == affinity_id}
            )
            for server_id in server_ids:
                server_devices = [device for device in self.devices if device.server_id == server_id]
                servers.append(
                    {
                        "server_id": server_id,
                        "rank_count": len(server_devices),
                        "ranks": [device.rank for device in server_devices],
                    }
                )
            result.append(
                {
                    "affinity_group_id": affinity_id,
                    "server_count": len(servers),
                    "rank_count": sum(server["rank_count"] for server in servers),
                    "servers": servers,
                }
            )
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_devices": self.total_devices,
                "server_count": self.server_count,
                "affinity_group_count": self.affinity_group_count,
                "devices_per_server": self.devices_per_server,
                "servers_per_affinity_group": self.servers_per_affinity_group,
                "devices_per_affinity_group": (
                    self.devices_per_server * self.servers_per_affinity_group
                    if self.devices_per_server and self.servers_per_affinity_group
                    else 0
                ),
            },
            "affinity_groups": self._hierarchy_dict(),
            "devices": [asdict(device) for device in self.devices],
            "device_overrides": [
                asdict(device) for device in self.devices if device.status != "normal" or device.note
            ],
            "link_overrides": [dict(item) for item in self._link_overrides],
            "domains": {name: [list(group) for group in groups] for name, groups in self.domains.items()},
            "default_links": {kind: asdict(profile) for kind, profile in self._links.items()},
        }
