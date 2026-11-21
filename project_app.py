"""PAIMANA infrastructure-project workspace; the tender application is kept intact."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.project_monitoring.analysis import entity_match_suggestions, review_projects, similar_projects
from src.project_monitoring.data import PAIMANA_SOURCE_URL, engineer_project_features, project_quality_summary, read_project_export
from src.project_monitoring.documents import extract_pdf, retrieve_passages
from src.project_monitoring.investigations import build_investigation, investigation_markdown
from src.project_monitoring.questions import answer_project_question
from src.project_monitoring.storage import DEFAULT_DB, list_evidence, list_imports, load_import, preserve_source_export, preserve_uploaded_document, save_document, save_import, save_investigation, save_review_results


st.set_page_config(page_title="EvidenceAI · Project Monitoring", page_icon="assets/evidenceai-mark.png", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{--navy:#142b4b;--blue:#176b9c;--teal:#167a84;--canvas:#f3f6fa;--border:#dbe3ec;--muted:#607387;--ink:#172b4d}
html,body,[data-testid=stAppViewContainer],[data-testid=stMain]{background:var(--canvas);color:var(--ink);font-family:Inter,'Segoe UI',sans-serif}
.block-container,[data-testid=stMainBlockContainer]{max-width:1640px;padding:1.1rem clamp(1rem,2vw,2rem) 3rem}
[data-testid=stSidebar]{background:var(--navy);border-right:1px solid #294666}
[data-testid=stSidebar] [data-testid=stSidebarContent]{padding:1rem .85rem}
[data-testid=stSidebar] [data-testid=stMarkdownContainer] p,[data-testid=stSidebar] [data-testid=stCaptionContainer]{color:#c6d1df}
.brand{display:flex;align-items:center;gap:.75rem;padding:.85rem .75rem;margin:.2rem 0 1rem;border:1px solid #3a5574;border-radius:10px;background:linear-gradient(130deg,#142746,#1c3a60);color:white}
.brand-mark{display:grid;place-items:center;width:2.5rem;height:2.5rem;border-radius:8px;background:#eaf4fa;color:#1686c8;font-size:1.2rem;font-weight:900}
.brand-title{font-size:1rem;font-weight:760}.brand-subtitle{font-size:.7rem;color:#c7d6e5;margin-top:.18rem}
.app-header{border-bottom:1px solid var(--border);padding:.2rem 0 .8rem;margin-bottom:.8rem}
.eyebrow{font-size:.67rem;font-weight:760;letter-spacing:.15em;text-transform:uppercase;color:var(--teal)}
.app-header h1{font-size:1.85rem;letter-spacing:-.04em;color:var(--navy);margin:.2rem 0}.app-header p{color:var(--muted);margin:0;font-size:.9rem}
.hero{padding:1.3rem 1.5rem;border-radius:12px;color:white;background:linear-gradient(108deg,#102646,#09648b);margin:.3rem 0 .9rem}
.hero h2{color:#fff;margin:.2rem 0}.hero p{color:#d5e8f0;margin:0}
[data-testid=stMetric]{background:white;border:1px solid var(--border);border-radius:9px;padding:1rem;min-height:100px;box-shadow:0 2px 8px #172b4d0a}
[data-testid=stMetricLabel] p{color:var(--muted);font-size:.75rem;font-weight:650}[data-testid=stMetricValue]{color:var(--navy);font-size:clamp(1.25rem,1.8vw,1.8rem)}
[data-testid=stDataFrame]{background:#fff;border:1px solid var(--border);border-radius:9px}
[data-testid=stPlotlyChart]{background:#fff;border:1px solid var(--border);border-radius:9px;padding:.35rem}
[data-testid=stButton] button,[data-testid=stDownloadButton] button{border-radius:7px;min-height:2.4rem;font-weight:650}
[data-testid=stSidebar] [data-testid=stRadio] [role=radiogroup]{gap:.25rem}[data-testid=stSidebar] [data-testid=stRadio] [role=radiogroup] label{padding:.55rem .6rem;border-radius:8px;color:#d0dbe8}
[data-testid=stSidebar] [data-testid=stRadio] [role=radiogroup] label:has(input:checked){background:#0d5c99;color:white}
@media(max-width:900px){[data-testid=stMain] [data-testid=stHorizontalBlock]{flex-wrap:wrap}[data-testid=stMain] [data-testid=stHorizontalBlock]>[data-testid=column]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}}
@media(max-width:560px){.block-container,[data-testid=stMainBlockContainer]{padding:.8rem .65rem 1.5rem}[data-testid=stMain] [data-testid=stHorizontalBlock]>[data-testid=column]{min-width:100%!important;flex:1 1 100%!important}}
</style>
""", unsafe_allow_html=True)


