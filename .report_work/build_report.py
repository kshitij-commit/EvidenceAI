from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

SRC=Path(r'C:\Users\kshit\Downloads\EvidenceAI_Report_PreviewWord.docx')
OUT=Path(r'C:\Users\kshit\Desktop\05_document\5th semester notes\EvidenceAi\EvidenceAI_Project_Report_Final.docx')
d=Document(str(SRC)); body=d._element.body
end=max(i for i,p in enumerate(d.paragraphs) if p.text.strip()=='(B2455R101A1018)')
seen=-1
for e in list(body):
    if e.tag==qn('w:sectPr'): continue
    if e.tag==qn('w:p'): seen+=1
    if seen>end: body.remove(e)
for p in d.paragraphs[:end+1]:
    if p.text.startswith('�EVIDENCEAI:') or p.text.startswith('EVIDENCE-BASED INVESTIGATION') or p.text.startswith('Session �'):
        old=p.text
        new='EVIDENCEAI' if old.startswith('�EVIDENCEAI:') else ('EVIDENCE-BASED INVESTIGATION AND ANOMALY INTELLIGENCE ENGINE' if old.startswith('EVIDENCE-BASED') else 'Session 2024–2028')
        for r in p.runs:r.text=''
        p.add_run(new)

normal=d.styles['Normal']; normal.font.name='Times New Roman'; normal.font.size=Pt(11); normal.font.color.rgb=RGBColor(32,43,58)
normal.paragraph_format.space_after=Pt(6); normal.paragraph_format.line_spacing=1.12
for nm,sz in [('Heading 1',16),('Heading 2',13),('Heading 3',11)]:
    s=d.styles[nm]; s.font.name='Arial'; s.font.size=Pt(sz); s.font.bold=True; s.font.color.rgb=RGBColor(20,43,75)
    s.paragraph_format.space_before=Pt(14 if nm=='Heading 1' else 9); s.paragraph_format.space_after=Pt(5); s.paragraph_format.keep_with_next=True

def p(text='',style=None,bold_lead=None,italic=False):
    x=d.add_paragraph(style=style)
    if bold_lead and text.startswith(bold_lead): x.add_run(bold_lead).bold=True; x.add_run(text[len(bold_lead):])
    else: x.add_run(text).italic=italic
    return x
def bullet(text):
    x=p('• '+text); x.paragraph_format.left_indent=Inches(.28); x.paragraph_format.first_line_indent=Inches(-.18); return x
def shade(c,color):
    x=OxmlElement('w:shd'); x.set(qn('w:fill'),color); c._tc.get_or_add_tcPr().append(x)
def table(head,rows):
    t=d.add_table(rows=1,cols=len(head)); t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,v in enumerate(head):
        c=t.rows[0].cells[i]; c.text=str(v); shade(c,'142B4B'); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for r in c.paragraphs[0].runs:r.bold=True; r.font.name='Arial'; r.font.size=Pt(9); r.font.color.rgb=RGBColor(255,255,255)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):
            cells[i].text=str(v); cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if len(t.rows)%2==0:shade(cells[i],'F3F6F9')
            for q in cells[i].paragraphs:
                q.paragraph_format.space_after=Pt(2)
                for r in q.runs:r.font.name='Arial'; r.font.size=Pt(8.5)
    d.add_paragraph()
def chapter(n,title):
    d.add_page_break(); p(f'{n}. {title}' if n else title,'Heading 1')
def sub(title):p(title,'Heading 2')
def contents(lines):
    d.add_page_break(); x=p('CONTENTS'); x.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for s in lines:
        q=p(s); q.paragraph_format.left_indent=Inches(.2); q.paragraph_format.space_after=Pt(3)

