from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
DESKTOP = Path.home() / "Desktop"
ISLAND_DIR = ROOT / "ScoreExpert" / "islands" / "programs"
ISLANDS = (
    "memory_safe",
    "topology_affinity",
    "pipeline_efficiency",
    "balanced_generalist",
)


def set_fonts() -> None:
    for font_path in (
        r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ):
        if Path(font_path).exists():
            font_manager.fontManager.addfont(font_path)
    plt.rcParams["font.family"] = ["Noto Sans SC", "Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["axes.unicode_minus"] = False


def load_instruction(island: str) -> str:
    source = (ISLAND_DIR / f"{island}.py").read_text(encoding="utf-8")
    doc = ast.get_docstring(ast.parse(source)) or ""
    match = re.search(r"Island instruction:\s*(.+)", doc)
    if not match:
        raise ValueError(f"missing instruction for {island}")
    return match.group(1).strip()


def box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    *,
    fc: str,
    ec: str,
    title_size: float = 13.5,
    body_size: float = 10.0,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=1.6,
        edgecolor=ec,
        facecolor=fc,
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.05, title, ha="center", va="top", fontsize=title_size, weight="bold", color="#102027", zorder=3)
    ax.text(x + 0.028, y + h - 0.105, body, ha="left", va="top", fontsize=body_size, color="#263238", linespacing=1.28, zorder=3)


def arrow(ax, start: tuple[float, float], end: tuple[float, float], *, color: str = "#455A64", rad: float = 0.0) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=1.8,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=6,
            shrinkB=6,
            zorder=1,
        )
    )


def wrap_instruction(text: str, width: int = 58) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def main() -> None:
    set_fonts()
    DESKTOP.mkdir(parents=True, exist_ok=True)
    instructions = {island: load_instruction(island) for island in ISLANDS}

    fig, ax = plt.subplots(figsize=(16, 8), dpi=240)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.955,
        "Score-stage LLM Framework / Score 阶段 LLM 框架",
        ha="center",
        va="top",
        fontsize=19,
        weight="bold",
        color="#102027",
    )

    island_lines = []
    for island in ISLANDS:
        island_lines.append(f"{island}")
        island_lines.append(wrap_instruction(instructions[island]))
        island_lines.append("")
    island_body = "\n".join(island_lines).strip()
    box(
        ax,
        0.035,
        0.205,
        0.39,
        0.64,
        "Four islands and instructions\n四个 island 及其 instruction",
        island_body,
        fc="#F5F7FA",
        ec="#37474F",
        title_size=12.5,
        body_size=8.9,
    )

    box(
        ax,
        0.51,
        0.47,
        0.13,
        0.16,
        "LLM",
        "Evolve scoring logic\n生成/改写打分逻辑",
        fc="#EDE7F6",
        ec="#5E35B1",
        title_size=18,
        body_size=9.4,
    )

    box(
        ax,
        0.73,
        0.62,
        0.18,
        0.15,
        "Strategy Library\n策略库",
        "Candidate parallel strategies\nPP / TP / DP / micro-batch",
        fc="#E3F2FD",
        ec="#1565C0",
        title_size=12.5,
        body_size=9.3,
    )
    box(
        ax,
        0.73,
        0.33,
        0.18,
        0.18,
        "Experience Library\n经验库",
        "Good / bad / missed cases\nFailure cases\n优劣案例与失败经验",
        fc="#E8F5E9",
        ec="#2E7D32",
        title_size=12.5,
        body_size=8.4,
    )
    box(
        ax,
        0.52,
        0.095,
        0.19,
        0.18,
        "Evaluation\n评估反馈",
        "RuleCheck + DAG + ValueSim\ntotal_latency_s feedback\n真实延迟反馈",
        fc="#FCE4EC",
        ec="#AD1457",
        title_size=12.5,
        body_size=8.4,
    )

    arrow(ax, (0.425, 0.525), (0.51, 0.55), color="#455A64")
    arrow(ax, (0.64, 0.575), (0.73, 0.685), color="#455A64")
    arrow(ax, (0.64, 0.515), (0.73, 0.425), color="#455A64")
    arrow(ax, (0.82, 0.62), (0.68, 0.275), color="#AD1457", rad=0.18)
    arrow(ax, (0.73, 0.36), (0.68, 0.275), color="#AD1457", rad=-0.12)
    arrow(ax, (0.52, 0.20), (0.57, 0.47), color="#6A1B9A", rad=-0.18)

    ax.text(0.455, 0.59, "instruction", fontsize=9.5, color="#455A64")
    ax.text(0.655, 0.705, "generate", fontsize=9.5, color="#455A64")
    ax.text(0.655, 0.445, "update", fontsize=9.5, color="#455A64")
    ax.text(0.48, 0.32, "feedback loop / 反馈闭环", fontsize=10.5, color="#6A1B9A")

    png_path = DESKTOP / "score_stage_llm_framework.png"
    svg_path = DESKTOP / "score_stage_llm_framework.svg"
    md_path = DESKTOP / "island_instructions.md"
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.18)
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)

    md_lines = ["# Four islands and instructions", ""]
    for island in ISLANDS:
        md_lines.append(f"## {island}")
        md_lines.append(instructions[island])
        md_lines.append("")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(png_path)
    print(svg_path)
    print(md_path)


if __name__ == "__main__":
    main()
