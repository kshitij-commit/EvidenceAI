"""Import and normalize official project exports without changing source files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd


PAIMANA_SOURCE_URL = "https://ipm.mospi.gov.in/Home/PublicDashboard"

FIELD_ALIASES = {
    "project_id": ("project code", "project id", "project_code", "projectid", "code"),
    "project_name": ("project name", "project title", "name"),
    "ministry": ("line ministry", "ministry department", "ministry/ department", "ministry", "department"),
    "sector": ("sector name", "sector"),
    "state": ("state/ut", "state / ut", "state", "location", "state name"),
    "original_cost": ("original cost (in cr.)", "original cost in cr", "original approved cost (in cr.)", "original cost", "approved cost"),
    "revised_cost": ("latest revised cost (in cr.)", "revised cost (in cr.)", "revised cost", "latest revised cost"),
    "expenditure": ("expenditure (in cr.)", "expenditure in cr", "cumulative expenditure (in cr.)", "cumulative expenditure", "expenditure"),
    "physical_progress_pct": ("physical progress (%)", "physical progress in percent", "physical progress (%)", "physical progress", "progress (%)"),
    "original_completion_date": ("original end date", "original completion date", "original completion", "original end"),
    "revised_completion_date": ("latest revised comp. date", "latest revised completion date", "revised completion date", "revised date", "revised end date"),
}

NUMERIC_FIELDS = ("original_cost", "revised_cost", "expenditure", "physical_progress_pct")
DATE_FIELDS = ("original_completion_date", "revised_completion_date")
QUALITY_FIELDS = tuple(FIELD_ALIASES)


def _header_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return re.sub(r"\s+", " ", text)


def _coerce_number(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip().str.replace(",", "", regex=False)
    text = text.str.replace("₹", "", regex=False).str.replace("%", "", regex=False)
    text = text.replace({"": pd.NA, "-": pd.NA, "—": pd.NA, "NA": pd.NA, "N/A": pd.NA, "null": pd.NA})
    return pd.to_numeric(text, errors="coerce")


@dataclass(frozen=True)
class ImportInfo:
    filename: str
    sha256: str
    imported_at: str
    source_url: str
    cost_unit: str


def read_project_export(filename: str, content: bytes, source_url: str = PAIMANA_SOURCE_URL) -> tuple[pd.DataFrame, ImportInfo]:
    """Read a PAIMANA CSV/XLSX export and map known source headings."""
    suffix = Path(filename).suffix.casefold()
    if suffix == ".csv":
        raw = pd.read_csv(BytesIO(content), dtype="string", low_memory=False)
    elif suffix in {".xlsx", ".xlsm"}:
        try:
            raw = pd.read_excel(BytesIO(content), dtype="string")
        except ImportError as exc:
            raise ValueError("Excel import needs openpyxl. Install it with: python -m pip install openpyxl") from exc
    else:
        raise ValueError("Choose an official CSV or Excel export (.csv, .xlsx, .xlsm).")
    if raw.empty or not len(raw.columns):
        raise ValueError("The selected export has no project rows or columns.")

    header_map: dict[str, str] = {}
    normalized_headers = {_header_key(column): str(column) for column in raw.columns}
    for canonical, aliases in FIELD_ALIASES.items():
        alias_keys = {_header_key(alias) for alias in aliases}
        match = next((source for normalized, source in normalized_headers.items() if normalized in alias_keys), None)
        if match is None:
            # Accept headers with a unit appended, while retaining conservative field matching.
            match = next((source for normalized, source in normalized_headers.items()
                          if any(normalized == _header_key(alias) or normalized.startswith(_header_key(alias) + " ") for alias in aliases)), None)
        if match is not None:
            header_map[canonical] = match

    if not ("project_id" in header_map or "project_name" in header_map):
        available = ", ".join(map(str, raw.columns[:18]))
        raise ValueError("Could not identify a Project Code or Project Name column. Detected columns: " + available)

    frame = pd.DataFrame(index=raw.index)
    for canonical, source in header_map.items():
        frame[canonical] = raw[source]
    for field in ("project_id", "project_name", "ministry", "sector", "state"):
        if field not in frame:
            frame[field] = pd.NA
        frame[field] = frame[field].astype("string").str.strip().replace("", pd.NA)
    for field in NUMERIC_FIELDS:
        frame[field] = _coerce_number(frame[field]) if field in frame else pd.Series(pd.NA, index=raw.index, dtype="Float64")
    for field in DATE_FIELDS:
        frame[field] = pd.to_datetime(frame[field], errors="coerce", dayfirst=True) if field in frame else pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")

    row_material = frame[["project_id", "project_name", "sector", "ministry"]].fillna("").astype(str).agg("|".join, axis=1)
    frame["record_key"] = row_material.map(lambda value: sha256(value.encode("utf-8")).hexdigest()[:20])
    frame["source_row_number"] = np.arange(len(frame), dtype=int) + 2
    frame["source_filename"] = Path(filename).name
    imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    frame["source_imported_at"] = imported_at
    frame["source_retrieved_at"] = pd.NA
    frame["source_url"] = source_url.strip() or PAIMANA_SOURCE_URL
    frame["source_sha256"] = sha256(content).hexdigest()

    # A blank project code is not replaced with a made-up source identifier.
    identity = frame["project_id"].fillna(frame["project_name"].fillna("").str.casefold())
    frame["duplicate_identity"] = identity.duplicated(keep=False) & identity.ne("")
    if "in cr" in " ".join(_header_key(c) for c in raw.columns):
        cost_unit = "INR crore (as labelled by source export)"
    else:
        cost_unit = "Source unit not specified"
    info = ImportInfo(Path(filename).name, sha256(content).hexdigest(), imported_at, frame["source_url"].iloc[0], cost_unit)
    frame["cost_unit"] = cost_unit
    return frame.reset_index(drop=True), info


def engineer_project_features(projects: pd.DataFrame) -> pd.DataFrame:
    """Calculate only indicators supported by non-missing source fields."""
    result = projects.copy()
    original = pd.to_numeric(result["original_cost"], errors="coerce")
    revised = pd.to_numeric(result["revised_cost"], errors="coerce")
    expenditure = pd.to_numeric(result["expenditure"], errors="coerce")
    progress = pd.to_numeric(result["physical_progress_pct"], errors="coerce")
    result["cost_overrun_pct"] = ((revised - original) / original * 100).where(original.gt(0) & revised.notna())
    cost_basis = revised.where(revised.notna(), original)
    result["expenditure_cost_basis"] = cost_basis
    result["expenditure_pct"] = (expenditure / cost_basis * 100).where(cost_basis.gt(0) & expenditure.notna())
    result["expenditure_progress_gap_pp"] = (result["expenditure_pct"] - progress).where(progress.between(0, 100))
    original_date = pd.to_datetime(result["original_completion_date"], errors="coerce")
    revised_date = pd.to_datetime(result["revised_completion_date"], errors="coerce")
    result["original_completion_date"] = original_date
    result["revised_completion_date"] = revised_date
    days = (revised_date - original_date).dt.total_seconds() / 86400
    result["schedule_deviation_months"] = (days / 30.4375).where(original_date.notna() & revised_date.notna())
    result["invalid_progress"] = progress.notna() & ~progress.between(0, 100)
    result["invalid_cost"] = ((original.notna() & original.lt(0)) | (revised.notna() & revised.lt(0)) | (expenditure.notna() & expenditure.lt(0)))
    result["expenditure_exceeds_revised_cost"] = expenditure.notna() & revised.gt(0) & expenditure.gt(revised)
    return result


def project_quality_summary(projects: pd.DataFrame) -> dict:
    """Return measured import checks without treating blanks as zero values."""
    total = len(projects)
    missing = {field: int(projects[field].isna().sum()) for field in QUALITY_FIELDS if field in projects}
    return {
        "rows": total,
        "distinct_project_codes": int(projects["project_id"].nunique(dropna=True)),
        "duplicate_identity_rows": int(projects["duplicate_identity"].sum()),
        "missing_by_field": missing,
        "invalid_progress_rows": int(projects["invalid_progress"].sum()),
        "invalid_cost_rows": int(projects["invalid_cost"].sum()),
        "expenditure_exceeds_revised_cost_rows": int(projects["expenditure_exceeds_revised_cost"].sum()),
        "completeness_pct": round(100 * (1 - sum(missing.values()) / max(total * len(missing), 1)), 1),
    }