# Abstract and contents replace the draft's placeholder-heavy body.
d.add_page_break(); x=p('ABSTRACT'); x.alignment=WD_ALIGN_PARAGRAPH.CENTER
p('EvidenceAI is a software project with two complementary workspaces. The procurement workspace analyses a bundled Himachal Pradesh procurement dataset organized across eight OCDS-related CSV files. It supports tender exploration, buyer and supplier lookup, linked-record review, data-quality inspection, rule-based indicators, and Isolation Forest anomaly screening. A separate PAIMANA workspace supports monitoring infrastructure projects using official exports selected by the user. It imports CSV or Excel snapshots, preserves source provenance, derives cost, progress, expenditure, and schedule indicators, and assembles evidence-grounded investigation briefs.')
p('The procurement application uses Python, Streamlit, Pandas, NumPy, scikit-learn, and Plotly. The project-monitoring workspace includes a React interface, local FastAPI service, Pandas/NumPy/scikit-learn processing, SQLite storage, and a Streamlit alternative. Its implemented features include validation, review queues, project comparisons, selectable-text PDF evidence search with page references, deterministic question answering, relationship graphs, entity-name suggestions, saved cases, and report exports.')
p('The project organizes records and prioritizes manual review. Procurement CSVs are bundled with the repository; no authentic PAIMANA project export is bundled, so project-monitoring outputs become available after an official snapshot is imported. Review indicators and statistical outliers are triage aids, not fraud probabilities or findings of misconduct.')
p('Keywords: EvidenceAI, procurement analytics, project monitoring, OCDS, PAIMANA, data quality, Isolation Forest, evidence retrieval.')
contents(['1. Introduction','2. Problem Definition and Existing Approaches','3. Objectives Scope and Constraints','4. Technical Background','5. Requirements and Feasibility','6. Architecture and Data Flow','7. Data Sources and Processing','8. Functional Modules','9. Methods and Algorithms','10. Implementation','11. Results and Evaluation','12. Testing and Validation','13. Limitations and Responsible Use','14. Conclusion and Future Scope','References','Appendices'])

chapter(1,'Introduction')
sub('1.1 Background'); p('Public procurement and infrastructure delivery produce structured records about organizations, projects, costs, schedules, and decisions. These records may be spread across linked tables and exports. Reviewers need to connect observations, identify missing information, compare records, and return to source material before drawing conclusions. EvidenceAI was built to make those review steps more organized and repeatable.')
p('The project includes two workspaces because its development covers procurement investigation and infrastructure project monitoring. The procurement workspace operates on the supplied Himachal Pradesh dataset. The PAIMANA workspace is a separate import-driven workflow and does not replace or reinterpret the tender data.')
sub('1.2 Purpose'); p('EvidenceAI combines data import, validation, transparent calculations, rule-based screening, statistical anomaly detection, visual summaries, record exploration, and source-linked investigation. It supports human review; a signal identifies a record that may deserve verification, while the user must inspect the underlying source and context.')
sub('1.3 Report Organization'); p('The following chapters describe the problem, objectives, data, architecture, modules, algorithms, implementation, evaluation limits, and future development. They distinguish implemented functionality from outputs that depend on importing a source dataset.')

chapter(2,'Problem Definition and Existing Approaches')
sub('2.1 Problem Definition'); p('Procurement and project records can be large, spread across files, and incomplete. Manual review makes it difficult to consistently find records, compare measurements, trace relationships, and preserve the source context behind an observation. Basic spreadsheets support filtering but do not provide the connected workflow for provenance, transparent indicators, evidence passages, saved cases, and relationship exploration implemented in EvidenceAI.')
sub('2.2 Proposed Approach'); p('The procurement workspace integrates tender tables through recorded link identifiers and presents related records for exploration. The PAIMANA workspace imports an official CSV or Excel snapshot, stores its provenance locally, calculates documented indicators, and lets a reviewer attach selectable-text PDF evidence and save a case brief. Both workspaces present review prompts without making findings of wrongdoing.')

chapter(3,'Objectives Scope and Constraints')
sub('3.1 Objectives')
for s in ['Load and inspect the eight supplied procurement CSV files while retaining source columns and row order.','Connect tenders with awards, suppliers, parties, documents, items, and participation-fee records through source identifiers.','Provide procurement summaries, filters, record search, buyer/supplier lookup, linked-record views, and quality reports.','Screen procurement records using explicit rules and a conditional Isolation Forest model.','Import official PAIMANA CSV/XLSX exports and preserve file and row provenance.','Calculate supported cost, expenditure, progress, schedule, and validation indicators.','Support project comparisons, PDF passage search, deterministic questions, case briefs, and report exports.','Keep project snapshots, documents, entity decisions, and saved cases in local SQLite-backed storage.']:bullet(s)
sub('3.2 Scope'); p('The repository covers two local workspaces. The procurement workspace is supplied with data. The project-monitoring workspace is an import-driven framework and ships without government project observations. Processing and persistence are local; optional semantic comparison requires a model already present on the computer.')
sub('3.3 Constraints')
for s in ['Analyses depend on source quality, completeness, labels, and link fields.','Financial comparisons are limited when amounts or currencies are missing or incompatible.','Scanned or image-only PDFs are not searchable because OCR is not enabled.','Similarity candidates are suggestions, not validated peer groups.','Anomaly methods identify unusual patterns, not causes or legal conclusions.']:bullet(s)

