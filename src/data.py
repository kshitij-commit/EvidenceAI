"""Loading and validation helpers for the local procurement CSV files.

Raw files are read only. These helpers do not normalize entity identities or
write cleaned data back to ``data/raw``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pandas as pd


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DATA_FILES = (
    "main.csv",
    "awards.csv",
    "awards_suppliers.csv",
    "parties.csv",
    "tender_documents.csv",
    "tender_items.csv",
    "tender_participationFee.csv",
    "tender_participationFees.csv",
)

def load_dataset(data_dir: str | Path = DEFAULT_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load the expected CSVs, preserving source columns and row order."""
    root = Path(data_dir)
    missing = [name for name in DATA_FILES if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing expected data files in {root}: {', '.join(missing)}")
    # Link values look numeric (for example, ``0.10``), but are identifiers.
    # Parsing them as floats collapses distinct values such as ``0.10``/``0.1``.
    link_columns = {"_link": str, "_link_main": str, "_link_awards": str}
    return {
        Path(name).stem: pd.read_csv(root / name, dtype=link_columns, low_memory=False)
        for name in DATA_FILES
    }


def audit_dataset(tables: Mapping[str, pd.DataFrame]) -> dict:
    """Return counts, missingness, duplicates, and observed link integrity."""
    if "main" not in tables or "_link" not in tables["main"].columns:
        raise ValueError("The dataset must include main.csv with an _link column")

    main = tables["main"]
    main_links = set(main["_link"].dropna().astype(str))
    files: dict[str, dict] = {}
    for name, frame in tables.items():
        links = frame["_link_main"].dropna().astype(str) if "_link_main" in frame else None
        matched = int(links.isin(main_links).sum()) if links is not None else None
        files[name] = {
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "missing_by_column": {str(k): int(v) for k, v in frame.isna().sum().items()},
            "duplicate_rows": int(frame.duplicated().sum()),
            "link_main_rows": int(len(links)) if links is not None else None,
            "link_main_matched_to_main": matched,
            "link_main_unmatched": int(len(links) - matched) if links is not None else None,
        }

    award_links = set(tables["awards"]["_link"].dropna().astype(str)) if "awards" in tables else set()
    supplier_table = tables.get("awards_suppliers")
    supplier_award_matched = None
    if supplier_table is not None and "_link_awards" in supplier_table:
        supplier_award_matched = int(supplier_table["_link_awards"].astype(str).isin(award_links).sum())

    return {
        "files": files,
        "main_link_rows": int(len(main)),
        "main_link_unique": int(main["_link"].nunique(dropna=True)),
        "main_ocid_unique": int(main["ocid"].nunique(dropna=True)) if "ocid" in main else None,
        "supplier_award_links_matched": supplier_award_matched,
    }
