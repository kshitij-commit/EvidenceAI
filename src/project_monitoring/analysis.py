"""Transparent project anomaly screening and similarity suggestions."""

from __future__ import annotations

from difflib import SequenceMatcher
from functools import lru_cache
from hashlib import sha256
import os
from pathlib import Path

import numpy as np
import pandas as pd


@lru_cache(maxsize=2)
def _local_sentence_model(path: str):
    """Load a user-configured local sentence model; never download one."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(path, device="cpu")


def _text(value: object) -> str:
    """Convert a nullable pandas value to text without truth-testing pd.NA."""
    return "" if value is None or pd.isna(value) else str(value)


def review_projects(projects: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """Add review indicators and an optional Isolation Forest flag.

    Scores are triage counts, never probabilities or findings of misconduct.
    The model uses only numeric fields available for at least 30 projects.
    """
    result = projects.copy()
    rules = {
        "flag_cost_increase": result.get("cost_overrun_pct", pd.Series(np.nan, index=result.index)).gt(0),
        "flag_expenditure_over_cost": result.get("expenditure_exceeds_revised_cost", pd.Series(False, index=result.index)).fillna(False),
        "flag_schedule_extension": result.get("schedule_deviation_months", pd.Series(np.nan, index=result.index)).gt(0),
        "flag_progress_out_of_range": result.get("invalid_progress", pd.Series(False, index=result.index)).fillna(False),
        "flag_financial_physical_gap": result.get("expenditure_progress_gap_pp", pd.Series(np.nan, index=result.index)).abs().ge(20),
    }
    for name, values in rules.items():
        result[name] = values.fillna(False).astype(bool)
    rule_columns = list(rules)
    result["rule_indicator_count"] = result[rule_columns].astype(int).sum(axis=1)
    result["model_flag"] = False
    result["model_score"] = np.nan
    result["model_status"] = "Model not run: fewer than 30 usable project records"
    feature_columns = [column for column in (
        "cost_overrun_pct", "expenditure_pct", "physical_progress_pct",
        "schedule_deviation_months", "expenditure_progress_gap_pp",
    ) if column in result]
    features = result[feature_columns].apply(pd.to_numeric, errors="coerce") if feature_columns else pd.DataFrame(index=result.index)
    usable = features.notna().any(axis=1)
    if int(usable.sum()) >= 30 and len(feature_columns) >= 2:
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.impute import SimpleImputer
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler

            model = make_pipeline(
                SimpleImputer(strategy="median"), StandardScaler(),
                IsolationForest(contamination=contamination, random_state=42, n_estimators=200),
            )
            model.fit(features.loc[usable])
            estimator = model[-1]
            matrix = model[:-1].transform(features.loc[usable])
            labels = estimator.predict(matrix)
            scores = estimator.decision_function(matrix)
            result.loc[usable, "model_flag"] = labels == -1
            result.loc[usable, "model_score"] = -scores
            result["model_status"] = f"Isolation Forest fit on {int(usable.sum()):,} records with numeric features"
        except Exception as exc:
            result["model_status"] = f"Model unavailable for this import: {type(exc).__name__}"
    result["review_priority"] = result["rule_indicator_count"] + result["model_flag"].astype(int)
    labels = {
        "flag_cost_increase": "Revised cost exceeds original cost",
        "flag_expenditure_over_cost": "Expenditure exceeds recorded revised cost",
        "flag_schedule_extension": "Revised completion date is later than original date",
        "flag_progress_out_of_range": "Physical progress is outside 0–100%",
        "flag_financial_physical_gap": "Expenditure-progress gap is at least 20 percentage points",
        "model_flag": "Isolation Forest statistical outlier",
    }
    result["review_indicators"] = result.apply(
        lambda row: " · ".join(label for key, label in labels.items() if bool(row.get(key, False))), axis=1
    )
    return result


def similar_projects(projects: pd.DataFrame, selected_key: str, limit: int = 10) -> pd.DataFrame:
    """Rank potential peers using recorded sector, cost range, and name text."""
    selected = projects[projects["record_key"].astype(str).eq(str(selected_key))]
    if selected.empty:
        return projects.iloc[0:0].copy()
    focus = selected.iloc[0]
    candidate_rows = projects[projects["record_key"].astype(str).ne(str(selected_key))].copy()
    if candidate_rows.empty:
        return candidate_rows

    scores = []
    criteria = []
    focus_sector = _text(focus.get("sector")).strip().casefold()
    focus_cost = pd.to_numeric(pd.Series([focus.get("original_cost")]), errors="coerce").iloc[0]
    focus_name = _text(focus.get("project_name")).casefold()
    semantic_scores = None
    model_path = os.environ.get("EVIDENCEAI_SENTENCE_MODEL", "").strip()
    if model_path and Path(model_path).is_dir():
        try:
            model = _local_sentence_model(str(Path(model_path).resolve()))
            texts = [focus_name] + candidate_rows.project_name.fillna("").astype(str).tolist()
            vectors = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True, show_progress_bar=False)
            semantic_scores = (vectors[1:] @ vectors[0]).cpu().numpy()
        except (ImportError, OSError, ValueError, RuntimeError):
            semantic_scores = None
    for candidate_index, (_, candidate) in enumerate(candidate_rows.iterrows()):
        score = 0.0
        reasons = []
        other_sector = _text(candidate.get("sector")).strip().casefold()
        if focus_sector and other_sector and focus_sector == other_sector:
            score += 0.5
            reasons.append("same sector")
        other_cost = pd.to_numeric(pd.Series([candidate.get("original_cost")]), errors="coerce").iloc[0]
        if pd.notna(focus_cost) and focus_cost > 0 and pd.notna(other_cost) and other_cost > 0:
            ratio = min(focus_cost, other_cost) / max(focus_cost, other_cost)
            if ratio >= 0.5:
                score += 0.3 * ratio
                reasons.append("original cost within a 2× range")
        other_name = _text(candidate.get("project_name")).casefold()
        if semantic_scores is not None and focus_name and other_name:
            semantic_score = max(0.0, float(semantic_scores[candidate_index]))
            if semantic_score >= 0.35:
                score += 0.4 * semantic_score
                reasons.append("local sentence-model description similarity")
        elif focus_name and other_name:
            text_score = SequenceMatcher(None, focus_name, other_name).ratio()
            if text_score >= 0.25:
                score += 0.2 * text_score
                reasons.append("project-name text overlap")
        scores.append(score)
        criteria.append("; ".join(reasons) or "No matching metadata; low-confidence fallback")
    candidate_rows["similarity_score"] = scores
    candidate_rows["comparison_criteria"] = criteria
    candidate_rows = candidate_rows[candidate_rows.similarity_score.gt(0)]
    return candidate_rows.sort_values("similarity_score", ascending=False).head(limit)


def entity_match_suggestions(names: list[str], threshold: int = 90) -> list[dict[str, str | int]]:
    """Suggest (never merge) similar recorded organization names."""
    unique = sorted({name.strip() for name in names if name and name.strip()}, key=str.casefold)
    if len(unique) < 2:
        return []
    try:
        from rapidfuzz import fuzz
        score_pair = lambda first, second: int(fuzz.token_set_ratio(first, second))
    except ImportError:
        score_pair = lambda first, second: round(100 * SequenceMatcher(None, first.casefold(), second.casefold()).ratio())
    suggestions = []
    for index, first in enumerate(unique):
        for second in unique[index + 1:]:
            score = score_pair(first, second)
            if score >= threshold:
                match_id = sha256(f"ministry|{first.casefold()}|{second.casefold()}".encode("utf-8")).hexdigest()
                suggestions.append({"match_id": match_id, "Recorded name A": first, "Recorded name B": second, "Similarity score": score, "Status": "Suggestion only; not merged"})
    return sorted(suggestions, key=lambda row: int(row["Similarity score"]), reverse=True)