PAGES = ["Overview", "Project Explorer", "Investigations", "Evidence Documents", "Evidence Graph", "Reports"]


def project_options(frame: pd.DataFrame) -> dict[str, tuple[str, int]]:
    """Use source row in labels so duplicate project codes remain inspectable."""
    options = {}
    for row in frame.itertuples():
        code = row.project_id if pd.notna(row.project_id) else "No code"
        name = str(row.project_name) if pd.notna(row.project_name) else "Name not recorded"
        options[f"{code} · {name[:72]} · source row {int(row.source_row_number)}"] = (str(row.record_key), int(row.source_row_number))
    return options
st.sidebar.markdown('<div class="brand"><div class="brand-mark">E</div><div><div class="brand-title">EvidenceAI</div><div class="brand-subtitle">Infrastructure project intelligence</div></div></div>', unsafe_allow_html=True)
st.sidebar.markdown("##### WORKSPACE")
page = st.sidebar.radio("Workspace", PAGES, key="project_workspace_page", label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown("**Official source**")
st.sidebar.link_button("Open PAIMANA public dashboard", PAIMANA_SOURCE_URL, width="stretch")
st.sidebar.caption("Download the official CSV/XLSX export there, then import it below. The app does not scrape or bypass the source portal.")

with st.sidebar.expander("Import project export", expanded=False):
    uploaded = st.file_uploader("PAIMANA project data", type=["csv", "xlsx", "xlsm"], key="project_export_upload")
    source_ref = st.text_input("Source page / report URL", value=PAIMANA_SOURCE_URL, key="project_source_ref")
    if st.button("Save imported snapshot", key="save_project_snapshot", width="stretch", disabled=uploaded is None):
        try:
            imported, import_info = read_project_export(uploaded.name, uploaded.getvalue(), source_ref)
            preserve_source_export(uploaded.getvalue(), import_info)
            import_id = save_import(imported, import_info)
            st.session_state["project_import_id"] = import_id
            st.success(f"Imported {len(imported):,} project rows. Source file: {import_info.filename}.")
        except Exception as exc:
            st.error(str(exc))

imports = list_imports()
if imports:
    import_options = {f"{item['filename']} · {item['row_count']:,} rows · {item['imported_at'][:10]}": item["import_id"] for item in imports}
    preferred = str(st.session_state.get("project_import_id", ""))
    if preferred not in import_options.values():
        preferred = imports[0]["import_id"]
    selected_label = st.sidebar.selectbox("Active project snapshot", list(import_options), index=list(import_options.values()).index(preferred), key="project_snapshot_choice")
    active_import_id = import_options[selected_label]
    st.session_state["project_import_id"] = active_import_id
    projects = load_import(active_import_id)
    if not projects.empty:
        projects = engineer_project_features(projects)
        projects = review_projects(projects)
        save_review_results(projects, active_import_id)
else:
    active_import_id = ""
    projects = pd.DataFrame()

page_descriptions = {
    "Overview": "A live summary of the official project export currently loaded.",
    "Project Explorer": "Search project records and inspect source fields, calculated indicators, and data gaps.",
    "Investigations": "Review transparent signals, peer candidates, and evidence for one selected project.",
    "Evidence Documents": "Extract searchable text from imported public PDF reports with page references.",
    "Evidence Graph": "Trace only project, sector, ministry, document, and indicator links supported by imported records.",
    "Reports": "Download a rule-based project brief and data-quality outputs for the active snapshot.",
}
st.markdown(f'<div class="app-header"><div class="eyebrow">PAIMANA · Public project records</div><h1>{escape(page)}</h1><p>{escape(page_descriptions[page])}</p></div>', unsafe_allow_html=True)

if projects.empty:
    st.markdown('<div class="hero"><div class="eyebrow" style="color:#bfe8f3">Evidence-based project monitoring</div><h2>Bring in an official project export</h2><p>Start with the PAIMANA public dashboard export. EvidenceAI keeps the source file name, checksum, import time, source reference, and source row details.</p></div>', unsafe_allow_html=True)
    st.info("No PAIMANA project snapshot is loaded yet. Use **Import project export** in the sidebar after downloading the official CSV or XLSX. The existing procurement tender dataset and dashboard remain unchanged in app.py.")
    st.markdown("#### What becomes available after import")
    st.markdown("- Project overview, explorer and data-quality checks from the uploaded records.\n- Cost, expenditure, physical-progress and schedule indicators where the required values exist.\n- Rule-based and Isolation Forest review signals, plus transparent peer candidates.\n- PDF text extraction, page-cited evidence, project relationship graph and downloadable brief.")
    st.stop()

import_record = next((item for item in imports if item["import_id"] == active_import_id), None)
search_term = ""
if page == "Overview":
    st.markdown('<div class="hero"><div class="eyebrow" style="color:#bfe8f3">Government infrastructure monitoring</div><h2>Project portfolio</h2><p>Actual project records from the active imported snapshot · no demonstration figures</p></div>', unsafe_allow_html=True)
    total_original = pd.to_numeric(projects.original_cost, errors="coerce").sum(min_count=1)
    total_revised = pd.to_numeric(projects.revised_cost, errors="coerce").sum(min_count=1)
    total_expenditure = pd.to_numeric(projects.expenditure, errors="coerce").sum(min_count=1)
    unit = str(projects.cost_unit.dropna().iloc[0]) if projects.cost_unit.notna().any() else "Source unit not specified"
    metrics = st.columns(5, gap="small")
    metrics[0].metric("Project records", f"{len(projects):,}")
    metrics[1].metric("Sectors", f"{projects.sector.nunique(dropna=True):,}")
    metrics[2].metric("Ministries / departments", f"{projects.ministry.nunique(dropna=True):,}")
    metrics[3].metric("Original cost total", "Not available" if pd.isna(total_original) else f"{total_original:,.2f}", help=unit)
    metrics[4].metric("Revised cost total", "Not available" if pd.isna(total_revised) else f"{total_revised:,.2f}", help=unit)
    quality = project_quality_summary(projects)
    review_count = int(projects.review_priority.gt(0).sum())
    st.caption(f"Snapshot: {import_record['filename'] if import_record else 'Unknown file'} · Imported {import_record['imported_at'] if import_record else 'date not available'} · {unit}. Review leads: {review_count:,}; not findings. Cumulative expenditure total: {'not available' if pd.isna(total_expenditure) else f'{total_expenditure:,.2f}'} {unit}.")
    left, right = st.columns([1.2, 1], gap="medium")
    with left:
        st.subheader("Projects by sector")
        sector_counts = projects.sector.fillna("Not recorded").value_counts().head(12).sort_values().rename_axis("Sector").reset_index(name="Projects")
        if sector_counts.empty:
            st.info("Sector is not recorded in this export.")
        else:
            chart = px.bar(sector_counts, x="Projects", y="Sector", orientation="h", text="Projects", color_discrete_sequence=["#2186c7"])
            chart.update_layout(height=350, margin={"l": 8, "r": 12, "t": 16, "b": 12})
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    with right:
        st.subheader("Cost revision distribution")
        cost_changes = pd.to_numeric(projects.cost_overrun_pct, errors="coerce").dropna()
        if cost_changes.empty:
            st.info("No project rows have both original and revised costs.")
        else:
            chart = px.histogram(x=cost_changes, nbins=20, labels={"x": "Change from original cost (%)", "count": "Project records"}, color_discrete_sequence=["#167a84"])
            chart.update_layout(height=350, margin={"l": 8, "r": 12, "t": 16, "b": 12})
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    progress_left, progress_right = st.columns(2, gap="medium")
    with progress_left:
        st.subheader("Physical progress")
        progress = pd.to_numeric(projects.physical_progress_pct, errors="coerce").dropna()
        progress = progress[progress.between(0, 100)]
        if progress.empty:
            st.info("No valid 0–100% physical-progress values are recorded.")
        else:
            bins = pd.cut(progress, bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], include_lowest=True, right=True).value_counts().sort_index()
            progress_frame = bins.rename_axis("Progress band").reset_index(name="Project records")
            progress_frame["Progress band"] = progress_frame["Progress band"].astype(str)
            chart = px.bar(progress_frame, x="Progress band", y="Project records", color_discrete_sequence=["#7259d7"])
            chart.update_layout(height=285, margin={"l": 8, "r": 10, "t": 16, "b": 12})
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    with progress_right:
        st.subheader("Completion-date deviation")
        deviations = pd.to_numeric(projects.schedule_deviation_months, errors="coerce").dropna()
        if deviations.empty:
            st.info("Original and revised completion dates are not both recorded for any project.")
        else:
            chart = px.histogram(x=deviations, nbins=18, labels={"x": "Revised minus original completion (months)", "count": "Projects"}, color_discrete_sequence=["#d99a27"])
            chart.update_layout(height=285, margin={"l": 8, "r": 10, "t": 16, "b": 12})
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    st.subheader("Projects requiring source review")
    leads = projects[projects.review_priority.gt(0)].sort_values(["review_priority", "rule_indicator_count"], ascending=False).head(10)
    if leads.empty:
        st.info("No review indicators were produced by the current screening checks. This does not prove that every record is complete or issue-free.")
    else:
        st.dataframe(leads[["project_id", "project_name", "sector", "review_priority", "review_indicators"]].rename(columns={"project_id": "Project code", "project_name": "Project name", "review_priority": "Review priority", "review_indicators": "Why it was flagged"}), width="stretch", hide_index=True)

