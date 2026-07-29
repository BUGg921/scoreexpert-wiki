from __future__ import annotations

import ast
import pprint
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


ISLANDS = ("memory_safe", "topology_affinity", "pipeline_efficiency", "balanced_generalist")
ROOT = Path(__file__).resolve().parent
ISLAND_ROOT = ROOT / "islands"
SEED_DIR = ISLAND_ROOT / "seeds"
PROGRAM_DIR = ISLAND_ROOT / "programs"


def island_path(island: str) -> Path:
    if island not in ISLANDS:
        raise ValueError(f"unknown island: {island}")
    return PROGRAM_DIR / f"{island}.py"


def seed_path(island: str) -> Path:
    if island not in ISLANDS:
        raise ValueError(f"unknown island: {island}")
    return SEED_DIR / f"{island}.py"


def read_island_source(island: str) -> str:
    return island_path(island).read_text(encoding="utf-8")


def read_seed_source(island: str) -> str:
    return seed_path(island).read_text(encoding="utf-8")


def extract_score_source(source: str) -> str:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "score_strategy":
            return ast.get_source_segment(source, node) or ""
    raise ValueError("score_strategy was not found.")


def load_score_source(island: str) -> str:
    active = load_active_program(island)
    if active is not None:
        return str(active["source"])
    return extract_score_source(read_island_source(island))


def load_instruction(island: str) -> str:
    tree = ast.parse(read_island_source(island))
    doc = ast.get_docstring(tree)
    return "" if doc is None else doc


def load_leaders(island: str) -> list[dict[str, Any]]:
    value = load_assignment(island, "ISLAND_LEADERS")
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    return []


def load_program_bank(island: str) -> list[dict[str, Any]]:
    value = load_assignment(island, "PROGRAM_BANK")
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    source = extract_score_source(read_island_source(island))
    return [
        {
            "program_id": "v0",
            "parent_ids": [],
            "source": source,
            "island_score": None,
            "evaluation": None,
            "origin": "seed_from_score_strategy",
        }
    ]


def load_active_program_id(island: str) -> str:
    value = load_assignment(island, "ACTIVE_PROGRAM_ID")
    if isinstance(value, str) and value:
        return value
    return "v0"


def load_active_program(island: str) -> dict[str, Any] | None:
    active_id = load_active_program_id(island)
    for program in load_program_bank(island):
        if str(program.get("program_id")) == active_id:
            return program
    bank = load_program_bank(island)
    return bank[0] if bank else None


def load_assignment(island: str, name: str) -> Any:
    tree = ast.parse(read_island_source(island))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if name in names:
                return ast.literal_eval(node.value)
    return None


def update_leaders(island: str, leaders: list[dict[str, Any]]) -> None:
    replace_assignment(island, "ISLAND_LEADERS", format_leaders(leaders))


def update_program_bank(island: str, program_bank: list[dict[str, Any]], active_program_id: str | None = None) -> None:
    if active_program_id is None:
        active_program_id = str(program_bank[0]["program_id"]) if program_bank else "v0"
    active_program = next((item for item in program_bank if str(item.get("program_id")) == active_program_id), None)
    if active_program is None:
        raise ValueError(f"active program {active_program_id} was not found in {island}")
    replace_assignment(island, "PROGRAM_BANK", format_program_bank(program_bank))
    replace_assignment(island, "ACTIVE_PROGRAM_ID", f"ACTIVE_PROGRAM_ID = {active_program_id!r}")
    replace_score_strategy(island, str(active_program["source"]))


def append_program(island: str, program: dict[str, Any], *, activate: bool = True, max_programs: int = 12) -> list[dict[str, Any]]:
    bank = load_program_bank(island)
    if any(str(item.get("program_id")) == str(program.get("program_id")) for item in bank):
        raise ValueError(f"duplicate program_id for {island}: {program.get('program_id')}")
    if activate:
        bank = sorted(bank, key=program_sort_key, reverse=True)[: max(0, max_programs - 1)]
        bank.append(dict(program))
    else:
        bank.append(dict(program))
        bank = sorted(bank, key=program_sort_key, reverse=True)[:max_programs]
    active_id = str(program["program_id"]) if activate else load_active_program_id(island)
    if active_id not in {str(item.get("program_id")) for item in bank}:
        active_id = str(bank[0]["program_id"])
    update_program_bank(island, bank, active_id)
    return bank


