"""Local SQLite persistence for imported project snapshots and evidence."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import sqlite3
from typing import Any

import pandas as pd


DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "processed" / "project_monitoring.sqlite3"

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS imports (
  import_id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  source_url TEXT NOT NULL,
  imported_at TEXT NOT NULL,
  cost_unit TEXT NOT NULL,
  row_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
  record_key TEXT PRIMARY KEY,
  project_id TEXT,
  project_name TEXT,
  first_seen_import TEXT NOT NULL REFERENCES imports(import_id)
);
CREATE TABLE IF NOT EXISTS project_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  record_key TEXT NOT NULL REFERENCES projects(record_key),
  import_id TEXT NOT NULL REFERENCES imports(import_id),
  source_row_number INTEGER,
  source_record_json TEXT NOT NULL,
  UNIQUE(import_id, source_row_number)
);
CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY,
  record_key TEXT REFERENCES projects(record_key),
  filename TEXT NOT NULL,
  source_url TEXT,
  sha256 TEXT NOT NULL,
  imported_at TEXT NOT NULL,
  metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(document_id),
  record_key TEXT REFERENCES projects(record_key),
  page_number INTEGER,
  passage TEXT NOT NULL,
  evidence_type TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS anomalies (
  finding_id TEXT PRIMARY KEY,
  record_key TEXT NOT NULL REFERENCES projects(record_key),
  import_id TEXT NOT NULL REFERENCES imports(import_id),
  indicator TEXT NOT NULL,
  observed_value TEXT,
  review_priority INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entities (
  entity_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  recorded_name TEXT NOT NULL,
  record_key TEXT NOT NULL REFERENCES projects(record_key),
  UNIQUE(entity_type, recorded_name, record_key)
);
CREATE TABLE IF NOT EXISTS entity_matches (
  match_id TEXT PRIMARY KEY,
  name_a TEXT NOT NULL,
  name_b TEXT NOT NULL,
  similarity_score INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'suggestion'
);
CREATE TABLE IF NOT EXISTS investigations (
  investigation_id TEXT PRIMARY KEY,
  record_key TEXT NOT NULL REFERENCES projects(record_key),
  import_id TEXT NOT NULL REFERENCES imports(import_id),
  created_at TEXT NOT NULL,
  summary_markdown TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshots_project ON project_snapshots(record_key);
CREATE INDEX IF NOT EXISTS idx_evidence_project ON evidence(record_key);
CREATE INDEX IF NOT EXISTS idx_anomalies_import ON anomalies(import_id);
"""


