import calendar
from datetime import date, datetime, timedelta
from io import BytesIO
from html import escape
import re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

PAS_YELLOW = "#FFD400"
PAS_BLACK = "#0A0A0A"
PAS_DARK = "#171717"
PAS_GREY = "#F4F4F4"

st.set_page_config(page_title="PAS Live Cost Dashboard", page_icon="pas_logo.png", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{ background: #f7f8fa !important; color: #0A0A0A !important; font-family: Inter, "Segoe UI", Arial, sans-serif; }}
    .block-container {{ max-width: 1580px !important; padding-top: 1.05rem !important; padding-left: 2rem !important; padding-right: 2rem !important; padding-bottom: 2rem !important; }}

    section[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #050606 0%, #0b1015 100%) !important; border-right: 1px solid #161b22; }}
    section[data-testid="stSidebar"] > div:first-child {{ padding-top: 1.05rem !important; }}
    section[data-testid="stSidebar"] * {{ color: white; }}
    section[data-testid="stSidebar"] img {{ border-radius: 14px !important; box-shadow: 0 10px 24px rgba(0,0,0,.26); }}
    .pas-sidebar-title {{ color:#fff; font-size:18px; font-weight:950; line-height:1.15; text-align:center; margin: 20px 0 8px; }}
    .pas-yellow-line {{ width:72px; height:4px; background:{PAS_YELLOW}; border-radius:99px; margin: 0 auto 22px; }}
    .pas-sidebar-copy {{ color:#fff !important; font-size:14px; line-height:1.52; font-weight:650; margin-bottom:24px; }}
    .pas-sidebar-rule {{ border-top:1px solid rgba(255,255,255,.22); margin:22px 0; }}
    .pas-sidebar-heading {{ color:{PAS_YELLOW}; font-size:19px; font-weight:950; margin: 0 0 16px; }}
    .pas-nav-row {{ display:grid; grid-template-columns: 26px 1fr; gap:10px; align-items:start; margin: 15px 0; color:#fff; font-weight:750; line-height:1.25; font-size:14px; }}
    .pas-nav-icon svg {{ width:21px; height:21px; stroke:{PAS_YELLOW}; stroke-width:2.4; fill:none; stroke-linecap:round; stroke-linejoin:round; }}
    .pas-sidebar-footer {{ color:#fff; font-size:12px; font-weight:800; margin-top:28px; }}

    .pas-hero {{ display:flex; align-items:center; gap:16px; background: linear-gradient(100deg, #08090b 0%, #151718 70%, #c9aa00 130%) !important; border-radius: 16px !important; padding: 12px 22px !important; margin: 0 0 18px 0 !important; box-shadow: 0 9px 25px rgba(0,0,0,.13) !important; min-height:60px; }}
    .pas-hero-logo {{ width:37px; height:37px; border-radius:7px; background:{PAS_YELLOW}; color:#000; display:inline-flex; align-items:center; justify-content:center; font-weight:950; font-size:14px; letter-spacing:-1px; }}
    .pas-hero-text {{ color:#fff; font-size:18px; font-weight:950; letter-spacing:-.02em; }}
    .pas-hero-dot {{ color:#fff; opacity:.8; margin: 0 7px; }}
    .pas-hero-version {{ color:{PAS_YELLOW}; font-weight:950; }}

    .pas-upload-card {{ background:#fff; border:1px solid #e5e7eb; border-radius:18px; box-shadow:0 5px 18px rgba(15,23,42,.08); padding:16px 18px 14px; margin-bottom:14px; }}
    .pas-upload-title {{ color:#0A0A0A; font-size:16px; font-weight:950; margin-bottom:10px; }}
    div[data-testid="stFileUploader"] {{ margin:0 !important; }}
    div[data-testid="stFileUploader"] label {{ display:none !important; }}
    div[data-testid="stFileUploader"] section {{ background: transparent !important; border: 0 !important; min-height: 0 !important; padding: 0 !important; }}
    div[data-testid="stFileUploaderDropzone"] {{ background: transparent !important; border: 0 !important; padding: 0 !important; min-height: 0 !important; }}
    div[data-testid="stFileUploaderDropzoneInstructions"] {{ display: none !important; }}
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {{ display: none !important; }}
    div[data-testid="stFileUploader"] button {{ background:#fff !important; color:#0A0A0A !important; border:1px solid #d7dce3 !important; border-radius:10px !important; font-weight:900 !important; min-height:44px !important; box-shadow:0 2px 8px rgba(0,0,0,.06) !important; }}
    div[data-testid="stFileUploader"] button * {{ color:#0A0A0A !important; fill:#0A0A0A !important; stroke:#0A0A0A !important; }}
    div[data-testid="stFileUploader"] small {{ color:#4b5563 !important; }}

    .stButton > button, .stDownloadButton > button {{ background: {PAS_YELLOW} !important; color: {PAS_BLACK} !important; border: 1px solid {PAS_BLACK} !important; border-radius: 12px !important; font-weight: 900 !important; min-height:52px !important; box-shadow:0 6px 18px rgba(255,212,0,.25) !important; }}
    .stDownloadButton > button {{ min-height:62px !important; font-size:20px !important; }}

    .kpi-card {{ background:#fff !important; border-radius:18px !important; border:1px solid #e4e7eb !important; box-shadow:0 5px 20px rgba(15,23,42,.08) !important; min-height:118px !important; padding:18px 22px !important; display:flex; align-items:center; gap:18px; }}
    .kpi-icon {{ width:64px; height:64px; border-radius:50%; background:#fff5bd; display:flex; align-items:center; justify-content:center; flex:none; }}
    .kpi-icon svg {{ width:35px; height:35px; stroke:#0A0A0A; stroke-width:2.5; fill:none; stroke-linecap:round; stroke-linejoin:round; }}
    .kpi-label {{ color:#111 !important; font-size:15px !important; font-weight:950 !important; margin:0 0 3px !important; }}
    .kpi-value {{ color:#e9b900 !important; font-size:34px !important; line-height:1.02 !important; font-weight:950 !important; text-shadow:none !important; }}
    .kpi-sub {{ color:#374151 !important; font-size:14px !important; margin-top:6px !important; }}

    .pas-results-title {{ color:#0A0A0A !important; font-size:28px !important; font-weight:950 !important; margin: 22px 0 8px !important; }}
    .pas-unmatched-pill {{ display:inline-flex; background:{PAS_YELLOW} !important; color:#0A0A0A !important; border:0 !important; border-radius:14px 14px 0 0 !important; padding:13px 20px !important; font-size:18px; font-weight:950; box-shadow:0 4px 14px rgba(0,0,0,.09); margin-top:12px; }}
    .pas-table-wrap {{ background:#fff !important; border:1px solid #e0e4e9 !important; border-radius:0 16px 16px 16px !important; max-height:430px !important; overflow:auto !important; box-shadow:0 7px 25px rgba(15,23,42,.10) !important; margin-bottom:18px; }}
    table.pas-table {{ width:100%; border-collapse:collapse; font-size:14px !important; color:#0A0A0A !important; }}
    table.pas-table thead th {{ background:{PAS_YELLOW} !important; color:#0A0A0A !important; border:1px solid #e2ba00 !important; padding:12px 14px !important; font-weight:950 !important; position:sticky; top:0; z-index:5; text-align:left; white-space:nowrap; }}
    table.pas-table tbody td {{ background:#fff !important; color:#0A0A0A !important; border:1px solid #e1e5eb !important; padding:10px 14px !important; }}
    table.pas-table tbody tr:nth-child(even) td {{ background:#fbfcfd !important; }}

    .pas-file-card {{ display:flex; align-items:center; gap:14px; background:#f4f6f8; border:1px solid #dfe4ea; border-radius:12px; padding:11px 14px; min-height:54px; margin: 4px 0 12px; }}
    .pas-file-icon {{ width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:950; font-size:11px; box-shadow:0 2px 8px rgba(0,0,0,.12); flex:none; }}
    .pas-file-icon.excel {{ background:#118a3b; }}
    .pas-file-main {{ flex:1; min-width:0; }}
    .pas-file-name {{ color:#0A0A0A; font-weight:950; font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
    .pas-file-size {{ color:#4b5563; font-weight:650; font-size:13px; margin-top:2px; }}
    .pas-file-check {{ width:24px; height:24px; border-radius:50%; background:#108a37; color:white; display:flex; align-items:center; justify-content:center; font-size:15px; font-weight:950; flex:none; }}

    .pas-bottom-chase-wrap {{ position: fixed; left: calc(18rem + 22px); right: 42px; bottom: 12px; height: 58px; pointer-events: none; z-index: 1; overflow: hidden; }}
    .pas-bottom-ground {{ position: absolute; left: 0; right: 0; bottom: 6px; border-bottom: 1px solid rgba(0,0,0,0.11); }}
    .pas-chase-pack {{ position: absolute; bottom: 8px; left: -150px; width: 150px; height: 48px; animation: pas-chase-run 13s linear 1 forwards; }}
    @keyframes pas-chase-run {{ 0% {{ transform: translateX(-120px); opacity: 0; }} 8% {{ opacity: 1; }} 88% {{ opacity: 1; }} 100% {{ transform: translateX(calc(100vw - 90px)); opacity: 0; }} }}
    .pas-truck-mini {{ position: absolute; left: 0; bottom: 5px; width: 54px; height: 30px; filter: drop-shadow(0 1px 1px rgba(0,0,0,.22)); }}
    .pas-truck-bed {{ position:absolute; left:0; top:5px; width:34px; height:19px; background:#FFD400; border:3px solid #0A0A0A; border-radius:4px 2px 3px 5px; transform:skewX(-10deg); }}
    .pas-truck-logo {{ position:absolute; left:7px; top:9px; font-size:9px; font-weight:950; color:#0A0A0A; line-height:1; z-index:3; }}
    .pas-truck-cab {{ position:absolute; left:30px; top:7px; width:19px; height:18px; background:#FFD400; border:3px solid #0A0A0A; border-radius:3px 5px 3px 2px; z-index:2; }}
    .pas-truck-window {{ position:absolute; left:34px; top:10px; width:7px; height:7px; background:#a8d8e8; border:2px solid #0A0A0A; border-radius:2px; z-index:4; }}
    .pas-truck-nose {{ position:absolute; left:47px; top:17px; width:8px; height:8px; background:#FFD400; border:3px solid #0A0A0A; border-left:none; border-radius:0 3px 3px 0; }}
    .pas-wheel {{ position:absolute; bottom:0; width:9px; height:9px; background:#0A0A0A; border:2px solid #222; border-radius:50%; animation: pas-wheel-spin .32s linear infinite; z-index:5; }}
    .pas-wheel::after {{ content:""; position:absolute; inset:2px; background:#FFD400; border-radius:50%; }}
    .pas-wheel.back {{ left:13px; }} .pas-wheel.front {{ left:41px; }} @keyframes pas-wheel-spin {{ to {{ transform: rotate(360deg); }} }}
    .pas-stickman {{ position:absolute; left:92px; bottom:5px; width:28px; height:34px; animation:pas-runner-bob .35s ease-in-out infinite alternate; }}
    @keyframes pas-runner-bob {{ from {{ transform:translateY(1px); }} to {{ transform:translateY(-2px); }} }}
    .pas-stick-head {{ position:absolute; top:0; left:11px; width:8px; height:8px; border:2px solid #111; border-radius:50%; background:white; }}
    .pas-stick-body {{ position:absolute; left:15px; top:9px; width:2px; height:13px; background:#111; transform:rotate(12deg); transform-origin:top; }}
    .pas-stick-arm-a,.pas-stick-arm-b,.pas-stick-leg-a,.pas-stick-leg-b {{ position:absolute; width:2px; height:12px; background:#111; transform-origin:top; border-radius:2px; }}
    .pas-stick-arm-a {{ left:15px; top:11px; transform:rotate(58deg); animation:pas-arm-a .35s linear infinite alternate; }}
    .pas-stick-arm-b {{ left:15px; top:11px; transform:rotate(-50deg); animation:pas-arm-b .35s linear infinite alternate; }}
    .pas-stick-leg-a {{ left:16px; top:21px; height:14px; transform:rotate(48deg); animation:pas-leg-a .35s linear infinite alternate; }}
    .pas-stick-leg-b {{ left:16px; top:21px; height:14px; transform:rotate(-42deg); animation:pas-leg-b .35s linear infinite alternate; }}
    @keyframes pas-arm-a {{ to {{ transform:rotate(-45deg); }} }} @keyframes pas-arm-b {{ to {{ transform:rotate(55deg); }} }} @keyframes pas-leg-a {{ to {{ transform:rotate(-45deg); }} }} @keyframes pas-leg-b {{ to {{ transform:rotate(48deg); }} }}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.image("pas_logo.png", use_container_width=True)
    st.markdown(
        """
        <div class="pas-sidebar-title">PAS Live Cost<br>Dashboard</div>
        <div class="pas-yellow-line"></div>
        <div class="pas-sidebar-copy">Upload the weekly cost spreadsheets, then export a clean live cost report by site.</div>
        <div class="pas-sidebar-rule"></div>
        <div class="pas-sidebar-heading">Instructions</div>
        <div class="pas-nav-row"><span class="pas-nav-icon"><svg viewBox="0 0 24 24"><path d="M16 16l-4-4-4 4"/><path d="M12 12v9"/><path d="M20 16.6A5 5 0 0 0 18 7h-1.3A8 8 0 1 0 4 15.3"/></svg></span><span>Upload Materials & Plant<br>Spreadsheet</span></div>
        <div class="pas-nav-row"><span class="pas-nav-icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M9 13h6"/><path d="M9 17h6"/></svg></span><span>Upload Vehicles, Labour<br>and Forecast Spreadsheets</span></div>
        <div class="pas-nav-row"><span class="pas-nav-icon"><svg viewBox="0 0 24 24"><path d="M5 3l14 9-14 9V3z"/></svg></span><span>Build Live Cost Report</span></div>
        <div class="pas-nav-row"><span class="pas-nav-icon"><svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg></span><span>Download Excel<br>Spreadsheet</span></div>
        <div class="pas-nav-row"><span class="pas-nav-icon"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/></svg></span><span>Smoke Crack</span></div>
        <div class="pas-sidebar-rule"></div>
        <div class="pas-sidebar-footer">PAS NW Ltd • v1.0 Prototype Build</div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="pas-hero">
      <div class="pas-hero-logo">PAS</div>
      <div class="pas-hero-text">PAS Live Cost Dashboard<span class="pas-hero-dot">•</span><span class="pas-hero-version">v1.0 Prototype Build</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)


def render_bottom_chase():
    st.markdown(
        """
        <div class="pas-bottom-chase-wrap" aria-hidden="true">
            <div class="pas-bottom-ground"></div>
            <div class="pas-chase-pack">
                <div class="pas-truck-mini">
                    <div class="pas-truck-bed"></div><div class="pas-truck-logo">PAS</div><div class="pas-truck-cab"></div>
                    <div class="pas-truck-window"></div><div class="pas-truck-nose"></div><div class="pas-wheel back"></div><div class="pas-wheel front"></div>
                </div>
                <div class="pas-stickman"><div class="pas-stick-head"></div><div class="pas-stick-body"></div><div class="pas-stick-arm-a"></div><div class="pas-stick-arm-b"></div><div class="pas-stick-leg-a"></div><div class="pas-stick-leg-b"></div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _file_size_label(uploaded_file):
    try:
        pos = uploaded_file.tell()
        uploaded_file.seek(0, 2)
        size = uploaded_file.tell()
        uploaded_file.seek(pos)
    except Exception:
        size = getattr(uploaded_file, "size", 0) or 0
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def render_selected_file_card(uploaded_file):
    if not uploaded_file:
        return
    name = escape(getattr(uploaded_file, "name", "Uploaded file"))
    size = escape(_file_size_label(uploaded_file))
    st.markdown(
        f"""
        <div class="pas-file-card">
            <div class="pas-file-icon excel">XLS</div>
            <div class="pas-file-main"><div class="pas-file-name">{name}</div><div class="pas-file-size">{size}</div></div>
            <div class="pas-file-check">✓</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(label, value, sub=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon"><svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-7"/></svg></div>
            <div><div class="kpi-label">{escape(label)}</div><div class="kpi-value">{escape(str(value))}</div><div class="kpi-sub">{escape(sub)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_table(df, max_rows=None):
    if df is None or df.empty:
        st.info("No records to display.")
        return
    shown = df.head(max_rows).copy() if max_rows else df.copy()
    html = shown.to_html(index=False, escape=False, classes="pas-table")
    st.markdown(f'<div class="pas-table-wrap">{html}</div>', unsafe_allow_html=True)

COST_CATEGORIES = [
    "Labour",
    "Plant",
    "Materials",
    "Muck Away",
    "Subbies",
    "Vehicles",
    "Fuel Card",
    "Site Fuel",
]

FORECAST_RENAME = {
    "job": "Job",
    "job no": "Job",
    "job no.": "Job",
    "material": "Materials",
    "materials": "Materials",
    "vans": "Vehicles",
    "van": "Vehicles",
    "vehicles": "Vehicles",
    "subby": "Subbies",
    "subbies": "Subbies",
    "muck away": "Muck Away",
    "site fuel": "Site Fuel",
    "fuel card": "Fuel Card",
    "overhead": "Overhead",
    "profit": "Profit",
    "labour": "Labour",
    "plant": "Plant",
}

# England & Wales bank holidays relevant to the current programme.
# Add future years here if needed.
UK_BANK_HOLIDAYS = {
    date(2025, 1, 1), date(2025, 4, 18), date(2025, 4, 21), date(2025, 5, 5),
    date(2025, 5, 26), date(2025, 8, 25), date(2025, 12, 25), date(2025, 12, 26),
    date(2026, 1, 1), date(2026, 4, 3), date(2026, 4, 6), date(2026, 5, 4),
    date(2026, 5, 25), date(2026, 8, 31), date(2026, 12, 25), date(2026, 12, 28),
    date(2027, 1, 1), date(2027, 3, 26), date(2027, 3, 29), date(2027, 5, 3),
    date(2027, 5, 31), date(2027, 8, 30), date(2027, 12, 27), date(2027, 12, 28),
}


def clean_col(col):
    if col is None:
        return ""
    return re.sub(r"\s+", " ", str(col).strip())


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).strip().lower()).strip()


def money(x):
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float, np.number)):
        return float(x)
    text = str(x).strip()
    if not text:
        return 0.0
    text = text.replace("£", "").replace(",", "").replace(" ", "")
    text = text.replace("−", "-")
    # Handle values like £12102,12 where comma may have been used as decimal.
    if re.match(r"^-?\d+,\d{1,2}$", str(x).replace("£", "").replace(" ", "")):
        text = str(x).replace("£", "").replace(" ", "").replace(",", ".")
    try:
        return float(text)
    except Exception:
        return 0.0


def to_date(value):
    if pd.isna(value) or value == "":
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return value.normalize()
    if isinstance(value, datetime):
        return pd.Timestamp(value.date())
    if isinstance(value, date):
        return pd.Timestamp(value)
    return pd.to_datetime(value, errors="coerce", dayfirst=True)


def month_start(value):
    d = to_date(value)
    if pd.isna(d):
        return pd.NaT
    return pd.Timestamp(date(d.year, d.month, 1))


def month_label(value):
    d = to_date(value)
    if pd.isna(d):
        return "Unknown"
    return d.strftime("%b %Y")


def end_of_month(d):
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def find_col(df, candidates, required=False):
    cols = {norm(c): c for c in df.columns}
    for cand in candidates:
        nc = norm(cand)
        if nc in cols:
            return cols[nc]
    # fuzzy contains fallback
    for cand in candidates:
        nc = norm(cand)
        for key, original in cols.items():
            if nc and (nc in key or key in nc):
                return original
    if required:
        raise KeyError(f"Missing required column. Tried: {candidates}")
    return None


def load_sheet(upload, sheet_name):
    try:
        df = pd.read_excel(upload, sheet_name=sheet_name)
        df.columns = [clean_col(c) for c in df.columns]
        df = df.dropna(how="all")
        return df
    except Exception:
        return pd.DataFrame()


def add_issue(issues, source, row_ref, job, issue, detail=""):
    issues.append({
        "Source": source,
        "Row": row_ref,
        "Job": "" if pd.isna(job) else str(job).strip(),
        "Issue": issue,
        "Detail": detail,
    })


def weekdays_between(start, end, exclude_bank_holidays=True):
    start = to_date(start)
    end = to_date(end)
    if pd.isna(start) or pd.isna(end) or end < start:
        return 0
    count = 0
    current = start.date()
    finish = end.date()
    while current <= finish:
        if current.weekday() < 5:
            if exclude_bank_holidays and current in UK_BANK_HOLIDAYS:
                pass
            else:
                count += 1
        current += timedelta(days=1)
    return count


def calendar_days_between(start, end):
    start = to_date(start)
    end = to_date(end)
    if pd.isna(start) or pd.isna(end) or end < start:
        return 0
    return (end.date() - start.date()).days + 1


def split_period_by_month(start, end):
    start = to_date(start)
    end = to_date(end)
    if pd.isna(start) or pd.isna(end) or end < start:
        return []
    periods = []
    cur = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cur <= last:
        m_start = cur
        m_end = end_of_month(cur)
        seg_start = max(start.date(), m_start)
        seg_end = min(end.date(), m_end)
        if seg_start <= seg_end:
            periods.append((pd.Timestamp(seg_start), pd.Timestamp(seg_end), pd.Timestamp(m_start)))
        cur = date(cur.year + (cur.month // 12), (cur.month % 12) + 1, 1)
    return periods


def normalise_job(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper().replace(" ", "")


def read_sites(material_file, labour_file=None):
    sites = {}
    for file_obj, sheet in [(material_file, "Sites"), (labour_file, "Sites")]:
        if file_obj is None:
            continue
        df = load_sheet(file_obj, sheet)
        if df.empty:
            continue
        job_col = find_col(df, ["Job No", "Job", "Job No."])
        site_col = find_col(df, ["Address", "Site", "Site Name"])
        if not job_col or not site_col:
            continue
        for _, row in df.iterrows():
            job = normalise_job(row.get(job_col))
            if job and job not in sites:
                sites[job] = str(row.get(site_col, "")).strip()
    return sites


def process_forecast(forecast_file, issues):
    df = load_sheet(forecast_file, "Forecast")
    if df.empty:
        add_issue(issues, "Forecast", "", "", "Forecast tab missing or empty")
        return pd.DataFrame(columns=["Job"] + COST_CATEGORIES + ["Overhead", "Profit"])

    renamed = {}
    for c in df.columns:
        key = norm(c)
        renamed[c] = FORECAST_RENAME.get(key, clean_col(c))
    df = df.rename(columns=renamed)

    if "Job" not in df.columns:
        add_issue(issues, "Forecast", "", "", "Missing Job column")
        return pd.DataFrame(columns=["Job"] + COST_CATEGORIES + ["Overhead", "Profit"])

    keep_cols = ["Job"] + COST_CATEGORIES + ["Overhead", "Profit"]
    for c in keep_cols:
        if c not in df.columns:
            df[c] = 0
            if c != "Job":
                add_issue(issues, "Forecast", "Header", "", f"Missing forecast column: {c}", "Filled as zero")

    out = df[keep_cols].copy()
    out["Job"] = out["Job"].apply(normalise_job)
    out = out[out["Job"] != ""]
    for c in keep_cols[1:]:
        out[c] = out[c].apply(money)
    return out.groupby("Job", as_index=False).sum(numeric_only=True)


def record(source, job, site, category, cost, cost_date, description="", supplier="", ref=""):
    return {
        "Source": source,
        "Job": normalise_job(job),
        "Site": "" if pd.isna(site) else str(site).strip(),
        "Category": category,
        "Cost": float(cost or 0),
        "Cost Date": to_date(cost_date),
        "Month": month_start(cost_date),
        "Month Label": month_label(cost_date),
        "Description": "" if pd.isna(description) else str(description).strip(),
        "Supplier": "" if pd.isna(supplier) else str(supplier).strip(),
        "Reference": "" if pd.isna(ref) else str(ref).strip(),
    }


def process_material_like(material_file, sheet_name, default_category, issues):
    df = load_sheet(material_file, sheet_name)
    rows = []
    if df.empty:
        return rows

    job_col = find_col(df, ["Job No.", "Job No", "Job"])
    site_col = find_col(df, ["Site Name", "Site", "Address"])
    desc_col = find_col(df, ["Description", "Item Description"])
    qty_col = find_col(df, ["Qty", "Ordered Qty", "Quantity"])
    cost_col = find_col(df, ["Cost", "Rate", "Unit Cost"])
    total_col = find_col(df, ["Total", "Total Cost", "Value", "Line Value"])
    supplier_col = find_col(df, ["Supplier", "Vendor"])
    deliv_col = find_col(df, ["Delivery Date", "Date Delivered", "Start Date"])
    ref_col = find_col(df, ["Sage Order No", "Order Number", "PO", "Sage Order No."])

    for idx, row in df.iterrows():
        excel_row = idx + 2
        job = row.get(job_col) if job_col else ""
        job_norm = normalise_job(job)
        desc = row.get(desc_col, "") if desc_col else ""
        d = row.get(deliv_col) if deliv_col else pd.NaT
        if not job_norm:
            add_issue(issues, sheet_name, excel_row, job, "Missing Job Number")
            continue
        if pd.isna(to_date(d)):
            add_issue(issues, sheet_name, excel_row, job, "Missing or invalid delivery/start date")
            continue

        if total_col and not pd.isna(row.get(total_col)):
            value = money(row.get(total_col))
        else:
            qty = money(row.get(qty_col)) if qty_col else 1
            unit_cost = money(row.get(cost_col)) if cost_col else 0
            value = qty * unit_cost

        desc_norm = norm(desc)
        if "muck away" in desc_norm:
            category = "Muck Away"
        elif sheet_name.lower() == "materials" and "diesel" in desc_norm:
            category = "Site Fuel"
        else:
            category = default_category

        if value == 0:
            add_issue(issues, sheet_name, excel_row, job, "Zero or missing cost", str(desc))

        rows.append(record(
            sheet_name, job, row.get(site_col, "") if site_col else "", category, value, d,
            description=desc,
            supplier=row.get(supplier_col, "") if supplier_col else "",
            ref=row.get(ref_col, "") if ref_col else "",
        ))
    return rows


def process_subbies(material_file, issues):
    df = load_sheet(material_file, "Subby")
    rows = []
    if df.empty:
        return rows
    job_col = find_col(df, ["Job No.", "Job No", "Job"])
    site_col = find_col(df, ["Site Name", "Site", "Address"])
    desc_col = find_col(df, ["Description", "Item Description"])
    qty_col = find_col(df, ["Qty", "Quantity"])
    cost_col = find_col(df, ["Cost", "Value", "Total", "Line Value"])
    supplier_col = find_col(df, ["Supplier", "Vendor"])
    start_col = find_col(df, ["Start Date", "Delivery Date", "Date"])
    ref_col = find_col(df, ["Sage Order No", "Order Number", "PO"])

    for idx, row in df.iterrows():
        excel_row = idx + 2
        job = row.get(job_col) if job_col else ""
        job_norm = normalise_job(job)
        d = row.get(start_col) if start_col else pd.NaT
        if not job_norm:
            add_issue(issues, "Subby", excel_row, job, "Missing Job Number")
            continue
        if pd.isna(to_date(d)):
            add_issue(issues, "Subby", excel_row, job, "Missing or invalid start date")
            continue
        qty = money(row.get(qty_col)) if qty_col else 1
        value = money(row.get(cost_col)) * (qty if qty_col else 1)
        rows.append(record(
            "Subby", job, row.get(site_col, "") if site_col else "", "Subbies", value, d,
            description=row.get(desc_col, "") if desc_col else "",
            supplier=row.get(supplier_col, "") if supplier_col else "",
            ref=row.get(ref_col, "") if ref_col else "",
        ))
    return rows


def process_plant(material_file, report_date, issues):
    df = load_sheet(material_file, "Plant")
    rows = []
    if df.empty:
        return rows
    job_col = find_col(df, ["Job No", "Job No.", "Job"])
    site_col = find_col(df, ["Site Name", "Site", "Address"])
    desc_col = find_col(df, ["Description", "Item Description"])
    supplier_col = find_col(df, ["Supplier", "Vendor"])
    weekly_col = find_col(df, ["Cost", "Weekly Rate", "Weekly Cost", "Rate"])
    on_col = find_col(df, ["On Hire / Delivery Date", "On Hire Date", "Delivery Date"])
    off_col = find_col(df, ["Off Hire Date", "Off-Hire Date", "Date Off Hired"])
    order_col = find_col(df, ["Order Number", "Sage Order No", "PO"])

    for idx, row in df.iterrows():
        excel_row = idx + 2
        job = row.get(job_col) if job_col else ""
        job_norm = normalise_job(job)
        if not job_norm:
            add_issue(issues, "Plant", excel_row, job, "Missing Job Number")
            continue
        on = to_date(row.get(on_col)) if on_col else pd.NaT
        off = to_date(row.get(off_col)) if off_col and not pd.isna(row.get(off_col)) else pd.Timestamp(report_date)
        if pd.isna(on):
            add_issue(issues, "Plant", excel_row, job, "Missing or invalid on-hire date")
            continue
        if off < on:
            add_issue(issues, "Plant", excel_row, job, "Off-hire date before on-hire date")
            continue
        weekly = money(row.get(weekly_col)) if weekly_col else 0
        if weekly == 0:
            add_issue(issues, "Plant", excel_row, job, "Missing weekly rate", str(row.get(desc_col, "")))
            continue
        daily = weekly / 5
        for seg_start, seg_end, m in split_period_by_month(on, off):
            charge_days = weekdays_between(seg_start, seg_end, exclude_bank_holidays=True)
            if charge_days > 0:
                rows.append(record(
                    "Plant", job, row.get(site_col, "") if site_col else "", "Plant", daily * charge_days, m,
                    description=row.get(desc_col, "") if desc_col else "",
                    supplier=row.get(supplier_col, "") if supplier_col else "",
                    ref=row.get(order_col, "") if order_col else "",
                ))
    return rows


def process_labour(labour_file, issues):
    df = load_sheet(labour_file, "Labour")
    rows = []
    if df.empty:
        add_issue(issues, "Labour", "", "", "Labour tab missing or empty")
        return rows
    job_col = find_col(df, ["Job No", "Job No.", "Job"])
    site_col = find_col(df, ["Site", "Site Name", "Address"])
    date_col = find_col(df, ["Week Ending", "Date"])
    cost_col = find_col(df, ["Total Cost", "Cost", "Value"])
    operatives_col = find_col(df, ["Operatives", "Men"])
    hours_col = find_col(df, ["Hours", "Total Hours"])

    for idx, row in df.iterrows():
        excel_row = idx + 2
        # skip summary/formula side columns rows without cost/job
        job = row.get(job_col) if job_col else ""
        job_norm = normalise_job(job)
        if not job_norm:
            continue
        d = row.get(date_col) if date_col else pd.NaT
        if pd.isna(to_date(d)):
            add_issue(issues, "Labour", excel_row, job, "Missing or invalid week ending date")
            continue
        value = money(row.get(cost_col)) if cost_col else 0
        if value == 0:
            add_issue(issues, "Labour", excel_row, job, "Zero or missing labour cost")
        desc = f"Operatives: {row.get(operatives_col, '')}; Hours: {row.get(hours_col, '')}"
        rows.append(record(
            "Labour", job, row.get(site_col, "") if site_col else "", "Labour", value, d,
            description=desc,
        ))
    return rows


def process_vehicle_sheet(vehicle_file, report_date, issues):
    if vehicle_file is None:
        return []

    xls = pd.ExcelFile(vehicle_file)
    selected_sheet = None
    for name in xls.sheet_names:
        if norm(name) in ["vehicles", "vehicle", "vehicle sheet", "vans", "hire"]:
            selected_sheet = name
            break
    if selected_sheet is None:
        selected_sheet = xls.sheet_names[0]

    df = pd.read_excel(vehicle_file, sheet_name=selected_sheet)
    df.columns = [clean_col(c) for c in df.columns]
    df = df.dropna(how="all")
    rows = []

    job_col = find_col(df, ["Job No", "Job No.", "Job", "Job Number"])
    site_col = find_col(df, ["Site", "Site Name", "Address"])
    desc_col = find_col(df, ["Description", "Vehicle", "Vehicle Reg", "Reg", "Registration"])
    weekly_col = find_col(df, ["Weekly Cost", "Weekly Rate", "Cost Per Week", "Hire Cost", "Vehicle Cost"])
    on_col = find_col(df, ["On Hire Date", "Start Date", "From", "Date From"])
    off_col = find_col(df, ["Off Hire Date", "End Date", "To", "Date To"])
    fuel_cost_col = find_col(df, ["Fuel Card", "Fuel Cost", "Fuel Spend", "Total Fuel", "Fuel"])
    fuel_date_col = find_col(df, ["Fuel Date", "Transaction Date", "Date", "Week Ending"])

    if not job_col:
        add_issue(issues, "Vehicles", "Header", "", "Missing Job Number column")
        return rows

    for idx, row in df.iterrows():
        excel_row = idx + 2
        job = row.get(job_col)
        job_norm = normalise_job(job)
        if not job_norm:
            add_issue(issues, "Vehicles", excel_row, job, "Missing Job Number")
            continue

        # Vehicle hire cost: 7-day week, bank holidays charged.
        if weekly_col and on_col:
            weekly = money(row.get(weekly_col))
            on = to_date(row.get(on_col))
            off = to_date(row.get(off_col)) if off_col and not pd.isna(row.get(off_col)) else pd.Timestamp(report_date)
            if weekly > 0 and not pd.isna(on) and not pd.isna(off) and off >= on:
                daily = weekly / 7
                for seg_start, seg_end, m in split_period_by_month(on, off):
                    days = calendar_days_between(seg_start, seg_end)
                    if days > 0:
                        rows.append(record(
                            "Vehicles", job, row.get(site_col, "") if site_col else "", "Vehicles", daily * days, m,
                            description=row.get(desc_col, "") if desc_col else "",
                        ))
            elif weekly > 0:
                add_issue(issues, "Vehicles", excel_row, job, "Missing/invalid vehicle hire dates")

        # Fuel card spend from vehicle sheet, allocated by transaction/week date if available.
        if fuel_cost_col:
            fuel_value = money(row.get(fuel_cost_col))
            if fuel_value != 0:
                fuel_date = row.get(fuel_date_col) if fuel_date_col else report_date
                if pd.isna(to_date(fuel_date)):
                    fuel_date = report_date
                    add_issue(issues, "Vehicles", excel_row, job, "Missing fuel date", "Used report date")
                rows.append(record(
                    "Vehicles", job, row.get(site_col, "") if site_col else "", "Fuel Card", fuel_value, fuel_date,
                    description=row.get(desc_col, "") if desc_col else "",
                ))

    return rows


def build_actuals(material_file, labour_file, vehicle_file, report_date, issues):
    rows = []
    rows += process_material_like(material_file, "Materials", "Materials", issues)
    rows += process_material_like(material_file, "Agg-Conc", "Materials", issues)
    rows += process_subbies(material_file, issues)
    rows += process_plant(material_file, report_date, issues)
    rows += process_labour(labour_file, issues)
    rows += process_vehicle_sheet(vehicle_file, report_date, issues)
    if not rows:
        return pd.DataFrame(columns=["Source", "Job", "Site", "Category", "Cost", "Cost Date", "Month", "Month Label", "Description", "Supplier", "Reference"])
    out = pd.DataFrame(rows)
    out = out[out["Job"] != ""].copy()
    return out


def format_currency(v):
    try:
        return f"£{float(v):,.0f}"
    except Exception:
        return "£0"


def build_summary(actuals, forecast, sites):
    actual_pivot = actuals.pivot_table(index="Job", columns="Category", values="Cost", aggfunc="sum", fill_value=0).reset_index() if not actuals.empty else pd.DataFrame(columns=["Job"])
    forecast_pivot = forecast.copy()
    for c in COST_CATEGORIES:
        if c not in actual_pivot.columns:
            actual_pivot[c] = 0
        if c not in forecast_pivot.columns:
            forecast_pivot[c] = 0
    for c in ["Overhead", "Profit"]:
        if c not in forecast_pivot.columns:
            forecast_pivot[c] = 0

    jobs = sorted(set(actual_pivot.get("Job", pd.Series(dtype=str))).union(set(forecast_pivot.get("Job", pd.Series(dtype=str)))))
    base = pd.DataFrame({"Job": jobs})
    base["Site"] = base["Job"].map(sites).fillna("")

    a = actual_pivot[["Job"] + COST_CATEGORIES].rename(columns={c: f"Actual {c}" for c in COST_CATEGORIES})
    f = forecast_pivot[["Job"] + COST_CATEGORIES + ["Overhead", "Profit"]].rename(columns={c: f"Forecast {c}" for c in COST_CATEGORIES})

    summary = base.merge(f, on="Job", how="left").merge(a, on="Job", how="left")
    for col in summary.columns:
        if col.startswith("Forecast ") or col.startswith("Actual ") or col in ["Overhead", "Profit"]:
            summary[col] = summary[col].fillna(0)

    summary["Overall Forecast"] = summary[[f"Forecast {c}" for c in COST_CATEGORIES]].sum(axis=1) + summary["Overhead"] + summary["Profit"]
    summary["Actual Cost"] = summary[[f"Actual {c}" for c in COST_CATEGORIES]].sum(axis=1)
    summary["Live Variance"] = summary["Overall Forecast"] - summary["Actual Cost"]
    summary["Profit %"] = np.where(summary["Overall Forecast"] != 0, summary["Profit"] / summary["Overall Forecast"], 0)

    display_cols = ["Job", "Site", "Overall Forecast", "Actual Cost", "Live Variance", "Profit", "Profit %"]
    display_cols += [f"Forecast {c}" for c in COST_CATEGORIES]
    display_cols += [f"Actual {c}" for c in COST_CATEGORIES]
    display_cols += ["Overhead"]
    return summary[display_cols].sort_values("Job")


def build_monthly(actuals):
    if actuals.empty:
        return pd.DataFrame(columns=["Job", "Month", "Month Label", "Category", "Cost"])
    monthly = actuals.groupby(["Job", "Month", "Month Label", "Category"], dropna=False, as_index=False)["Cost"].sum()
    monthly = monthly.sort_values(["Month", "Job", "Category"])
    return monthly


def excel_export(summary, monthly, raw, issues):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="dd/mm/yyyy", date_format="dd/mm/yyyy") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        monthly.to_excel(writer, sheet_name="Monthly Breakdown", index=False)
        raw.to_excel(writer, sheet_name="Raw Data", index=False)
        pd.DataFrame(issues).to_excel(writer, sheet_name="Issues", index=False)

        workbook = writer.book
        header_fmt = workbook.add_format({"bold": True, "bg_color": "#FFD400", "font_color": "#111111", "border": 1})
        money_fmt = workbook.add_format({"num_format": "£#,##0", "border": 1})
        pct_fmt = workbook.add_format({"num_format": "0.0%", "border": 1})
        body_fmt = workbook.add_format({"border": 1})

        for sheet_name, df in [("Summary", summary), ("Monthly Breakdown", monthly), ("Raw Data", raw), ("Issues", pd.DataFrame(issues))]:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            ws.set_row(0, 24, header_fmt)
            for i, col in enumerate(df.columns):
                width = min(max(len(str(col)) + 3, 12), 34)
                if "Description" in str(col):
                    width = 36
                if "Cost" in str(col) or "Forecast" in str(col) or "Profit" in str(col) or "Variance" in str(col) or col in ["Overhead"]:
                    ws.set_column(i, i, width, money_fmt)
                elif "%" in str(col):
                    ws.set_column(i, i, width, pct_fmt)
                else:
                    ws.set_column(i, i, width, body_fmt)

        # One tab per site/job
        for _, srow in summary.iterrows():
            job = srow["Job"]
            tab = str(job)[:31]
            site_detail = []
            for cat in COST_CATEGORIES:
                forecast_col = f"Forecast {cat}"
                actual_col = f"Actual {cat}"
                # Forecast columns are not in displayed summary, recover from raw merge not available here -> leave blank if missing.
                forecast_val = srow.get(forecast_col, np.nan)
                actual_val = srow.get(actual_col, 0)
                site_detail.append({
                    "Category": cat,
                    "Forecast": forecast_val if not pd.isna(forecast_val) else "",
                    "Actual": actual_val,
                    "Variance": (forecast_val - actual_val) if not pd.isna(forecast_val) and forecast_val != "" else "",
                })
            site_df = pd.DataFrame(site_detail)
            site_df.to_excel(writer, sheet_name=tab, index=False, startrow=2)
            ws = writer.sheets[tab]
            ws.write(0, 0, f"{job} - {srow.get('Site', '')}", workbook.add_format({"bold": True, "font_size": 14}))
            ws.set_row(2, 24, header_fmt)
            ws.set_column(0, 0, 20, body_fmt)
            ws.set_column(1, 3, 15, money_fmt)

    output.seek(0)
    return output



# ============================================================
# PAS Live Cost UI
# ============================================================

up1, up2 = st.columns(2)
with up1:
    st.markdown('<div class="pas-upload-card"><div class="pas-upload-title">Materials & Plant Spreadsheet</div>', unsafe_allow_html=True)
    material_file = st.file_uploader("Materials & Plant Spreadsheet", type=["xlsx", "xlsm", "xls"], label_visibility="collapsed", key="materials")
    if material_file:
        render_selected_file_card(material_file)
    st.markdown('</div>', unsafe_allow_html=True)
with up2:
    st.markdown('<div class="pas-upload-card"><div class="pas-upload-title">Vehicles Spreadsheet</div>', unsafe_allow_html=True)
    vehicle_file = st.file_uploader("Vehicles Spreadsheet", type=["xlsx", "xlsm", "xls"], label_visibility="collapsed", key="vehicles")
    if vehicle_file:
        render_selected_file_card(vehicle_file)
    st.markdown('</div>', unsafe_allow_html=True)

up3, up4 = st.columns(2)
with up3:
    st.markdown('<div class="pas-upload-card"><div class="pas-upload-title">Labour Spreadsheet</div>', unsafe_allow_html=True)
    labour_file = st.file_uploader("Labour Spreadsheet", type=["xlsx", "xlsm", "xls"], label_visibility="collapsed", key="labour")
    if labour_file:
        render_selected_file_card(labour_file)
    st.markdown('</div>', unsafe_allow_html=True)
with up4:
    st.markdown('<div class="pas-upload-card"><div class="pas-upload-title">Forecast Spreadsheet</div>', unsafe_allow_html=True)
    forecast_file = st.file_uploader("Forecast Spreadsheet", type=["xlsx", "xlsm", "xls"], label_visibility="collapsed", key="forecast")
    if forecast_file:
        render_selected_file_card(forecast_file)
    st.markdown('</div>', unsafe_allow_html=True)

report_date = st.date_input("Report / upload date", value=date.today(), help="Plant with no off-hire date and vehicles with no end date are costed up to this date.")
run = st.button("▶  Build Live Cost Report", use_container_width=True)

if "live_cost_results" not in st.session_state:
    st.session_state["live_cost_results"] = None

if run:
    if not all([material_file, labour_file, forecast_file]):
        st.warning("Please upload the Materials & Plant Spreadsheet, Labour Spreadsheet and Forecast Spreadsheet. Vehicles Spreadsheet is optional for first testing.")
        render_bottom_chase()
        st.stop()
    try:
        issues = []
        with st.spinner("Reading site data..."):
            sites = read_sites(material_file, labour_file)
        with st.spinner("Reading forecast spreadsheet..."):
            forecast = process_forecast(forecast_file, issues)
        with st.spinner("Calculating actual costs..."):
            actuals = build_actuals(material_file, labour_file, vehicle_file, report_date, issues)
        if not actuals.empty:
            actuals["Site"] = actuals.apply(lambda r: r["Site"] if str(r["Site"]).strip() else sites.get(r["Job"], ""), axis=1)
        summary = build_summary(actuals, forecast, sites)
        monthly = build_monthly(actuals)
        st.session_state["live_cost_results"] = {
            "issues": issues,
            "sites": sites,
            "forecast": forecast,
            "actuals": actuals,
            "summary": summary,
            "monthly": monthly,
        }
    except Exception as exc:
        st.error(f"Could not build the report: {exc}")
        render_bottom_chase()
        st.stop()

if not st.session_state["live_cost_results"]:
    st.info("Upload the four weekly files and press Build Live Cost Report to populate the dashboard.")
    render_bottom_chase()
    st.stop()

results = st.session_state["live_cost_results"]
issues = results["issues"]
actuals = results["actuals"]
summary = results["summary"]
monthly = results["monthly"]

forecast_total = summary["Overall Forecast"].sum() if not summary.empty else 0
actual_total = summary["Actual Cost"].sum() if not summary.empty else 0
profit_total = summary["Profit"].sum() if not summary.empty else 0
variance_total = summary["Live Variance"].sum() if not summary.empty else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Overall Forecast", format_currency(forecast_total), "Forecast total across all sites")
with k2:
    render_kpi("Actual Cost", format_currency(actual_total), "Actual spend from uploads")
with k3:
    render_kpi("Forecast Profit", format_currency(profit_total), "Profit from Forecast Spreadsheet")
with k4:
    render_kpi("Live Variance", format_currency(variance_total), "Forecast minus actual")

st.markdown('<div class="pas-results-title">Live Cost Results</div>', unsafe_allow_html=True)
st.markdown('<div class="pas-unmatched-pill">Site Summary</div>', unsafe_allow_html=True)
summary_display_cols = ["Job", "Site", "Overall Forecast", "Actual Cost", "Live Variance", "Profit", "Profit %"]
summary_display = summary[summary_display_cols].copy() if not summary.empty else pd.DataFrame(columns=summary_display_cols)
for c in summary_display.columns:
    if c == "Profit %":
        summary_display[c] = summary_display[c].map(lambda x: f"{x:.1%}" if pd.notna(x) else "")
    elif c not in ["Job", "Site"]:
        summary_display[c] = summary_display[c].map(format_currency)
render_table(summary_display)

st.markdown('<div class="pas-unmatched-pill">S-Curve: Cumulative Actual Cost</div>', unsafe_allow_html=True)
if not monthly.empty:
    curve = monthly.groupby("Month", as_index=False)["Cost"].sum().sort_values("Month")
    curve["Cumulative Actual"] = curve["Cost"].cumsum()
    curve["Month Label"] = curve["Month"].dt.strftime("%b %Y")
    curve["Overall Forecast"] = forecast_total
    fig = px.line(
        curve,
        x="Month Label",
        y=["Cumulative Actual", "Overall Forecast"],
        markers=True,
        labels={"value": "Cost", "Month Label": "Month", "variable": "Measure"},
        title="Cumulative Actual vs Overall Forecast",
    )
    fig.update_layout(legend_title_text="", hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No monthly costs found to build an S-curve.")

left, right = st.columns([2, 1])
with left:
    st.markdown('<div class="pas-unmatched-pill">Monthly Breakdown</div>', unsafe_allow_html=True)
    if not monthly.empty:
        monthly_display = monthly.copy()
        monthly_display["Month"] = monthly_display["Month"].dt.strftime("%d/%m/%Y")
        monthly_display["Cost"] = monthly_display["Cost"].map(format_currency)
        render_table(monthly_display, max_rows=200)
with right:
    st.markdown('<div class="pas-unmatched-pill">Issues</div>', unsafe_allow_html=True)
    issue_df = pd.DataFrame(issues)
    if issue_df.empty:
        st.success("No issues found.")
    else:
        render_table(issue_df, max_rows=100)

st.markdown('<div class="pas-unmatched-pill">Download Report</div>', unsafe_allow_html=True)
export_bytes = excel_export(summary, monthly, actuals, issues)
st.download_button(
    "Download Excel Report",
    data=export_bytes,
    file_name=f"PAS_Live_Cost_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

with st.expander("Raw imported cost records"):
    raw_display = actuals.copy()
    if not raw_display.empty:
        raw_display["Cost Date"] = pd.to_datetime(raw_display["Cost Date"], errors="coerce").dt.strftime("%d/%m/%Y")
        raw_display["Month"] = pd.to_datetime(raw_display["Month"], errors="coerce").dt.strftime("%d/%m/%Y")
        raw_display["Cost"] = raw_display["Cost"].map(format_currency)
    render_table(raw_display, max_rows=300)

render_bottom_chase()
