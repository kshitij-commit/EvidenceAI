"""Deterministic explanations from project fields and imported evidence only."""

from __future__ import annotations

import pandas as pd


def answer_project_question(project: pd.Series, question: str, evidence: list[dict] | None = None, peers: pd.DataFrame | None = None) -> str:
    """Answer common project questions without an LLM or unsupported inference."""
    query = question.casefold()
    def value(field: str) -> str:
        item = project.get(field)
        return "not recorded in this snapshot" if item is None or pd.isna(item) or not str(item).strip() else str(item)
    source = f"Source: {value('source_filename')}, row {value('source_row_number')} ({value('source_url')})."
    if any(term in query for term in ("evidence", "document", "report", "page", "source")):
        matches = evidence or []
        if not matches:
            return "No supporting document found in the available dataset. The imported project row remains available as source evidence. " + source
        citations = "\n".join(f"- {item.get('filename', 'Uploaded report')}, page {item.get('page_number', '?')}: {item.get('passage', '')}" for item in matches[:5])
        return "Matching text passages from uploaded reports:\n" + citations
    if any(term in query for term in ("why", "flag", "anomal", "review", "signal")):
        signal_value = project.get("review_indicators")
        signals = [part.strip() for part in ("" if signal_value is None or pd.isna(signal_value) else str(signal_value)).split("·") if part.strip()]
        explanation = "; ".join(signals) if signals else "No review signal was produced by the current checks."
        return f"The current review indicators are: {explanation} Review signals organize verification work; they are not proof, probability, or a finding of misconduct. {source}"
    if any(term in query for term in ("similar", "comparable", "peer")):
        if peers is None or peers.empty:
            return "No other project rows are available to compare in this snapshot. " + source
        labels = [str(row.get("project_name", "Project name not recorded")) for _, row in peers.head(5).iterrows()]
        return "Potential peers ranked using recorded sector, original-cost scale, and project-name text: " + "; ".join(labels) + ". These are comparison candidates, not validated like-for-like projects. " + source
    if any(term in query for term in ("overrun", "cost change", "cost revision", "revised cost")):
        result = value("cost_overrun_pct")
        basis = value("original_cost")
        revised = value("revised_cost")
        return f"Recorded original cost is {basis}; recorded revised cost is {revised}. Cost change is calculated as (revised − original) / original × 100 when original cost is positive. Calculated change: {result}%. {source}"
    if any(term in query for term in ("expenditure", "spent", "spending")):
        basis = value("revised_cost") if value("revised_cost") != "not recorded in this snapshot" else value("original_cost")
        return f"Recorded cumulative expenditure is {value('expenditure')}. Expenditure percentage uses revised cost when available, otherwise original cost; selected basis: {basis}. Calculated percentage: {value('expenditure_pct')}%. {source}"
    if any(term in query for term in ("physical progress", "progress", "expenditure gap", "financial")):
        return f"Physical progress: {value('physical_progress_pct')}%. Expenditure-progress gap: {value('expenditure_progress_gap_pp')} percentage points, calculated as expenditure percentage minus physical progress where progress is between 0% and 100%. {source}"
    if any(term in query for term in ("schedule", "delay", "completion date", "finish")):
        return f"Original completion date: {value('original_completion_date')}; revised completion date: {value('revised_completion_date')}. Schedule deviation is revised minus original date, expressed in average calendar months: {value('schedule_deviation_months')}. A positive value indicates a later recorded date; it does not by itself explain why the date changed. {source}"
    if any(term in query for term in ("ministry", "department", "sector", "state", "location", "project name", "project code", "project id")):
        return f"Project: {value('project_name')} (code {value('project_id')}); sector: {value('sector')}; ministry/department: {value('ministry')}; state/location: {value('state')}. {source}"
    return "I can explain recorded project facts, cost change, expenditure percentage, progress gap, schedule deviation, current review indicators, comparable-project candidates, and uploaded PDF passages. This question does not match those fields, so I won't infer an answer. " + source