elif page == "Project Explorer":
    search_term = st.text_input("Search projects", placeholder="Project code, name, sector, ministry, state…", key="project_search")
    filters = st.columns(3, gap="small")
    sector_filter = filters[0].multiselect("Sector", sorted(projects.sector.dropna().astype(str).unique()), key="explorer_sector")
    ministry_filter = filters[1].multiselect("Ministry / department", sorted(projects.ministry.dropna().astype(str).unique()), key="explorer_ministry")
    review_only = filters[2].toggle("Review signals only", key="explorer_review_only")
    view = projects.copy()
    if sector_filter:
        view = view[view.sector.astype("string").isin(sector_filter)]
    if ministry_filter:
        view = view[view.ministry.astype("string").isin(ministry_filter)]
    if review_only:
        view = view[view.review_priority.gt(0)]
    if search_term.strip():
        term = search_term.strip().casefold()
        search_columns = [column for column in ("project_id", "project_name", "sector", "ministry", "state") if column in view]
        mask = view[search_columns].fillna("").astype(str).apply(lambda col: col.str.casefold().str.contains(term, regex=False)).any(axis=1)
        view = view[mask]
    st.caption(f"Showing {len(view):,} of {len(projects):,} project records.")
    table_cols = ["project_id", "project_name", "sector", "ministry", "state", "original_cost", "revised_cost", "expenditure", "physical_progress_pct", "cost_overrun_pct", "schedule_deviation_months"]
    st.dataframe(view[[column for column in table_cols if column in view]].rename(columns={
        "project_id": "Project code", "project_name": "Project name", "sector": "Sector", "ministry": "Ministry / department", "state": "State / location", "original_cost": "Original cost", "revised_cost": "Revised cost", "expenditure": "Cumulative expenditure", "physical_progress_pct": "Physical progress (%)", "cost_overrun_pct": "Cost change (%)", "schedule_deviation_months": "Schedule deviation (months)"
    }), width="stretch", height=480, hide_index=True)
    options = project_options(view)
    if options:
        label = st.selectbox("Open project record", list(options), key="explorer_project")
        record_key, source_row = options[label]
        selected = view[pd.to_numeric(view.source_row_number, errors="coerce").eq(source_row)].iloc[0]
        st.markdown(f"### {escape(str(selected.project_name) if pd.notna(selected.project_name) else 'Project name not recorded')}")
        st.caption(f"Project code: {selected.project_id if pd.notna(selected.project_id) else 'Not recorded'} · Source row {selected.source_row_number} · {selected.source_filename}")
        details = st.columns(4, gap="small")
        details[0].metric("Cost change", "Not available" if pd.isna(selected.cost_overrun_pct) else f"{selected.cost_overrun_pct:+.1f}%")
        details[1].metric("Expenditure", "Not available" if pd.isna(selected.expenditure_pct) else f"{selected.expenditure_pct:.1f}% of selected cost basis")
        details[2].metric("Schedule deviation", "Not available" if pd.isna(selected.schedule_deviation_months) else f"{selected.schedule_deviation_months:+.1f} months")
        details[3].metric("Review indicators", f"{int(selected.review_priority)}")
        raw_cols = ["sector", "ministry", "state", "original_cost", "revised_cost", "expenditure", "physical_progress_pct", "original_completion_date", "revised_completion_date", "source_url", "source_sha256"]
        detail_frame = pd.DataFrame({"Field": [column.replace("_", " ").title() for column in raw_cols if column in selected.index], "Recorded value": [str(selected[column]) if pd.notna(selected[column]) else "Not recorded" for column in raw_cols if column in selected.index]})
        st.dataframe(detail_frame, width="stretch", hide_index=True)

