import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, ArrowDownToLine, BarChart3, Building2, ChevronDown, CircleHelp,
  Database, FileSearch, FileText, GitBranch, LayoutDashboard, LoaderCircle,
  Search, ShieldCheck, Upload, X,
} from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Background, Controls, MiniMap, ReactFlow } from "@xyflow/react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
const NAV = [
  ["Overview", LayoutDashboard], ["Project Explorer", Search], ["Investigations", AlertTriangle],
  ["Evidence Documents", FileText], ["Evidence Graph", GitBranch], ["Reports", BarChart3],
];
const money = (value) => value == null ? "Not available" : Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
const field = (value) => value == null || value === "" ? "Not recorded" : String(value);

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try { message = (await response.json()).detail || message; } catch { /* keep status text */ }
    throw new Error(message);
  }
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response;
}

function App() {
  const [page, setPage] = useState("Overview");
  const [imports, setImports] = useState([]);
  const [importId, setImportId] = useState("");
  const [summary, setSummary] = useState(null);
  const [projects, setProjects] = useState([]);
  const [projectCount, setProjectCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState(null);
  const [review, setReview] = useState([]);
  const [reviewCount, setReviewCount] = useState(0);
  const [query, setQuery] = useState("");
  const [sector, setSector] = useState("");
  const [reviewOnly, setReviewOnly] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [caseData, setCaseData] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [documentQuery, setDocumentQuery] = useState("");
  const [documentSource, setDocumentSource] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const refreshImports = useCallback(async () => {
    try {
      const data = await request("/imports");
      setImports(data);
      if (!importId && data.length) setImportId(data[0].import_id);
      else if (importId && !data.some((item) => item.import_id === importId)) setImportId(data[0]?.import_id || "");
      setError("");
    } catch (err) { setError(`API is not connected. Start the local backend and retry. ${err.message}`); }
  }, [importId]);

  useEffect(() => { refreshImports(); }, [refreshImports]);

  const refreshWorkspace = useCallback(async () => {
    if (!importId) { setSummary(null); setProjects([]); setReview([]); setReviewCount(0); return; }
    setBusy(true);
    try {
      const [dash, list, flags] = await Promise.all([
        request(`/imports/${importId}/summary`),
        request(`/imports/${importId}/projects?query=${encodeURIComponent(query)}&sector=${encodeURIComponent(sector)}&review_only=${reviewOnly}&offset=${offset}&limit=100`),
        request(`/imports/${importId}/reviews?limit=250`),
      ]);
      setSummary(dash); setProjects(list.records); setProjectCount(list.total); setReview(flags.records); setReviewCount(flags.total); setError("");
      setSelected((old) => old || list.records[0] || null);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }, [importId, query, sector, reviewOnly, offset]);

  useEffect(() => { refreshWorkspace(); }, [refreshWorkspace]);

  const loadInvestigation = useCallback(async (record = selected) => {
    if (!record || !importId) return;
    setBusy(true);
    setCaseData(null); setEvidence([]);
    try {
      const result = await request(`/imports/${importId}/projects/${encodeURIComponent(record.record_key)}/${record.source_row_number}/investigation`);
      setCaseData(result);
      const documents = await request(`/imports/${importId}/evidence?query=${encodeURIComponent(`${record.project_id || ""} ${record.project_name || ""} ${record.sector || ""}`)}&record_key=${encodeURIComponent(record.record_key)}`);
      setEvidence(documents.records);
      setError("");
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }, [selected, importId]);

  const importFile = async (file) => {
    if (!file) return;
    setBusy(true); setUploadMessage("");
    try {
      const body = new FormData(); body.append("file", file); body.append("source_url", "https://ipm.mospi.gov.in/Home/PublicDashboard");
      const result = await request("/imports", { method: "POST", body });
      setUploadMessage(`Imported ${result.rows.toLocaleString()} project rows from ${result.filename}. Source retrieval date was not present in the file; local import time is recorded.`);
      setSelected(null); setCaseData(null); setEvidence([]); setOffset(0); setImportId(result.import_id); setPage("Overview");
      const allImports = await request("/imports");
      setImports(allImports); setImportId(result.import_id);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const uploadPdf = async (file) => {
    if (!file || !selected || !importId) return;
    setBusy(true);
    try {
      const body = new FormData(); body.append("file", file); body.append("record_key", selected.record_key); body.append("source_url", documentSource);
      await request(`/imports/${importId}/documents`, { method: "POST", body });
      setUploadMessage(`Extracted selectable text from ${file.name}; scanned PDF images are not OCRed.`);
      if (page === "Investigations") await loadInvestigation(selected);
      else setEvidence((await request(`/imports/${importId}/evidence?query=${encodeURIComponent(documentQuery || selected.project_name || "project")}`)).records);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const searchDocuments = async () => {
    if (!documentQuery.trim() || !importId) return;
    try {
      const result = await request(`/imports/${importId}/evidence?query=${encodeURIComponent(documentQuery)}${selected ? `&record_key=${encodeURIComponent(selected.record_key)}` : ""}`);
      setEvidence(result.records); setError("");
    } catch (err) { setError(err.message); }
  };

  const startQuestion = async (event) => {
    event.preventDefault();
    if (!selected || !question.trim()) return;
    try {
      const result = await request(`/imports/${importId}/projects/${encodeURIComponent(selected.record_key)}/${selected.source_row_number}/question`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
      setAnswer(result.answer); setError("");
    } catch (err) { setError(err.message); }
  };

  const heading = `${page}`;
  const activeImport = imports.find((item) => item.import_id === importId);
  const sectors = summary?.sectors || [];

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><BarChart3 size={22}/></div><div><strong>EvidenceAI</strong><span>Project intelligence</span></div></div>
      <div className="nav-label">WORKSPACE</div>
      <nav>{NAV.map(([label, Icon]) => <button key={label} className={`nav-item ${page === label ? "active" : ""}`} onClick={() => setPage(label)}><Icon size={17}/><span>{label}</span></button>)}</nav>
      {imports.length > 0 && <div className="snapshot"><div className="nav-label">ACTIVE SNAPSHOT</div><select value={importId} onChange={(e) => { setSelected(null); setCaseData(null); setEvidence([]); setOffset(0); setImportId(e.target.value); }} aria-label="Active project snapshot">{imports.map((item) => <option key={item.import_id} value={item.import_id}>{item.filename} · {item.row_count.toLocaleString()}</option>)}</select><small>{activeImport?.imported_at ? `Imported ${activeImport.imported_at.slice(0, 10)}` : "Local source snapshot"}</small></div>}
      <div className="sidebar-bottom"><Database size={16}/><div><strong>Local analysis</strong><span>Project source files stay on this computer.</span></div></div>
    </aside>
    <main className="main-area">
      <header className="topbar">
        <label className="global-search"><Search size={17}/><input value={query} onChange={(e) => { setOffset(0); setQuery(e.target.value); }} onKeyDown={(e) => { if (e.key === "Enter") setPage("Project Explorer"); }} placeholder="Search projects, sectors, ministries…" aria-label="Search project records"/></label>
        <span className="source-pill"><span className="status-dot"/>PAIMANA public records</span>
        <a className="outline-button source-link" href="https://ipm.mospi.gov.in/Home/PublicDashboard" target="_blank" rel="noreferrer">Source portal <ArrowDownToLine size={15}/></a>
      </header>
      <div className="workspace">
        <div className="page-heading"><div><div className="eyebrow">Project Assessment · Infrastructure Monitoring</div><h1>{heading}</h1><p>{pageCopy(page)}</p></div><div className="header-actions"><label className="primary-button upload-button"><Upload size={16}/>{busy ? "Working…" : "Import CSV / XLSX"}<input type="file" accept=".csv,.xlsx,.xlsm" onChange={(e) => importFile(e.target.files?.[0])}/></label></div></div>
        {error && <div className="notice error"><AlertTriangle size={18}/><span>{error}</span><button onClick={refreshImports}>Retry</button></div>}
        {uploadMessage && <div className="notice success"><ShieldCheck size={18}/><span>{uploadMessage}</span><button className="icon-button" onClick={() => setUploadMessage("")}><X size={16}/></button></div>}
        {!importId ? <Onboarding onFile={importFile} busy={busy}/> : <>
          {busy && <div className="inline-loading"><LoaderCircle className="spin" size={16}/> Loading current project snapshot…</div>}
          {page === "Overview" && <Overview summary={summary} activeImport={activeImport} onOpen={(row) => { setSelected(row); setPage("Project Explorer"); }}/>} 
          {page === "Project Explorer" && <Explorer projects={projects} count={projectCount} offset={offset} setOffset={setOffset} query={query} setQuery={setQuery} sector={sector} setSector={setSector} sectors={sectors.map((item) => item.sector)} reviewOnly={reviewOnly} setReviewOnly={setReviewOnly} selected={selected} setSelected={setSelected} openInvestigation={(record) => { setSelected(record); setPage("Investigations"); loadInvestigation(record); }}/>} 
          {page === "Investigations" && <Investigations review={review} reviewCount={reviewCount} summary={summary} projects={projects} selected={selected} setSelected={setSelected} caseData={caseData} evidence={evidence} loadCase={loadInvestigation} question={question} setQuestion={setQuestion} answer={answer} ask={startQuestion} importId={importId}/>} 
          {page === "Evidence Documents" && <Documents selected={selected} setSelected={setSelected} projects={projects} evidence={evidence} setDocumentQuery={setDocumentQuery} documentQuery={documentQuery} documentSource={documentSource} setDocumentSource={setDocumentSource} search={searchDocuments} upload={uploadPdf}/>} 
          {page === "Evidence Graph" && <Graph importId={importId} selected={selected} projects={projects} setSelected={setSelected}/>} 
          {page === "Reports" && <Reports importId={importId} summary={summary} selected={selected} activeImport={activeImport}/>} 
        </>}
      </div>
    </main>
  </div>;
}

function pageCopy(page) {
  return {
    Overview: "Portfolio summary and real-data monitoring indicators from the active source export.",
    "Project Explorer": "Filter and inspect individual records while keeping source fields and calculated values distinct.",
    Investigations: "Review a project with transparent signals, peer candidates, supporting evidence, and limitations.",
    "Evidence Documents": "Search selectable text extracted from official reports with page-level references.",
    "Evidence Graph": "Trace project, sector, ministry, source document, and indicator links in the imported data.",
    Reports: "Export the active snapshot, its data-quality summary, or a selected investigation brief.",
  }[page];
}

function Onboarding({ onFile, busy }) {
  return <section className="welcome-card"><div className="welcome-icon"><Database size={25}/></div><div className="eyebrow">Evidence-based project monitoring</div><h2>Start with an official PAIMANA export</h2><p>Download project data from the MoSPI public dashboard, then import the CSV or XLSX here. EvidenceAI keeps the source file, checksum, import time, source reference, and row-level provenance.</p><div className="welcome-actions"><label className="primary-button upload-button"><Upload size={16}/>{busy ? "Importing…" : "Choose project export"}<input type="file" accept=".csv,.xlsx,.xlsm" onChange={(e) => onFile(e.target.files?.[0])}/></label><a className="outline-button" href="https://ipm.mospi.gov.in/Home/PublicDashboard" target="_blank" rel="noreferrer">Open official dashboard <ChevronDown size={15}/></a></div><div className="welcome-note"><CircleHelp size={16}/>No demonstration records are bundled. Missing values remain blank and are never treated as zero.</div></section>;
}

function Metric({ label, value, note, icon: Icon }) {
  return <div className="metric-card"><div className="metric-head"><span>{label}</span>{Icon && <div className="metric-icon"><Icon size={17}/></div>}</div><div className="metric-value">{value}</div>{note && <div className="metric-note">{note}</div>}</div>;
}

function Overview({ summary, activeImport, onOpen }) {
  if (!summary) return <div className="empty-card">Load a snapshot to see data-derived project metrics.</div>;
  const totals = summary.totals || {};
  const progress = summary.progress_bands || [];
  return <>
    <section className="portfolio-hero"><div><div className="hero-eyebrow">Infrastructure portfolio · active imported snapshot</div><h2>{activeImport?.filename || "PAIMANA project records"}</h2><p>{summary.quality.rows.toLocaleString()} source rows · {activeImport?.cost_unit || "Source units retained"} · record-level source refs preserved</p></div><div className="hero-badge"><Database size={16}/>LOCAL SNAPSHOT</div></section>
    <div className="metric-grid five"><Metric label="Project records" value={summary.quality.rows.toLocaleString()} icon={Building2}/><Metric label="Review leads" value={summary.review_records.toLocaleString()} note="Triage only · no misconduct finding" icon={AlertTriangle}/><Metric label="Original cost total" value={money(totals.original_cost)} note={activeImport?.cost_unit}/><Metric label="Latest revised total" value={money(totals.revised_cost)} note={activeImport?.cost_unit}/><Metric label="Cumulative expenditure" value={money(totals.expenditure)} note={activeImport?.cost_unit}/></div>
    <div className="chart-grid">
      <section className="panel chart-panel"><PanelTitle title="Projects by sector" note="Top recorded sectors in this snapshot"/><ResponsiveContainer width="100%" height={300}><BarChart data={summary.sectors || []} layout="vertical" margin={{ left: 15, right: 22, top: 8, bottom: 5 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e7ecf2"/><XAxis type="number" tickLine={false} axisLine={false}/><YAxis dataKey="sector" type="category" width={150} tickLine={false} axisLine={false} tick={{ fontSize: 11 }}/><Tooltip/><Bar dataKey="projects" fill="#2186c7" radius={[0,5,5,0]}/></BarChart></ResponsiveContainer></section>
      <section className="panel chart-panel"><PanelTitle title="Physical progress" note="Valid progress observations grouped into 10-point bands"/>{progress.length ? <ResponsiveContainer width="100%" height={300}><BarChart data={progress} margin={{ left: 0, right: 12, top: 8, bottom: 5 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e7ecf2"/><XAxis dataKey="band" tickLine={false} axisLine={false} tick={{ fontSize: 10 }}/><YAxis tickLine={false} axisLine={false}/><Tooltip/><Bar dataKey="projects" fill="#167a84" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer> : <EmptyInline>No valid 0–100% progress values are recorded.</EmptyInline>}</section>
    </div>
    <div className="chart-grid">
      <BandChart title="Cost revision distribution" note="Revised versus original cost; the top band groups large revisions for source review" data={summary.cost_change_bands} color="#167a84" empty="No comparable original and revised cost values are available."/>
      <BandChart title="Expenditure against cost basis" note="Uses revised cost when available, otherwise original cost" data={summary.expenditure_bands} color="#7259d7" empty="No expenditure values with a usable cost basis are available."/>
    </div>
    <BandChart title="Completion-date deviation" note="Recorded revised date minus original date, grouped in months" data={summary.schedule_deviation_bands} color="#d99a27" empty="No records have both original and revised completion dates."/>
    <div className="content-grid overview-bottom">
      <section className="panel"><PanelTitle title="Projects requiring source review" note="Transparent rule indicators and statistical outliers"/><DataTable rows={summary.review_leads || []} columns={[["project_id","Project code"],["project_name","Project name"],["sector","Sector"],["review_priority","Priority"],["review_indicators","Why flagged"]]} onRow={onOpen}/></section>
      <section className="panel quality-panel"><PanelTitle title="Data quality snapshot" note="Completeness describes presence, not correctness"/><div className="quality-stat"><span>Recognized-field completeness</span><strong>{summary.quality.completeness_pct}%</strong></div><div className="progress-track"><span style={{ width: `${summary.quality.completeness_pct}%` }}/></div><div className="quality-stat"><span>Duplicate identity rows</span><strong>{summary.quality.duplicate_identity_rows.toLocaleString()}</strong></div><div className="quality-stat"><span>Invalid progress rows</span><strong>{summary.quality.invalid_progress_rows.toLocaleString()}</strong></div><div className="quality-stat"><span>Negative value rows</span><strong>{summary.quality.invalid_cost_rows.toLocaleString()}</strong></div><p className="muted-small">{summary.model_status}</p></section>
    </div>
  </>;
}

function PanelTitle({ title, note, action }) { return <div className="panel-title"><div><h3>{title}</h3>{note && <p>{note}</p>}</div>{action}</div>; }
function EmptyInline({ children }) { return <div className="empty-inline">{children}</div>; }

function BandChart({ title, note, data, color, empty }) {
  return <section className="panel chart-panel"><PanelTitle title={title} note={note}/>{data?.length ? <ResponsiveContainer width="100%" height={260}><BarChart data={data} margin={{ left: 0, right: 12, top: 8, bottom: 5 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e7ecf2"/><XAxis dataKey="band" tickLine={false} axisLine={false} tick={{ fontSize: 11 }}/><YAxis tickLine={false} axisLine={false}/><Tooltip/><Bar dataKey="projects" fill={color} radius={[5,5,0,0]}/></BarChart></ResponsiveContainer> : <EmptyInline>{empty}</EmptyInline>}</section>;
}

function DataTable({ rows, columns, onRow }) {
  if (!rows?.length) return <EmptyInline>No matching records are available.</EmptyInline>;
  return <div className="table-wrap"><table><thead><tr>{columns.map(([key,label]) => <th key={key}>{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.record_key || row.project_id || "row"}-${row.source_row_number ?? index}`} onClick={() => onRow?.(row)} onKeyDown={(event) => { if (onRow && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); onRow(row); } }} tabIndex={onRow ? 0 : undefined} className={onRow ? "click-row" : ""}>{columns.map(([key]) => <td key={key}>{typeof row[key] === "string" && /^https?:\/\//i.test(row[key]) ? <a href={row[key]} target="_blank" rel="noreferrer">{row[key]}</a> : field(row[key])}</td>)}</tr>)}</tbody></table></div>;
}

function Explorer({ projects, count, offset, setOffset, query, setQuery, sector, setSector, sectors, reviewOnly, setReviewOnly, selected, setSelected, openInvestigation }) {
  return <>
    <section className="filter-card"><div className="filter-control search-control"><label>Search this list</label><div className="search-input"><Search size={16}/><input value={query} onChange={(e) => { setOffset(0); setQuery(e.target.value); }} placeholder="Project ID, title, sector, ministry…"/></div></div><div className="filter-control"><label>Sector</label><select value={sector} onChange={(e) => { setOffset(0); setSector(e.target.value); }}><option value="">All sectors</option>{sectors.map((item) => <option key={item}>{item}</option>)}</select></div><label className="check-control"><input type="checkbox" checked={reviewOnly} onChange={(e) => { setOffset(0); setReviewOnly(e.target.checked); }}/>Review signals only</label><span className="results-count">{count.toLocaleString()} records</span></section>
    <section className="panel"><PanelTitle title="Project records" note="Select a row to inspect source fields and calculated indicators"/><DataTable rows={projects} columns={[["project_id","Project code"],["project_name","Project name"],["sector","Sector"],["ministry","Ministry / department"],["state","State / location"],["original_cost","Original cost"],["revised_cost","Revised cost"],["expenditure","Expenditure"],["physical_progress_pct","Progress (%)"],["cost_overrun_pct","Cost change (%)"]]} onRow={(row) => setSelected(row)}/><div className="table-pagination"><span>Showing {count ? offset + 1 : 0}–{Math.min(offset + projects.length, count)} of {count.toLocaleString()} records</span><div><button className="outline-button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous</button><button className="outline-button" disabled={offset + 100 >= count} onClick={() => setOffset(offset + 100)}>Next</button></div></div></section>
    {selected && <ProjectDetail project={selected} action={() => openInvestigation(selected)}/>} 
  </>;
}

function ProjectDetail({ project, action }) {
  const sourceFacts = [
    ["Project code", field(project.project_id)], ["Ministry / department", field(project.ministry)], ["Sector", field(project.sector)], ["State / location", field(project.state)],
    ["Original cost", `${field(project.original_cost)} · ${field(project.cost_unit)}`], ["Latest revised cost", `${field(project.revised_cost)} · ${field(project.cost_unit)}`], ["Cumulative expenditure", `${field(project.expenditure)} · ${field(project.cost_unit)}`], ["Physical progress", project.physical_progress_pct == null ? "Not recorded" : `${project.physical_progress_pct}%`],
    ["Original completion date", field(project.original_completion_date)?.slice(0,10)], ["Latest revised completion", field(project.revised_completion_date)?.slice(0,10)],
  ];
  return <section className="panel detail-panel"><div className="detail-head"><div><div className="eyebrow">Selected source record · row {project.source_row_number}</div><h2>{field(project.project_name)}</h2><p>{field(project.project_id)} · {field(project.sector)} · {field(project.ministry)}</p></div><button className="primary-button" onClick={action}><FileSearch size={16}/>Investigate project</button></div><div className="fact-heading"><strong>Fields reported by the source</strong><span>Blank fields remain “Not recorded”; values are not estimated.</span></div><div className="source-fields-grid">{sourceFacts.map(([label,value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div><div className="fact-heading calculated-heading"><strong>Calculated indicators</strong><span>Review priority and model scores support triage only.</span></div><div className="detail-metrics"><Metric label="Cost change" value={project.cost_overrun_pct == null ? "Not available" : `${Number(project.cost_overrun_pct).toFixed(1)}%`}/><Metric label="Expenditure" value={project.expenditure_pct == null ? "Not available" : `${Number(project.expenditure_pct).toFixed(1)}%`} note="of revised cost when available; else original"/><Metric label="Schedule deviation" value={project.schedule_deviation_months == null ? "Not available" : `${Number(project.schedule_deviation_months).toFixed(1)} months`}/><Metric label="Review priority" value={Number(project.review_priority || 0).toLocaleString()} note="Indicator count, not a probability"/><Metric label="Isolation Forest score" value={project.model_score == null ? "Not available" : Number(project.model_score).toFixed(4)} note="Statistical outlier score; not a probability"/></div><div className="record-provenance"><strong>Source</strong><span>{field(project.source_filename)} · row {project.source_row_number}</span><span>SHA-256: {field(project.source_sha256)}</span><a href={project.source_url} target="_blank" rel="noreferrer">Open recorded source ↗</a></div></section>;
}

function Investigations({ review, reviewCount, summary, projects, selected, setSelected, caseData, evidence, loadCase, question, setQuestion, answer, ask, importId }) {
  const [detailOpen, setDetailOpen] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  useEffect(() => { if (caseData) setDetailOpen(true); }, [caseData]);
  const choose = (row) => {
    const match = projects.find((candidate) => candidate.record_key === row.record_key && candidate.source_row_number === row.source_row_number) || row;
    setSelected(match); setDetailOpen(true); setSaveMessage(""); loadCase(match);
  };
  const saveCase = async () => {
    if (!selected || !caseData?.report_markdown) return;
    try {
      const result = await request(`/imports/${importId}/projects/${encodeURIComponent(selected.record_key)}/${selected.source_row_number}/investigations`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ report_markdown: caseData.report_markdown }) });
      setSaveMessage(`Investigation case saved locally (${result.case_id}).`);
    } catch (err) { setSaveMessage(`Could not save case: ${err.message}`); }
  };
  const downloadReport = () => {
    if (!caseData?.report_markdown) return;
    const blob = new Blob([caseData.report_markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = `evidenceai_project_${selected?.project_id || "case"}_brief.md`; anchor.click(); URL.revokeObjectURL(url);
  };
  return <>
    <div className="notice caution"><AlertTriangle size={18}/><span>Review signal only. Flags are prompts to verify source records; they are not fraud probabilities or findings.</span></div>
    <div className="metric-grid four"><Metric label="Projects screened" value={summary ? summary.quality.rows.toLocaleString() : "Loading"} icon={Building2}/><Metric label="Any review signal" value={summary ? reviewCount.toLocaleString() : "Loading"} icon={AlertTriangle}/><Metric label="Multiple rule indicators" value={review.filter((row) => Number(row.rule_indicator_count) > 1).length.toLocaleString()} note="Among the first 250 highest-priority rows"/><Metric label="Model status" value={caseData ? field(caseData.model_status) : field(summary?.model_status)} note="Isolation Forest requires enough usable rows"/></div>
    <section className="panel"><PanelTitle title="Investigation queue" note="Top 250 high-priority rows. Priority ranks checks; it is not a finding."/><DataTable rows={review} columns={[["project_id","Project code"],["project_name","Project name"],["sector","Sector"],["review_priority","Review priority"],["review_indicators","Why flagged"]]} onRow={choose}/></section>
    {detailOpen && selected && <>
      <ProjectDetail project={selected} action={() => loadCase(selected)}/>
      {caseData && <section className="investigation-grid">
        <div className="panel"><PanelTitle title="Evidence and limitations" note="Only imported project records and uploaded public PDFs are used"/><div className="signal-list">{caseData.indicators.length ? caseData.indicators.map((item) => <div className="signal-row" key={item}><AlertTriangle size={15}/>{item}</div>) : <EmptyInline>No review indicators were produced under the current checks.</EmptyInline>}</div><h4>Supporting document passages</h4>{evidence.length ? evidence.slice(0,6).map((item) => <blockquote className="evidence-quote" key={`${item.filename}-${item.page_number}`}><span>{item.filename} · page {item.page_number}{item.source_url ? <> · <a href={item.source_url} target="_blank" rel="noreferrer">source</a></> : " · source URL not recorded"}</span><p>{item.passage}</p></blockquote>) : <EmptyInline>No supporting document found in the available dataset.</EmptyInline>}<h4>Data limitations</h4><ul className="limit-list">{caseData.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>
        <div className="panel"><PanelTitle title="Comparable projects" note="Candidates ranked from recorded sector, cost scale, and name text"/><DataTable rows={caseData.similar_projects?.slice(0,8)} columns={[["project_id","Project code"],["project_name","Project name"],["sector","Sector"],["comparison_criteria","Comparison criteria"]]}/><div className="qa-box"><h4>Ask about this project</h4><p>Answers use only this project row, calculated indicators, peer metadata, and imported PDF text.</p><form onSubmit={ask}><input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="How is the cost change calculated?"/><button className="primary-button">Explain</button></form>{answer && <div className="answer-box">{answer}</div>}</div><div className="case-actions"><button className="outline-button" onClick={downloadReport}><ArrowDownToLine size={16}/>Download investigation brief</button><button className="primary-button" onClick={saveCase} disabled={!caseData?.report_markdown}>Save case locally</button></div>{saveMessage && <span className="quiet-caption">{saveMessage}</span>}<span className="quiet-caption">The brief is generated locally from the selected {importId ? "snapshot" : "record"}.</span></div>
      </section>}
    </>}
  </>;
}

function Documents({ selected, setSelected, projects, evidence, setDocumentQuery, documentQuery, documentSource, setDocumentSource, search, upload }) {
  const choices = selected && !projects.some((item) => item.record_key === selected.record_key && item.source_row_number === selected.source_row_number) ? [selected, ...projects] : projects;
  return <>
    <section className="panel"><PanelTitle title="Associate a public report" note="Text PDFs only · scanned/image-only files are reported as unsupported; no OCR is performed"/><div className="document-tools"><select value={selected ? `${selected.record_key}|${selected.source_row_number}` : ""} onChange={(e) => { const [key,row] = e.target.value.split("|"); setSelected(choices.find((item) => item.record_key === key && String(item.source_row_number) === row) || null); }}><option value="">Choose associated project</option>{choices.map((item) => <option key={`${item.record_key}-${item.source_row_number}`} value={`${item.record_key}|${item.source_row_number}`}>{field(item.project_id)} · {field(item.project_name).slice(0,65)} · row {item.source_row_number}</option>)}</select><input className="source-url-input" value={documentSource} onChange={(e) => setDocumentSource(e.target.value)} placeholder="Official report URL (optional)" aria-label="Official report source URL"/><label className={`outline-button upload-button ${!selected ? "disabled" : ""}`}><Upload size={16}/>Upload PDF<input type="file" accept="application/pdf,.pdf" disabled={!selected} onChange={(e) => upload(e.target.files?.[0])}/></label></div></section>
    <section className="panel"><PanelTitle title="Search extracted evidence" note="Each result carries its source document and page reference"/><div className="search-row"><input value={documentQuery} onChange={(e) => setDocumentQuery(e.target.value)} placeholder="Search a project code, name, or phrase…"/><button className="primary-button" onClick={search}><Search size={16}/>Search passages</button></div>{evidence.length ? <DataTable rows={evidence} columns={[["filename","Source document"],["source_url","Official source URL"],["page_number","Page"],["passage","Extracted passage"]]}/> : <EmptyInline>No matching passages. Upload a text PDF or change the search terms.</EmptyInline>}</section>
  </>;
}

function Graph({ importId, selected, projects, setSelected }) {
  const [graph, setGraph] = useState(null);
  const [error, setError] = useState("");
  const choices = selected && !projects.some((item) => item.record_key === selected.record_key && item.source_row_number === selected.source_row_number) ? [selected, ...projects] : projects;
  useEffect(() => {
    if (!selected || !importId) return;
    request(`/imports/${importId}/projects/${encodeURIComponent(selected.record_key)}/${selected.source_row_number}/graph`).then(setGraph).catch((err) => setError(err.message));
  }, [importId, selected]);
  const nodes = useMemo(() => (graph?.nodes || []).map((node, index) => ({ id: node.id, position: { x: index === 0 ? 80 : 360, y: index === 0 ? 190 : 42 + ((index - 1) * 105) }, data: { label: <div className={`graph-node node-${node.type}`}><small>{node.type}</small><strong>{node.label}</strong></div> }, type: "default", draggable: true })), [graph]);
  const edges = useMemo(() => (graph?.edges || []).map((edge) => ({ ...edge, animated: false, style: { stroke: "#1683a3", strokeWidth: 1.8 }, labelStyle: { fill: "#50647a", fontSize: 10 } })), [graph]);
  return <>
    <section className="filter-card"><div className="filter-control"><label>Project record</label><select value={selected ? `${selected.record_key}|${selected.source_row_number}` : ""} onChange={(e) => { const [key,row] = e.target.value.split("|"); setSelected(choices.find((item) => item.record_key === key && String(item.source_row_number) === row) || null); }}>{choices.map((item) => <option key={`${item.record_key}-${item.source_row_number}`} value={`${item.record_key}|${item.source_row_number}`}>{field(item.project_id)} · {field(item.project_name).slice(0,75)}</option>)}</select></div><span className="results-count">Source-backed links only</span></section>
    <section className="panel graph-panel"><PanelTitle title={selected ? field(selected.project_name) : "Evidence graph"} note="Nodes and edges are grounded in the active project record"/>{error ? <EmptyInline>{error}</EmptyInline> : nodes.length > 1 ? <div className="react-flow-canvas"><ReactFlow nodes={nodes} edges={edges} fitView fitViewOptions={{ padding: 0.25 }} nodesConnectable={false}><Background color="#e5ebf1" gap={22}/><Controls/><MiniMap zoomable pannable/></ReactFlow></div> : <EmptyInline>No supported relationships are available for this project yet.</EmptyInline>}<p className="muted-small">The graph shows recorded sector, ministry, location, user-associated PDF, or calculated review-signal links. It does not infer ownership or geography.</p></section>
  </>;
}

function Reports({ importId, summary, selected, activeImport }) {
  const reportLinks = [
    ["Data-quality summary (JSON)", `/imports/${importId}/reports/quality`, "snapshot-quality.json"],
    ["Active project snapshot (CSV)", `/imports/${importId}/reports/projects.csv`, "project-snapshot.csv"],
  ];
  const saveReport = async (url, filename) => {
    try { const response = await request(url); const blob = await response.blob(); const objectUrl = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = objectUrl; a.download = filename; a.click(); URL.revokeObjectURL(objectUrl); } catch (err) { window.alert(err.message); }
  };
  const [suggestions, setSuggestions] = useState([]);
  const [savedCases, setSavedCases] = useState([]);
  const missingRows = Object.entries(summary?.quality?.missing_by_field || {}).map(([name,count]) => ({ field: name.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()), missing_rows: count, missing_percent: summary.quality.rows ? `${(100 * count / summary.quality.rows).toFixed(1)}%` : "Not available" }));
  useEffect(() => { request(`/imports/${importId}/entities/suggestions`).then((data) => setSuggestions(data.matches || [])).catch(() => setSuggestions([])); }, [importId]);
  useEffect(() => { request(`/imports/${importId}/investigations`).then((data) => setSavedCases(data.records || [])).catch(() => setSavedCases([])); }, [importId]);
  const confirmSuggestion = async (matchId) => {
    try {
      const result = await request(`/imports/${importId}/entities/${encodeURIComponent(matchId)}/confirm`, { method: "POST" });
      setSuggestions((old) => old.map((item) => item.match_id === matchId ? { ...item, Status: result.status } : item));
    } catch (err) { window.alert(err.message); }
  };
  return <>
    <div className="report-grid">{reportLinks.map(([label,url,file]) => <button className="report-card" key={url} onClick={() => saveReport(url,file)}><div className="report-icon"><FileText size={18}/></div><strong>{label}</strong><span>Built from the active imported snapshot.</span><div className="report-link">Download <ArrowDownToLine size={15}/></div></button>)}</div>
    <section className="panel"><PanelTitle title="Data quality findings" note="Missing means not present in this export; it does not mean zero or incorrect"/><div className="metric-grid five"><Metric label="Recognized-field completeness" value={summary ? `${summary.quality.completeness_pct}%` : "Loading"}/><Metric label="Duplicate identity rows" value={summary ? summary.quality.duplicate_identity_rows.toLocaleString() : "Loading"}/><Metric label="Invalid progress rows" value={summary ? summary.quality.invalid_progress_rows.toLocaleString() : "Loading"}/><Metric label="Negative costs / expenditure" value={summary ? summary.quality.invalid_cost_rows.toLocaleString() : "Loading"}/><Metric label="Expenditure above revised cost" value={summary ? summary.quality.expenditure_exceeds_revised_cost_rows.toLocaleString() : "Loading"}/></div>{summary ? <DataTable rows={missingRows} columns={[["field","Recognized field"],["missing_rows","Missing rows"],["missing_percent","Missing (%)"]]}/> : <EmptyInline>Data-quality summary is loading.</EmptyInline>}<p className="muted-small">Check flagged values against the original source before interpreting them. Cost units remain those shown by the imported export.</p></section>
    <section className="panel"><PanelTitle title="Snapshot provenance" note="Import time is recorded; source retrieval time is not inferred if the export omits it"/><div className="provenance-grid"><div><small>Source file</small><strong>{field(activeImport?.filename)}</strong></div><div><small>Imported at</small><strong>{field(activeImport?.imported_at)}</strong></div><div><small>Source page</small><a href={activeImport?.source_url} target="_blank" rel="noreferrer">Open source ↗</a></div><div><small>Imported rows</small><strong>{(activeImport?.row_count || 0).toLocaleString()}</strong></div></div></section>
    <section className="panel"><PanelTitle title="Potential ministry-name matches" note="String similarity suggestions; only analyst-confirmed pairs are marked confirmed"/>{suggestions.length ? <div className="table-wrap"><table><thead><tr><th>Recorded name A</th><th>Recorded name B</th><th>Similarity</th><th>Status</th><th>Action</th></tr></thead><tbody>{suggestions.map((item) => <tr key={item.match_id}><td>{item["Recorded name A"]}</td><td>{item["Recorded name B"]}</td><td>{item["Similarity score"]}%</td><td>{item.Status}</td><td>{item.Status === "confirmed by analyst" ? <span className="confirmed-tag">Confirmed</span> : <button className="outline-button" onClick={() => confirmSuggestion(item.match_id)}>Confirm pair</button>}</td></tr>)}</tbody></table></div> : <EmptyInline>No high-similarity name pairs were found in this snapshot.</EmptyInline>}</section>
    <section className="panel"><PanelTitle title="Saved investigation cases" note="Cases saved locally from a selected source snapshot"/>{savedCases.length ? <div className="table-wrap"><table><thead><tr><th>Project</th><th>Saved at</th><th>Source record key</th><th>Report</th></tr></thead><tbody>{savedCases.map((item) => <tr key={item.investigation_id}><td>{field(item.project_id)} · {field(item.project_name)}</td><td>{field(item.created_at)}</td><td>{item.record_key}</td><td><button className="outline-button" onClick={() => { const blob=new Blob([item.summary_markdown],{type:"text/markdown"}); const objectUrl=URL.createObjectURL(blob); const link=document.createElement("a"); link.href=objectUrl; link.download=`evidenceai_case_${item.project_id || item.investigation_id}.md`; link.click(); URL.revokeObjectURL(objectUrl); }}>Download brief</button></td></tr>)}</tbody></table></div> : <EmptyInline>No investigation cases have been saved for this snapshot yet.</EmptyInline>}</section>
    {selected && <div className="notice"><FileSearch size={17}/><span>Selected project: {field(selected.project_id)} · {field(selected.project_name)}. Open Investigations to download a record-level brief.</span></div>}
  </>;
}

export default App;