def initialize_new_island(island: str, instruction: str, score_source: str) -> None:
    if island in ISLANDS:
        raise ValueError(f"island already exists: {island}")
    program = {
        "program_id": "v0",
        "parent_ids": [],
        "source": score_source,
        "island_score": None,
        "evaluation": None,
        "origin": "seed",
    }
    seed_file = render_island_file(instruction, program, immutable=True)
    program_file = render_island_file(instruction, program, immutable=False)
    seed_target = SEED_DIR / f"{island}.py"
    program_target = PROGRAM_DIR / f"{island}.py"
    if seed_target.exists() or program_target.exists():
        raise ValueError(f"island file already exists: {island}")
    seed_target.write_text(seed_file, encoding="utf-8")
    program_target.write_text(program_file, encoding="utf-8")


def program_sort_key(program: dict[str, Any]) -> tuple[int, float, int, int]:
    score = program.get("island_score")
    has_score = 1 if isinstance(score, (int, float)) else 0
    score_value = float(score) if has_score else float("-inf")
    source_len = len(str(program.get("source", "")))
    version = int(str(program.get("program_id", "v0")).lstrip("v") or 0) if str(program.get("program_id", "v0")).startswith("v") else 0
    return (has_score, score_value, -source_len, version)


def replace_assignment(island: str, assignment_name: str, replacement: str) -> None:
    path = island_path(island)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assign_node: ast.Assign | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if assignment_name in names:
                assign_node = node
                break
    if assign_node is None or assign_node.lineno is None or assign_node.end_lineno is None:
        raise ValueError(f"{assignment_name} was not found in {path}")

    lines = source.splitlines()
    updated = lines[: assign_node.lineno - 1] + replacement.splitlines() + lines[assign_node.end_lineno :]
    path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def format_leaders(leaders: list[dict[str, Any]]) -> str:
    lines = ["ISLAND_LEADERS = ["]
    for item in leaders[:4]:
        formatted = pprint.pformat(normalize_payload(item), width=100, sort_dicts=False)
        indented = "\n".join(f"    {line}" for line in formatted.splitlines())
        lines.append(f"{indented},")
    lines.append("]")
    return "\n".join(lines)


def format_program_bank(program_bank: list[dict[str, Any]]) -> str:
    lines = ["PROGRAM_BANK = ["]
    for program in program_bank:
        normalized = normalize_payload({key: value for key, value in program.items() if key != "source"})
        lines.append("    {")
        for key, value in normalized.items():
            lines.append(f"        {key!r}: {value!r},")
        lines.append("        'source': " + triple_quote(str(program.get("source", ""))) + ",")
        lines.append("    },")
    lines.append("]")
    return "\n".join(lines)


def triple_quote(value: str) -> str:
    escaped = value.replace('"""', '\\"\\"\\"').rstrip() + "\n"
    return f'"""{escaped}"""'


def replace_score_strategy(island: str, score_source: str) -> None:
    path = island_path(island)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn_node: ast.FunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "score_strategy":
            fn_node = node
            break
    if fn_node is None or fn_node.lineno is None or fn_node.end_lineno is None:
        raise ValueError(f"score_strategy was not found in {path}")
    lines = source.splitlines()
    replacement = score_source.strip().splitlines()
    updated = lines[: fn_node.lineno - 1] + replacement + lines[fn_node.end_lineno :]
    path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def render_island_file(instruction: str, seed_program: dict[str, Any], *, immutable: bool) -> str:
    header = "This file is an immutable record. Evolution must update ScoreExpert/islands/programs only." if immutable else "Active evolution file."
    source = str(seed_program["source"]).strip()
    lines = [
        '"""',
        f"Island instruction: {instruction}",
        header,
        '"""',
        "",
        "ACTIVE_PROGRAM_ID = 'v0'",
        "",
        format_program_bank([seed_program]),
        "",
        "ISLAND_LEADERS = []",
        "",
        "",
        source,
        "",
    ]
    return "\n".join(lines)


def normalize_payload(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return normalize_payload(asdict(value))
    if isinstance(value, dict):
        return {str(key): normalize_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_payload(item) for item in value]
    if isinstance(value, float):
        return round(value, 9)
    return value
