import calendar
from datetime import date, datetime, timedelta
from io import BytesIO
import re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# PAS LIVE COST DASHBOARD
# Four uploads:
# 1. Materials & Plant Orders
# 2. Labour Cost Sheet
# 3. Vehicle Sheet
# 4. Forecast Template
# ============================================================

st.set_page_config(
    page_title="PAS Live Cost Dashboard",
    page_icon="🏗️",
    layout="wide",
)

PAS_YELLOW = "#ffd400"
PAS_BLACK = "#111111"
PAS_GREY = "#f4f4f4"

st.markdown(
    f"""
    <style>
        .main {{ background-color: #ffffff; }}
        .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
        .pas-hero {{
            background: linear-gradient(135deg, #111111 0%, #2d2d2d 100%);
            border-left: 10px solid {PAS_YELLOW};
            padding: 24px 28px;
            border-radius: 18px;
            color: white;
            margin-bottom: 18px;
        }}
        .pas-hero h1 {{ margin: 0; font-size: 2.2rem; font-weight: 800; }}
        .pas-hero p {{ margin: 8px 0 0 0; color: #e6e6e6; font-size: 1rem; }}
        .kpi-card {{
            background: #111111;
            color: white;
            border-radius: 16px;
            padding: 20px 18px;
            min-height: 118px;
            border-bottom: 6px solid #ffd400;
        }}
        .kpi-label {{ font-size: 0.85rem; color: #d7d7d7; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 1.7rem; font-weight: 800; }}
        .section-title {{
            background: #ffd400;
            color: #111111;
            padding: 10px 14px;
            border-radius: 10px;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 10px;
        }}
        div[data-testid="stDataFrame"] {{ border: 1px solid #e6e6e6; border-radius: 10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="pas-hero">
        <h1>PAS Live Cost Dashboard</h1>
        <p>Upload the four weekly cost files to build a site-by-site forecast vs actual dashboard and Excel report.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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


with st.sidebar:
    st.markdown("### Upload weekly files")
    material_file = st.file_uploader("1. Materials & Plant Orders", type=["xlsx", "xlsm", "xls"], key="materials")
    labour_file = st.file_uploader("2. Labour Cost Sheet", type=["xlsx", "xlsm", "xls"], key="labour")
    vehicle_file = st.file_uploader("3. Vehicle Sheet", type=["xlsx", "xlsm", "xls"], key="vehicles")
    forecast_file = st.file_uploader("4. Forecast Template", type=["xlsx", "xlsm", "xls"], key="forecast")
    report_date = st.date_input("Report / upload date", value=date.today())
    st.caption("Plant with no off-hire date and vehicles with no end date are costed up to this date.")

if not all([material_file, labour_file, forecast_file]):
    st.info("Upload the Materials & Plant Orders, Labour Cost Sheet and Forecast Template to build the dashboard. Vehicle Sheet is optional for first testing, but needed for vehicle and fuel card costs.")
    st.stop()

issues = []
sites = read_sites(material_file, labour_file)
forecast = process_forecast(forecast_file, issues)
actuals = build_actuals(material_file, labour_file, vehicle_file, report_date, issues)

# Fill site names from site master where source rows are blank.
if not actuals.empty:
    actuals["Site"] = actuals.apply(lambda r: r["Site"] if str(r["Site"]).strip() else sites.get(r["Job"], ""), axis=1)

summary = build_summary(actuals, forecast, sites)
monthly = build_monthly(actuals)

# KPI cards
forecast_total = summary["Overall Forecast"].sum() if not summary.empty else 0
actual_total = summary["Actual Cost"].sum() if not summary.empty else 0
profit_total = summary["Profit"].sum() if not summary.empty else 0
variance_total = summary["Live Variance"].sum() if not summary.empty else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
for col, label, value in [
    (kpi1, "Overall Forecast", forecast_total),
    (kpi2, "Actual Cost", actual_total),
    (kpi3, "Forecast Profit", profit_total),
    (kpi4, "Live Variance", variance_total),
]:
    with col:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>{label}</div><div class='kpi-value'>{format_currency(value)}</div></div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Site Summary</div>", unsafe_allow_html=True)
# Keep the on-screen summary concise. The Excel export contains the full forecast/actual detail.
summary_display_cols = ["Job", "Site", "Overall Forecast", "Actual Cost", "Live Variance", "Profit", "Profit %"]
summary_display = summary[summary_display_cols].copy()
for c in summary_display.columns:
    if c == "Profit %":
        summary_display[c] = summary_display[c].map(lambda x: f"{x:.1%}" if pd.notna(x) else "")
    elif c not in ["Job", "Site"]:
        summary_display[c] = summary_display[c].map(format_currency)
st.dataframe(summary_display, use_container_width=True, hide_index=True)

st.markdown("<div class='section-title'>S-Curve: Cumulative Actual Cost</div>", unsafe_allow_html=True)
if not monthly.empty:
    curve = monthly.groupby("Month", as_index=False)["Cost"].sum().sort_values("Month")
    curve["Cumulative Actual"] = curve["Cost"].cumsum()
    curve["Month Label"] = curve["Month"].dt.strftime("%b %Y")
    # With no monthly forecast profile, show total forecast as a reference line.
    curve["Overall Forecast"] = forecast_total
    fig = px.line(
        curve,
        x="Month Label",
        y=["Cumulative Actual", "Overall Forecast"],
        markers=True,
        labels={"value": "Cost", "Month Label": "Month", "variable": "Measure"},
        title="Cumulative Actual vs Overall Forecast",
    )
    fig.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No monthly costs found to build an S-curve.")

left, right = st.columns([2, 1])
with left:
    st.markdown("<div class='section-title'>Monthly Breakdown</div>", unsafe_allow_html=True)
    if not monthly.empty:
        monthly_display = monthly.copy()
        monthly_display["Month"] = monthly_display["Month"].dt.strftime("%d/%m/%Y")
        monthly_display["Cost"] = monthly_display["Cost"].map(format_currency)
        st.dataframe(monthly_display, use_container_width=True, hide_index=True)
with right:
    st.markdown("<div class='section-title'>Issues</div>", unsafe_allow_html=True)
    issue_df = pd.DataFrame(issues)
    if issue_df.empty:
        st.success("No issues found.")
    else:
        st.dataframe(issue_df, use_container_width=True, hide_index=True)

st.markdown("<div class='section-title'>Download Report</div>", unsafe_allow_html=True)
export_bytes = excel_export(summary, monthly, actuals, issues)
st.download_button(
    "Download Excel Report",
    data=export_bytes,
    file_name=f"PAS_Live_Cost_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

with st.expander("Raw imported cost records"):
    raw_display = actuals.copy()
    if not raw_display.empty:
        raw_display["Cost Date"] = pd.to_datetime(raw_display["Cost Date"], errors="coerce").dt.strftime("%d/%m/%Y")
        raw_display["Month"] = pd.to_datetime(raw_display["Month"], errors="coerce").dt.strftime("%d/%m/%Y")
        raw_display["Cost"] = raw_display["Cost"].map(format_currency)
    st.dataframe(raw_display, use_container_width=True, hide_index=True)
