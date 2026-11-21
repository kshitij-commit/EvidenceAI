from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

src=Path(r'C:\Users\kshit\Downloads\EvidenceAI_Report_PreviewWord.docx')
out=Path(r'C:\Users\kshit\Desktop\05_document\5th semester notes\EvidenceAi\EvidenceAI_Project_Report_70_Pages.docx')
d=Document(src)

def replace_para(p, text):
    for r in p.runs: r.text=''
    p.add_run(text)

def apply_body(p):
    p.paragraph_format.space_after=Pt(6)
    p.paragraph_format.line_spacing=1.12
    for r in p.runs:
        r.font.name='Times New Roman'; r.font.size=Pt(11)

# Remove draft production notes and replace known unsubstantiated statements.
for p in list(d.paragraphs):
    t=p.text.strip()
    if t.startswith('Target length: approximately'):
        p._element.getparent().remove(p._element); continue
    if t=='Suggested screenshots for this section:':
        replace_para(p,'Implementation evidence in this report consists of the documented architecture, source excerpts and data-flow diagrams. The deployed interface is not represented by fabricated screenshots.'); continue
    if t.startswith('Note: Insert actual screenshots captured'):
        p._element.getparent().remove(p._element); continue
    if 'Isolation Forest model was fitted on 453' in t:
        replace_para(p,'Isolation Forest screening is conditional on the installed dependency and eligible numeric records. Its eligible set and flags depend on the runtime data and preprocessing configuration; this report therefore does not present a fixed outlier count as a verified result.'); continue
    if 'fitted on 453 eligible INR-denominated records' in t:
        replace_para(p,'The model uses eligible INR-denominated records when the required dependency is available. The application can report the model as unavailable when its optional dependency or minimum data conditions are not met.'); continue
    if 'model was fitted on 453 records' in t:
        replace_para(p,'When enabled and supplied with enough eligible rows, the model evaluates selected numerical features and returns statistical flags. These flags are runtime-dependent and are not treated as confirmed findings.'); continue
    if 'model identified 23 records' in t or 'model marked 23 records' in t:
        replace_para(p,'The number of records flagged is determined at runtime by the eligible input rows, installed dependencies and configured model. No fixed count is asserted here.'); continue
    if 'Due to the availability of comparable financial information, the model was fitted on 453' in t:
        replace_para(p,'Isolation Forest screening is conditional on comparable eligible values and an available scikit-learn installation. The result is recalculated from the current input rather than treated as a fixed dataset statistic.'); continue
    if '<badge color="success">4 out of 4 tests passed</badge>' in t:
        replace_para(p,'The repository currently defines two unit tests. This report describes their purpose and does not claim an execution result.'); continue
    if 'The test results indicate that all four tested functions performed successfully' in t:
        replace_para(p,'The two test definitions cover exact tender-award-supplier links and handling of a missing currency as a quality note. Their presence documents intended checks; no pass status is reported here.'); continue
    if 'successful execution of the existing unit tests' in t.lower():
        replace_para(p,'The repository includes unit-test definitions for selected analysis behavior. Test execution should be recorded separately with the environment and date when performed.'); continue

# Update abstract with a concise accurate summary of the second workspace.
for p in d.paragraphs:
    if p.text.startswith('EvidenceAI: Evidence-Based Investigation') and p.text.strip().startswith('EvidenceAI:'):
        p.add_run(' A separate PAIMANA project-monitoring workspace imports analyst-selected CSV and Excel project snapshots, preserves source provenance, computes cost, expenditure, progress and schedule indicators, and supports evidence search over selectable-text PDF documents. It provides deterministic question answering and locally saved investigation briefs. Procurement and infrastructure data remain separate workflows.');
        apply_body(p); break

# Correct model facts in tables.
for ti in (12,19):
    if ti < len(d.tables):
        for row in d.tables[ti].rows:
            if row.cells and row.cells[0].text.strip() in ('Records used','Records analysed'):
                row.cells[1].text='Runtime-dependent eligible rows'
# Update test case table (table 22 in source).
if len(d.tables)>22:
    t=d.tables[22]
    for row in list(t.rows)[1:]:
        t._tbl.remove(row._tr)
    for vals in [
        ('Tender-award-supplier exact links','Checks that tender, award and supplier identifiers join exactly','Defined in repository; execution not claimed'),
        ('Missing currency handling','Checks that missing currency becomes a quality note and does not raise priority score','Defined in repository; execution not claimed')]:
        cells=t.add_row().cells
        for c,v in zip(cells,vals): c.text=v
