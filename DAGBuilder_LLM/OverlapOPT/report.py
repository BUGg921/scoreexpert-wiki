from __future__ import annotations

from typing import Any


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# OverlapOPT Report: {report['status'].upper()}",
        "",
        f"- Source DAG: `{report['source_dag_id']}`",
        f"- Overlapped DAG: `{report['overlapped_dag_id']}`",
        f"- Baseline latency: {report['baseline_latency_s']:.9f} s",
        f"- Overlap latency: {report['overlap_latency_s']:.9f} s",
        f"- Saved latency: {report['overlap_saved_s']:.9f} s",
        f"- Saved ratio: {report['overlap_saved_ratio']:.4%}",
        "",
        "## Applied Rules",
        "",
    ]
    if report["overlap_plan"]:
        for event in report["overlap_plan"]:
            lines.append(
                f"- `{event['rule']}` on `{event['node_id']}`: hidden {event['hidden_s']:.9f} s, remaining {event['remaining_s']:.9f} s."
            )
    else:
        lines.append("- No communication was hidden by the v1 rules.")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Original weighted DAG is left unchanged.",
            "- No dependency edge is removed in the derived DAG.",
            "- Only communication node durations and overlap annotations are rewritten.",
            "- Evaluation continues to use longest-path latency over the derived DAG.",
            "",
        ]
    )
    return "\n".join(lines)
