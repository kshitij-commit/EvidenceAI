"""EvidenceAI local investigation-support dashboard."""

from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analysis import comparable_tenders, investigation_flags, tender_records
from src.data import audit_dataset, load_dataset


st.set_page_config(page_title="EvidenceAI", page_icon="assets/evidenceai-mark.png", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
  :root {color-scheme:light; --navy:#172B4D; --teal:#176B87; --canvas:#F4F6FA; --surface:#FFFFFF; --border:#DEE4EB; --text:#172B4D; --muted:#617387; --amber:#D99A27;}
  html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"] {background:#fff !important; color:var(--text); font-family:Inter,"Segoe UI",sans-serif;}
  .block-container,[data-testid="stMainBlockContainer"] {width:100% !important; max-width:1550px !important; padding:1.7rem clamp(1.5rem,3vw,3.2rem) 3.5rem !important; background:var(--canvas) !important;}
  [data-testid="stHeader"] {background:transparent;}
  [data-testid="stSidebar"] {background:var(--navy) !important; border-right:1px solid #263d60; min-width:18rem;}
  [data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding:1.25rem 1rem 1.8rem;}
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#c0cad8; line-height:1.55;}
  [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {font-size:.78rem;}
  [data-testid="stSidebar"] h4 {color:#fff; font-size:.96rem; margin:.2rem 0 .35rem;}
  .brand-panel {display:flex; align-items:center; gap:.8rem; padding:1rem .9rem; margin:.1rem 0 1.5rem; border:1px solid #31486a; border-left:3px solid #56a5b8; border-radius:8px; background:#1d3558;}
  .brand-mark {position:relative; display:grid; place-items:center; flex:0 0 2.55rem; height:2.55rem; border-radius:7px; background:#e8f2f4; color:var(--navy); font-size:.83rem; font-weight:850; letter-spacing:-.08em;}
  .brand-mark:after {content:""; position:absolute; width:.38rem; height:.38rem; top:.35rem; right:.35rem; border-radius:50%; background:#56a5b8; border:2px solid #e8f2f4;}
  .brand-name {color:#fff; font-size:1.08rem; font-weight:760; letter-spacing:-.025em; line-height:1.2;}
  .brand-caption {color:#c2cfdd; font-size:.72rem; margin-top:.25rem;}
  .sidebar-section-label {margin:.35rem 0 .55rem; color:#8da3bf; font-size:.69rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase;}
  [data-testid="stSidebar"] [data-testid="stRadio"] > label {display:none;}
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:.3rem;}
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {padding:.7rem .72rem; border:1px solid transparent; border-radius:7px; color:#c8d2df; font-size:.9rem; font-weight:560; transition:background .15s ease,border-color .15s ease;}
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {background:#203a60; border-color:#2b466b; color:#fff;}
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {background:#28476f; border-color:#3b5c85; border-left:3px solid #62b1c1; color:#fff; font-weight:700;}
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked)>div>div:first-child {background:#62b1c1 !important; border-color:#62b1c1 !important;}
  .sidebar-dataset {margin-top:1.4rem; padding:.8rem .75rem; border-top:1px solid #314766; color:#8da3bf; font-size:.69rem; letter-spacing:.08em; text-transform:uppercase; line-height:1.7;}
  .sidebar-dataset strong {color:#e2e9f1; font-size:.77rem; font-weight:600; letter-spacing:0; text-transform:none;}
  [data-testid="stSidebar"] hr {border-color:#344a69; margin:1.15rem 0;}
  [data-testid="stSidebar"] [data-testid="stTextInput"] input,[data-testid="stSidebar"] [data-baseweb="select"]>div,[data-testid="stSidebar"] [data-testid="stDateInput"] input,[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div {background:#20385a !important; border-color:#3b5273 !important; color:#f5f7fa !important; border-radius:7px !important; min-height:2.7rem;}
  [data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder {color:#bac7d7;}
  [data-testid="stSidebar"] [data-testid="stExpander"] {background:#1d3558; border-color:#344d70; border-radius:8px;}
  [data-testid="stSidebar"] [data-testid="stExpander"] summary {color:#f2f5f8; min-height:2.8rem;}
  [data-testid="stSidebar"] [data-testid="stButton"] button {background:#26466f; border:1px solid #42648c; color:#fff; border-radius:7px;}
  [data-testid="stMain"] [data-testid="stTextInput"] input,[data-testid="stMain"] [data-testid="stDateInput"] input,[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"]>div,[data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div,[data-testid="stMain"] textarea {background:#fff !important; border-color:#d7dee7 !important; color:var(--text) !important; border-radius:7px !important; min-height:2.65rem;}
  .page-header {padding:.25rem 0 1.2rem; margin:0 0 1.2rem; border:0; border-bottom:1px solid #dce3eb; border-radius:0; background:transparent; min-height:0;}
  .page-eyebrow {color:var(--teal); font-size:.72rem; font-weight:750; letter-spacing:.13em; text-transform:uppercase; margin-bottom:.45rem;}
  .page-header h1 {color:var(--navy); font-size:clamp(2rem,3vw,2.65rem); margin:.08rem 0 .4rem; letter-spacing:-.045em;}
  .page-subtitle {color:#596d82; font-size:1rem; max-width:950px; line-height:1.6;}
  .section-kicker {display:flex; align-items:center; gap:.6rem; color:#536a80; border-bottom:1px solid #dce3eb; margin:.7rem 0 1rem; padding-bottom:.6rem; font-size:.73rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase;}
  .section-kicker:before {content:""; width:4px; height:18px; background:var(--teal); border-radius:3px;}
  .intro-panel,.tender-card,.investigation-context,.entity-card {background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:9px; box-shadow:0 2px 8px rgba(23,43,77,.035);}
  .intro-panel {border-left:4px solid var(--teal); padding:1rem 1.15rem; margin:.6rem 0 1.35rem; line-height:1.65;}
  .intro-label,.tender-card-label,.entity-label {color:var(--teal) !important;}
  .intro-label {font-size:.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; display:block; margin-bottom:.3rem;}
  .tender-card {border-top:2px solid var(--teal); padding:1.2rem 1.3rem; margin:.55rem 0 .85rem;}
  .tender-card h3,.entity-value {color:#1c3552;}
  .tender-card p {color:#5e7184;}
  .tender-card-label {font-size:.68rem !important; letter-spacing:.09em; text-transform:uppercase; font-weight:700;}
  .entity-card {background:#fff; min-height:6rem; padding:1rem;}
  .entity-label {font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; font-weight:750; color:#60788a; margin-bottom:.4rem;}
  .entity-value {font-size:.9rem; font-weight:650; overflow-wrap:anywhere;}
  .flow-arrow {position:absolute; top:1.35rem; right:-1rem; z-index:2; color:var(--teal); font-size:1.15rem; font-weight:750;}
  .investigation-context {border-left:4px solid var(--teal); padding:1rem 1.15rem; margin:.35rem 0 .8rem; line-height:1.65;}
  .investigation-context strong {color:var(--navy); font-size:1rem;}
  .investigation-context small {color:#596d82; font-size:.8rem;}
  .evidence-chip {display:inline-block; padding:.38rem .66rem; margin:0 .22rem .32rem 0; border-radius:999px; border:1px solid #c8dce5; background:#edf5f8; color:#18526c; font-size:.8rem; font-weight:650;}
  [data-testid="stMetric"] {background:#fff; border:1px solid #dce3eb; border-radius:9px; padding:1.3rem 1.35rem; min-height:128px; box-shadow:0 2px 8px rgba(23,43,77,.035);}
  [data-testid="stMetricLabel"] p {color:#607387; font-size:.82rem; font-weight:650;}
  [data-testid="stMetricValue"] {color:var(--navy); font-size:clamp(1.6rem,2.2vw,2.15rem);}
  [data-testid="stDataFrame"] {border:1px solid #dce3eb; border-radius:9px; background:#fff;}
  [data-testid="stTabs"] [role="tablist"] {gap:.4rem; border-bottom:1px solid #dce3eb;}
  [data-testid="stTabs"] button[role="tab"] {color:#607387; border-radius:6px 6px 0 0;}
  [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {color:var(--teal); border-bottom:2px solid var(--teal);}
  [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] {display:inline-flex; gap:.25rem; padding:.28rem; border:1px solid #dce3eb; border-radius:8px; background:#fff;}
  [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label {padding:.45rem .95rem; border:1px solid transparent; border-radius:6px; color:#536a80;}
  [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {background:#eaf3f6; border-color:#c4dce4; color:#145a73; font-weight:700;}
  [data-testid="stButton"] button,[data-testid="stDownloadButton"] button {background:#fff; border:1px solid #cfd9e3; color:#23455f; border-radius:7px; font-weight:650; min-height:2.55rem;}
  [data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover {border-color:var(--teal); color:#124e67; background:#f3f8fa;}
  [data-testid="stAlert"] {background:#fff; border:1px solid #dce3eb; border-radius:9px; color:var(--text);}
  [data-testid="stCaptionContainer"] {color:#617387;}
  h1,h2,h3,h4 {color:var(--navy); letter-spacing:-.025em;}
  h2 {padding-top:.75rem; margin-bottom:.5rem;}
  [data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:1.15rem;}
  [data-testid="stMain"] [data-testid="stHorizontalBlock"] {gap:1rem;}
  button:focus-visible,a:focus-visible,input:focus-visible,[tabindex]:focus-visible {outline:3px solid var(--teal) !important; outline-offset:2px !important;}
  [data-testid="stSlider"] [data-rac][style*="left:"] {background-color:var(--teal) !important;}
  [data-testid="stSlider"] [data-rac][style*="left:"]::before {background-color:var(--teal) !important;}
  [data-testid="stSliderThumbValue"] {color:var(--teal) !important;}
  /* Shared EvidenceAI dashboard shell */
  [data-testid="stSidebar"] {width:15rem !important; min-width:15rem !important; max-width:15rem !important;}
  [data-testid="stSidebar"] > div {width:15rem !important; min-width:15rem !important;}
  [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"], [data-testid="stSidebar"] button[kind="headerNoPadding"] {display:none !important;}
  [data-testid="collapsedControl"] {display:none !important;}
  [data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding:1.05rem .78rem 1.2rem !important;}
  .brand-panel {padding:.8rem .68rem; margin:.1rem 0 1.05rem; border-radius:10px; background:linear-gradient(135deg,#142746,#1c3a60);}
  .brand-mark {display:flex; align-items:flex-end; justify-content:center; gap:3px; padding:0 8px 8px; background:#eaf4fa; border-radius:8px;}
  .brand-mark span {display:block; width:4px; border-radius:3px 3px 1px 1px; background:#1686c8;}
  .brand-mark span:nth-child(1) {height:10px; opacity:.72;}
  .brand-mark span:nth-child(2) {height:16px; opacity:.88;}
  .brand-mark span:nth-child(3) {height:22px;}
  .brand-mark:after {display:none;}
  .brand-name {font-size:1rem;}
  [data-testid="stSidebar"] [data-testid="stButton"] {margin:.13rem 0;}
  [data-testid="stSidebar"] [data-testid="stButton"] button {justify-content:flex-start; gap:.72rem; padding:.62rem .68rem; min-height:2.75rem; background:transparent; border:1px solid transparent; border-radius:8px; color:#d5dfeb; font-size:.84rem; font-weight:560; text-align:left;}
  [data-testid="stSidebar"] [data-testid="stButton"] button:hover {background:#203c62; border-color:#2c4b73; color:#fff;}
  [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {background:#1769aa; border:1px solid #287dbb; border-left:4px solid #76c5ff; padding-left:calc(.68rem - 3px); color:#fff; font-weight:720; box-shadow:0 3px 9px rgba(5,18,39,.2);}
  [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]:hover {background:#1a74b9;}
  [data-testid="stSidebar"] [data-testid="stButton"] button:focus-visible {outline:2px solid #a6d8ff !important; outline-offset:2px;}
  .sidebar-dataset {position:fixed !important; left:.72rem; bottom:.8rem; z-index:1001; width:calc(15rem - 1.44rem); box-sizing:border-box; margin:0 !important; padding:.72rem .68rem; border:1px solid #344b6b; border-radius:9px; background:#1b3557; box-shadow:0 8px 20px rgba(4,15,32,.18);}
  .sidebar-dataset .dataset-heading {display:flex; align-items:center; gap:.48rem; margin-bottom:.35rem; color:#a9c3dc; font-size:.63rem; font-weight:750; letter-spacing:.11em; text-transform:uppercase;}
  .sidebar-dataset .dataset-count {color:#fff; font-size:.92rem; font-weight:750; letter-spacing:0;}
  .sidebar-dataset .dataset-meta {display:block; margin-top:.28rem; color:#a9b9cc; font-size:.68rem; line-height:1.4; letter-spacing:0; text-transform:none;}
  .sidebar-dataset .dataset-meta strong {color:#e4edf6; font-weight:620;}
  .block-container,[data-testid="stMainBlockContainer"] {max-width:1680px !important; padding:1.05rem clamp(1rem,2vw,2rem) 2.4rem !important;}
  [data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:.78rem;}
  [data-testid="stMain"] [data-testid="stHorizontalBlock"] {gap:.72rem;}
  .page-header {padding:1.05rem 1.25rem 1.1rem; margin:0 0 .7rem; border:1px solid #dce3eb; border-top:3px solid var(--navy); border-radius:10px; background:#fff; box-shadow:0 2px 9px rgba(23,43,77,.045);}
  .page-header h1 {font-size:clamp(1.65rem,2.2vw,2.15rem); margin:.05rem 0 .25rem;}
  .page-subtitle {font-size:.91rem; line-height:1.45;}
  .overview-hero {position:relative; overflow:hidden; min-height:178px; display:flex; align-items:center; padding:1.4rem 1.7rem; margin:.3rem 0 .85rem; border-radius:12px; color:#fff; background:linear-gradient(105deg,rgba(9,34,69,.96),rgba(10,91,143,.83)),linear-gradient(135deg,#17365f,#087da6); box-shadow:0 8px 22px rgba(17,49,85,.16);}
  .overview-hero:before {content:""; position:absolute; inset:0 0 0 42%; opacity:.5; background:linear-gradient(145deg,transparent 48%,rgba(210,232,246,.26) 48.2%,rgba(210,232,246,.12) 65%,transparent 65.2%),linear-gradient(32deg,transparent 53%,rgba(255,255,255,.2) 53.2%,rgba(255,255,255,.08) 71%,transparent 71.2%); clip-path:polygon(0 78%,12% 52%,20% 67%,34% 31%,45% 57%,57% 23%,70% 61%,84% 38%,100% 70%,100% 100%,0 100%);}
  .overview-hero:after {content:""; position:absolute; inset:auto 0 0; height:34%; opacity:.24; background:linear-gradient(165deg,transparent 40%,#dbeaf3 40.5%,#9bb8cc 42%,transparent 43%),linear-gradient(18deg,transparent 51%,#f6fbff 51.5%,#b8cedd 53%,transparent 54%); clip-path:polygon(0 40%,18% 16%,29% 55%,42% 18%,55% 68%,70% 8%,84% 44%,100% 22%,100% 100%,0 100%);}
  .hero-copy {position:relative; z-index:1; max-width:740px;}
  .hero-eyebrow {color:#bfe8f3; font-size:.68rem; font-weight:750; letter-spacing:.16em; text-transform:uppercase;}
  .hero-title {color:#fff !important; font-size:clamp(2rem,3.6vw,3.1rem); letter-spacing:-.045em; line-height:1.03; margin:.25rem 0 .35rem;}
  .hero-subtitle {color:#eef6fb; font-size:1rem; font-weight:650; margin:0 0 .25rem;}
  .hero-note {color:#d6e6f1; font-size:.82rem; margin:0;}
  [class*="st-key-app-topbar"] {padding:.48rem .68rem; margin:0 0 .75rem; border:1px solid #dce3eb; border-radius:10px; background:#fff; box-shadow:0 2px 8px rgba(23,43,77,.04);}
  [class*="st-key-app-topbar"] [data-testid="stHorizontalBlock"] {align-items:center;}
  .topbar-dataset {min-height:2.45rem; display:flex; flex-direction:column; justify-content:center; padding:.2rem .65rem; border-left:1px solid #e5eaf0; line-height:1.25;}
  .topbar-dataset span {font-size:.62rem; color:#6a7b90; font-weight:750; letter-spacing:.1em; text-transform:uppercase;}
  .topbar-dataset strong {font-size:.78rem; color:#172b4d; font-weight:700;}
  .topbar-user {display:flex; align-items:center; justify-content:center; gap:.4rem; min-height:2.45rem; color:#31465f; font-size:.72rem; font-weight:650;}
  .topbar-avatar {display:grid; place-items:center; width:1.8rem; height:1.8rem; border-radius:50%; background:#e7f0f8; color:#155d91; font-size:.7rem; font-weight:800;}
  [class*="st-key-filter-strip"] {padding:.4rem .62rem .15rem; margin:0 0 .5rem; border:1px solid #dce3eb; border-radius:10px; background:#fff;}
  [class*="st-key-filter-strip"] label {font-size:.72rem !important; font-weight:650 !important; color:#3d5067 !important;}
  [data-testid="stMetric"] {padding:.9rem 1rem; min-height:102px; box-shadow:0 2px 8px rgba(23,43,77,.045);}
  [data-testid="stMetricLabel"] p {font-size:.72rem;}
  [data-testid="stMetricValue"] {font-size:clamp(1.25rem,1.8vw,1.75rem);}
  [data-testid="stDataFrame"] {border:1px solid #dce3eb; border-radius:9px; background:#fff;}
  [data-testid="stPlotlyChart"] {border:0; border-radius:8px; background:#fff; padding:.35rem .45rem .1rem;}
  [data-testid="stVerticalBlockBorderWrapper"] {border-color:#dce3eb !important; border-radius:11px !important; background:#fff !important; box-shadow:0 3px 12px rgba(23,43,77,.045);}
  [data-testid="stVerticalBlockBorderWrapper"] > div {border-radius:inherit;}
  [class*="st-key-kpi-tenders"] [data-testid="stMetric"] {background:#e9f8f8; border-color:#c6e9e8; border-top:3px solid #31a4aa;}
  [class*="st-key-kpi-awards"] [data-testid="stMetric"] {background:#fff6df; border-color:#f0dfb1; border-top:3px solid #e1a827;}
  [class*="st-key-kpi-buyers"] [data-testid="stMetric"] {background:#edf3ff; border-color:#d2def6; border-top:3px solid #597fd0;}
  [class*="st-key-kpi-suppliers"] [data-testid="stMetric"] {background:#eef8e9; border-color:#d5e8c7; border-top:3px solid #68a94d;}
  [class*="st-key-kpi-review"] [data-testid="stMetric"] {background:#fff3ed; border-color:#f0d8ca; border-top:3px solid #d76d47;}
  [class*="st-key-kpi-quality"] [data-testid="stMetric"] {background:#f1f4f8; border-color:#dbe2ec; border-top:3px solid #758ba5;}
  [data-testid="stButton"] button,[data-testid="stDownloadButton"] button {min-height:2.35rem; font-size:.8rem;}
  .dashboard-section-title {margin:.35rem 0 .2rem; color:#172b4d; font-size:1.03rem; font-weight:750; letter-spacing:-.02em;}
  .dashboard-section-note {margin:0 0 .45rem; color:#6b7d91; font-size:.74rem;}
  @media (max-width:900px) {.block-container,[data-testid="stMainBlockContainer"] {padding:1.25rem 1.25rem 2.8rem !important;} [data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:.95rem;} .page-header {padding:.9rem 1rem;}}
  @media (max-width:1100px) {[class*="st-key-filter-strip"] [data-testid="stHorizontalBlock"] {flex-wrap:wrap;} [class*="st-key-filter-strip"] [data-testid="column"] {min-width:calc(33.33% - .5rem) !important; flex:1 1 calc(33.33% - .5rem) !important;}}
  @media (max-width:900px) {[data-testid="stMain"] [data-testid="stHorizontalBlock"] {flex-wrap:wrap;} [data-testid="stMain"] [data-testid="stHorizontalBlock"]>[data-testid="column"] {min-width:calc(50% - .5rem) !important; flex:1 1 calc(50% - .5rem) !important;} [class*="st-key-app-topbar"] [data-testid="column"] {min-width:100% !important; flex:1 1 100% !important;} .overview-hero {min-height:150px; padding:1.2rem;}}
  @media (max-width:560px) {.block-container,[data-testid="stMainBlockContainer"] {padding:.8rem .65rem 1.5rem !important;} [data-testid="stMain"] [data-testid="stHorizontalBlock"]>[data-testid="column"] {min-width:100% !important; flex:1 1 100% !important;} [class*="st-key-filter-strip"] [data-testid="column"] {min-width:100% !important; flex:1 1 100% !important;} [data-testid="stMetric"] {padding:.75rem; min-height:88px;} .page-header h1 {font-size:1.65rem;} .overview-hero {min-height:138px;} .hero-title {font-size:2rem;}}
  /* PAIMANA-inspired public dashboard shell, using EvidenceAI's own identity. */
  [data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none !important;}
  .block-container,[data-testid="stMainBlockContainer"] {width:100% !important; max-width:none !important; margin:0 !important; padding:0 2.7rem 2.5rem !important; background:#fff !important;}
  [class*="st-key-app-topbar"] {border:0; border-radius:0; border-bottom:1px solid #e3e8ef; box-shadow:none; margin:0 -2.7rem .1rem; padding:.65rem 2.7rem; background:#fff;}
  .top-brand {display:flex; align-items:center; gap:.65rem; min-height:2.8rem; color:#172b4d;}
  .top-brand-mark {width:2.55rem; height:2.55rem; display:flex; align-items:flex-end; justify-content:center; gap:3px; padding:0 8px 7px; box-sizing:border-box; border-radius:7px; background:#e9f4fb;}
  .top-brand-mark span {display:block; width:4px; border-radius:3px 3px 1px 1px; background:#1686c8;}
  .top-brand-mark span:nth-child(1) {height:10px; opacity:.72;} .top-brand-mark span:nth-child(2) {height:16px; opacity:.88;} .top-brand-mark span:nth-child(3) {height:22px;}
  .top-brand-name {font-size:1.05rem; font-weight:800; letter-spacing:-.025em; line-height:1.15;}
  .top-brand-caption {margin-top:.18rem; color:#687b90; font-size:.68rem;}
  .workflow-ribbon {display:flex; align-items:center; justify-content:space-between; gap:.5rem; margin-top:.65rem; padding:.62rem .8rem; border-radius:6px; background:#f0f6fa; color:#244b6b; font-size:.75rem; font-weight:750;}
  .workflow-ribbon b {color:#159fd0; font-size:1.05rem;}
  .section-heading-row {display:flex; align-items:center; justify-content:space-between; gap:.7rem; margin:.25rem 0 .25rem;}
  .section-heading-row strong {font-size:1.05rem; color:#172b4d;}
  .section-heading-row span {padding:.25rem .5rem; border-radius:999px; background:#fff4db; color:#8a5a00; font-size:.67rem; font-weight:700;}
  .topbar-dataset {border:0; padding-left:.4rem;}
  [class*="st-key-module-nav"] {margin:0 -2.7rem .75rem; padding:.22rem 2.7rem; background:#159fd0; border-bottom:3px solid #087eaf;}
  [class*="st-key-module-nav"] [data-testid="stHorizontalBlock"] {gap:.2rem; align-items:center;}
  [class*="st-key-module-nav"] [data-testid="stButton"] button {min-height:2.65rem; border:0; border-radius:5px; background:transparent; color:#fff; font-size:.82rem; font-weight:700; box-shadow:none;}
  [class*="st-key-module-nav"] [data-testid="stButton"] button:hover {background:#087eaf; color:#fff;}
  [class*="st-key-module-nav"] [data-testid="stButton"] button[kind="primary"] {background:#fff; color:#123e68; box-shadow:0 2px 5px rgba(8,65,107,.18);}
  .page-header {padding:.6rem 0 .8rem; margin:0 0 .6rem; border:0; border-radius:0; background:transparent; box-shadow:none;}
  .page-header h1 {font-size:clamp(1.55rem,2.4vw,2rem); margin:.05rem 0 .1rem;}
  .page-subtitle {display:none;}
  .page-eyebrow {font-size:.66rem; margin-bottom:.18rem;}
  .overview-hero {min-height:235px; margin:.25rem 0 .8rem; border-radius:2px; background:linear-gradient(90deg,rgba(8,32,62,.88),rgba(9,83,128,.44)),linear-gradient(135deg,#0b2c50,#1ca8c6 60%,#e1b54a);}
  .hero-title {font-size:clamp(2.4rem,4vw,3.7rem); letter-spacing:-.035em;}
  .hero-subtitle {font-size:1.12rem;}
  [class*="st-key-filter-strip"] {padding:.75rem .8rem .2rem; border-radius:8px; border-top:3px solid #159fd0; box-shadow:0 3px 12px rgba(28,55,89,.06);}
  [data-testid="stMetric"] {min-height:116px; padding:1rem 1.1rem; border-radius:7px; box-shadow:0 3px 12px rgba(28,55,89,.055);}
  [data-testid="stVerticalBlockBorderWrapper"] {border-radius:8px !important; box-shadow:0 3px 14px rgba(28,55,89,.06);}
  [data-testid="stDataFrame"] {border-radius:7px;}
  [data-testid="stPlotlyChart"] {padding:.15rem .25rem;}
  [data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:.9rem;}
  [data-testid="stMain"] [data-testid="stHorizontalBlock"] {gap:.85rem;}
  @media (max-width:900px) {.block-container,[data-testid="stMainBlockContainer"] {padding:0 1.25rem 2.5rem !important;} [class*="st-key-app-topbar"] {margin-left:-1.25rem; margin-right:-1.25rem; padding-left:1.25rem; padding-right:1.25rem;} [class*="st-key-module-nav"] {margin-left:-1.25rem; margin-right:-1.25rem; padding-left:1.25rem; padding-right:1.25rem;} [class*="st-key-app-topbar"] [data-testid="column"] {min-width:50% !important; flex:1 1 50% !important;} [class*="st-key-module-nav"] [data-testid="stHorizontalBlock"] {flex-wrap:wrap;} [class*="st-key-module-nav"] [data-testid="column"] {min-width:31% !important; flex:1 1 31% !important;} .overview-hero {min-height:185px;}}
  @media (max-width:560px) {.block-container,[data-testid="stMainBlockContainer"] {padding:0 .65rem 2.5rem !important;} [class*="st-key-app-topbar"] {margin-left:-.65rem; margin-right:-.65rem; padding-left:.65rem; padding-right:.65rem;} [class*="st-key-module-nav"] {margin-left:-.65rem; margin-right:-.65rem; padding-left:.65rem; padding-right:.65rem; overflow:hidden;} [class*="st-key-app-topbar"] [data-testid="column"] {min-width:100% !important; flex:1 1 100% !important;} [class*="st-key-module-nav"] [data-testid="column"] {min-width:48% !important; flex:1 1 48% !important;} .overview-hero {min-height:160px; padding:1rem;} .hero-title {font-size:2.1rem;}}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Reading local procurement files…")
def get_data():
    tables = load_dataset()
    return tables, tender_records(tables), audit_dataset(tables)


@st.cache_data(show_spinner=False)
def score_records(frame: pd.DataFrame, contamination: float = 0.05, fit_model: bool = True) -> pd.DataFrame:
    """Cache review indicators for the same filtered tender selection."""
    return investigation_flags(frame, contamination=contamination, fit_model=fit_model)


def fmt_count(value: int) -> str:
    return f"{value:,}"


def buyer_display(values: pd.Series) -> pd.Series:
    """Use the primary recorded buyer name for compact table labels."""
    return values.fillna("Not recorded").astype(str).str.split("||", regex=False).str[0].str.strip()


def clean_text(value, fallback: str = "Not recorded") -> str:
    """Return a readable string for missing or whitespace-only source values."""
    if pd.isna(value) or not str(value).strip():
        return fallback
    return str(value).strip()


def award_value_summary(frame: pd.DataFrame) -> str:
    """Summarize award values by currency without combining currencies."""
    if frame.empty or "value_currency" not in frame:
        return "No linked award values recorded"
    amount_col = "value_amount" if "value_amount" in frame else "total"
    totals = frame.assign(_amount=pd.to_numeric(frame[amount_col], errors="coerce")).dropna(subset=["_amount"])
    if totals.empty:
        return "No linked award values recorded"
    return " · ".join(
        f"{clean_text(currency, 'Currency not recorded')}: {amount:,.0f}"
        for currency, amount in totals.groupby("value_currency", dropna=False)["_amount"].sum().items()
    )


def readable_field(value: str) -> str:
    """Turn an underscore-delimited source field into a readable label."""
    return " ".join(part.capitalize() for part in str(value).replace("_", " ").split())


def style_chart(fig):
    """Apply a consistent chart style that follows the active Streamlit theme."""
    dark = st.get_option("theme.base") == "dark"
    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white",
        colorway=["#2186c7", "#12a78a", "#7259d7", "#f29b38", "#d95252", "#526b8a"],
        font={"family": "Inter, Segoe UI, sans-serif", "size": 13, "color": "#344b62"},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 16, "r": 18, "t": 28, "b": 18},
        height=310,
        hoverlabel={"bgcolor": "#0f172a", "font_color": "#f8fafc"},
    )
    fig.update_xaxes(showline=False, zeroline=False, gridcolor="rgba(128,145,165,.18)")
    fig.update_yaxes(showline=False, zeroline=False, gridcolor="rgba(128,145,165,.18)")
    return fig


def quality_gauge(value: float, title: str, color: str):
    """Render a compact scan indicator using a rate calculated from the CSV audit."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=float(value), number={"suffix": "%", "font": {"size": 25, "color": "#172b4d"}},
        title={"text": title, "font": {"size": 12, "color": "#617387"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)"},
            "bar": {"color": color, "thickness": .28}, "bgcolor": "white", "borderwidth": 0,
            "steps": [{"range": [0, 100], "color": "#edf1f6"}],
        },
    ))
    fig.update_layout(height=180, margin={"l": 15, "r": 15, "t": 42, "b": 8}, paper_bgcolor="rgba(0,0,0,0)")
    return fig


def publication_activity_chart(frame: pd.DataFrame):
    """Build an entity-specific publication chart from recorded tender dates."""
    dates = frame["published_date_parsed"].dropna()
    if dates.empty:
        return None
    yearly = dates.dt.year.value_counts().sort_index().rename_axis("Publication year").reset_index(name="Tender records")
    fig = px.bar(yearly, x="Publication year", y="Tender records", text="Tender records")
    fig.update_traces(marker_color="#2186c7", textposition="outside", hovertemplate="%{x}: %{y:,} tenders<extra></extra>")
    fig.update_layout(yaxis_title="Tender records")
    return style_chart(fig)


def reset_filters(start_date, end_date) -> None:
    st.session_state["publication_range"] = (start_date, end_date)
    st.session_state["buyer_filter"] = []
    st.session_state["method_filter"] = []
    st.session_state["supplier_filter"] = []
    st.session_state["record_search"] = ""
    st.session_state["explore_search"] = ""
    st.session_state["explore_buyer"] = "All buyers"
    st.session_state["explore_method"] = "All methods"
    for key in list(st.session_state):
        if key.startswith("explore_estimate_"):
            del st.session_state[key]


def remember_active_tender(widget_key: str) -> None:
    st.session_state["active_tender_id"] = str(st.session_state[widget_key])


def navigate_investigation(destination: str, tender_id: str | None = None, clear_filters: bool = False, date_bounds=None) -> None:
    if tender_id is not None:
        st.session_state["active_tender_id"] = str(tender_id)
    if clear_filters and date_bounds:
        reset_filters(*date_bounds)
    if destination == "Explore records":
        st.session_state["explore_search"] = ""
        st.session_state["explore_buyer"] = "All buyers"
        st.session_state["explore_method"] = "All methods"
    st.session_state["workspace_page"] = destination


def set_workspace_page(destination: str) -> None:
    """Switch the shared workspace module without changing the current filters."""
    st.session_state["workspace_page"] = destination


def shared_tender_selectbox(label: str, options: list[str], key: str, format_func=None):
    """Select a tender while keeping its ID shared across investigation pages."""
    if not options:
        return None
    active = str(st.session_state.get("active_tender_id", ""))
    existing = str(st.session_state.get(key, ""))
    if active in options:
        st.session_state[key] = active
    elif existing not in options:
        st.session_state[key] = options[0]
    widget_args = {"key": key, "on_change": remember_active_tender, "args": (key,)}
    if format_func is not None:
        widget_args["format_func"] = format_func
    return st.selectbox(label, options, **widget_args)


try:
    tables, records, audit = get_data()
except Exception as exc:
    st.error(f"Could not load the local dataset: {exc}")
    st.info("Check that all eight CSV files are present in data/raw, then restart the app.")
    st.stop()

st.session_state.setdefault("workspace_page", "Overview")
st.session_state.setdefault("active_tender_id", "")
page = st.session_state["workspace_page"]
module_items = [
    ("Overview", "Overview", "dashboard"),
    ("Explore records", "Explore records", "search"),
    ("Anomaly review", "Anomaly review", "warning"),
    ("Buyer & supplier search", "Buyer & supplier search", "domain"),
    ("Relationships", "Relationships", "hub"),
    ("Data quality", "Data quality & reports", "fact_check"),
]

page_guidance = {
    "Overview": ("Procurement Dashboard", "Start here for the dataset summary. Charts and counts update when you change the filters."),
    "Explore records": ("Explore records", "Search and inspect tender rows. Download the currently filtered tenders as a CSV."),
    "Anomaly review": ("Anomaly review", "Review unusual records and verify each one against its source context."),
    "Buyer & supplier search": ("Buyer & supplier search", "Compare activity for recorded buyer IDs and supplier names, then inspect linked tenders."),
    "Relationships": ("Relationships", "Choose a tender to inspect its linked awards, suppliers, parties, items, and document descriptions."),
    "Data quality & reports": ("Data quality", "Check source-file completeness and link matching, then download a summary or filtered records."),
}
page_title, page_description = page_guidance[page]
with st.container(key="app-topbar"):
    top_brand, top_search, top_dataset, top_export, top_reports, top_user = st.columns([1.8, 3.7, 2.2, .85, .85, .85], gap="small", vertical_alignment="center")
    top_brand.markdown('<div class="top-brand"><div class="top-brand-mark"><span></span><span></span><span></span></div><div><div class="top-brand-name">EvidenceAI</div><div class="top-brand-caption">Procurement intelligence</div></div></div>', unsafe_allow_html=True)
    search = top_search.text_input("", key="record_search", placeholder="Search tenders, buyers, suppliers, or keywords…", label_visibility="collapsed")
    top_dataset.markdown('<div class="topbar-dataset"><span>Dataset</span><strong>Himachal Pradesh Procurement</strong></div>', unsafe_allow_html=True)
    export_placeholder = top_export.empty()
    top_reports.button("Reports", key="topbar_reports", on_click=navigate_investigation, args=("Data quality & reports", None, False, None), width="stretch")
    top_user.markdown('<div class="topbar-user"><span class="topbar-avatar">EA</span><span>Analyst</span></div>', unsafe_allow_html=True)

with st.container(key="module-nav"):
    nav_columns = st.columns([1, 1.2, 1.2, 1.65, 1.1, 1.45], gap="small")
    for nav_column, (nav_label, destination, nav_icon) in zip(nav_columns, module_items):
        nav_column.button(
            nav_label, key=f"top_nav_{nav_icon}",
            type="primary" if page == destination else "secondary",
            on_click=set_workspace_page, args=(destination,), width="stretch",
        )

if page == "Overview":
    st.markdown(
        '<div class="page-header"><div class="page-eyebrow">Himachal Pradesh · Public Procurement</div>'
        '<h1>Procurement Dashboard</h1></div>', unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="page-header"><div class="page-eyebrow">Himachal Pradesh · Public Procurement</div>'
        f'<h1>{page_title}</h1></div>',
        unsafe_allow_html=True,
    )

# Common filters stay in the analytical workspace so they are visible and
# persistent while the user moves between modules. Date filtering uses tender
# publication dates; the compiled `date` field is an extraction timestamp.
date_series = records["published_date_parsed"].dropna()
if not date_series.empty:
    start, end = date_series.min().date(), date_series.max().date()
    if "publication_range" not in st.session_state:
        st.session_state["publication_range"] = (start, end)
else:
    start, end = None, None

buyers = sorted(records["buyer_name"].dropna().astype(str).unique())
methods = sorted(records["tender_procurementMethod"].dropna().astype(str).unique())
supplier_options = sorted({
    name.strip()
    for group in records["supplier_names"].dropna().astype(str)
    for name in group.split("; ")
    if name.strip()
}, key=str.casefold)

with st.container(key="filter-strip", border=True):
    filter_cols = st.columns([1.25, 1.15, 1.05, 1.1, .72], gap="small", vertical_alignment="bottom")
    if start is not None and end is not None:
        selected_range = filter_cols[0].date_input("Publication date", min_value=start, max_value=end, key="publication_range")
    else:
        selected_range = ()
        filter_cols[0].caption("Publication date not recorded")
    buyer_filter = filter_cols[1].multiselect("Buyer / department", buyers, key="buyer_filter", placeholder="All buyers")
    method_filter = filter_cols[2].multiselect("Procurement method", methods, key="method_filter", placeholder="All methods")
    supplier_filter = filter_cols[3].multiselect("Supplier", supplier_options, key="supplier_filter", placeholder="All suppliers")
    if start is not None and end is not None:
        filter_cols[4].button("Reset filters", key="reset_shared_filters", on_click=reset_filters, args=(start, end), width="stretch")

filtered = records.copy()
if len(selected_range) == 2:
    # Compare calendar dates so records published late on the selected end date
    # are not accidentally excluded by a midnight timestamp cutoff.
    filtered = filtered[filtered.published_date_parsed.dt.date.between(selected_range[0], selected_range[1])]
if buyer_filter:
    filtered = filtered[filtered.buyer_name.isin(buyer_filter)]
if method_filter:
    filtered = filtered[filtered.tender_procurementMethod.isin(method_filter)]
if supplier_filter:
    supplier_keys = {name.casefold() for name in supplier_filter}
    filtered = filtered[filtered.supplier_names.fillna("").astype(str).apply(
        lambda value: bool(supplier_keys.intersection(name.strip().casefold() for name in value.split("; ")))
    )]
if search.strip():
    term = search.strip().casefold()
    mask = filtered[["id", "ocid", "tender_id", "tender_title", "buyer_name", "supplier_names"]].fillna("").astype(str).apply(
        lambda col: col.str.casefold().str.contains(term, regex=False)
    ).any(axis=1)
    filtered = filtered[mask]

active_filter_labels = []
if search.strip():
    active_filter_labels.append(f"Search: {search.strip()}")
if len(selected_range) == 2 and start is not None and end is not None and tuple(selected_range) != (start, end):
    active_filter_labels.append(f"Dates: {selected_range[0]:%d %b %Y}–{selected_range[1]:%d %b %Y}")
if buyer_filter:
    active_filter_labels.append(f"{len(buyer_filter)} buyer(s)")
if method_filter:
    active_filter_labels.append(f"{len(method_filter)} method(s)")
if supplier_filter:
    active_filter_labels.append(f"{len(supplier_filter)} supplier(s)")
view_status, filter_status = st.columns([1.15, 4.2], gap="small", vertical_alignment="center")
view_status.markdown(f'<div class="dashboard-section-title">{len(filtered):,} tenders in view</div>', unsafe_allow_html=True)
filter_status.caption("Applied: " + (" · ".join(active_filter_labels) if active_filter_labels else "All procurement records"))
export_columns = [
    "tender_id", "ocid", "tender_title", "buyer_name", "tender_procurementMethod",
    "tender_datePublished", "tender_value_amount", "tender_value_currency",
    "tender_numberOfTenderers", "award_count", "supplier_names",
]
export_columns = [column for column in export_columns if column in filtered.columns]
export_placeholder.download_button(
    "Export", filtered[export_columns].to_csv(index=False).encode("utf-8-sig"),
    "evidenceai_filtered_tenders.csv", "text/csv", width="stretch", disabled=filtered.empty,
    help="Download the currently filtered tender records as a CSV.",
)

active_tender_id = str(st.session_state.get("active_tender_id", ""))
active_tender = None
active_matches = records[records.tender_id.astype(str).eq(active_tender_id)] if active_tender_id else records.iloc[0:0]
if not active_matches.empty:
    active_tender = active_matches.iloc[0]
    active_in_filter = filtered.tender_id.astype(str).eq(active_tender_id).any()
    active_buyer = buyer_display(pd.Series([active_tender.buyer_name])).iloc[0]
    active_data_note = "" if pd.notna(active_tender.tender_value_amount) and pd.notna(active_tender.tender_value_currency) else " · Data note: estimate/currency incomplete"
    with st.container():
        st.markdown(
            f'<div class="investigation-context"><small>ACTIVE INVESTIGATION · {escape(active_tender_id)}</small><br>'
            f'<strong>{escape(clean_text(active_tender.tender_title, "Untitled tender"))}</strong><br>'
            f'<small>Buyer: {escape(active_buyer)} · Supplier names: {escape(clean_text(active_tender.supplier_names, "No linked supplier recorded"))}{escape(active_data_note)}</small></div>',
            unsafe_allow_html=True,
        )
        if not active_in_filter:
            st.caption("This tender is outside the current filter set. Continuing to it will clear the current search and filters.")
        nav1, nav2, nav3, nav4, nav5 = st.columns(5, gap="small")
        date_bounds = (start, end) if start is not None and end is not None else None
        nav1.button("Open in Explore", key="context_open_explore", width="stretch", on_click=navigate_investigation, args=("Explore records", active_tender_id, not active_in_filter, date_bounds))
        nav2.button("Trace relationships", key="context_open_relationships", width="stretch", on_click=navigate_investigation, args=("Relationships", active_tender_id, not active_in_filter, date_bounds))
        nav3.button("Buyer & supplier", key="context_open_entities", width="stretch", on_click=navigate_investigation, args=("Buyer & supplier search", active_tender_id, not active_in_filter, date_bounds))
        nav4.button("Review signals", key="context_open_anomaly", width="stretch", on_click=navigate_investigation, args=("Anomaly review", active_tender_id, not active_in_filter, date_bounds))
        nav5.button("Data quality", key="context_open_quality", width="stretch", on_click=navigate_investigation, args=("Data quality & reports", active_tender_id, not active_in_filter, date_bounds))

if page == "Overview":
    st.markdown('<div class="section-heading-row"><strong>Procurement at a glance</strong><span>Review leads ≠ findings</span></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1.container(key="kpi-tenders"):
        st.metric("Total tenders", fmt_count(len(filtered)))
    overview_awards = tables["awards"][tables["awards"]["_link_main"].isin(set(filtered["_link"]))]
    overview_inr = overview_awards.value_currency.fillna("").astype(str).str.upper().eq("INR")
    inr_awards = pd.to_numeric(overview_awards.loc[overview_inr, "value_amount"], errors="coerce").sum()
    with c2.container(key="kpi-awards"):
        st.metric("Award value · INR", f"₹{inr_awards / 10_000_000:,.0f} Cr", help=f"Recorded INR award rows only: ₹{inr_awards:,.0f}. Values in other currencies are excluded, never converted or combined.")
    names = tables["awards_suppliers"][["_link_awards", "name"]].merge(tables["awards"][["_link", "_link_main"]], left_on="_link_awards", right_on="_link", how="inner")
    names = names[names["_link_main"].isin(set(filtered["_link"]))]["name"].dropna().astype(str).str.strip().str.casefold()
    with c3.container(key="kpi-buyers"):
        st.metric("Unique buyers", fmt_count(filtered["buyer_id"].dropna().astype(str).nunique()), help="Distinct buyer IDs recorded in the current filtered tender set.")
    with c4.container(key="kpi-suppliers"):
        st.metric("Unique suppliers", fmt_count(names.nunique()), help="Distinct supplier name strings after case/whitespace normalization; legal identities are not verified.")
    overview_flags = score_records(filtered, contamination=0.05, fit_model=True)
    review_leads = int(overview_flags.investigation_score.gt(0).sum()) if not overview_flags.empty else 0
    critical_missing = filtered[["tender_value_amount", "tender_value_currency", "tender_numberOfTenderers"]].isna().any(axis=1) | filtered["award_count"].eq(0)

    overview_flagged = overview_flags[overview_flags.investigation_score.gt(0)].sort_values(
        ["investigation_score", "tender_id"], ascending=[False, True]
    )
    with st.container(border=True):
        st.markdown("#### Start an investigation")
        st.caption("Choose a review lead to carry its tender across modules.")
        if overview_flagged.empty:
            st.info("No review leads match the current filters. Explore the tender records or adjust the filters to continue.")
            st.button("Browse tender records", key="guided_browse_records", on_click=navigate_investigation, args=("Explore records", None, False, None))
        else:
            lead_options = overview_flagged.head(100).tender_id.astype(str).tolist()
            lead_labels = overview_flagged.set_index(overview_flagged.tender_id.astype(str)).apply(
                lambda row: f"{row['tender_id']} · Priority {int(row['investigation_score'])} · {clean_text(row['tender_title'], 'Untitled tender')}",
                axis=1,
            ).to_dict()
            start_col, action_col = st.columns([4, 1], gap="small", vertical_alignment="bottom")
            chosen_lead = start_col.selectbox(
                "Review lead", lead_options, key="overview_start_tender",
                format_func=lambda tender_id: lead_labels.get(str(tender_id), str(tender_id)),
            )
            action_col.button(
                "Begin review", key="guided_begin_review", type="primary", width="stretch",
                on_click=navigate_investigation, args=("Anomaly review", chosen_lead, False, None),
            )
        st.markdown('<div class="workflow-ribbon"><span>01&nbsp; Find</span><b>›</b><span>02&nbsp; Review</span><b>›</b><span>03&nbsp; Trace</span><b>›</b><span>04&nbsp; Report</span></div>', unsafe_allow_html=True)

    st.subheader("Procurement analytics")
    st.caption("Explore the filtered records as charts or exact figures. The same date, buyer, supplier, method, and search filters apply to both views.")
    buyer_counts = filtered.groupby("buyer_id", dropna=False).size().sort_values(ascending=False).head(8).rename("Tender records").reset_index()
    buyer_modes = filtered.groupby("buyer_id", dropna=False)["buyer_name"].agg(lambda values: values.mode().iloc[0] if not values.mode().empty else "Not recorded")
    buyer_counts["Buyer"] = buyer_counts["buyer_id"].map(buyer_modes).fillna("Not recorded").astype(str).str.split("||", regex=False).str[0].str.slice(0, 40) + " · " + buyer_counts["buyer_id"].fillna("unknown").astype(str)
    yearly = filtered.assign(year=filtered.published_date_parsed.dt.year).dropna(subset=["year"]).groupby("year").size().rename("Tender records").reset_index()
    counts = filtered.tender_procurementMethod.fillna("Not recorded").value_counts().rename_axis("Method").reset_index(name="Records")
    bidder_counts = pd.to_numeric(filtered.tender_numberOfTenderers, errors="coerce").dropna()
    award_currency = overview_awards.copy()
    award_currency["Award value"] = pd.to_numeric(award_currency["value_amount"], errors="coerce")
    award_currency["Currency"] = award_currency["value_currency"].fillna("Currency not recorded").astype(str).str.upper()
    award_currency = award_currency.dropna(subset=["Award value"]).groupby("Currency", as_index=False)["Award value"].sum().sort_values("Award value", ascending=False)
    supplier_rows_for_chart = tables["awards_suppliers"][["_link_awards", "name"]].merge(
        tables["awards"][["_link", "_link_main"]], left_on="_link_awards", right_on="_link", how="inner"
    )
    supplier_rows_for_chart = supplier_rows_for_chart[supplier_rows_for_chart["_link_main"].isin(set(filtered["_link"]))].copy()
    supplier_rows_for_chart["name"] = supplier_rows_for_chart.name.fillna("").astype(str).str.strip()
    supplier_distribution = supplier_rows_for_chart[supplier_rows_for_chart.name.ne("")].groupby("name")["_link_main"].nunique().sort_values(ascending=False).head(10).rename("Linked tenders").reset_index()
    chart_mode = st.radio("Display", ["Charts", "Data"], horizontal=True, key="overview_display_mode", label_visibility="collapsed")
    award_dated = overview_awards.merge(
        filtered[["_link", "award_date_parsed"]].drop_duplicates("_link"),
        left_on="_link_main", right_on="_link", how="left",
    )
    award_dated["Award value"] = pd.to_numeric(award_dated["value_amount"], errors="coerce")
    award_dated["Award year"] = award_dated.award_date_parsed.dt.year
    award_trend = award_dated[
        award_dated.value_currency.fillna("").astype(str).str.upper().eq("INR")
        & award_dated["Award value"].notna()
        & award_dated["Award year"].notna()
    ].groupby("Award year", as_index=False)["Award value"].sum()
    buyer_award_rows = overview_awards.merge(
        filtered[["_link", "buyer_name"]].drop_duplicates("_link"),
        left_on="_link_main", right_on="_link", how="left",
    )
    buyer_award_rows["Award value"] = pd.to_numeric(buyer_award_rows["value_amount"], errors="coerce")
    buyer_award_rows = buyer_award_rows[
        buyer_award_rows["value_currency"].fillna("").astype(str).str.upper().eq("INR")
        & buyer_award_rows["Award value"].notna()
    ].copy()
    buyer_award_rows["Buyer"] = buyer_display(buyer_award_rows["buyer_name"])
    buyer_award_values = buyer_award_rows.groupby("Buyer", as_index=False)["Award value"].sum().nlargest(8, "Award value")
    if not yearly.empty:
        dates = filtered.published_date_parsed.dropna()
        date_min = dates.min().strftime("%d %b %Y")
        date_max = dates.max().strftime("%d %b %Y")
        busiest = yearly.loc[yearly["Tender records"].idxmax()]
        st.caption(f"Publication period: {date_min} – {date_max} · busiest year {int(busiest['year'])} ({int(busiest['Tender records']):,} tenders).")
    else:
        st.caption("No publication dates are recorded for the current selection.")
    if chart_mode == "Charts":
        trend_col, buyer_award_col = st.columns(2, gap="medium")
        with trend_col.container(border=True):
            st.markdown("#### Tender publication activity")
            if not yearly.empty:
                trend = px.bar(yearly, x="year", y="Tender records", text="Tender records")
                trend.update_traces(marker_color="#2186c7", textposition="outside", hovertemplate="Year %{x}: %{y:,} tenders<extra></extra>")
                trend.update_layout(xaxis_title="Publication year", yaxis_title="Tender records")
                st.plotly_chart(style_chart(trend), width="stretch")
            else:
                st.info("No publication-year data in this selection.")
        with buyer_award_col.container(border=True):
            st.markdown("#### Award value by buyer · INR")
            st.caption("Linked recorded INR awards only; other currencies are not converted.")
            if not buyer_award_values.empty:
                buyer_chart = px.bar(buyer_award_values.sort_values("Award value"), x="Award value", y="Buyer", orientation="h", labels={"Award value": "Recorded award total (INR)"})
                buyer_chart.update_traces(marker_color="#2186c7", hovertemplate="%{y}<br>₹%{x:,.0f}<extra></extra>")
                st.plotly_chart(style_chart(buyer_chart), width="stretch")
            else:
                st.info("No linked INR award values are recorded for these buyers.")
        methods_tab, buyers_tab, suppliers_tab, bidders_tab, awards_tab = st.tabs(["Methods", "Buyers", "Suppliers", "Tenderers", "Award values"])
        with methods_tab:
            if not counts.empty:
                method_chart = px.bar(counts, x="Records", y="Method", orientation="h", text="Records")
                method_chart.update_traces(marker_color="#176B87", textposition="outside", cliponaxis=False)
                st.plotly_chart(style_chart(method_chart), width="stretch")
            else:
                st.info("No tenders in this selection.")
        with buyers_tab:
            if not buyer_counts.empty:
                st.plotly_chart(style_chart(px.bar(buyer_counts, x="Tender records", y="Buyer", orientation="h", color_discrete_sequence=["#176B87"])), width="stretch")
            else:
                st.info("No buyer records in this selection.")
        with suppliers_tab:
            st.caption("Counts are linked tender records per recorded supplier name. Similar names are not merged into legal entities.")
            if not supplier_distribution.empty:
                supplier_chart = px.bar(supplier_distribution, x="Linked tenders", y="name", orientation="h", labels={"name": "Supplier name as recorded"}, color_discrete_sequence=["#176B87"])
                supplier_chart.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(style_chart(supplier_chart), width="stretch")
            else:
                st.info("No supplier names are linked to tenders in this selection.")
        with bidders_tab:
            if not bidder_counts.empty:
                st.plotly_chart(style_chart(px.histogram(x=bidder_counts, nbins=20, labels={"x": "Number of tenderers", "count": "Tender records"}, color_discrete_sequence=["#176B87"])), width="stretch")
            else:
                st.info("Tenderer count is not available in this selection.")
        with awards_tab:
            st.caption("Award amounts remain grouped by recorded currency; currencies are not added together or converted.")
            if not award_currency.empty:
                award_chart = px.bar(award_currency, x="Currency", y="Award value", color="Currency", labels={"Award value": "Total recorded award value"})
                st.plotly_chart(style_chart(award_chart), width="stretch")
            else:
                st.info("No linked award amounts are recorded for this selection.")
            inr_values = pd.to_numeric(overview_awards.loc[overview_inr, "value_amount"], errors="coerce").dropna()
            inr_values = inr_values[inr_values.gt(0)]
            if not inr_values.empty:
                st.caption("INR award distribution · logarithmic scale. A long tail is visible without hiding common values.")
                award_dist = px.histogram(x=inr_values, nbins=30, log_x=True, labels={"x": "Award value (INR)", "count": "Award records"}, color_discrete_sequence=["#176B87"])
                st.plotly_chart(style_chart(award_dist), width="stretch")
    else:
        st.markdown("#### Tender activity by year")
        if not yearly.empty:
            st.dataframe(yearly.rename(columns={"year": "Publication year"}), width="stretch", hide_index=True)
        else:
            st.info("No publication-year data in this selection.")
        data_left, data_right = st.columns(2)
        with data_left:
            st.markdown("#### Procurement methods")
            st.dataframe(counts.rename(columns={"Records": "Tender records"}), width="stretch", hide_index=True)
            st.markdown("#### Buyers with most tenders")
            st.dataframe(buyer_counts[["Buyer", "Tender records"]], width="stretch", hide_index=True)
            st.markdown("#### Supplier names with most linked tenders")
            st.dataframe(supplier_distribution.rename(columns={"name": "Supplier name as recorded"}), width="stretch", hide_index=True)
        with data_right:
            st.markdown("#### Award totals by currency")
            st.dataframe(award_currency, width="stretch", hide_index=True, column_config={"Award value": st.column_config.NumberColumn("Award value", format="%,.2f")})
            st.markdown("#### Recorded tenderer counts")
            if not bidder_counts.empty:
                bidder_table = bidder_counts.value_counts().sort_index().rename_axis("Tenderers recorded").reset_index(name="Tender records")
                st.dataframe(bidder_table, width="stretch", hide_index=True)
            else:
                st.info("Tenderer count is not available in this selection.")
        st.markdown("#### Award value trend · INR")
        if not award_trend.empty:
            st.dataframe(award_trend, width="stretch", hide_index=True, column_config={"Award value": st.column_config.NumberColumn("Award value (INR)", format="₹%,.2f")})
        else:
            st.info("No dated INR award values are available for this selection.")

    st.markdown('<div class="dashboard-section-title">Recent records and investigation cues</div><div class="dashboard-section-note">Open a record to continue the same investigation across modules.</div>', unsafe_allow_html=True)
    recent_col, review_col, insights_col = st.columns([1.25, 1.25, .9], gap="small")
    with recent_col.container(border=True):
        st.markdown("#### Recently published tenders")
        recent = filtered.sort_values("published_date_parsed", ascending=False, na_position="last").head(6)
        recent_view = recent[["tender_id", "tender_title", "buyer_name", "tender_datePublished", "tender_procurementMethod"]].copy()
        recent_view["buyer_name"] = buyer_display(recent_view["buyer_name"])
        recent_view["tender_datePublished"] = pd.to_datetime(recent_view["tender_datePublished"], errors="coerce", utc=True).dt.strftime("%d %b %Y")
        st.dataframe(recent_view.rename(columns={
            "tender_id": "Tender ID", "tender_title": "Title", "buyer_name": "Buyer",
            "tender_datePublished": "Published", "tender_procurementMethod": "Method",
        }), width="stretch", height=290, hide_index=True)
        st.button("View all records", key="overview_to_explore", on_click=navigate_investigation, args=("Explore records", None, False, None), width="stretch")
    with review_col.container(border=True):
        st.markdown("#### High-priority review leads")
        overview_flagged_preview = overview_flagged.head(6)
        if overview_flagged_preview.empty:
            st.info("No records in this filtered selection received a review signal.")
        else:
            review_view = overview_flagged_preview[["tender_id", "tender_title", "investigation_score", "flag_single_tenderer", "flag_high_inr_amount", "flag_zero_or_negative_amount"]].copy()
            review_view["Indicators"] = review_view.apply(lambda row: ", ".join(label for key, label in [
                ("flag_single_tenderer", "Single tenderer"),
                ("flag_high_inr_amount", "High INR estimate"),
                ("flag_zero_or_negative_amount", "Non-positive estimate"),
            ] if bool(row[key])), axis=1)
            st.dataframe(review_view[["tender_id", "tender_title", "investigation_score", "Indicators"]].rename(columns={
                "tender_id": "Tender ID", "tender_title": "Title", "investigation_score": "Priority",
            }), width="stretch", height=290, hide_index=True)
        st.button("Open review queue", key="overview_to_anomaly", on_click=navigate_investigation, args=("Anomaly review", None, False, None), width="stretch")
    with insights_col.container(border=True):
        st.markdown("#### Key insights")
        if not filtered.empty:
            top_buyer = buyer_counts.iloc[0]["Buyer"] if not buyer_counts.empty else "Not recorded"
            newest = filtered.published_date_parsed.max()
            st.markdown(f"**{review_leads:,}** records have at least one transparent review indicator.")
            st.markdown(f"**{critical_missing.sum():,}** records have one or more selected data gaps.")
            st.markdown(f"Most active buyer: **{escape(str(top_buyer))}**.")
            st.markdown(f"Newest publication: **{newest:%d %b %Y}**." if pd.notna(newest) else "Publication date is not recorded.")
        else:
            st.info("No records match the current filters.")
        st.caption("Insights update with the current search and filters. Review leads are not findings.")

elif page == "Explore records":
    st.markdown("#### Find a tender")
    search_col, buyer_col, method_col = st.columns([1.5, 1, 1], gap="small")
    explore_term = search_col.text_input("Search this list", key="explore_search", placeholder="Title, tender ID, buyer, supplier")
    buyer_options = ["All buyers"] + sorted(buyer_display(filtered.buyer_name).dropna().unique().tolist())
    explore_buyer = buyer_col.selectbox("Buyer", buyer_options, key="explore_buyer")
    method_options = ["All methods"] + sorted(filtered.tender_procurementMethod.dropna().astype(str).unique().tolist())
    explore_method = method_col.selectbox("Method", method_options, key="explore_method")
    explore_rows = filtered.copy()
    with st.expander("Filter by tender estimate", expanded=False):
        st.caption("Choose one recorded currency before setting an estimate range. Amounts in different currencies are never combined.")
        st.caption("The supplied source records do not provide a reliable tender-status field, so status is not offered as a filter.")
        estimate_currencies = ["All currencies"] + sorted(filtered.tender_value_currency.dropna().astype(str).str.upper().unique().tolist())
        estimate_currency = st.selectbox("Estimate currency", estimate_currencies, key="explore_estimate_currency")
        if estimate_currency != "All currencies":
            currency_mask = explore_rows.tender_value_currency.fillna("").astype(str).str.upper().eq(estimate_currency)
            explore_rows = explore_rows[currency_mask]
            amount_values = pd.to_numeric(
                explore_rows.tender_value_amount,
                errors="coerce",
            ).dropna()
            if amount_values.empty:
                st.info(f"No tender estimates are recorded in {estimate_currency} for this view.")
            elif amount_values.min() == amount_values.max():
                st.caption(f"All recorded {estimate_currency} estimates in this view equal {amount_values.min():,.0f}.")
            else:
                estimate_key = "".join(ch for ch in estimate_currency.lower() if ch.isalnum()) or "currency"
                low_bound, high_bound = float(amount_values.min()), float(amount_values.max())
                min_key = f"explore_estimate_min_{estimate_key}"
                max_key = f"explore_estimate_max_{estimate_key}"
                if min_key in st.session_state:
                    st.session_state[min_key] = min(max(float(st.session_state[min_key]), low_bound), high_bound)
                if max_key in st.session_state:
                    st.session_state[max_key] = min(max(float(st.session_state[max_key]), low_bound), high_bound)
                range_col_a, range_col_b = st.columns(2)
                estimate_min = range_col_a.number_input(
                    f"Minimum estimate ({estimate_currency})", min_value=low_bound, max_value=high_bound,
                    value=low_bound, step=max((high_bound - low_bound) / 100, 1.0), format="%.0f",
                    key=min_key,
                )
                estimate_max = range_col_b.number_input(
                    f"Maximum estimate ({estimate_currency})", min_value=low_bound, max_value=high_bound,
                    value=high_bound, step=max((high_bound - low_bound) / 100, 1.0), format="%.0f",
                    key=max_key,
                )
                if estimate_min <= estimate_max:
                    estimate_amounts = pd.to_numeric(explore_rows.tender_value_amount, errors="coerce")
                    explore_rows = explore_rows[estimate_amounts.between(estimate_min, estimate_max)]
                else:
                    st.warning("Minimum estimate must be less than or equal to maximum estimate.")
    if explore_buyer != "All buyers":
        explore_rows = explore_rows[buyer_display(explore_rows.buyer_name).eq(explore_buyer)]
    if explore_method != "All methods":
        explore_rows = explore_rows[explore_rows.tender_procurementMethod.eq(explore_method)]
    if explore_term.strip():
        term = explore_term.strip().casefold()
        search_fields = ["tender_id", "tender_title", "buyer_name", "supplier_names"]
        matches = explore_rows[search_fields].fillna("").astype(str).apply(lambda col: col.str.casefold().str.contains(term, regex=False)).any(axis=1)
        explore_rows = explore_rows[matches]
    display_cols = ["tender_id", "ocid", "tender_title", "buyer_name", "tender_procurementMethod", "tender_datePublished", "tender_value_amount", "tender_value_currency", "tender_numberOfTenderers", "award_count", "supplier_names"]
    if explore_rows.empty:
        st.info("No tenders match this search. Clear a field or widen the filters.")
    else:
        page_controls = st.columns([1, 1, 3], gap="small")
        page_size = page_controls[0].selectbox("Rows per page", [25, 50, 100], key="explore_page_size")
        total_pages = max(1, (len(explore_rows) + page_size - 1) // page_size)
        page_key = "explore_page_number"
        if page_key in st.session_state:
            st.session_state[page_key] = min(max(int(st.session_state[page_key]), 1), total_pages)
        page_number = page_controls[1].selectbox("Page", list(range(1, total_pages + 1)), key=page_key)
        page_start = (page_number - 1) * page_size
        page_end = min(page_start + page_size, len(explore_rows))
        page_controls[2].markdown(f"<div style='padding-top:2rem;color:#617387'>Showing {page_start + 1:,}–{page_end:,} of {len(explore_rows):,} matching tenders</div>", unsafe_allow_html=True)
        table_page = explore_rows.iloc[page_start:page_end]
        main_rows = table_page[["tender_id", "tender_title", "buyer_name", "tender_datePublished", "tender_procurementMethod"]].copy()
        main_rows["buyer_name"] = buyer_display(main_rows["buyer_name"])
        main_rows["tender_datePublished"] = pd.to_datetime(main_rows["tender_datePublished"], errors="coerce", utc=True).dt.date
        main_rows = main_rows.rename(columns={
            "tender_id": "Tender ID", "tender_title": "Tender title", "buyer_name": "Buyer",
            "tender_datePublished": "Published", "tender_procurementMethod": "Method",
        })
        st.dataframe(main_rows, width="stretch", height=min(560, max(240, 38 * min(len(main_rows), 14) + 42)), hide_index=True, column_config={
            "Tender ID": st.column_config.TextColumn("Tender ID", width="small"),
            "Tender title": st.column_config.TextColumn("Tender title", width="large"),
            "Buyer": st.column_config.TextColumn("Buyer", width="medium"),
            "Published": st.column_config.DateColumn("Published", format="DD MMM YYYY", width="small"),
            "Method": st.column_config.TextColumn("Procurement method", width="small"),
        })
        st.markdown("#### Open a tender")
        selected_id = shared_tender_selectbox("Select a Tender ID to inspect", explore_rows.tender_id.astype(str).tolist(), key="explore_selected_tender")
        record = explore_rows[explore_rows.tender_id.astype(str).eq(selected_id)].iloc[0]
        with st.container(border=True):
            st.markdown(f"### {clean_text(record.tender_title, 'Untitled tender')}")
            st.caption(f"Tender ID: {record.tender_id} · Buyer: {buyer_display(pd.Series([record.buyer_name])).iloc[0]}")
            info1, info2, info3, info4 = st.columns(4)
            info1.metric("Published", pd.to_datetime(record.tender_datePublished, errors="coerce").strftime("%d %b %Y") if pd.notna(pd.to_datetime(record.tender_datePublished, errors="coerce")) else "Not recorded")
            info2.metric("Method", clean_text(record.tender_procurementMethod))
            info3.metric("Estimated value", f"{record.tender_value_amount:,.0f}" if pd.notna(record.tender_value_amount) else "Not recorded")
            info4.metric("Currency", clean_text(record.tender_value_currency))
            st.write(f"**Recorded tenderers:** {clean_text(record.tender_numberOfTenderers)} · **Linked awards:** {int(record.award_count)}")
            st.write(f"**Supplier names as recorded:** {clean_text(record.supplier_names, 'No linked supplier name recorded')}")
            with st.expander("Source description and identifiers"):
                st.write(f"**Description:** {clean_text(record.get('tender_description'))}")
                st.write(f"**Source record ID:** {clean_text(record.ocid)} · **Source link:** {clean_text(record['_link'])}")
            action_a, action_b, action_c, action_d = st.columns(4, gap="small")
            action_a.button("Trace buyer, awards & suppliers", key="explore_trace_relationships", width="stretch", on_click=navigate_investigation, args=("Relationships", selected_id, False, None))
            action_b.button("Review its signals", key="explore_review_signals", width="stretch", on_click=navigate_investigation, args=("Anomaly review", selected_id, False, None))
            action_c.button("Open buyer & supplier", key="explore_open_entities", width="stretch", on_click=navigate_investigation, args=("Buyer & supplier search", selected_id, False, None))
            action_d.button("Check data quality", key="explore_open_quality", width="stretch", on_click=navigate_investigation, args=("Data quality & reports", selected_id, False, None))
    st.download_button("Download filtered tenders (CSV)", explore_rows[display_cols].to_csv(index=False).encode("utf-8-sig"), "evidenceai_filtered_tenders.csv", "text/csv", disabled=explore_rows.empty)
    vals = pd.to_numeric(explore_rows.tender_value_amount, errors="coerce")
    valid_inr = vals[explore_rows.tender_value_currency.eq("INR") & vals.gt(0)]
    if not valid_inr.empty:
        st.subheader("Tender estimate distribution · INR")
        st.caption("Tender estimates are highly skewed. The logarithmic horizontal scale keeps common values visible alongside a small high-value tail. High values are not, by themselves, evidence of a problem.")
        p50, p95 = valid_inr.quantile(.50), valid_inr.quantile(.95)
        stat1, stat2, stat3 = st.columns(3)
        stat1.metric("Comparable INR tenders", fmt_count(len(valid_inr)))
        stat2.metric("Median estimate", f"₹{p50:,.0f}")
        stat3.metric("95th percentile", f"₹{p95:,.0f}")
        chart = px.histogram(x=valid_inr, nbins=35, labels={"x": "Tender estimate (INR)", "count": "Tenders"}, color_discrete_sequence=["#176B87"], log_x=True)
        chart.update_layout(bargap=.08)
        st.plotly_chart(style_chart(chart), width="stretch")

elif page == "Anomaly review":
    st.markdown('<div class="intro-panel"><span class="intro-label">Review signal only</span>A flag is a prompt to verify a source record. It is not a fraud probability, a finding, or proof of wrongdoing. Missing amount or currency is shown as a data-quality note and does not add to the priority score.</div>', unsafe_allow_html=True)
    with st.expander("How the review score works and its limits"):
        contamination = st.slider("Isolation Forest review fraction", 0.01, 0.20, 0.05, 0.01, help="Share of comparable INR records the unsupervised model labels as outliers.")
        st.markdown("**Transparent indicator score:** one point each for a single recorded tenderer, zero/negative INR estimate, and estimate in the top 1% of positive INR values. **Model flag:** adds one point when Isolation Forest is available and comparable records are sufficient. Award-versus-estimate differences and peer comparisons are context only; they do not increase the score. **Limit:** these checks do not account for all procurement context, and the score is not calibrated as a probability.")
    scored = score_records(filtered, contamination=contamination)
    model_status = scored.model_status.iloc[0] if not scored.empty else "No records match the selected filters."
    flagged = scored[scored.investigation_score.gt(0)].sort_values(["investigation_score", "tender_id"], ascending=[False, True])
    stat1, stat2, stat3, stat4 = st.columns(4, gap="small")
    stat1.metric("Records with a review signal", fmt_count(len(flagged)))
    stat2.metric("Multiple indicators", fmt_count(int(scored.investigation_score.ge(2).sum()) if not scored.empty else 0), help="Two or more transparent indicators/model flags. A higher count means more checks were triggered, not a higher probability of wrongdoing.")
    stat3.metric("Single indicator", fmt_count(int(scored.investigation_score.eq(1).sum()) if not scored.empty else 0))
    model_available = not scored.empty and scored.model_status.astype(str).str.startswith("Isolation Forest fit").any()
    stat4.metric("Isolation Forest", "Available" if model_available else "Unavailable", help=model_status)
    st.caption(f"Records checked: {len(scored):,}. Isolation Forest: {model_status}. These categories organize the review queue; they are not risk levels or findings.")
    active_scored = scored[scored.tender_id.astype(str).eq(active_tender_id)] if active_tender_id else scored.iloc[0:0]
    if not active_scored.empty and not bool(active_scored.iloc[0].investigation_score > 0):
        st.info(f"The selected investigation ({active_tender_id}) has no review signal under the current rules and filters. This is not an all-clear; it means these checks did not flag it.")
        st.button("Trace selected tender relationships", key="anomaly_trace_unflagged", on_click=navigate_investigation, args=("Relationships", active_tender_id, False, None))
    if not flagged.empty:
        display = flagged.copy()
        display["Buyer"] = buyer_display(display.buyer_name)
        display["Indicators"] = display.apply(lambda r: " · ".join(label for key, label in [
            ("flag_single_tenderer", "Single tenderer recorded"),
            ("flag_zero_or_negative_amount", "Zero/negative INR estimate"),
            ("flag_high_inr_amount", "Top 1% positive INR estimate"),
            ("model_flag", "Statistical outlier"),
        ] if bool(r[key])), axis=1)
        display["Data-quality note"] = display.flag_missing_amount_or_currency.map({True: "Amount/currency missing", False: "—"})
        st.dataframe(display[["tender_id", "Buyer", "investigation_score", "Indicators", "Data-quality note"]].rename(columns={
            "tender_id": "Tender ID", "investigation_score": "Priority score",
        }), width="stretch", height=min(470, max(240, 38 * min(len(flagged), 12) + 42)), hide_index=True, column_config={
            "Tender ID": st.column_config.TextColumn("Tender ID", width="small"),
            "Buyer": st.column_config.TextColumn("Buyer", width="medium"),
            "Priority score": st.column_config.NumberColumn("Review priority", width="small", help="Count of transparent indicators plus a possible model flag; not a probability."),
            "Indicators": st.column_config.TextColumn("Why it was flagged", width="large"),
            "Data-quality note": st.column_config.TextColumn("Data-quality note", width="medium"),
        })
        selected = shared_tender_selectbox("Choose a record to investigate", flagged["tender_id"].astype(str).tolist(), key="anomaly_selected_tender")
        row = flagged[flagged.tender_id.astype(str).eq(selected)].iloc[0]
        selected_buyer = buyer_display(pd.Series([row.buyer_name])).iloc[0]
        with st.container(border=True):
            st.markdown(f"### {clean_text(row.tender_title, 'Untitled tender')}")
            st.caption(f"Tender {row.tender_id} · {selected_buyer}")
            metric_a, metric_b, metric_c, metric_d = st.columns(4)
            metric_a.metric("Review priority", int(row.investigation_score), help="A triage count, not a probability or determination.")
            metric_b.metric("Tenderers recorded", clean_text(row.tender_numberOfTenderers))
            estimate_display = f"{row.tender_value_amount:,.0f} {clean_text(row.tender_value_currency, '')}" if pd.notna(row.tender_value_amount) else "Missing"
            metric_c.metric("Tender estimate", estimate_display)
            award_gap = row.get("award_to_estimate_pct")
            metric_d.metric(
                "Award vs estimate",
                f"{award_gap:+.1f}%" if pd.notna(award_gap) else "Not comparable",
                help="Difference between linked award total and tender estimate. Shown only when both amounts are recorded in the same currency and the estimate is positive.",
            )
            st.markdown("#### Review indicators")
            indicator_labels = [label for key, label in [
                ("flag_single_tenderer", "Single tenderer recorded"),
                ("flag_zero_or_negative_amount", "Zero or negative INR amount"),
                ("flag_high_inr_amount", "Top 1% of positive INR estimates"),
                ("model_flag", "Isolation Forest outlier"),
            ] if bool(row[key])]
            if indicator_labels:
                st.markdown(" &nbsp; ".join(f'<span class="evidence-chip">{escape(label)}</span>' for label in indicator_labels), unsafe_allow_html=True)
            if bool(row.flag_missing_amount_or_currency):
                st.warning("Data-quality note: tender amount or currency is missing. This note is excluded from the review priority score.")
            st.markdown("#### Evidence available in this dataset")
            st.write(f"**Description:** {clean_text(row.get('tender_description'))}")
            st.write(f"**Supplier names as recorded:** {clean_text(row.supplier_names, 'No linked supplier name recorded')}")
            row_awards = tables["awards"][tables["awards"]["_link_main"].eq(row["_link"])]
            st.write(f"**Associated awards:** {len(row_awards):,} · **Award values by currency:** {award_value_summary(row_awards)}")
            st.write(f"**Tender ID / source record:** {row.tender_id} / {clean_text(row.ocid)}")
            peers = comparable_tenders(filtered, str(selected))
            if not peers.empty:
                peer_values = pd.to_numeric(peers["tender_value_amount"], errors="coerce").dropna()
                selected_value = pd.to_numeric(pd.Series([row.tender_value_amount]), errors="coerce").iloc[0]
                peer_median = float(peer_values.median()) if not peer_values.empty else float("nan")
                st.markdown("#### Same-method comparison group")
                st.caption(
                    f"{len(peers):,} tenders in the current filtered view use the same procurement method and currency, "
                    f"with estimates between 0.5× and 2× this tender. Group median: {peer_median:,.0f} "
                    f"{clean_text(row.tender_value_currency)}; selected estimate: {selected_value:,.0f}. "
                    "This broad screening group is not a validated like-for-like comparison."
                )
                peer_view = peers[["tender_id", "tender_title", "buyer_name", "tender_value_amount", "tender_value_currency"]].copy()
                peer_view["buyer_name"] = buyer_display(peer_view["buyer_name"])
                st.dataframe(peer_view.rename(columns={
                    "tender_id": "Tender ID", "tender_title": "Tender title", "buyer_name": "Buyer",
                    "tender_value_amount": "Tender estimate", "tender_value_currency": "Currency",
                }), width="stretch", hide_index=True)
            else:
                st.caption("No comparable tender group is available under the current filters. A group requires the same recorded method and currency plus a positive estimate.")
            row_documents = tables["tender_documents"][tables["tender_documents"]["_link_main"].eq(row["_link"])]
            described_documents = row_documents.dropna(subset=["description"]).copy()
            if not described_documents.empty:
                st.markdown("#### Linked document metadata")
                document_columns = [column for column in ["documentType", "description", "format", "url"] if column in described_documents]
                st.dataframe(described_documents[document_columns].rename(columns={
                    "documentType": "Document type", "description": "Description", "format": "Format", "url": "Source URL",
                }), width="stretch", hide_index=True)
                st.caption("These are source-recorded descriptions and links; document contents are not included or verified by this local dataset.")
            if bool(row.flag_missing_amount_or_currency):
                st.write("**Data limitation:** the tender amount or its currency is missing, so the tender estimate cannot be compared reliably.")
            if pd.isna(row.tender_numberOfTenderers):
                st.write("**Data limitation:** the source has no tenderer count for this record.")
            st.markdown("#### Verify before drawing a conclusion")
            checks = []
            if bool(row.flag_single_tenderer):
                checks.append("Check the bid opening record and whether the source count reflects valid bids or submitted bids.")
            if bool(row.flag_high_inr_amount) or bool(row.flag_zero_or_negative_amount):
                checks.append("Confirm the estimate, currency, scope, and comparable procurement context in the original tender documents.")
            if bool(row.model_flag):
                checks.append("Compare with similar tenders; an unsupervised outlier can reflect legitimate differences in scale or scope.")
            if not checks:
                checks.append("Review the source tender and award context; the score alone cannot explain the record.")
            for check in checks:
                st.markdown(f"- {check}")
            action_a, action_b, action_c = st.columns(3, gap="small")
            action_a.button("Trace buyer, awards & suppliers", key="anomaly_trace_relationships", width="stretch", on_click=navigate_investigation, args=("Relationships", selected, False, None))
            action_b.button("Open buyer & supplier search", key="anomaly_open_entities", width="stretch", on_click=navigate_investigation, args=("Buyer & supplier search", selected, False, None))
            action_c.button("Inspect data limitations", key="anomaly_open_quality", width="stretch", on_click=navigate_investigation, args=("Data quality & reports", selected, False, None))
        out = display[["tender_id", "ocid", "Buyer", "tender_value_amount", "tender_value_currency", "tender_numberOfTenderers", "investigation_score", "Indicators", "Data-quality note"]].rename(columns={
            "tender_id": "Tender ID", "ocid": "Source record ID", "Buyer": "Buyer", "tender_value_amount": "Tender estimate",
            "tender_value_currency": "Currency", "tender_numberOfTenderers": "Recorded tenderers", "investigation_score": "Review priority",
        })
        st.download_button("Download review list (CSV)", out.to_csv(index=False).encode("utf-8-sig"), "evidenceai_review_list.csv", "text/csv")
    else:
        st.success("No review indicators were produced for this filtered selection. This does not establish that all tenders are free of issues.")

elif page == "Buyer & supplier search":
    st.caption("Select a buyer or supplier to see a compact summary and its linked tenders. Names are shown exactly as recorded and are not merged into legal entities.")
    entity_tab1, entity_tab2 = st.tabs(["Buyers", "Suppliers"])
    award_supplier_links = tables["awards_suppliers"][["_link_awards", "name"]].merge(
        tables["awards"][["_link", "_link_main"]], left_on="_link_awards", right_on="_link", how="inner"
    )
    with entity_tab1:
        buyer_summary = filtered.groupby("buyer_id", dropna=False).agg(
            tender_records=("id", "count"),
            buyer_name=("buyer_name", lambda values: values.mode().iloc[0] if not values.mode().empty else "Not recorded"),
        ).reset_index()
        buyer_summary["buyer_name"] = buyer_display(buyer_summary["buyer_name"])
        buyer_summary["buyer_id"] = buyer_summary["buyer_id"].fillna("Not recorded").astype(str)
        buyer_summary = buyer_summary.sort_values("tender_records", ascending=False)
        if buyer_summary.empty:
            st.info("No buyer records match the current filters.")
        else:
            buyer_options = {f"{r.buyer_name} · {r.buyer_id}": r.buyer_id for r in buyer_summary.itertuples()}
            if st.session_state.get("_buyer_context_tender") != active_tender_id:
                if active_tender is not None:
                    target_buyer_id = clean_text(active_tender.buyer_id)
                    target_label = next((label for label, buyer_id in buyer_options.items() if buyer_id == target_buyer_id), None)
                    if target_label:
                        st.session_state["selected_buyer_entity"] = target_label
                st.session_state["_buyer_context_tender"] = active_tender_id
            chosen = st.selectbox("Choose a buyer", list(buyer_options), key="selected_buyer_entity")
            chosen_id = buyer_options[chosen]
            buyer_rows = filtered[filtered.buyer_id.fillna("Not recorded").astype(str).eq(chosen_id)]
            buyer_links = set(buyer_rows._link)
            buyer_awards = tables["awards"][tables["awards"]._link_main.isin(buyer_links)]
            buyer_suppliers = tables["awards_suppliers"][tables["awards_suppliers"]._link_awards.isin(set(buyer_awards._link))]
            b1, b2, b3 = st.columns(3)
            b1.metric("Tender records", fmt_count(len(buyer_rows)))
            b2.metric("Award records", fmt_count(len(buyer_awards)))
            b3.metric("Supplier names as recorded", fmt_count(buyer_suppliers.name.dropna().astype(str).str.strip().str.casefold().nunique()))
            st.caption(f"**Award values by recorded currency:** {award_value_summary(buyer_awards)}")
            tender_col, activity_col = st.columns([1.5, 1], gap="medium")
            with tender_col:
                st.subheader("Tenders linked to this buyer")
                buyer_tenders = buyer_rows[["tender_id", "tender_title", "tender_datePublished", "tender_procurementMethod", "award_count", "supplier_names"]].copy()
                buyer_tenders = buyer_tenders.rename(columns={"tender_id": "Tender ID", "tender_title": "Tender title", "tender_datePublished": "Published", "tender_procurementMethod": "Method", "award_count": "Awards", "supplier_names": "Supplier names"})
                st.dataframe(buyer_tenders, width="stretch", height=min(500, max(240, 38 * min(len(buyer_tenders), 13) + 42)), hide_index=True)
                st.download_button("Download this buyer's tenders (CSV)", buyer_tenders.to_csv(index=False).encode("utf-8-sig"), "evidenceai_buyer_tenders.csv", "text/csv")
                linked_id = shared_tender_selectbox("Open one of this buyer's tenders", buyer_rows.tender_id.astype(str).tolist(), key="buyer_linked_tender")
                st.button("Trace selected tender", key="buyer_trace_selected", on_click=navigate_investigation, args=("Relationships", linked_id, False, None))
            with activity_col:
                st.subheader("Publication activity")
                st.caption("Tender records grouped by their recorded publication year.")
                activity_chart = publication_activity_chart(buyer_rows)
                if activity_chart is not None:
                    st.plotly_chart(activity_chart, width="stretch", config={"displayModeBar": False})
                else:
                    st.info("Publication dates are not recorded for this buyer's tenders.")
            with st.expander("Compare all buyers"):
                st.dataframe(buyer_summary.rename(columns={"buyer_name": "Buyer", "buyer_id": "Buyer ID", "tender_records": "Tender records"}), width="stretch", hide_index=True)
    with entity_tab2:
        award_suppliers = tables["awards_suppliers"][["_link_awards", "name"]].merge(
            tables["awards"][["_link", "_link_main", "value_amount", "value_currency"]], left_on="_link_awards", right_on="_link", how="left"
        )
        award_suppliers = award_suppliers[award_suppliers._link_main.isin(set(filtered._link))]
        supplier_summary = award_suppliers.dropna(subset=["name"]).groupby("name", dropna=False).agg(
            award_rows=("_link_awards", "nunique"), tender_links=("_link_main", "nunique"),
        ).reset_index().sort_values("award_rows", ascending=False)
        if supplier_summary.empty:
            st.info("No supplier names are linked to tenders in the current selection.")
        else:
            supplier_options = supplier_summary.name.astype(str).tolist()
            if st.session_state.get("_supplier_context_tender") != active_tender_id:
                if active_tender is not None:
                    first_linked_supplier = clean_text(active_tender.supplier_names, "").split("; ")[0]
                    if first_linked_supplier in supplier_options:
                        st.session_state["selected_supplier_entity"] = first_linked_supplier
                st.session_state["_supplier_context_tender"] = active_tender_id
            chosen_supplier = st.selectbox("Choose a supplier name", supplier_options, key="selected_supplier_entity")
            supplier_rows = award_suppliers[award_suppliers.name.eq(chosen_supplier)]
            supplier_links = set(supplier_rows._link_main)
            linked_tenders = filtered[filtered._link.isin(supplier_links)]
            s1, s2, s3 = st.columns(3)
            s1.metric("Award records", fmt_count(supplier_rows._link.nunique()))
            s2.metric("Linked tenders", fmt_count(linked_tenders._link.nunique()))
            s3.metric("Buyer names", fmt_count(buyer_display(linked_tenders.buyer_name).nunique()))
            st.caption(f"**Award values by recorded currency:** {award_value_summary(supplier_rows.drop_duplicates('_link'))}")
            tender_col, activity_col = st.columns([1.5, 1], gap="medium")
            with tender_col:
                st.subheader("Tenders linked to this supplier")
                supplier_tenders = linked_tenders[["tender_id", "tender_title", "buyer_name", "tender_datePublished", "tender_procurementMethod", "award_count"]].copy()
                supplier_tenders["buyer_name"] = buyer_display(supplier_tenders.buyer_name)
                supplier_tenders = supplier_tenders.rename(columns={"tender_id": "Tender ID", "tender_title": "Tender title", "buyer_name": "Buyer", "tender_datePublished": "Published", "tender_procurementMethod": "Method", "award_count": "Awards"})
                st.dataframe(supplier_tenders, width="stretch", height=min(500, max(240, 38 * min(len(supplier_tenders), 13) + 42)), hide_index=True)
                st.download_button("Download this supplier's tenders (CSV)", supplier_tenders.to_csv(index=False).encode("utf-8-sig"), "evidenceai_supplier_tenders.csv", "text/csv")
                linked_id = shared_tender_selectbox("Open one of this supplier's tenders", linked_tenders.tender_id.astype(str).tolist(), key="supplier_linked_tender")
                st.button("Trace selected tender", key="supplier_trace_selected", on_click=navigate_investigation, args=("Relationships", linked_id, False, None))
            with activity_col:
                st.subheader("Publication activity")
                st.caption("Tender records grouped by their recorded publication year.")
                activity_chart = publication_activity_chart(linked_tenders)
                if activity_chart is not None:
                    st.plotly_chart(activity_chart, width="stretch", config={"displayModeBar": False})
                else:
                    st.info("Publication dates are not recorded for this supplier's tenders.")
            with st.expander("Compare all supplier names"):
                st.dataframe(supplier_summary.rename(columns={"name": "Supplier name (as recorded)", "award_rows": "Award records", "tender_links": "Linked tenders"}), width="stretch", hide_index=True)

elif page == "Relationships":
    st.caption("Follow the recorded links from a tender to its buyer, awards, and suppliers. These are source-data relationships, not a claim about organizational ownership.")
    if filtered.empty:
        st.info("No tenders match the current filters.")
    else:
        relation_ids = filtered.tender_id.astype(str).tolist()
        relation_titles = filtered.set_index(filtered.tender_id.astype(str)).tender_title.to_dict()
        selected_relation_id = shared_tender_selectbox(
            "Choose a tender", relation_ids, key="relationship_tender",
            format_func=lambda identifier: f"{identifier} · {clean_text(relation_titles.get(identifier), 'Untitled tender')[:70]}",
        )
        row = filtered[filtered.tender_id.astype(str).eq(selected_relation_id)].iloc[0]
        link = row["_link"]
        relation_buyer = buyer_display(pd.Series([row.buyer_name])).iloc[0]
        st.markdown(f"### {clean_text(row.tender_title, 'Untitled tender')}")
        st.caption(f"Tender {row.tender_id} · Published {clean_text(row.tender_datePublished)} · {clean_text(row.tender_procurementMethod)}")
        awards = tables["awards"][tables["awards"]["_link_main"].eq(link)].copy()
        suppliers = tables["awards_suppliers"]
        award_suppliers = awards.merge(suppliers[["_link_awards", "name"]], left_on="_link", right_on="_link_awards", how="left")
        supplier_names = sorted(award_suppliers.name.dropna().astype(str).unique().tolist())
        award_count = len(awards)
        flow = st.columns(4, gap="small")
        flow_data = [
            ("Tender", clean_text(row.tender_id)),
            ("Buyer", clean_text(relation_buyer)),
            ("Awards", f"{award_count:,} linked"),
            ("Suppliers", f"{len(supplier_names):,} recorded names"),
        ]
        for i, (label_text, value_text) in enumerate(flow_data):
            arrow = " <span class='flow-arrow'>→</span>" if i < len(flow_data) - 1 else ""
            flow[i].markdown(
                f'<div class="entity-card"><div class="entity-label">{escape(label_text)}</div>'
                f'<div class="entity-value">{escape(value_text)}</div>{arrow}</div>',
                unsafe_allow_html=True,
            )
        if supplier_names:
            st.caption("Recorded suppliers: " + " · ".join(supplier_names))
        st.caption(f"Award values by recorded currency: {award_value_summary(awards)}")
        relationship_mode = st.radio("Relationship view", ["Graph", "Records"], horizontal=True, key="relationship_display_mode", label_visibility="collapsed")
        if relationship_mode == "Graph":
            node_labels = [f"Tender\n{clean_text(row.tender_id)}", f"Buyer\n{clean_text(relation_buyer)}\nID {clean_text(row.buyer_id)}"]
            node_x = [0.03, 0.34]
            node_y = [0.5, 0.5]
            sources, targets, values, link_labels = [0], [1], [1], ["Buyer ID recorded on tender"]
            award_node_index = {}
            for _, award in awards.iterrows():
                award_link = str(award["_link"])
                award_node_index[award_link] = len(node_labels)
                node_labels.append(f"Award\n{award_link}")
                node_x.append(0.64)
                node_y.append((len(award_node_index)) / (len(awards) + 1))
                sources.append(0)
                targets.append(award_node_index[award_link])
                values.append(1)
                link_labels.append(f"Tender source link {award['_link_main']}")
            supplier_index = {}
            for _, linked in award_suppliers.iterrows():
                supplier_name = clean_text(linked["name"], "")
                award_link = str(linked["_link"])
                if not supplier_name or award_link not in award_node_index:
                    continue
                if supplier_name not in supplier_index:
                    supplier_index[supplier_name] = len(node_labels)
                    node_labels.append(f"Supplier\n{supplier_name}")
                    node_x.append(0.96)
                    node_y.append(len(supplier_index) / (len(supplier_index) + 1))
                sources.append(award_node_index[award_link])
                targets.append(supplier_index[supplier_name])
                values.append(1)
                link_labels.append(f"Supplier recorded under award {award_link}")
            award_y_count = len(award_node_index)
            for position in range(award_y_count):
                node_y[2 + position] = (position + 1) / (award_y_count + 1)
            supplier_y_start = 2 + award_y_count
            for position in range(len(supplier_index)):
                node_y[supplier_y_start + position] = (position + 1) / (len(supplier_index) + 1)
            node_colors = ["#176B87", "#172B4D"] + ["#527D9B"] * len(award_node_index) + ["#D99A27"] * len(supplier_index)
            relationship_graph = go.Figure(go.Sankey(
                arrangement="fixed",
                node={"label": node_labels, "x": node_x, "y": node_y, "color": node_colors, "pad": 22, "thickness": 18, "line": {"color": "#dce3eb", "width": 1}, "customdata": node_labels, "hovertemplate": "%{label}<extra>Recorded entity</extra>"},
                link={"source": sources, "target": targets, "value": values, "label": link_labels, "color": "rgba(23,107,135,.28)", "hovertemplate": "%{label}<extra>Source relationship</extra>"},
            ))
            relationship_graph.update_layout(height=420, font={"family": "Inter, Segoe UI, sans-serif", "size": 12, "color": "#344b62"}, margin={"l": 8, "r": 8, "t": 12, "b": 12}, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(relationship_graph, width="stretch")
            st.caption("Each connection is built from the tender buyer ID, award-to-tender source link, or supplier-to-award source link. Hover for the recorded relationship. Missing award or supplier links are not inferred.")
        else:
            st.caption("The tables below preserve exact identifiers and recorded fields for traceability.")
        if relationship_mode == "Records":
            parties = tables["parties"][tables["parties"]["_link_main"].eq(link)]
            items = tables["tender_items"][tables["tender_items"]["_link_main"].eq(link)]
            documents = tables["tender_documents"][tables["tender_documents"]["_link_main"].eq(link)]
            award_tab, parties_tab, items_tab = st.tabs(["Awards & suppliers", "Party records", "Items & documents"])
            with award_tab:
                if awards.empty:
                    st.info("No award record is linked to this tender in the supplied files.")
                else:
                    awards_view = award_suppliers.groupby(["_link", "value_amount", "value_currency"], dropna=False).agg(
                        supplier_names=("name", lambda values: ", ".join(sorted(set(values.dropna().astype(str)))) or "No name recorded")
                    ).reset_index().rename(columns={"value_amount": "Award value", "value_currency": "Currency", "supplier_names": "Supplier name(s)"})
                    st.dataframe(awards_view[["Award value", "Currency", "Supplier name(s)"]], width="stretch", hide_index=True)
            with parties_tab:
                if parties.empty:
                    st.info("No party rows are linked to this tender in the supplied files.")
                else:
                    parties_view = parties[["roles", "id", "contactPoint_name", "address_locality"]].rename(columns={
                        "roles": "Recorded role", "id": "Party ID", "contactPoint_name": "Contact name", "address_locality": "Locality",
                    })
                    st.dataframe(parties_view, width="stretch", hide_index=True)
                    st.caption("A party contact name may differ from the buyer display name.")
            with items_tab:
                st.markdown("**Tender items**")
                item_details = items.dropna(subset=["description"]).copy()
                item_details = item_details[item_details.description.astype(str).str.strip().ne("")]
                if item_details.empty:
                    st.info("No item description is recorded for this tender.")
                else:
                    st.dataframe(item_details[["id", "description"]].rename(columns={"id": "Recorded item/category", "description": "Item description"}), width="stretch", hide_index=True)
                st.markdown("**Document descriptions**")
                document_details = documents.dropna(subset=["description"]).copy()
                document_details = document_details[document_details.description.astype(str).str.strip().ne("")]
                if document_details.empty:
                    st.info("No document description is recorded for this tender.")
                else:
                    st.dataframe(document_details[["description"]].rename(columns={"description": "Document description"}), width="stretch", hide_index=True)
                st.caption("The dataset contains document metadata only; source document files are not included.")
            with st.expander("Source identifiers for traceability"):
                st.write(f"**Tender source link:** {link} · **OCID:** {row.ocid}")
                st.write("Award source links: " + (", ".join(awards["_link"].astype(str)) if not awards.empty else "No linked award ID"))
                st.write(f"**Buyer source ID:** {row.buyer_id}")
            st.caption("Associations are based on exact source link identifiers present in the supplied files.")

else:
    st.markdown('<div class="dashboard-section-title">Dataset scan results</div><div class="dashboard-section-note">Rates below are calculated from the supplied CSV files. They describe completeness and link checks, not overall data accuracy.</div>', unsafe_allow_html=True)
    main_audit = audit["files"]["main"]
    main_cells = main_audit["rows"] * max(len(main_audit["columns"]), 1)
    main_missing_cells = sum(main_audit["missing_by_column"].values())
    main_completeness = 100 * (1 - main_missing_cells / main_cells) if main_cells else 100.0
    unique_link_rate = 100 * audit["main_link_unique"] / audit["main_link_rows"] if audit["main_link_rows"] else 100.0
    linked_rows = sum(info["link_main_rows"] or 0 for info in audit["files"].values())
    matched_rows = sum(info["link_main_matched_to_main"] or 0 for info in audit["files"].values())
    link_rate = (100 * matched_rows / linked_rows) if linked_rows else 100.0
    gauge_cols = st.columns(3, gap="small")
    gauge_titles = [
        (main_completeness, "Main-file cell completeness", "#f29b38"),
        (unique_link_rate, "Unique tender source links", "#2186c7"),
        (link_rate, "Child links matched to tenders", "#12a78a"),
    ]
    for gauge_col, (rate, label, color) in zip(gauge_cols, gauge_titles):
        with gauge_col.container(border=True):
            st.plotly_chart(quality_gauge(rate, label, color), width="stretch", config={"displayModeBar": False})
    st.caption("Completeness is measured across cells in main.csv. Source-link uniqueness compares unique main links with main rows. Child-link match rate checks recorded links against main tender links.")
    st.caption("These checks summarize the supplied CSV files. EvidenceAI reads the raw files without changing them.")
    st.markdown("#### Current investigation record")
    quality_options = filtered.tender_id.astype(str).tolist()
    quality_id = shared_tender_selectbox("Select a tender to inspect its data limitations", quality_options, key="quality_selected_tender")
    if quality_id:
        quality_row = filtered[filtered.tender_id.astype(str).eq(quality_id)].iloc[0]
        with st.container(border=True):
            st.markdown(f"**{clean_text(quality_row.tender_title, 'Untitled tender')}**")
            st.caption(f"Tender {quality_row.tender_id} · {buyer_display(pd.Series([quality_row.buyer_name])).iloc[0]}")
            limitation_notes = []
            if pd.isna(quality_row.tender_value_amount):
                limitation_notes.append("Tender estimate is blank; the amount cannot be assessed from this file.")
            if pd.isna(quality_row.tender_value_currency) or not str(quality_row.tender_value_currency).strip():
                limitation_notes.append("Tender currency is blank; an estimate cannot be compared safely across currencies.")
            if pd.isna(quality_row.tender_numberOfTenderers):
                limitation_notes.append("Tenderer count is blank; competition cannot be assessed from this field.")
            if int(quality_row.award_count) == 0:
                limitation_notes.append("No linked award record is present in the supplied files; this may reflect missing source coverage or an unawarded tender.")
            if limitation_notes:
                for note in limitation_notes:
                    st.warning(note)
            else:
                st.success("No blank estimate, currency, tenderer-count, or award-link fields were found for this selected record. This is not a guarantee that all source information is complete.")
            qa_action1, qa_action2 = st.columns(2, gap="small")
            qa_action1.button("Trace this tender", key="quality_trace_tender", on_click=navigate_investigation, args=("Relationships", quality_id, False, None))
            qa_action2.button("Review its signals", key="quality_review_tender", on_click=navigate_investigation, args=("Anomaly review", quality_id, False, None))
            report_awards = tables["awards"][tables["awards"]["_link_main"].eq(quality_row["_link"])]
            report_docs = tables["tender_documents"][tables["tender_documents"]["_link_main"].eq(quality_row["_link"])]
            report_scores = score_records(filtered, contamination=0.05)
            report_score_rows = report_scores[report_scores.tender_id.astype(str).eq(str(quality_id))]
            report_score = report_score_rows.iloc[0] if not report_score_rows.empty else None
            report_signals = []
            if report_score is not None:
                report_signals = [label for key, label in [
                    ("flag_single_tenderer", "Single tenderer recorded"),
                    ("flag_zero_or_negative_amount", "Zero or negative INR estimate"),
                    ("flag_high_inr_amount", "Estimate in the top 1% of positive INR estimates"),
                    ("model_flag", "Isolation Forest statistical outlier"),
                ] if bool(report_score.get(key, False))]
            missing_fields = [
                label for column, label in [
                    ("tender_value_amount", "Tender estimate"),
                    ("tender_value_currency", "Tender currency"),
                    ("tender_numberOfTenderers", "Tenderer count"),
                ] if column not in quality_row.index or pd.isna(quality_row.get(column)) or not str(quality_row.get(column)).strip()
            ]
            award_gap = quality_row.get("award_to_estimate_pct")
            award_comparison_text = f"{award_gap:+.1f}%" if pd.notna(award_gap) else "Not comparable from recorded amounts/currencies"
            signal_text = "\n".join(f"- {signal}" for signal in report_signals) or "- No review indicators were produced under the current checks and filters."
            missing_text = "\n".join(f"- {field} is missing in this source record." for field in missing_fields) or "- The selected record has values for the estimate, currency, and tenderer count fields checked here."
            priority_text = str(int(report_score.investigation_score)) if report_score is not None else "Not available"
            report = f"""# EvidenceAI investigation brief

## Selected tender

- Tender ID: {quality_row.tender_id}
- Title: {clean_text(quality_row.tender_title, 'Untitled tender')}
- Buyer: {buyer_display(pd.Series([quality_row.buyer_name])).iloc[0]}
- Published: {clean_text(quality_row.tender_datePublished)}
- Procurement method: {clean_text(quality_row.tender_procurementMethod)}
- Tender estimate: {clean_text(quality_row.tender_value_amount)} {clean_text(quality_row.tender_value_currency, '')}
- Recorded tenderers: {clean_text(quality_row.tender_numberOfTenderers)}
- Linked awards: {len(report_awards):,}
- Supplier names as recorded: {clean_text(quality_row.supplier_names, 'No linked supplier name recorded')}
- Award total versus tender estimate: {award_comparison_text}

## Review signals

{signal_text}
- Review priority: {priority_text} (triage count, not a probability or finding).
- These are screening leads, not findings of fraud or wrongdoing. The Isolation Forest result depends on the current filtered comparison set.

## Data limitations

{missing_text}
- Linked document metadata rows: {len(report_docs):,}. The local dataset does not include document contents.
- Source record ID (OCID): {clean_text(quality_row.ocid)}
- Source link: {clean_text(quality_row['_link'])}

## Interpretation

Supplier names and links are shown as recorded in the supplied CSVs. Similar names are not merged into legal entities. Confirm all details against the original procurement source before drawing conclusions.
"""
            st.download_button(
                "Download this tender's investigation brief",
                report.encode("utf-8"), f"evidenceai_tender_{quality_id}_brief.md", "text/markdown", width="stretch",
            )
    duplicate_total = sum(info["duplicate_rows"] for info in audit["files"].values())
    linked_rows = sum(info["link_main_rows"] or 0 for info in audit["files"].values())
    matched_rows = sum(info["link_main_matched_to_main"] or 0 for info in audit["files"].values())
    link_rate = (100 * matched_rows / linked_rows) if linked_rows else 100.0
    qa1, qa2, qa3, qa4 = st.columns(4, gap="small")
    qa1.metric("Tender records", fmt_count(audit["main_link_rows"]), help="Rows in the main source CSV; repeated source links are reported separately.")
    qa2.metric("Source files", f"{len(audit['files'])} / 8", help="Expected procurement CSV files found and audited.")
    qa3.metric("Exact duplicate rows", fmt_count(duplicate_total), "None found" if duplicate_total == 0 else "Review repeated rows")
    qa4.metric("Child links matched", f"{link_rate:.1f}%", help=f"{matched_rows:,} of {linked_rows:,} child rows with a main-record link match a main source link.")
    st.caption(f"Supplier-to-award links matched: {audit['supplier_award_links_matched']:,} of {len(tables['awards_suppliers']):,} supplier rows.")
    st.markdown("#### File-by-file checks")
    file_rows = []
    for name, info in audit["files"].items():
        total_missing = sum(info["missing_by_column"].values())
        cells = info["rows"] * max(len(info["columns"]), 1)
        pct_complete = 100 * (1 - total_missing / cells) if cells else 100.0
        file_rows.append({
            "Source file": f"{name}.csv", "Rows": info["rows"], "Completeness": f"{pct_complete:.1f}%",
            "Exact duplicate rows": info["duplicate_rows"], "Linked rows": info["link_main_rows"] if info["link_main_rows"] is not None else "Not applicable",
            "Matched to main": info["link_main_matched_to_main"] if info["link_main_matched_to_main"] is not None else "Not applicable",
            "Unmatched links": info["link_main_unmatched"] if info["link_main_unmatched"] is not None else "Not applicable",
        })
    st.dataframe(pd.DataFrame(file_rows), width="stretch", hide_index=True)
    st.caption(f"Main records: {audit['main_link_rows']:,} · unique source links: {audit['main_link_unique']:,} · unique OCIDs: {audit['main_ocid_unique']:,}. Exact duplicate rows are counted within each file.")
    st.markdown('<div class="intro-panel"><span class="intro-label">How to read missing values</span>A blank field means the source CSV did not provide a value. The dataset does not reliably label a blank as unavailable versus not applicable, so confirm the field against its source context before interpreting it.</div>', unsafe_allow_html=True)
    missing_currency = int(records.tender_value_currency.isna().sum())
    st.warning(f"Tender estimate currency is blank on {missing_currency:,} of {len(records):,} tender records. Without currency, an estimate cannot be safely compared with other amounts; these rows are excluded from INR amount analysis.")
    missingness = records.isna().mean().mul(100).sort_values(ascending=False).head(12).rename("Missing (%)").rename_axis("Field").reset_index()
    missingness["Field"] = missingness["Field"].map(readable_field)
    by_currency = tables["awards"].groupby("value_currency", dropna=False).value_amount.agg(records="count", total="sum").reset_index()
    by_currency = by_currency.rename(columns={"value_currency": "Recorded currency", "records": "Award records", "total": "Total award value"})
    quality_mode = st.radio("Data quality display", ["Charts", "Data"], horizontal=True, key="quality_display_mode", label_visibility="collapsed")
    quality_left, quality_right = st.columns(2, gap="medium")
    if quality_mode == "Charts":
        missing_chart = px.bar(missingness.sort_values("Missing (%)"), x="Missing (%)", y="Field", orientation="h", range_x=[0, 100], text="Missing (%)", color_discrete_sequence=["#176B87"])
        missing_chart.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
        with quality_left.container(border=True):
            st.subheader("Fields most often blank")
            st.caption("Completeness measure for the main tender file; not a validity judgment.")
            st.plotly_chart(style_chart(missing_chart), width="stretch")
        award_count_chart = px.bar(by_currency, x="Recorded currency", y="Award records", color="Recorded currency", labels={"Award records": "Award records"})
        with quality_right.container(border=True):
            st.subheader("Award records by currency")
            st.caption("Counts stay separate by recorded currency; amounts are not combined.")
            st.plotly_chart(style_chart(award_count_chart), width="stretch")
    else:
        with quality_left.container(border=True):
            st.subheader("Fields most often blank")
            st.caption("Completeness measure for the main tender file; not a validity judgment.")
            st.dataframe(missingness, width="stretch", hide_index=True, column_config={"Missing (%)": st.column_config.NumberColumn("Missing (%)", format="%.1f%%")})
        with quality_right.container(border=True):
            st.subheader("Award values by currency")
            st.caption("Currency totals remain separate; different currencies are never added together.")
            st.dataframe(by_currency, width="stretch", hide_index=True, column_config={"Total award value": st.column_config.NumberColumn("Total award value", format="%,.2f")})
    summary = f"""# EvidenceAI data-quality summary

- Scope: Himachal Pradesh procurement CSV files stored locally in `data/raw/`.
- Tender records in current filtered view: {len(filtered):,}.
- Linked award records in current filtered view: {int(tables['awards']['_link_main'].isin(set(filtered['_link'])).sum()):,}.
- Exact duplicate rows across source files: {duplicate_total:,}.
- Child rows matched to a main tender: {link_rate:.1f}% ({matched_rows:,}/{linked_rows:,}).
- Tender estimate currency blank: {missing_currency:,} of {len(records):,}; those values are excluded from INR comparisons.
- Blank values may be unavailable or inapplicable; the source does not distinguish these cases consistently.
- Anomaly scores are review leads only and do not establish misconduct.
- Source links are matched exactly; similar supplier names are not merged.
"""
    st.markdown("#### Download reports")
    st.caption("Choose an evidence summary or the records currently in view.")
    download_a, download_b = st.columns(2, gap="medium")
    with download_a.container(border=True):
        st.markdown("##### Investigation summary")
        st.caption("Diagnostic counts, coverage notes, and interpretation limits.")
        st.download_button("Download summary", summary.encode("utf-8"), "evidenceai_investigation_summary.md", "text/markdown", width="stretch")
    with download_b.container(border=True):
        st.markdown("##### Filtered tender records")
        st.caption(f"{len(filtered):,} tender records matching the current filters.")
        st.download_button("Download CSV", filtered.to_csv(index=False).encode("utf-8-sig"), "evidenceai_filtered_tenders.csv", "text/csv", width="stretch", disabled=filtered.empty)