# Replace screenshot placeholder table with a truthful implementation reference table.
if len(d.tables)>14:
    t=d.tables[14]
    rows=[('Module','Implementation evidence described'),('Overview','Summary metrics and procurement charts'),('Explore Records','Search and filter tender records'),('Anomaly Review','Rule indicators and conditional statistical screening'),('Buyer and Supplier Search','Party lookup and linked procurement records'),('Relationships','Tender, award and supplier links'),('Data Quality and Reports','Missing-value audit and report outputs')]
    while len(t.rows)<len(rows): t.add_row()
    while len(t.rows)>len(rows): t._tbl.remove(t.rows[-1]._tr)
    for row,vals in zip(t.rows,rows):
        for c,v in zip(row.cells,vals): c.text=v

# Refresh the contents chapter list, including the expanded project-monitoring chapter.
if d.tables:
    t=d.tables[0]
    toc=[('1','Introduction'),('2','Literature Review'),('3','Problem Definition and Existing System'),('4','Objectives and Scope'),('5','Proposed System'),('6','System Requirements and Feasibility'),('7','Technical Overview'),('8','System Architecture and Design'),('9','Data Flow Diagram and Data Relationships'),('10','Main Modules of the Project'),('11','Algorithms and Methodology'),('12','System Implementation and Coding'),('13','Results and Analysis'),('14','Software Testing'),('15','Project Monitoring Workspace PAIMANA'),('16','Conclusion and Future Scope'),('17','Bibliography / References'),('18','Appendix')]
    while len(t.rows)<len(toc): t.add_row()
    while len(t.rows)>len(toc): t._tbl.remove(t.rows[-1]._tr)
    for row,(n,title) in zip(t.rows,toc):
        row.cells[0].text=n; row.cells[1].text=title
    # Content in body uses the existing chapter sequence: add PAIMANA as 16 and increment ending chapters.

# Update old chapter headings and conclusion references in body.
for p in d.paragraphs:
    s=p.text.strip()
    mapping={'CONCLUSION':'CONCLUSION','16.1 Conclusion':'17.1 Conclusion','16.2 Limitations':'17.2 Limitations','16.3 Future Scope':'17.3 Future Scope','BIBLIOGRAPHY / REFERENCES':'BIBLIOGRAPHY / REFERENCES','APPENDIX':'APPENDIX'}
    if s in mapping and s!='CONCLUSION': replace_para(p,mapping[s])
    elif s.startswith('Chapter 16') and 'Conclusion' in s: replace_para(p,'Chapter 17 – Conclusion')
    elif s.startswith('Chapter 17') and 'Bibliography' in s: replace_para(p,'Chapter 18 – Bibliography / References')
    elif s.startswith('Chapter 18') and 'Appendix' in s: replace_para(p,'Chapter 19 – Appendix')
# Replace explicit numbered subheadings throughout conclusion.
for p in d.paragraphs:
    s=p.text.strip()
    if s.startswith('16.') and any(k in s.lower() for k in ('conclusion','limitation','future scope')):
        replace_para(p,'17.'+s[3:])

# Add acknowledgement before abstract, retaining all original front matter.
abstract=next(p for p in d.paragraphs if p.text.strip()=='ABSTRACT')
ack=abstract.insert_paragraph_before('ACKNOWLEDGEMENT')
ack.style='Heading 1'; ack.paragraph_format.page_break_before=True
ack.paragraph_format.keep_with_next=True
acktext=abstract.insert_paragraph_before('I express my sincere gratitude to my project guide, Mr. Anmol Dubey, for his guidance during the planning and development of EvidenceAI. I thank the Department of Computer Science and Engineering, Faculty of Engineering and Technology, AKS University, for providing the academic setting in which this work was completed. I also acknowledge the public procurement data and the open-source software communities whose documented formats and tools made the procurement analysis workspace possible. The PAIMANA workspace was developed as a separate, import-driven project-monitoring workflow. Finally, I thank my family and peers for their encouragement during the project. The design, implementation and limitations described in this report are my responsibility.')
apply_body(acktext)

