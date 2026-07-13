#!/usr/bin/env python3
"""Zero-dependency health check for this Markdown wiki."""

from __future__ import annotations

import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE_DIRS = ("entities", "concepts", "comparisons", "queries")
REQUIRED = {"title", "created", "updated", "type", "tags", "sources"}
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def parse_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return {}, text
    head, body = text[4:].split("\n---\n", 1)
    data: dict[str, object] = {}
    for line in head.splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            data[key] = [] if not inner else [x.strip().strip("'\"") for x in inner.split(",")]
        elif raw in {"true", "false"}:
            data[key] = raw == "true"
        else:
            data[key] = raw.strip("'\"")
    return data, body


def links(text: str) -> set[str]:
    return {match.strip() for match in WIKILINK_RE.findall(text)}


def taxonomy() -> set[str]:
    text = (ROOT / "SCHEMA.md").read_text(encoding="utf-8")
    section = text.split("## Tag Taxonomy", 1)[1].split("\n## ", 1)[0]
    return set(re.findall(r"^- `([^`]+)`", section, flags=re.MULTILINE))


def main() -> int:
    errors: list[str] = []
    reviews: list[str] = []
    pages = [p for d in PAGE_DIRS for p in sorted((ROOT / d).glob("*.md"))]
    by_slug = {p.stem: p for p in pages}
    allowed_tags = taxonomy()
    outbound: dict[str, set[str]] = {}
    inbound: dict[str, set[str]] = defaultdict(set)

    for page in pages:
        meta, body = parse_frontmatter(page)
        rel = page.relative_to(ROOT)
        missing = REQUIRED - meta.keys()
        if missing:
            errors.append(f"{rel}: missing frontmatter fields {sorted(missing)}")
        tags = set(meta.get("tags", []))
        unknown = tags - allowed_tags
        if unknown:
            errors.append(f"{rel}: unknown tags {sorted(unknown)}")
        sources = meta.get("sources", [])
        for source in sources if isinstance(sources, list) else []:
            if not (ROOT / str(source)).exists():
                errors.append(f"{rel}: missing source {source}")
        page_links = links(body)
        outbound[page.stem] = page_links
        if len(page_links) < 2:
            errors.append(f"{rel}: only {len(page_links)} outbound wikilink(s)")
        for target in page_links:
            if target not in by_slug:
                errors.append(f"{rel}: broken wikilink [[{target}]]")
            else:
                inbound[target].add(page.stem)
        if meta.get("confidence") == "low":
            reviews.append(f"{rel}: confidence=low")
        if meta.get("contested") is True:
            reviews.append(f"{rel}: contested=true")
        if len(page.read_text(encoding="utf-8").splitlines()) > 200:
            reviews.append(f"{rel}: over 200 lines")

    for slug, page in by_slug.items():
        if not inbound.get(slug):
            errors.append(f"{page.relative_to(ROOT)}: orphan page with no inbound wikilinks")

    index_links = links((ROOT / "index.md").read_text(encoding="utf-8"))
    for slug, page in by_slug.items():
        if slug not in index_links:
            errors.append(f"{page.relative_to(ROOT)}: missing from index.md")
    for target in index_links:
        if target not in by_slug:
            errors.append(f"index.md: broken wikilink [[{target}]]")

    for raw in sorted((ROOT / "raw").rglob("*.md")):
        meta, body = parse_frontmatter(raw)
        rel = raw.relative_to(ROOT)
        expected = str(meta.get("sha256", ""))
        actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if not expected:
            errors.append(f"{rel}: missing raw-source sha256")
        elif expected != actual:
            errors.append(f"{rel}: source drift, sha256 mismatch")
        source_path = Path(str(meta.get("source_path", "")))
        original_sha = str(meta.get("original_sha256", ""))
        if source_path.is_file() and original_sha:
            current_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if current_sha != original_sha:
                reviews.append(f"{rel}: upstream source changed; ingest a new snapshot")

    log_entries = len(re.findall(r"^## \[", (ROOT / "log.md").read_text(encoding="utf-8"), re.M))
    if log_entries > 500:
        reviews.append("log.md: over 500 entries; rotate the log")

    print(f"Pages: {len(pages)} | Errors: {len(errors)} | Review items: {len(reviews)}")
    if errors:
        print("\nERRORS")
        for item in errors:
            print(f"- {item}")
    if reviews:
        print("\nREVIEW")
        for item in reviews:
            print(f"- {item}")
    if not errors:
        print("\nStructural checks passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