def connect(db_path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def save_import(projects: pd.DataFrame, info, db_path: str | Path = DEFAULT_DB) -> str:
    """Persist the uploaded export and each source row as a dated snapshot."""
    import_id = info.sha256
    with connect(db_path) as db:
        db.execute(
            "INSERT OR IGNORE INTO imports(import_id,filename,source_url,imported_at,cost_unit,row_count) VALUES(?,?,?,?,?,?)",
            (import_id, info.filename, info.source_url, info.imported_at, info.cost_unit, len(projects)),
        )
        for _, row in projects.iterrows():
            record_key = str(row["record_key"])
            db.execute(
                "INSERT OR IGNORE INTO projects(record_key,project_id,project_name,first_seen_import) VALUES(?,?,?,?)",
                (record_key, _json_value(row.get("project_id")), _json_value(row.get("project_name")), import_id),
            )
            snapshot_id = f"{import_id}:{int(row['source_row_number'])}"
            record = {str(key): _json_value(value) for key, value in row.items()}
            db.execute(
                "INSERT OR IGNORE INTO project_snapshots(snapshot_id,record_key,import_id,source_row_number,source_record_json) VALUES(?,?,?,?,?)",
                (snapshot_id, record_key, import_id, int(row["source_row_number"]), json.dumps(record, ensure_ascii=False, allow_nan=False)),
            )
            for entity_type, field in (("sector", "sector"), ("ministry", "ministry"), ("state", "state")):
                value = row.get(field)
                if value is not None and not pd.isna(value) and str(value).strip():
                    entity_id = f"{entity_type}:{record_key}:{str(value).casefold()}"
                    db.execute(
                        "INSERT OR IGNORE INTO entities(entity_id,entity_type,recorded_name,record_key) VALUES(?,?,?,?)",
                        (entity_id, entity_type, str(value).strip(), record_key),
                    )
    return import_id


def preserve_source_export(content: bytes, info, db_path: str | Path = DEFAULT_DB) -> Path:
    """Keep the exact uploaded bytes under a content-addressed local filename."""
    digest = sha256(content).hexdigest()
    suffix = Path(info.filename).suffix.casefold()
    safe_suffix = suffix if suffix in {".csv", ".xlsx", ".xlsm", ".pdf"} else ".bin"
    source_dir = Path(db_path).parent / "project_sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    target = source_dir / f"{digest}{safe_suffix}"
    if not target.exists():
        target.write_bytes(content)
    return target


def preserve_uploaded_document(filename: str, content: bytes, db_path: str | Path = DEFAULT_DB) -> Path:
    """Keep exact uploaded PDF bytes alongside their extracted, page-linked text."""
    from types import SimpleNamespace

    info = SimpleNamespace(filename=filename)
    return preserve_source_export(content, info, db_path)


def save_review_results(projects: pd.DataFrame, import_id: str, db_path: str | Path = DEFAULT_DB) -> None:
    """Persist indicator evidence for the imported snapshot, never a verdict."""
    from datetime import datetime, timezone

    signal_columns = [
        ("flag_cost_increase", "Revised cost exceeds original cost", "cost_overrun_pct"),
        ("flag_expenditure_over_cost", "Expenditure exceeds recorded revised cost", "expenditure"),
        ("flag_schedule_extension", "Revised completion date is later than original", "schedule_deviation_months"),
        ("flag_progress_out_of_range", "Physical progress is outside 0–100%", "physical_progress_pct"),
        ("flag_financial_physical_gap", "Expenditure-progress gap is at least 20 percentage points", "expenditure_progress_gap_pp"),
        ("model_flag", "Isolation Forest statistical outlier", "model_score"),
    ]
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect(db_path) as db:
        for _, row in projects.iterrows():
            for flag, label, field in signal_columns:
                if not bool(row.get(flag, False)):
                    continue
                finding_id = f"{import_id}:{row['record_key']}:{flag}"
                observed = _json_value(row.get(field))
                db.execute(
                    "INSERT OR IGNORE INTO anomalies(finding_id,record_key,import_id,indicator,observed_value,review_priority,created_at) VALUES(?,?,?,?,?,?,?)",
                    (finding_id, str(row["record_key"]), import_id, label, None if observed is None else str(observed), int(row.get("review_priority", 0)), created_at),
                )


def save_entity_match_suggestions(suggestions: list[dict[str, Any]], db_path: str | Path = DEFAULT_DB) -> None:
    """Persist deterministic name-match suggestions as unconfirmed candidates."""
    with connect(db_path) as db:
        for suggestion in suggestions:
            name_a = str(suggestion.get("Recorded name A", ""))
            name_b = str(suggestion.get("Recorded name B", ""))
            score = int(suggestion.get("Similarity score", 0))
            match_id = str(suggestion.get("match_id") or sha256(f"ministry|{name_a.casefold()}|{name_b.casefold()}".encode("utf-8")).hexdigest())
            db.execute(
                "INSERT OR IGNORE INTO entity_matches(match_id,name_a,name_b,similarity_score,status) VALUES(?,?,?,?,?)",
                (match_id, name_a, name_b, score, "suggestion; unconfirmed"),
            )


def confirm_entity_match(match_id: str, db_path: str | Path = DEFAULT_DB) -> bool:
    """Store an explicit analyst confirmation for one suggested name pair."""
    with connect(db_path) as db:
        cursor = db.execute(
            "UPDATE entity_matches SET status='confirmed by analyst' WHERE match_id=?",
            (match_id,),
        )
        return cursor.rowcount == 1


def list_entity_match_statuses(db_path: str | Path = DEFAULT_DB) -> dict[str, str]:
    if not Path(db_path).exists():
        return {}
    with connect(db_path) as db:
        return {row["match_id"]: row["status"] for row in db.execute("SELECT match_id,status FROM entity_matches")}


def save_investigation(record_key: str, import_id: str, markdown: str, db_path: str | Path = DEFAULT_DB) -> str:
    """Persist a generated brief as a locally stored investigation case."""
    from datetime import datetime, timezone
    import uuid

    case_id = str(uuid.uuid4())
    with connect(db_path) as db:
        db.execute(
            "INSERT INTO investigations(investigation_id,record_key,import_id,created_at,summary_markdown) VALUES(?,?,?,?,?)",
            (case_id, record_key, import_id, datetime.now(timezone.utc).isoformat(timespec="seconds"), markdown),
        )
    return case_id


def list_imports(db_path: str | Path = DEFAULT_DB) -> list[dict[str, Any]]:
    if not Path(db_path).exists():
        return []
    with connect(db_path) as db:
        return [dict(row) for row in db.execute("SELECT * FROM imports ORDER BY imported_at DESC")]


def list_investigations(import_id: str, db_path: str | Path = DEFAULT_DB) -> list[dict[str, Any]]:
    if not Path(db_path).exists():
        return []
    with connect(db_path) as db:
        rows = db.execute(
            "SELECT i.investigation_id,i.record_key,i.created_at,i.summary_markdown,p.project_id,p.project_name "
            "FROM investigations i LEFT JOIN projects p ON p.record_key=i.record_key "
            "WHERE i.import_id=? ORDER BY i.created_at DESC",
            (import_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def load_import(import_id: str, db_path: str | Path = DEFAULT_DB) -> pd.DataFrame:
    if not Path(db_path).exists():
        return pd.DataFrame()
    with connect(db_path) as db:
        rows = db.execute("SELECT source_record_json FROM project_snapshots WHERE import_id=? ORDER BY source_row_number", (import_id,)).fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([json.loads(row[0]) for row in rows])


def save_document(document: dict[str, Any], passages: list[dict[str, Any]], db_path: str | Path = DEFAULT_DB) -> None:
    with connect(db_path) as db:
        db.execute(
            "INSERT OR IGNORE INTO documents(document_id,record_key,filename,source_url,sha256,imported_at,metadata_json) VALUES(?,?,?,?,?,?,?)",
            (document["document_id"], document.get("record_key"), document["filename"], document.get("source_url"), document["sha256"], document["imported_at"], json.dumps(document.get("metadata", {}), ensure_ascii=False)),
        )
        db.executemany(
            "INSERT OR IGNORE INTO evidence(evidence_id,document_id,record_key,page_number,passage,evidence_type) VALUES(?,?,?,?,?,?)",
            [(item["evidence_id"], document["document_id"], document.get("record_key"), item.get("page_number"), item["passage"], "pdf_text") for item in passages],
        )


def list_evidence(db_path: str | Path = DEFAULT_DB, record_key: str | None = None) -> pd.DataFrame:
    if not Path(db_path).exists():
        return pd.DataFrame(columns=["filename", "page_number", "passage", "source_url", "record_key"])
    query = "SELECT d.filename,d.source_url,e.record_key,e.page_number,e.passage FROM evidence e JOIN documents d ON d.document_id=e.document_id"
    params: tuple = ()
    if record_key:
        query += " WHERE e.record_key=?"
        params = (record_key,)
    query += " ORDER BY d.imported_at DESC,e.page_number"
    with connect(db_path) as db:
        return pd.read_sql_query(query, db, params=params)
