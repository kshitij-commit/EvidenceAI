"""FastAPI interface for the PAIMANA project-monitoring workspace."""

from __future__ import annotations

from io import BytesIO
import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import pandas as pd

from src.project_monitoring.analysis import entity_match_suggestions, review_projects, similar_projects
from src.project_monitoring.data import PAIMANA_SOURCE_URL, engineer_project_features, project_quality_summary, read_project_export
from src.project_monitoring.documents import extract_pdf, retrieve_passages
from src.project_monitoring.investigations import build_investigation, investigation_markdown
from src.project_monitoring.questions import answer_project_question
from src.project_monitoring.storage import DEFAULT_DB, confirm_entity_match, list_entity_match_statuses, list_evidence, list_imports, list_investigations, load_import, preserve_source_export, preserve_uploaded_document, save_document, save_entity_match_suggestions, save_import, save_investigation, save_review_results


app = FastAPI(title="EvidenceAI Project Monitoring API", version="1.0.0", description="Local, evidence-grounded analysis for user-imported PAIMANA project exports.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@lru_cache(maxsize=4)
def _load_reviewed_cached(import_id: str) -> pd.DataFrame:
    if not any(item["import_id"] == import_id for item in list_imports(DEFAULT_DB)):
        raise HTTPException(status_code=404, detail="Import snapshot was not found.")
    projects = load_import(import_id, DEFAULT_DB)
    if projects.empty:
        raise HTTPException(status_code=404, detail="This import has no project rows.")
    projects = review_projects(engineer_project_features(projects))
    save_review_results(projects, import_id, DEFAULT_DB)
    return projects


def _load_reviewed(import_id: str) -> pd.DataFrame:
    # Model fitting is expensive; compute once per source snapshot per API process.
    return _load_reviewed_cached(import_id).copy()


def _project(projects: pd.DataFrame, record_key: str, source_row: int | None = None) -> pd.Series:
    matches = projects[projects.record_key.astype(str).eq(str(record_key))]
    if source_row is not None:
        matches = matches[pd.to_numeric(matches.source_row_number, errors="coerce").eq(int(source_row))]
    if matches.empty:
        raise HTTPException(status_code=404, detail="Project record was not found in this snapshot.")
    return matches.iloc[0]


def _safe_value(value):
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _records(frame: pd.DataFrame) -> list[dict]:
    return [{str(key): _safe_value(value) for key, value in row.items()} for row in frame.to_dict("records")]


@app.get("/api/health")
def health():
    return {"status": "ok", "workspace": "PAIMANA project monitoring", "database": str(DEFAULT_DB)}


@app.get("/api/imports")
def imports():
    return list_imports(DEFAULT_DB)


@app.post("/api/imports")
async def import_projects(file: UploadFile = File(...), source_url: str = Form(default=PAIMANA_SOURCE_URL)):
    suffix = Path(file.filename or "").suffix.casefold()
    if suffix not in {".csv", ".xlsx", ".xlsm"}:
        raise HTTPException(status_code=415, detail="Upload a PAIMANA CSV or XLSX/XLSM export.")
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Project exports must be 50 MB or smaller.")
    try:
        projects, info = read_project_export(file.filename or "project-export.csv", content, source_url)
        preserve_source_export(content, info, DEFAULT_DB)
        import_id = save_import(projects, info, DEFAULT_DB)
        reviewed = review_projects(engineer_project_features(projects))
        save_review_results(reviewed, import_id, DEFAULT_DB)
        return {"import_id": import_id, "filename": info.filename, "rows": len(projects), "source_url": info.source_url, "imported_at": info.imported_at, "cost_unit": info.cost_unit, "quality": project_quality_summary(reviewed)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Import failed: {type(exc).__name__}: {exc}") from exc


@app.get("/api/imports/{import_id}/summary")
def portfolio_summary(import_id: str):
    projects = _load_reviewed(import_id)
    quality = project_quality_summary(projects)
    def total(field):
        return _safe_value(pd.to_numeric(projects[field], errors="coerce").sum(min_count=1))
    sector_counts = projects.sector.fillna("Not recorded").value_counts().head(15).rename_axis("sector").reset_index(name="projects")
    yearly = projects.original_completion_date.dropna().dt.year.value_counts().sort_index().rename_axis("year").reset_index(name="projects") if pd.api.types.is_datetime64_any_dtype(projects.original_completion_date) else pd.DataFrame(columns=["year", "projects"])
    valid_progress = pd.to_numeric(projects.physical_progress_pct, errors="coerce")
    progress_counts = (pd.cut(valid_progress[valid_progress.between(0, 100)], bins=[0,10,20,30,40,50,60,70,80,90,100], include_lowest=True).value_counts().sort_index().rename_axis("band").reset_index(name="projects"))
    progress_counts["band"] = progress_counts.band.astype(str)
    def band_counts(values: pd.Series, edges: list[float], labels: list[str]) -> list[dict]:
        numeric = pd.to_numeric(values, errors="coerce").dropna()
        if numeric.empty:
            return []
        counts = pd.cut(numeric, bins=edges, labels=labels, include_lowest=True, right=False).value_counts(sort=False)
        return [{"band": label, "projects": int(counts.loc[label])} for label in labels]
    cost_change_bands = band_counts(projects.cost_overrun_pct, [-float("inf"), 0, 10, 25, 50, 100, float("inf")], ["Below zero", "0–10%", "10–25%", "25–50%", "50–100%", "Above 100%"])
    expenditure_bands = band_counts(projects.expenditure_pct, [-float("inf"), 0, 50, 80, 100, 120, float("inf")], ["Below zero", "0–50%", "50–80%", "80–100%", "100–120%", "Above 120%"])
    schedule_bands = band_counts(projects.schedule_deviation_months, [-float("inf"), 0, 3, 6, 12, 24, 60, float("inf")], ["Earlier", "0–3 mo", "3–6 mo", "6–12 mo", "1–2 yr", "2–5 yr", "Over 5 yr"])
    leads = projects[projects.review_priority.gt(0)].sort_values("review_priority", ascending=False).head(10)
    return {
        "import": next(item for item in list_imports(DEFAULT_DB) if item["import_id"] == import_id),
        "quality": quality,
        "totals": {"original_cost": total("original_cost"), "revised_cost": total("revised_cost"), "expenditure": total("expenditure")},
        "sectors": _records(sector_counts),
        "progress_bands": _records(progress_counts),
        "cost_change_bands": cost_change_bands,
        "expenditure_bands": expenditure_bands,
        "schedule_deviation_bands": schedule_bands,
        "review_records": int(projects.review_priority.gt(0).sum()),
        "model_status": str(projects.model_status.iloc[0]) if len(projects) else "Model not run",
        "review_leads": _records(leads),
    }


@app.get("/api/imports/{import_id}/projects")
def project_list(
    import_id: str,
    query: str = "",
    sector: str = "",
    review_only: bool = False,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=250),
):
    projects = _load_reviewed(import_id)
    if sector:
        projects = projects[projects.sector.fillna("").astype(str).eq(sector)]
    if review_only:
        projects = projects[projects.review_priority.gt(0)]
    if query.strip():
        term = query.strip().casefold()
        fields = [field for field in ("project_id", "project_name", "sector", "ministry", "state") if field in projects]
        mask = projects[fields].fillna("").astype(str).apply(lambda col: col.str.casefold().str.contains(term, regex=False)).any(axis=1)
        projects = projects[mask]
    count = len(projects)
    return {"total": count, "offset": offset, "limit": limit, "records": _records(projects.iloc[offset:offset + limit])}


@app.get("/api/imports/{import_id}/projects/{record_key}/{source_row}")
def project_detail(import_id: str, record_key: str, source_row: int):
    projects = _load_reviewed(import_id)
    row = _project(projects, record_key, source_row)
    return {key: _safe_value(value) for key, value in row.items()}


@app.get("/api/imports/{import_id}/reviews")
def reviews(import_id: str, limit: int = Query(default=250, ge=1, le=1000)):
    projects = _load_reviewed(import_id)
    findings = projects[projects.review_priority.gt(0)].sort_values("review_priority", ascending=False).head(limit)
    return {"total": int(projects.review_priority.gt(0).sum()), "model_status": str(projects.model_status.iloc[0]), "records": _records(findings[["record_key", "source_row_number", "project_id", "project_name", "sector", "review_priority", "rule_indicator_count", "review_indicators", "model_score"]])}


@app.get("/api/imports/{import_id}/projects/{record_key}/{source_row}/similar")
def peers(import_id: str, record_key: str, source_row: int, limit: int = Query(default=10, ge=1, le=50)):
    projects = _load_reviewed(import_id)
    _project(projects, record_key, source_row)
    candidates = similar_projects(projects, record_key, limit=limit)
    semantic_used = bool(candidates.get("comparison_criteria", pd.Series(dtype=str)).astype(str).str.contains("local sentence-model").any())
    return {"criteria": ["recorded sector", "original-cost scale", "project-name text"], "semantic_model": "local model" if semantic_used else "documented text fallback", "records": _records(candidates)}


@app.get("/api/imports/{import_id}/projects/{record_key}/{source_row}/investigation")
def investigate(import_id: str, record_key: str, source_row: int):
    projects = _load_reviewed(import_id)
    project = _project(projects, record_key, source_row)
    evidence = list_evidence(DEFAULT_DB, record_key)
    case = build_investigation(projects, record_key, evidence, source_row)
    report = investigation_markdown(case)
    return {"project": {key: _safe_value(value) for key, value in project.items()}, "indicators": case["indicators"], "review_priority": case["review_priority"], "model_status": str(project.get("model_status", "Model status unavailable")), "limitations": case["limitations"], "similar_projects": _records(case["peers"]), "evidence": case["evidence"], "report_markdown": report}


@app.post("/api/imports/{import_id}/projects/{record_key}/{source_row}/investigations")
def save_case(import_id: str, record_key: str, source_row: int, body: dict):
    projects = _load_reviewed(import_id)
    _project(projects, record_key, source_row)
    report = str(body.get("report_markdown", "")).strip()
    if not report:
        raise HTTPException(status_code=422, detail="Generate the investigation brief before saving the case.")
    case_id = save_investigation(record_key, import_id, report, DEFAULT_DB)
    return {"case_id": case_id, "saved": True}


@app.get("/api/imports/{import_id}/investigations")
def saved_cases(import_id: str):
    _load_reviewed(import_id)
    return {"records": list_investigations(import_id, DEFAULT_DB)}


@app.post("/api/imports/{import_id}/projects/{record_key}/{source_row}/question")
def question(import_id: str, record_key: str, source_row: int, body: dict):
    projects = _load_reviewed(import_id)
    project = _project(projects, record_key, source_row)
    case = build_investigation(projects, record_key, list_evidence(DEFAULT_DB, record_key), source_row)
    query = str(body.get("question", "")).strip()
    if not query:
        raise HTTPException(status_code=422, detail="Enter a question about this project.")
    return {"answer": answer_project_question(project, query, case["evidence"], case["peers"]), "mode": "deterministic local explanation"}


@app.post("/api/imports/{import_id}/documents")
async def add_document(import_id: str, record_key: str = Form(...), file: UploadFile = File(...), source_url: str = Form(default="")):
    _load_reviewed(import_id)
    if Path(file.filename or "").suffix.casefold() != ".pdf":
        raise HTTPException(status_code=415, detail="Upload a PDF document.")
    content = await file.read()
    if len(content) > 30 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF files must be 30 MB or smaller.")
    try:
        document, passages = extract_pdf(file.filename or "report.pdf", content, record_key, source_url.strip() or None)
        preserve_uploaded_document(document["filename"], content, DEFAULT_DB)
        save_document(document, passages, DEFAULT_DB)
        return {"document": document, "passages_saved": len(passages)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/imports/{import_id}/evidence")
def evidence_search(import_id: str, query: str, record_key: str | None = None):
    _load_reviewed(import_id)
    passages = list_evidence(DEFAULT_DB, record_key)
    return {"query": query, "records": retrieve_passages(passages.to_dict("records"), query)}


@app.get("/api/imports/{import_id}/projects/{record_key}/{source_row}/graph")
def evidence_graph(import_id: str, record_key: str, source_row: int):
    projects = _load_reviewed(import_id)
    row = _project(projects, record_key, source_row)
    nodes = [{"id": f"project:{record_key}", "type": "project", "label": str(row.project_name) if pd.notna(row.project_name) else "Project name not recorded"}]
    edges = []
    for field, kind in (("sector", "sector"), ("ministry", "ministry"), ("state", "state")):
        value = row.get(field)
        if value is not None and not pd.isna(value) and str(value).strip():
            node_id = f"{kind}:{str(value).casefold()}"
            nodes.append({"id": node_id, "type": kind, "label": str(value)})
            edges.append({"id": f"{record_key}:{kind}", "source": f"project:{record_key}", "target": node_id, "label": f"Recorded {kind}"})
    evidence_rows = list_evidence(DEFAULT_DB, record_key)
    for document in evidence_rows.filename.dropna().astype(str).unique():
        node_id = f"document:{record_key}:{document}"
        nodes.append({"id": node_id, "type": "document", "label": document})
        edges.append({"id": f"{record_key}:document:{len(edges)}", "source": f"project:{record_key}", "target": node_id, "label": "User-associated report"})
        passages = evidence_rows[evidence_rows.filename.astype(str).eq(document)]
        for index, passage in enumerate(passages.to_dict("records")):
            page = _safe_value(passage.get("page_number"))
            evidence_id = f"evidence:{record_key}:{document}:{page}:{index}"
            excerpt = str(passage.get("passage", ""))
            nodes.append({"id": evidence_id, "type": "evidence", "label": f"Page {page}: {excerpt[:130]}"})
            edges.append({"id": f"{evidence_id}:source", "source": node_id, "target": evidence_id, "label": f"Text from page {page}"})
    indicator_value = row.get("review_indicators")
    indicators = [item.strip() for item in ("" if indicator_value is None or pd.isna(indicator_value) else str(indicator_value)).split("·") if item.strip()]
    for index, indicator in enumerate(indicators):
        node_id = f"signal:{record_key}:{index}"
        nodes.append({"id": node_id, "type": "signal", "label": indicator})
        edges.append({"id": f"{record_key}:signal:{index}", "source": f"project:{record_key}", "target": node_id, "label": "Calculated review signal"})
    return {"nodes": nodes, "edges": edges, "provenance": {"source_file": str(row.source_filename), "source_row": int(row.source_row_number), "source_url": str(row.source_url)}}


@app.get("/api/imports/{import_id}/reports/quality")
def quality_report(import_id: str):
    projects = _load_reviewed(import_id)
    report = {"import": next(item for item in list_imports(DEFAULT_DB) if item["import_id"] == import_id), "quality": project_quality_summary(projects), "model_status": str(projects.model_status.iloc[0])}
    return Response(json.dumps(report, ensure_ascii=False, indent=2), media_type="application/json", headers={"Content-Disposition": "attachment; filename=evidenceai_project_data_quality.json"})


@app.get("/api/imports/{import_id}/reports/projects.csv")
def projects_csv(import_id: str):
    projects = _load_reviewed(import_id)
    return Response(projects.to_csv(index=False), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=evidenceai_project_snapshot.csv"})


@app.get("/api/imports/{import_id}/entities/suggestions")
def entity_suggestions(import_id: str):
    projects = _load_reviewed(import_id)
    names = projects.ministry.dropna().astype(str).unique().tolist()
    matches = entity_match_suggestions(names)
    save_entity_match_suggestions(matches, DEFAULT_DB)
    statuses = list_entity_match_statuses(DEFAULT_DB)
    for match in matches:
        match["Status"] = statuses.get(match["match_id"], match["Status"])
    return {"mode": "suggestions only; saved as unconfirmed; no automatic merging", "matches": matches}


@app.post("/api/imports/{import_id}/entities/{match_id}/confirm")
def confirm_entity(import_id: str, match_id: str):
    _load_reviewed(import_id)
    if not confirm_entity_match(match_id, DEFAULT_DB):
        raise HTTPException(status_code=404, detail="Entity suggestion was not found. Refresh the suggestion list and retry.")
    return {"match_id": match_id, "status": "confirmed by analyst"}