chapter(4,'Technical Background')
sub('4.1 Structured Data and Links'); p('CSV and Excel files hold observations in rows and fields in columns. When related information is split across tables, identifiers connect records. EvidenceAI preserves link identifiers as strings where their representation carries meaning.')
sub('4.2 Rule-Based Screening'); p('A rule is a transparent condition applied to available fields. Its usefulness depends on source quality and threshold choice. A rule hit is a review lead, not evidence of cause or intent.')
sub('4.3 Isolation Forest'); p('Isolation Forest recursively selects features and split values to isolate observations. Observations isolated with fewer splits are treated as more unusual relative to the fitted data. Its score depends on features, preprocessing, sample, and contamination setting; it is not a fraud probability.')
sub('4.4 Evidence Retrieval'); p('The monitoring workspace extracts selectable text from PDFs, records page references, and ranks passages through deterministic term counts. Retrieved text helps locate material but must be read in its source context.')

chapter(5,'Requirements and Feasibility')
sub('5.1 Functional Requirements')
table(['ID','Requirement'],[('FR-01','Load procurement files and inspect data quality.'),('FR-02','Search, filter, summarize, and inspect tenders and linked entities.'),('FR-03','Show rule indicators and statistical flags with reasons and limits.'),('FR-04','Import PAIMANA CSV/XLSX and preserve source metadata and row numbers.'),('FR-05','Map recognized fields and calculate project indicators.'),('FR-06','Compare candidate projects, search PDF evidence, answer supported questions, and assemble briefs.'),('FR-07','Save local snapshots, documents, entity-match status, and cases; export reports.')])
sub('5.2 Non-Functional Requirements')
for s in ['Usability: navigable pages, filters, charts, and readable missing-value states.','Traceability: retain source filenames, row references, identifiers, and page references.','Interpretability: expose rule reasons and formulas.','Local handling: process and persist imported project evidence in the local workspace.','Graceful limits: distinguish empty, unavailable, unsupported, and zero values.']:bullet(s)
sub('5.3 Feasibility'); p('The system uses established local technologies: Python data libraries, Streamlit, FastAPI, React, and SQLite. Operational usefulness depends on importing the correct official export and checking findings against the original record. The software does not replace audit or engineering judgment.')

chapter(6,'Architecture and Data Flow')
table(['Workspace','Technology','Flow'],[('Procurement','Streamlit','Bundled CSVs → load and validate → link and analyze → dashboards, investigation views, and exports.'),('PAIMANA monitoring','React, FastAPI, SQLite; Streamlit fallback','CSV/XLSX/PDF import → mapping and validation → indicators and screening → local storage → investigation, evidence, graphs, and exports.')])
sub('6.1 Monitoring Request Flow'); p('The user selects an official export. The importer maps recognized headings while retaining source metadata and row references. Numeric and date fields are parsed; missing values remain missing. Indicators and checks are calculated. The local API supplies summaries, records, reviews, documents, graphs, and reports to the interface. The reviewer inspects source facts and calculated values, optionally attaches a PDF, asks a supported question, and saves a case.')
sub('6.2 Storage'); p('The tender application reads bundled CSV source files. The monitoring workspace stores import metadata, project rows, review results, document passages, match statuses, and saved cases in SQLite, with uploaded exports and PDFs retained locally and checksums recorded.')