elif page == "Investigations":
    screened = projects
    findings = screened[screened.review_priority.gt(0)].sort_values(["review_priority", "rule_indicator_count"], ascending=False)
    st.info("Review priority organizes checks and is not a fraud probability or finding. Model signals are statistical outliers only.")
    priority_cols = st.columns(4, gap="small")
    priority_cols[0].metric("Projects screened", f"{len(projects):,}")
    priority_cols[1].metric("Any review signal", f"{len(findings):,}")
    priority_cols[2].metric("Multiple rule indicators", f"{int(findings.rule_indicator_count.gt(1).sum()):,}")
    model_status = str(projects.model_status.iloc[0]) if len(projects) else "Model not run"
    priority_cols[3].metric("Isolation Forest", "Available" if "fit on" in model_status else "Not available", help=model_status)
    if findings.empty:
        st.info("No rows have a signal under the current checks. Data limitations still need review.")
    else:
        st.dataframe(findings[["project_id", "project_name", "sector", "review_priority", "review_indicators"]].rename(columns={"project_id": "Project code", "project_name": "Project name", "sector": "Sector", "review_priority": "Review priority", "review_indicators": "Why flagged"}), width="stretch", height=330, hide_index=True)
    options = project_options(projects)
    if options:
        selected_label = st.selectbox("Investigate project", list(options), key="investigation_project")
        selected_key, selected_row = options[selected_label]
        all_evidence = list_evidence(DEFAULT_DB, selected_key)
        case = build_investigation(projects, selected_key, all_evidence, selected_row)
        project = case["project"]
        st.markdown(f"### {escape(str(project.project_name) if pd.notna(project.project_name) else 'Project name not recorded')}")
        st.caption(f"Project {project.project_id if pd.notna(project.project_id) else 'ID not recorded'} · {project.sector if pd.notna(project.sector) else 'Sector not recorded'} · Source row {project.source_row_number}")
        facts, signals = st.columns([1, 1], gap="medium")
        with facts:
            st.markdown("#### Observed and calculated values")
            st.write(f"Original cost: **{project.original_cost if pd.notna(project.original_cost) else 'Not recorded'}**")
            st.write(f"Revised cost: **{project.revised_cost if pd.notna(project.revised_cost) else 'Not recorded'}**")
            st.write(f"Cumulative expenditure: **{project.expenditure if pd.notna(project.expenditure) else 'Not recorded'}**")
            st.write(f"Physical progress: **{project.physical_progress_pct if pd.notna(project.physical_progress_pct) else 'Not recorded'}**")
            st.write(f"Calculated schedule deviation: **{project.schedule_deviation_months if pd.notna(project.schedule_deviation_months) else 'Not available'} months**")
        with signals:
            st.markdown("#### Review indicators")
            if case["indicators"]:
                for indicator in case["indicators"]:
                    st.markdown(f"- {indicator}")
            else:
                st.write("No review indicators produced by the current checks.")
            st.caption(f"Review priority: {case['review_priority']} · triage count, not a probability.")
        st.markdown("#### Comparable projects")
        st.caption("Candidates are ranked by exact sector match, original-cost scale, and project-name text. No semantic model is auto-downloaded.")
        if case["peers"].empty:
            st.info("No other project records are available for comparison.")
        else:
            st.dataframe(case["peers"][["project_id", "project_name", "sector", "original_cost", "similarity_score", "comparison_criteria"]].rename(columns={"project_id": "Project code", "project_name": "Project name", "sector": "Sector", "original_cost": "Original cost", "similarity_score": "Candidate score", "comparison_criteria": "Criteria"}), width="stretch", hide_index=True)
        st.markdown("#### Retrieved document evidence")
        if case["evidence"]:
            st.dataframe(pd.DataFrame(case["evidence"])[["filename", "page_number", "match_score", "passage"]].rename(columns={"filename": "Source document", "page_number": "Page", "match_score": "Text matches", "passage": "Extracted passage"}), width="stretch", hide_index=True)
        else:
            st.info("No supporting document found in the available dataset.")
        st.markdown("#### Ask about this project")
        st.caption("Answers are generated from this project row, calculated indicators, peer metadata, and uploaded PDF text. No LLM or external source is used.")
        with st.form("project_question_form"):
            question = st.text_input("Question", placeholder="Why was this project flagged? How is cost change calculated?")
            ask = st.form_submit_button("Get explanation")
        answer_key = f"project_question_answer:{selected_key}"
        if ask and question.strip():
            st.session_state[answer_key] = answer_project_question(project, question, case["evidence"], case["peers"])
        if st.session_state.get(answer_key):
            st.info(st.session_state[answer_key])
        with st.expander("Data limitations"):
            for note in case["limitations"] or ["No checked fields are missing from this record. This does not guarantee source accuracy."]:
                st.markdown(f"- {note}")
        report = investigation_markdown(case)
        st.download_button("Download investigation report (Markdown)", report.encode("utf-8"), f"evidenceai_project_{project.project_id or selected_key}_brief.md", "text/markdown", width="stretch")
        if st.button("Save investigation case to local SQLite", key="save_investigation_case"):
            case_id = save_investigation(str(project.record_key), active_import_id, report)
            st.success(f"Saved case {case_id} with the selected project snapshot and report.")

