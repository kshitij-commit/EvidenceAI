"""Deterministic project investigation assembly and report generation."""

from __future__ import annotations

import pandas as pd

from src.project_monitoring.analysis import similar_projects
from src.project_monitoring.documents import retrieve_passages


def build_investigation(projects: pd.DataFrame, selected_key: str, documents: pd.DataFrame | None = None, source_row_number: int | None = None) -> dict:
    selected_rows = projects[projects["record_key"].astype(str).eq(str(selected_key))]
    if source_row_number is not None and "source_row_number" in selected_rows:
        selected_rows = selected_rows[pd.to_numeric(selected_rows.source_row_number, errors="coerce").eq(int(source_row_number))]
    if selected_rows.empty:
        raise ValueError("Selected project is not present in the current imported snapshot.")
    project = selected_rows.iloc[0]
    peer_rows = similar_projects(projects, selected_key, limit=10)
    evidence = []
    if documents is not None and not documents.empty:
        query_values = [project.get(field) for field in ("project_id", "project_name", "sector", "ministry")]
        query = " ".join(str(value) for value in query_values if value is not None and not pd.isna(value))
        evidence = retrieve_passages(documents.to_dict("records"), query)
    limits = []
    for field, label in (
        ("original_cost", "Original cost"), ("revised_cost", "Revised cost"),
        ("expenditure", "Cumulative expenditure"), ("physical_progress_pct", "Physical progress"),
        ("original_completion_date", "Original completion date"), ("revised_completion_date", "Revised completion date"),
    ):
        if field not in project.index or pd.isna(project.get(field)):
            limits.append(f"{label} is not available in this imported record.")
    if not evidence:
        limits.append("No supporting document found in the available dataset.")
    indicator_value = project.get("review_indicators")
    indicator_text = "" if indicator_value is None or pd.isna(indicator_value) else str(indicator_value).strip()
    return {
        "project": project,
        "peers": peer_rows,
        "evidence": evidence,
        "limitations": limits,
        "indicators": [item.strip() for item in indicator_text.split("·") if item.strip()],
        "review_priority": int(project.get("review_priority", 0) or 0),
    }


def investigation_markdown(case: dict) -> str:
    """Create an evidence-linked Markdown brief from an assembled case."""
    project = case["project"]
    def value(field, fallback="Not recorded"):
        item = project.get(field)
        return fallback if item is None or pd.isna(item) or str(item).strip() == "" else str(item)
    evidence_lines = [
        f"- **{item.get('filename', 'Uploaded report')}, page {item.get('page_number', '?')}:** {item.get('passage', '')} Source URL: {item.get('source_url') or 'Not recorded'}."
        for item in case["evidence"]
    ] or ["- No supporting document found in the available dataset."]
    peer_lines = [
        f"- {row.get('project_name', 'Unnamed project')} ({row.get('project_id', 'Project ID not recorded')}) — {row.get('comparison_criteria', 'No matching metadata')}; similarity score {float(row.get('similarity_score', 0)):.2f}."
        for _, row in case["peers"].head(5).iterrows()
    ] or ["- No other project records are available for comparison."]
    indicators = [f"- {item}" for item in case["indicators"]] or ["- No review indicators were produced."]
    limitations = [f"- {item}" for item in case["limitations"]] or ["- Required fields checked for this workflow are present; source completeness is not guaranteed."]
    return f"""# EvidenceAI project investigation brief

## Project record

- Project code: {value('project_id')}
- Project name: {value('project_name')}
- Sector: {value('sector')}
- Ministry/department: {value('ministry')}
- State/location: {value('state')}
- Original cost: {value('original_cost')} ({value('cost_unit', 'Source unit not specified')})
- Latest revised cost: {value('revised_cost')}
- Cumulative expenditure: {value('expenditure')}
- Physical progress: {value('physical_progress_pct')}%
- Original completion date: {value('original_completion_date')}
- Revised completion date: {value('revised_completion_date')}
- Source file: {value('source_filename')}
- Source row: {value('source_row_number')}
- Source reference: {value('source_url')}
- Source file SHA-256: {value('source_sha256')}

## Calculated indicators

- Cost overrun: {value('cost_overrun_pct')}%
- Expenditure against selected cost basis: {value('expenditure_pct')}%
- Schedule deviation: {value('schedule_deviation_months')} months
- Expenditure-progress gap: {value('expenditure_progress_gap_pp')} percentage points
- Review priority: {case['review_priority']} indicator count; this is not a probability or finding.

## Review signals

{chr(10).join(indicators)}

## Comparable project candidates

{chr(10).join(peer_lines)}

Comparison is a metadata-based candidate search. It does not establish equivalent scope, a validated benchmark, or causality.

## Retrieved document evidence

{chr(10).join(evidence_lines)}

## Data limitations

{chr(10).join(limitations)}

Signals and calculations support human review only. Confirm project values and documents against the originating source before drawing a conclusion.
"""