chapter(7,'Data Sources and Processing')
sub('7.1 Procurement Dataset'); p('Eight CSV files are bundled: main tenders, awards, award suppliers, parties, tender documents, tender items, tender_participationFee, and tender_participationFees. The dataset is described in project materials as OCDS-structured Himachal Pradesh procurement data. Source files are read without writing normalized values back to them.')
table(['File','Role'],[('main.csv','Primary tender records.'),('awards.csv','Award values, currencies, and tender links.'),('awards_suppliers.csv','Supplier names associated with awards.'),('parties.csv','Recorded organizations and parties.'),('tender_documents.csv','Document metadata and descriptions.'),('tender_items.csv','Tender item information.'),('tender_participationFee.csv','Participation fee records.'),('tender_participationFees.csv','Additional fee records as supplied.')])
sub('7.2 PAIMANA Export'); p('The importer accepts CSV and XLSX/XLSM files and recognizes aliases for project code/name, ministry or department, sector, state/location, original and revised costs, expenditure, physical progress, and original/revised completion dates. If source headings specify crore, the unit is recorded as labelled; otherwise it is marked unspecified. Original file name, SHA-256 checksum, import time, source URL, and source row number are retained. Retrieval time is not inferred when absent.')
sub('7.3 Data Quality'); p('The workspaces measure missingness, duplicates, and link or range issues. Project checks include progress outside 0–100%, negative costs or expenditure, expenditure above a positive revised cost, and missing recognized fields. Completeness measures presence, not correctness. Blank values are never silently converted to zero.')

chapter(8,'Functional Modules')
sub('8.1 Procurement Workspace')
for s in ['Overview: KPIs, publication trends, analysis breakdowns, and leads under active filters.','Explore records: search, filters, source fields, and links into related review modules.','Anomaly review: transparent rules and Isolation Forest status with tender drill-through.','Buyer and supplier search: recorded entities and their linked tenders.','Relationships: recorded links to awards, suppliers, parties, items, and document descriptions.','Data quality and reports: missingness, link and currency limitations, and report/data export.']:p(s,bold_lead=s.split(':')[0]+':')
sub('8.2 PAIMANA Workspace')
for s in ['Overview: portfolio values and data-derived sector, progress, cost, expenditure, schedule, review, and quality summaries.','Project Explorer: search, filters, pagination, source record details, and calculated indicators.','Investigations: rule reasons, optional model results, peer candidates, a case brief, and deterministic questions.','Evidence Documents: selectable-text PDF extraction, page references, and passage search; image-only PDFs are unsupported.','Evidence Graph: source-backed project, ministry, sector, location, document/page, and indicator connections.','Reports: snapshot CSV, quality report, and selected case brief exports.','Entity suggestions: similar ministry labels remain unconfirmed until an analyst confirms them.']:p(s,bold_lead=s.split(':')[0]+':')

chapter(9,'Methods and Algorithms')
sub('9.1 Procurement Integration'); p('Award records are summarized separately from supplier links. Supplier names are joined through award identifiers and aggregated by tender, avoiding duplicated award values when multiple suppliers are linked. Award/estimate comparisons require matching currencies and a positive tender estimate.')
table(['Procurement check','Implemented condition'],[('Single tenderer','Recorded number of tenderers equals one.'),('Missing amount/currency','Amount missing or currency blank; kept as a quality note.'),('Zero/negative INR','Recorded INR amount is at most zero.'),('High INR estimate','At/above the 99th percentile of positive INR estimates when enough values exist.'),('Isolation Forest','Eligible positive INR records with tenderer count and other available numeric fields.')])
sub('9.2 Project Calculations'); table(['Indicator','Calculation'],[('Cost change','(Revised − original) / original × 100 when original is positive.'),('Expenditure percentage','Expenditure / revised cost when present, otherwise original cost, when positive.'),('Financial-physical gap','Expenditure percentage − valid physical progress.'),('Schedule deviation','Revised completion date − original completion date in average calendar months.'),('Review rules','Cost increase, expenditure above revised cost, date extension, invalid progress, and absolute financial-progress gap ≥20 points.')])
sub('9.3 Project Isolation Forest'); p('The model selects numeric fields available for at least 30 records and requires at least two usable features. It applies median imputation, standardization, and Isolation Forest with a fixed random seed and 200 trees. The configured contamination is a model parameter, not a probability. If dependencies or data conditions are unmet, the status reports that the model was not run or is unavailable.')
sub('9.4 Similarity and Entity Matching'); p('Project candidates use recorded sector, original-cost scale, and project-name similarity. A local sentence-transformer may be used only if a model folder is already configured. Ministry-name string similarity creates suggestions, not automatic merges.')

