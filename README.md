# EvidenceAI

EvidenceAI has two related workspaces in this folder. The original Himachal Pradesh procurement-tender application and its eight source CSVs remain intact. A separate PAIMANA infrastructure-project monitoring workspace adds the project workflow described in the supplied blueprint; it does not replace or reinterpret the tender data.

## Original procurement workspace

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The original app reads `data/raw/` and is normally available at `http://localhost:8501`. Its existing filters, analysis, charts, source links, and reports remain the tender-specific application.

### Quick presentation walkthrough

Use this path to show how the six modules work together:

1. **Overview:** introduce the real dataset, apply a publication-date or buyer filter, and explain the trend charts and KPI definitions.
2. **Start an investigation:** choose one of the filtered review leads and select **Begin review**. The tender stays selected as you move between modules.
3. **Anomaly review:** explain the visible rule indicators and why they are review prompts, not proof of wrongdoing or a fraud probability.
4. **Explore records:** inspect the tender row and its source fields; show how the search and filters narrow the same dataset.
5. **Buyer & supplier search:** inspect the recorded entities and follow their linked tenders.
6. **Relationships:** trace the selected tender to its award, supplier, and other linked source records.
7. **Data quality & reports:** show missingness and link-matching limits, then export the filtered records or report.

Finish by explaining that all counts and charts come from the bundled source CSVs; missing or unmatched information is shown as a limitation, not filled with invented values.

## PAIMANA project-monitoring workspace

The new interface uses React, Tailwind CSS, Recharts, and React Flow, with a local FastAPI service, Pandas/NumPy/scikit-learn processing, and SQLite persistence. To install its Python and JavaScript dependencies once:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-project.txt
cd web
npm install
cd ..
```

Then run `run-project-monitor.bat` from Windows Explorer or a terminal. The API listens on `http://127.0.0.1:8000`; the React application is at `http://127.0.0.1:5173`.

The PAIMANA workspace starts with an empty state because no authentic project export was bundled in this repository. Open the official MoSPI public dashboard, download its CSV/Excel export, and use **Import CSV / XLSX**. Imports are retained as source snapshots in a local SQLite database and source-file folder; original tender CSVs are not changed. Source retrieval time is recorded as unavailable when it is not supplied by the export.

The optional Streamlit version of the PAIMANA workflow is available with `run-project-monitor-streamlit.bat` at `http://localhost:8502` after installing `requirements-project.txt`.

## Implemented PAIMANA workflow

1. Import official CSV/XLSX snapshots and preserve their source filename, checksum, import time, reference URL, and row numbers.
2. Normalize recognized project fields; calculate missing-field completeness, duplicates, invalid progress/costs, and related validation flags.
3. View data-derived sector and progress charts, cost totals, and review leads.
4. Search and inspect individual projects, with original source values separated from derived cost, progress, and schedule indicators.
5. Review transparent rules and Isolation Forest outliers as human-review leads, never as fraud scores or verdicts.
6. Compare candidate projects using recorded sector, cost scale, and name similarity. Sentence Transformers is optional, local-only, and never auto-downloaded.
7. Suggest similar ministry labels without merging them; suggestions are saved in SQLite as unconfirmed matches.
8. Upload selectable-text public PDFs, preserve page references and checksums, and search their extracted passages. Scanned/image-only PDFs are unsupported; OCR is not enabled.
9. Assemble an investigation brief with source facts, calculated indicators, comparison criteria, retrieved passages, and data limitations; save cases explicitly to SQLite.
10. Explore source-backed project/entity/document/page/indicator links, ask deterministic questions over available records, and export the snapshot and data-quality report.

No government records, reports, evidence, statistics, or sample dashboard values are fabricated. Empty, unavailable, and inapplicable values remain distinct from zero. Investigations describe source-reported facts and derived review signals; they do not establish wrongdoing.

## Project structure

- `app.py`, `src/data.py`, `src/analysis.py` — original procurement app and analysis.
- `project_app.py` — Streamlit fallback for the separate PAIMANA workspace.
- `src/project_monitoring/data.py` — source import, field normalization, feature calculations, and quality metrics.
- `src/project_monitoring/analysis.py` — review indicators, Isolation Forest, similar-project scoring, and entity suggestions.
- `src/project_monitoring/storage.py` — local SQLite schema and source/evidence/case persistence.
- `src/project_monitoring/documents.py`, `investigations.py`, `questions.py` — PDF text extraction, evidence retrieval, investigation reports, and deterministic answers.
- `src/project_monitoring/api.py` — FastAPI endpoints for imports, analytics, projects, review queues, evidence, graphs, Q&A, and reports.
- `web/src/` — React workflow and responsive interface.
- `requirements-project.txt` — additional API, Excel, PDF, and entity-matching dependencies.
- `requirements-semantic.txt` — optional local Sentence Transformer installation.

## Optional local semantic model

By default, candidate similarity uses sector, cost scale, and project-name text. To enable semantic similarity, install `requirements-semantic.txt`, point `EVIDENCEAI_SENTENCE_MODEL` to a model directory already present on the computer, and restart the API. The app does not download models or send records to an external service.

## Existing tender-project checks

```powershell
.\.venv\Scripts\python.exe -m src.inspect_data
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