elif page == "Evidence Documents":
    st.caption("Upload a public PDF report, associate it with one project record, and search extracted text. Only text-bearing PDFs are supported; OCR is not enabled.")
    options = project_options(projects)
    if options:
        selected_doc_project = st.selectbox("Associate report with project", list(options), key="pdf_project_association")
        pdf_source = st.text_input("Document source URL (optional)", key="pdf_source_url")
        pdf_upload = st.file_uploader("Public project report (PDF)", type=["pdf"], key="project_pdf_upload")
        if st.button("Extract and save PDF text", key="save_project_pdf", disabled=pdf_upload is None):
            try:
                document, passages = extract_pdf(pdf_upload.name, pdf_upload.getvalue(), options[selected_doc_project][0], pdf_source.strip() or None)
                preserve_uploaded_document(document["filename"], pdf_upload.getvalue())
                save_document(document, passages)
                st.success(f"Saved {len(passages):,} page-addressable passages from {document['metadata']['pages_with_text']:,} pages containing text.")
            except Exception as exc:
                st.error(str(exc))
        stored = list_evidence(DEFAULT_DB)
        if stored.empty:
            st.info("No PDF text has been imported yet. Document contents are never fabricated.")
        else:
            query = st.text_input("Search saved passages", key="pdf_evidence_query", placeholder="Project code, name, sector, or phrase…")
            if query.strip():
                matches = retrieve_passages(stored.to_dict("records"), query.strip())
                if matches:
                    st.dataframe(pd.DataFrame(matches)[["filename", "source_url", "record_key", "page_number", "match_score", "passage"]].rename(columns={"filename": "Source document", "source_url": "Source URL", "record_key": "Project record key", "page_number": "Page", "match_score": "Text matches", "passage": "Extracted passage"}), width="stretch", hide_index=True)
                else:
                    st.info("No passage matched the search terms in the imported PDFs.")
            else:
                st.dataframe(stored.rename(columns={"filename": "Source document", "page_number": "Page", "passage": "Extracted passage", "source_url": "Source URL", "record_key": "Project record key"}), width="stretch", hide_index=True)