chapter(10,'Implementation')
table(['Area','Technology'],[('Tender interface','Python and Streamlit'),('Data processing','Pandas and NumPy'),('Statistical screening','scikit-learn when available'),('Charts','Plotly and Recharts'),('Monitoring API/UI','FastAPI and React'),('Relationship graph','React Flow'),('Persistence','SQLite and local files'),('Documents','Selectable-text PDF extraction')])
sub('10.1 Source Files'); table(['Path','Responsibility'],[('app.py','Procurement interface.'),('src/data.py','Tender CSV loading and quality audit.'),('src/analysis.py','Tender integration and screening.'),('project_app.py','Streamlit monitoring alternative.'),('src/project_monitoring/data.py','Import, mappings, provenance, and quality.'),('src/project_monitoring/analysis.py','Rules, model, similarity, entity suggestions.'),('src/project_monitoring/api.py','Local service endpoints.'),('src/project_monitoring/storage.py','SQLite and source file persistence.'),('src/project_monitoring/documents.py','PDF extraction and retrieval.'),('src/project_monitoring/investigations.py','Case brief construction.'),('src/project_monitoring/questions.py','Deterministic grounded answers.'),('web/src/App.jsx','React application workflow.')])
sub('10.2 Local Execution'); p('The procurement workspace runs using the virtual environment and Streamlit instructions in README.md. The React monitoring workspace uses run-project-monitor.bat after dependencies are installed; its API uses 127.0.0.1:8000 and interface 127.0.0.1:5173. A Streamlit alternative is available through run-project-monitor-streamlit.bat.')

chapter(11,'Results and Evaluation')
sub('11.1 Bundled Procurement Snapshot'); p('Current repository file counts are: main.csv 3,791; awards.csv 4,211; awards_suppliers.csv 4,211; parties.csv 8,002; tender_documents.csv 4,132; tender_items.csv 3,791; tender_participationFee.csv 3,791; and tender_participationFees.csv 7,582.')
p('Implemented rules identify 128 tenders with one recorded tenderer, 3 zero or negative INR amounts, and 5 estimates at the high-value threshold. Missing amount or currency is separately identified as a quality condition; the current integration marks 3,334 records with that condition. Counts apply to the bundled files and current implementation only.')
p('Isolation Forest execution depends on the active runtime having scikit-learn and enough eligible observations. An earlier preview gives model counts from a different run, so they are not presented here as current verified results. The application exposes model status with the analysis.')
sub('11.2 Monitoring Workspace State'); p('No authentic PAIMANA export is bundled. There are therefore no project totals, sector rankings, or project-model counts to report. Monitoring charts, indicators, quality checks, peer candidates, and investigation outputs are calculated after a user imports a source snapshot.')
sub('11.3 Evaluation Interpretation'); p('The procurement workspace can be checked against the bundled files and observed links. The monitoring workflow can be evaluated after importing an official export and comparing mapped fields, calculations, row provenance, PDF retrieval, and exports against their sources. Flags are review prompts, not outcome measures.')

chapter(12,'Testing and Validation')
sub('12.1 Existing Coverage'); p('The repository includes unit tests for tender-award-supplier linkage and for ensuring missing currency remains a quality note rather than an anomaly-priority contribution. Source code also validates required files, recognized fields, missingness, duplicate identities, parsed values, links, invalid progress, and negative values. This report does not claim a current test-run result.')
sub('12.2 Recommended End-to-End Checks')
for s in ['Reconcile tender file counts with the displayed counts.','Check award aggregation for tenders linked to multiple suppliers.','Verify currency-compatible tender and award comparisons.','Import CSV and XLSX snapshots and compare mapped fields and row references with the original.','Check calculations using known values, blanks, zero costs, and invalid ranges.','Compare extracted PDF passage text and page numbers to the source.','Save and reopen a case; confirm it retains snapshot references.','Compare exported row counts and quality findings with the active import.']:bullet(s)

