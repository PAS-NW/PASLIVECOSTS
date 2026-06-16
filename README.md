# PAS Live Cost Dashboard

Streamlit app for building a weekly PAS Live Cost dashboard from four uploaded spreadsheets.

## Uploads

1. Materials & Plant Spreadsheet
2. Vehicles Spreadsheet
3. Labour Spreadsheet
4. Forecast Spreadsheet

## Outputs

- On-screen KPI cards
- Site summary dashboard
- Cumulative S-curve chart
- Monthly breakdown
- Issues report
- Excel download containing:
  - Summary
  - Monthly Breakdown
  - Raw Data
  - Issues
  - One tab per site/job

## Costing rules included

- Job Number is the master key.
- Materials includes Materials + Agg-Conc.
- Muck Away is separated where description/category is `Muck Away`.
- Site Fuel is diesel from the Materials sheet.
- Fuel Card is from the Vehicles sheet.
- Plant is costed on a 5-day week, excluding weekends and UK bank holidays entered in the app logic.
- Vehicles are costed on a 7-day week.
- Subbies are allocated by Start Date.
- Delivery month drives monthly allocation for Materials, Agg-Conc, Muck Away and Site Fuel.

## Deploying on Streamlit Cloud

Upload these files to a GitHub repository:

- `app.py`
- `requirements.txt`
- `README.md`
- `pas_logo.png`

Then create a new Streamlit Cloud app pointing to `app.py`.
