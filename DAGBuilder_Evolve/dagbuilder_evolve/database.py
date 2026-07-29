from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from .programs import ISLANDS, ProgramRecord


def fitness(record: ProgramRecord) -> tuple[float, float, int, int]:
    return (
        float("inf") if record.best_latency_s is None else record.best_latency_s,
        float("inf") if record.top3_mean_latency_s is None else record.top3_mean_latency_s,
        record.failures,
        len(record.source),
    )


@dataclass
class ProgramDatabase:
    capacity: int
    archive_size: int
    records: dict[str, ProgramRecord] = field(default_factory=dict)
    populations: dict[str, list[str]] = field(default_factory=lambda: {name: [] for name in ISLANDS})
    grids: dict[str, dict[str, str]] = field(default_factory=lambda: {name: {} for name in ISLANDS})
    global_archive: list[str] = field(default_factory=list)

    def _diversity(self, record: ProgramRecord) -> float:
        candidates = [
            set(self.records[item].nominated)
            for item in self.populations[record.island]
            if self.records[item].nominated
        ]
        current = set(record.nominated)
        if not candidates or not current:
            return 1.0
        similarity = max(
            len(current & other) / max(1, len(current | other)) for other in candidates
        )
        return 1.0 - similarity

    def add(self, record: ProgramRecord) -> bool:
        if any(item.source == record.source for item in self.records.values() if item.island == record.island):
            return False
        record.cell = f"c{min(4, record.complexity // 20)}_d{min(4, int(self._diversity(record) * 5))}"
        self.records[record.program_id] = record
        self.populations[record.island].append(record.program_id)
        prior = self.grids[record.island].get(record.cell)
        if prior is None or fitness(record) < fitness(self.records[prior]):
            self.grids[record.island][record.cell] = record.program_id
        self._refresh()
        return True

    def _refresh(self) -> None:
        ranked = sorted(
            (record for record in self.records.values() if record.best_latency_s is not None),
            key=fitness,
        )
        self.global_archive = [record.program_id for record in ranked[: self.archive_size]]
        protected = set(self.global_archive)
        for island in ISLANDS:
            population = self.populations[island]
            if population:
                protected.add(min(population, key=lambda item: fitness(self.records[item])))
            if len(population) > self.capacity:
                keep = sorted(
                    population,
                    key=lambda item: (item not in protected, fitness(self.records[item])),
                )[: self.capacity]
                self.populations[island] = keep
                allowed = set(keep)
                self.grids[island] = {
                    cell: item for cell, item in self.grids[island].items() if item in allowed
                }

    def best(self, island: str | None = None) -> ProgramRecord | None:
        ids = self.global_archive if island is None else self.populations[island]
        return self.records[min(ids, key=lambda item: fitness(self.records[item]))] if ids else None

    def sample(self, island: str, rng: random.Random) -> tuple[ProgramRecord, list[ProgramRecord]]:
        ids = self.populations[island]
        if not ids:
            raise ValueError(f"Island {island} is empty")
        chance = rng.random()
        if chance < 0.20:
            parent_id = rng.choice(ids)
        elif chance < 0.90:
            elite_ids = list(dict.fromkeys(self.grids[island].values()))
            parent_id = min(elite_ids, key=lambda item: fitness(self.records[item]))
        else:
            weights = [max(self.records[item].combined_score, 1e-12) for item in ids]
            parent_id = rng.choices(ids, weights=weights, k=1)[0]
        parent = self.records[parent_id]
        alternatives = [
            self.records[item] for item in dict.fromkeys(self.grids[island].values())
            if item != parent_id and self.records[item].cell != parent.cell
        ]
        if len(alternatives) < 2:
            alternatives.extend(
                self.records[item] for item in self.global_archive
                if item != parent_id and self.records[item] not in alternatives
            )
        return parent, alternatives[:2]

    def migrate_ring(self, generation: int) -> list[str]:
        migrated: list[str] = []
        for index, source_island in enumerate(ISLANDS):
            source = self.best(source_island)
            if source is None:
                continue
            target = ISLANDS[(index + 1) % len(ISLANDS)]
            copy = ProgramRecord.create(
                target, source.source, generation, parents=[source.program_id], origin="migration"
            )
            copy.complexity = source.complexity
            copy.nominated = list(source.nominated)
            copy.nominated_scores = dict(source.nominated_scores)
            copy.nominated_ranks = dict(source.nominated_ranks)
            copy.best_latency_s = source.best_latency_s
            copy.top3_mean_latency_s = source.top3_mean_latency_s
            copy.failures = source.failures
            copy.combined_score = source.combined_score
            if self.add(copy):
                migrated.append(copy.program_id)
        return migrated

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": {key: value.to_dict() for key, value in self.records.items()},
            "populations": self.populations,
            "grids": self.grids,
            "global_archive": self.global_archive,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any], capacity: int, archive_size: int) -> "ProgramDatabase":
        instance = cls(capacity, archive_size)
        instance.records = {
            key: ProgramRecord(**record) for key, record in value["records"].items()
        }
        instance.populations = {key: list(items) for key, items in value["populations"].items()}
        instance.grids = {
            key: dict(items) for key, items in value["grids"].items()
        }
        instance.global_archive = list(value["global_archive"])
        return instance