chapter(13,'Limitations and Responsible Use')
sub('13.1 Data and Model Limits'); p('Missing values, inconsistent labels, duplicate records, currency differences, and incomplete links affect results. Field mapping is limited to recognized headings. Similar candidates may not be true peers. Isolation Forest depends on features, sample composition, missingness, and configuration.')
sub('13.2 Evidence Limits'); p('PDF retrieval uses selectable text and simple term counts, so synonyms may be missed. Scanned documents need OCR, which is not enabled. Retrieved text requires contextual review. The graph shows recorded links and does not infer unrecorded ownership, causes, or geography.')
sub('13.3 Local Data Handling'); p('The monitoring service is designed for local execution and local database/file storage. Users should protect imported records and documents under their institution’s data-handling rules.')
sub('13.4 Interpretation'); p('EvidenceAI does not produce a fraud probability, legal conclusion, or misconduct verdict. Users should verify source records, documents, rules, context, and possible data errors before making determinations.')

chapter(14,'Conclusion and Future Scope')
sub('14.1 Conclusion'); p('EvidenceAI brings together a procurement analysis workspace and a separate infrastructure project-monitoring workflow. The first organizes bundled Himachal Pradesh files and supports tender review through linked records, dashboards, rules, and data-quality views. The second accepts user-selected PAIMANA exports and supports provenance-aware analysis, evidence retrieval, case briefs, and exports. Both emphasize traceable source information and transparent calculations.')
p('The project demonstrates how data processing, visualization, rules, and unsupervised methods can organize records for human review. Conclusions remain bounded by the available data. No PAIMANA export is bundled, and neither workspace can establish misconduct from an anomaly signal.')
sub('14.2 Future Scope')
for s in ['Evaluate field mappings against multiple official PAIMANA export versions.','Add optional OCR for scanned documents with explicit source limitations.','Expand automated and end-to-end checks for imports, calculations, evidence, persistence, and exports.','Add configurable, versioned review rules.','Improve citation and source-document cross-checking.','Support more procurement datasets with explicit schema and currency mappings.','Study model stability across periods and source groups before operational use.','Improve accessibility and export usability.']:bullet(s)

chapter('', 'References')
for s in ['Python Software Foundation. Python Documentation. https://docs.python.org/3/','The pandas development team. pandas Documentation. https://pandas.pydata.org/docs/','NumPy Developers. NumPy Documentation. https://numpy.org/doc/','scikit-learn Developers. Isolation Forest and preprocessing documentation. https://scikit-learn.org/stable/','Streamlit. Documentation. https://docs.streamlit.io/','Plotly Technologies Inc. Plotly Python Documentation. https://plotly.com/python/','Open Contracting Partnership. OCDS Documentation. https://standard.open-contracting.org/','FastAPI. Documentation. https://fastapi.tiangolo.com/','React. Documentation. https://react.dev/','Ministry of Statistics and Programme Implementation. Public project dashboard. https://ipm.mospi.gov.in/Home/PublicDashboard','Himachal Pradesh procurement dataset bundled in data/raw/; eight CSV source files.','EvidenceAI source code and README.md.']:bullet(s)

chapter('', 'Appendix A Project Structure')
table(['Path','Purpose'],[('data/raw/','Bundled procurement CSVs.'),('src/','Procurement data and analysis.'),('src/project_monitoring/','Project import, analysis, API, storage, documents, and investigations.'),('web/','React monitoring interface.'),('tests/','Selected automated checks.'),('app.py','Procurement app.'),('project_app.py','Monitoring Streamlit alternative.'),('README.md','Setup and implementation notes.')])
chapter('', 'Appendix B Indicator Definitions')
p('Procurement indicator score is the sum of the implemented single-tenderer, zero/negative INR, and high-INR flags. Missing amount or currency is a separate data-quality note. An eligible Isolation Forest flag can add one to the investigation score.')
p('Project review priority is the count of true review rules plus one when the model flags an outlier. It ranks prompts within the imported snapshot; it is not a calibrated probability.')
p('Completeness is one minus the missing-value share across recognized fields and imported rows. It describes field presence, not correctness.')

d.core_properties.title='EvidenceAI Project Report'; d.core_properties.subject='Procurement analysis and PAIMANA project monitoring'; d.core_properties.author='Kshitij Verma'
u=d.settings.element.find(qn('w:updateFields'))
if u is None:u=OxmlElement('w:updateFields'); d.settings.element.append(u)
u.set(qn('w:val'),'true')
d.save(OUT)
print(OUT, 'paragraphs',len(d.paragraphs),'tables',len(d.tables))