elif page == "Evidence Graph":
    st.caption("Connections come only from fields in the project export and PDFs associated by the user. No coordinates or hidden links are inferred.")
    options = project_options(projects)
    selected_label = st.selectbox("Select project", list(options), key="graph_project")
    graph_key, graph_row = options[selected_label]
    project = projects[pd.to_numeric(projects.source_row_number, errors="coerce").eq(graph_row)].iloc[0]
    labels = [f"Project\n{project.project_id if pd.notna(project.project_id) else 'No project code'}"]
    sources, targets, weights = [], [], []
    categories = []
    for field in ("sector", "ministry", "state"):
        value = project.get(field)
        if pd.notna(value) and str(value).strip():
            labels.append(f"{field.replace('_',' ').title()}\n{value}")
            sources.append(0); targets.append(len(labels) - 1); weights.append(1)
            categories.append(field)
    related_docs = list_evidence(DEFAULT_DB, str(project.record_key))
    for filename in related_docs.filename.dropna().astype(str).unique():
        labels.append(f"Report\n{filename}")
        sources.append(0); targets.append(len(labels) - 1); weights.append(1)
        categories.append("document")
    if int(project.review_priority) > 0:
        for indicator in [item.strip() for item in str(project.review_indicators).split("·") if item.strip()]:
            labels.append(f"Review signal\n{indicator}")
            sources.append(0); targets.append(len(labels) - 1); weights.append(1)
            categories.append("review signal")
    if len(labels) == 1:
        st.info("No sector, ministry, state, document or review-signal relationship is recorded for this selected project.")
    else:
        colors = ["#176b87"] + ["#213e60" if kind in {"sector", "ministry", "state"} else "#d99a27" if kind == "review signal" else "#12a78a" for kind in categories]
        graph = go.Figure(go.Sankey(
            arrangement="snap",
            node={"label": labels, "color": colors, "pad": 24, "thickness": 20, "line": {"color": "#dbe3ec", "width": 1}},
            link={"source": sources, "target": targets, "value": weights, "color": "rgba(23,107,135,.28)"},
        ))
        graph.update_layout(height=480, font={"family": "Inter, Segoe UI, sans-serif", "size": 12, "color": "#344b62"}, margin={"l": 8, "r": 8, "t": 12, "b": 12}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(graph, width="stretch", config={"displayModeBar": False})
    st.markdown("#### Potential ministry-name matches")
    st.caption("String similarity produces suggestions only. Names are never merged automatically; ministry labels may represent distinct organizations.")
    suggestions = entity_match_suggestions(projects.ministry.dropna().astype(str).unique().tolist())
    if suggestions:
        st.dataframe(pd.DataFrame(suggestions), width="stretch", hide_index=True)
    else:
        st.info("No high-similarity ministry-name suggestions were produced.")

else:
    quality = project_quality_summary(projects)
    st.subheader("Snapshot quality summary")
    summary_cols = st.columns(4, gap="small")
    summary_cols[0].metric("Project rows", f"{quality['rows']:,}")
    summary_cols[1].metric("Distinct project codes", f"{quality['distinct_project_codes']:,}")
    summary_cols[2].metric("Duplicate-identity rows", f"{quality['duplicate_identity_rows']:,}")
    summary_cols[3].metric("Measured field completeness", f"{quality['completeness_pct']:.1f}%")
    st.caption("Completeness is the percentage of populated values across recognized PAIMANA fields. It does not measure correctness; blank values remain missing, never converted to zero.")
    if quality["invalid_progress_rows"] or quality["invalid_cost_rows"] or quality["expenditure_exceeds_revised_cost_rows"]:
        st.warning(f"Invalid progress values: {quality['invalid_progress_rows']:,} · negative cost/expenditure values: {quality['invalid_cost_rows']:,} · expenditure above revised cost: {quality['expenditure_exceeds_revised_cost_rows']:,}. Check each against its source; these are validation flags.")
    missing_frame = pd.DataFrame([{"Field": field.replace("_", " ").title(), "Missing rows": count, "Missing (%)": round(100 * count / max(quality["rows"], 1), 1)} for field, count in quality["missing_by_field"].items()])
    st.subheader("Missing values by recognized field")
    if not missing_frame.empty:
        st.dataframe(missing_frame, width="stretch", hide_index=True)
    summary_json = pd.Series(quality).to_json(indent=2)
    st.download_button("Download data-quality summary (JSON)", summary_json.encode("utf-8"), "evidenceai_project_data_quality.json", "application/json")
    st.download_button("Download active project records (CSV)", projects.to_csv(index=False).encode("utf-8-sig"), "evidenceai_project_snapshot.csv", "text/csv")
    entity_suggestions = entity_match_suggestions(projects.ministry.dropna().astype(str).unique().tolist())
    with st.expander("Ministry name resolution suggestions"):
        st.caption("Suggestions are based on string similarity only and are not treated as confirmed entity matches.")
        if entity_suggestions:
            st.dataframe(pd.DataFrame(entity_suggestions), width="stretch", hide_index=True)
        else:
            st.info("No possible ministry-name matches were identified.")