# Add a substantial, eight-page chapter before conclusion. Each section begins on its own page;
# 16.1 shares the chapter-opening page to maintain exactly eight content pages.
conclusion=next(p for p in d.paragraphs if p.text.strip()=='CONCLUSION')
sections=[
('16. Project Monitoring Workspace PAIMANA',[
('16.1 Purpose and Workflow','PAIMANA is the second, separate workspace in EvidenceAI. It supports monitoring of public infrastructure projects from project snapshots supplied by an analyst. The procurement workspace uses the bundled Himachal Pradesh OCDS-related files; PAIMANA does not silently merge those records with project-monitoring data. This separation keeps the meaning, source and units of each dataset clear.\n\nThe workflow starts when an analyst imports a CSV, XLSX or XLSM export. The user maps source columns to project identity, ministry, sector, location, original and revised cost, expenditure, progress and original or revised dates. After mapping, the system normalizes values, reports quality issues and derives indicators. An analyst can inspect candidate peer projects, attach selectable-text PDF evidence, ask deterministic questions over extracted passages, and save an investigation brief.\n\nThe six React pages are Overview, Project Explorer, Investigations, Evidence Documents, Evidence Graph and Reports. A FastAPI service provides the API and SQLite persistence. A Streamlit fallback is available for environments where the React interface is not used. The workspace is designed as decision support: imported data and computed indicators require review against official records.'),
('16.2 Import, Mapping and Provenance','The importer accepts CSV and common Excel workbook formats. Since source spreadsheets differ in headings and layout, the analyst maps columns to a normalized project schema. Core fields include a project code or name, ministry, sector and location; original and revised project cost; expenditure and progress; and planned or revised dates. Mapping is explicit so that a value is not assigned to a field solely because a column happens to occupy a particular position.\n\nFor traceability, imported records retain the source filename, import timestamp, file checksum, source URL when supplied, and source row number. The SHA-256 digest helps distinguish file versions and detect whether an imported snapshot changed. The row reference lets a reviewer return to the original spreadsheet. These fields form provenance metadata; they do not establish that the source itself is authoritative or current.\n\nAn analyst should preserve the downloaded export and record its publication context before import. If a new export is loaded, it should be treated as a separate snapshot rather than assumed to be a continuation of the previous one. This allows a reviewer to compare changes while retaining the evidence trail needed to explain which source produced a displayed indicator.'),
('16.3 Data Quality and Derived Indicators','The workspace computes quality measures for missing fields, duplicate project identities, invalid ranges, negative costs and expenditure above revised cost. These checks help identify records that may need correction or context before comparison. A missing value is kept distinct from zero: zero is a reported number, while missing means that the source did not supply a usable value. The application exposes such issues for review instead of treating them as proof of a project problem.\n\nDerived measures include cost overrun percentage, expenditure percentage, the gap between expenditure and reported physical progress, and schedule deviation between planned and revised dates. The cost-overrun calculation compares revised cost with original cost relative to original cost. Expenditure percentage compares expenditure with the selected revised-cost basis. The progress gap compares expenditure percentage with physical progress percentage; schedule deviation compares revised and original dates.\n\nEach calculation depends on valid denominators and consistently mapped units. An undefined ratio should not be interpreted as zero. Currency, date conventions and the meaning of progress must be checked in the source export. The workspace can calculate a transparent indicator, but it cannot resolve inconsistent reporting definitions by itself.'),
('16.4 Transparent Rules and Conditional Anomaly Screening','PAIMANA includes explicit rules for records such as negative cost, expenditure greater than revised cost, invalid progress ranges and schedule or cost deviations. A rule result can be explained by its condition and source values, which makes it suitable for triage. Rule thresholds are signals for review and should be interpreted in context: a revised budget or schedule may have a documented reason that is not present in the imported row.\n\nThe optional Isolation Forest path is conditional. It requires scikit-learn, at least 30 eligible records and at least two usable numeric features. The implementation uses median imputation, standardization, 200 estimators and a fixed random seed; the default contamination setting is 0.05. The eligible dataset and resulting flags depend on the imported snapshot and missingness. If prerequisites are absent, the model is unavailable rather than a fabricated zero-result.\n\nA statistical flag means that a record differs from the fitted data pattern under the selected features. It does not establish fraud, delay, poor quality or misconduct. The review interface should be used to inspect the source row, compare relevant projects and consult supporting documents before drawing conclusions.'),
('16.5 Peer Candidates and Entity Suggestions','The workspace supports candidate peer comparisons using available attributes such as sector, project cost and name similarity. Peer candidates are leads for contextual review. Similar cost alone does not make two projects comparable: scope, geography, time period, implementation stage and reporting basis can differ. The reviewer should confirm comparability before treating peer values as a benchmark.\n\nWhere configured with a local model path, the application can use a Sentence Transformer for semantic similarity. This mode depends on a model already available locally and does not require downloading a model as part of normal operation. If the local model is not configured, the feature may be unavailable; that state should be reported clearly.\n\nMinistry-name suggestions use fuzzy matching to identify possible spelling or naming variants. These are suggestions only. The application requires analyst confirmation before treating two names as the same entity. Keeping proposed and confirmed matches separate prevents a similarity score from silently changing the meaning of the underlying source. A reviewer should preserve the original name alongside any confirmed canonical mapping.'),
('16.6 PDF Evidence, Questions and Investigation Briefs','Analysts can attach PDF documents as supporting evidence. The current extraction path works with selectable text and records page references and checksums. It does not perform OCR on scanned image-only documents. If a PDF contains no extractable text, the user must provide a text-readable source or use an external OCR workflow and verify its output before relying on it.\n\nEvidence search ranks passages using term overlap and returns the supporting text with its page reference. The question-answering interface is deterministic: it uses the retrieved passages and does not call a generative language model. Responses should therefore be read as a navigation aid to source passages, not as an independent factual conclusion. The user should open the cited page and check that the passage supports the intended interpretation.\n\nAn investigation brief can assemble project indicators, provenance and evidence references for local review. Saving the brief does not make it an official audit finding. The analyst remains responsible for confirming that documents are relevant, current and connected to the project under examination.'),
('16.7 Application Architecture, API and Storage','The PAIMANA frontend uses React, Tailwind CSS, Recharts and React Flow. It organizes project browsing, investigations, evidence documents, graph relationships and report views. FastAPI exposes backend operations and SQLite provides local persistence for supported application records. The architecture separates the user interface from data import, analysis and storage so that each stage can be inspected and maintained.\n\nThe repository provides a Windows launcher, run-project-monitor.bat, for the API and frontend workflow. The documented local services use port 8000 for the API and 5173 for the React development interface. A separate run-project-monitor-streamlit.bat starts the fallback interface. Exact behavior depends on the installed dependencies and local configuration; users should follow the README and keep imported exports in an access-controlled project directory.\n\nPersistent data may include imported snapshots, mappings, evidence documents, entity-match decisions and investigation cases. These records should be backed up and handled according to the project’s data-management practices. The workspace is not presented as a deployed government integration or a live connection to official project systems.'),
('16.8 Results, Verification and Limitations','No authentic PAIMANA project export is bundled with the repository. Consequently, this report does not invent project counts, cost overruns, schedule delays or document findings for that workspace. Its results are described as implemented functions and formulas, not as empirical project-monitoring outcomes. A meaningful demonstration should record the source export, date, mappings, quality warnings and selected project examples.\n\nThe procurement workspace has a bundled dataset and reports dataset-derived indicators in its own chapter. PAIMANA requires an imported snapshot and human validation. The source repository also contains two procurement unit-test definitions: exact tender-award-supplier linking and handling missing currency as a quality note. This report does not claim those tests were executed or passed.\n\nCurrent limitations include dependence on analyst-selected exports, variation in field definitions, no OCR for scanned PDFs, conditional availability of machine-learning and semantic features, and the need for human confirmation of entity matches and evidence relevance. Future work can add version-to-version comparison, validated OCR, richer audit logging, controlled user access and repeatable test coverage. Any expansion should retain source references and explain the basis of each computed indicator.')])]

# Add chapter title and its subsections before the existing conclusion.
title, subs=sections[0]
h=conclusion.insert_paragraph_before(title); h.style='Heading 1'; h.paragraph_format.page_break_before=True
for idx,(st,body) in enumerate(subs):
    sh=conclusion.insert_paragraph_before(st); sh.style='Heading 2'
    if idx>0: sh.paragraph_format.page_break_before=True
    sh.paragraph_format.keep_with_next=True
    bp=conclusion.insert_paragraph_before(body); apply_body(bp)

# Clean replacement character and ampersand title in visible front matter.
for p in d.paragraphs:
    if '\ufffd' in p.text:
        txt=p.text.replace('\ufffd','-').replace('EvidenceAI:','EvidenceAI:')
        replace_para(p,txt)
# Set section page background/border is retained from source; preserve all original images/tables.
d.save(out)
print('Saved',out,'paragraphs',len(d.paragraphs),'tables',len(d.tables))
