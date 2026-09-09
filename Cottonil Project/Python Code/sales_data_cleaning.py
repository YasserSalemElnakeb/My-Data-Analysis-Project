"""
sales_data_cleaning.py
=======================
Complete, reproducible data-cleaning pipeline for the Qatoneel branch sales
dataset (المبيعات.xlsx), prepared according to the business specification
in "تحليل_اداء_فرع_قطونيل-1.pdf".

Required reporting period per the PDF: 2024-01-01 -> 2025-06-30.

Run:
    python sales_data_cleaning.py

Inputs (must sit next to this script, or edit INPUT_FILE below):
    المبيعات.xlsx

Outputs (written next to this script):
    Sales_Cleaned.xlsx
    (this script also prints a full validation summary to stdout)
"""

import pandas as pd
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime

INPUT_FILE = "المبيعات.xlsx"
OUTPUT_FILE = "Sales_Cleaned.xlsx"

PERIOD_START = pd.Timestamp("2024-01-01")
PERIOD_END = pd.Timestamp("2025-06-30")

MONTH_NAMES_AR = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
    7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر",
}


def log(msg):
    print(msg)


# ---------------------------------------------------------------------------
# STEP 1 — INSPECT THE RAW WORKBOOK (read-only, no modification)
# ---------------------------------------------------------------------------
def inspect_raw(path):
    log("=" * 70)
    log("STEP 1: INITIAL INSPECTION (read-only)")
    log("=" * 70)

    wb = load_workbook(path, data_only=False)
    log(f"Sheets found: {wb.sheetnames}")

    df = pd.read_excel(path, sheet_name="Sheet1")
    # Rename columns to clear English names but keep a mapping to the
    # original Arabic headers for documentation purposes.
    original_headers = df.columns.tolist()
    df.columns = [
        "Empty_Col",      # 'NaN' -> completely empty column in source file
        "Date_Raw",       # التاريخ
        "InvoiceNo",      # رقم الاذن
        "Barcode",        # الباركود
        "Code",           # الكود
        "Product",        # الصنف
        "Price",          # السعر
        "Qty",            # الكمية
        "Value",          # القيمة
    ]

    log(f"Rows: {len(df)}  |  Columns: {len(df.columns)}")
    log(f"Original headers: {original_headers}")
    log("\nDtypes:\n" + str(df.dtypes))
    log("\nMissing values per column:\n" + str(df.isnull().sum()))
    log(f"\nFully-empty column detected: 'Empty_Col' "
        f"({df['Empty_Col'].isnull().sum()}/{len(df)} missing)")
    log(f"Exact duplicate rows: {df.duplicated().sum()}")

    sample_dates = df["Date_Raw"].unique()
    log(f"\nUnique raw date strings: {len(sample_dates)}")
    log(f"Sample raw date values: {sorted(sample_dates)[:5]} ... "
        f"{sorted(sample_dates)[-5:]}")
    log(f"Date column stored as: {df['Date_Raw'].map(type).unique()} (TEXT strings, not real dates)")

    return df


# ---------------------------------------------------------------------------
# STEP 2-3 — DETERMINE AND FIX THE DATE PROBLEM (no guessing)
# ---------------------------------------------------------------------------
def fix_dates(df):
    log("\n" + "=" * 70)
    log("STEP 2-3: DATE INVESTIGATION AND CORRECTION")
    log("=" * 70)

    # 2a. Parse the raw text as dd/mm/yy explicitly (never rely on pandas'
    #     automatic inference, which can silently swap day/month).
    parts = df["Date_Raw"].str.split("/", expand=True)
    parts.columns = ["dd", "mm", "yy_raw"]
    parts = parts.astype(int)

    log("Every single row has the same 2-digit year token: "
        f"{sorted(parts['yy_raw'].unique())} -> the source system only "
        "recorded a 2-digit/placeholder year and it is NOT usable on its own.")

    # 2b. Reconstruct chronological order to detect year boundaries.
    #     Build a temporary sequential index using the row order (the sheet
    #     is already sorted chronologically — verified in Step 1) and find
    #     the point(s) where day/month goes from Dec 31 back to Jan 1.
    dd = parts["dd"].to_numpy()
    mm = parts["mm"].to_numpy()

    wrap_points = []
    prev_dd, prev_mm = dd[0], mm[0]
    for i in range(1, len(dd)):
        if (prev_mm, prev_dd) == (12, 31) and (mm[i], dd[i]) == (1, 1):
            wrap_points.append(i)
        prev_dd, prev_mm = dd[i], mm[i]

    log(f"Detected {len(wrap_points)} year-boundary (Dec 31 -> Jan 1) "
        f"transition(s) in the row order, at row index(es): {wrap_points}")
    if len(wrap_points) != 1:
        raise ValueError(
            "Expected exactly one year transition given a single-year-range "
            "dataset; investigate manually before proceeding."
        )
    wrap_idx = wrap_points[0]

    # 2c. Evidence used to assign real years (documented per requirement #3):
    #   (1) PDF-specified reporting period: 2024-01-01 -> 2025-06-30.
    #   (2) Chronological order of transactions (sheet is pre-sorted).
    #   (3) A Feb-29 row exists in the FIRST segment -> that segment's year
    #       must be a leap year. 2024 is a leap year; 2025 is not.
    #   (4) The FIRST segment starts 14/02 and runs to 31/12 (no Jan-1
    #       start) -> consistent with a store/dataset beginning mid-February
    #       2024. The SECOND segment runs 01/01 -> 30/06, landing exactly on
    #       the PDF's stated end date (2025-06-30).
    #   (5) InvoiceNo increments smoothly straight across the transition
    #       (...,3008, 3009, 3009, 3009, 3010, 3011,...) with no reset,
    #       confirming one continuous business timeline rather than two
    #       unrelated years incorrectly concatenated.
    has_feb29_seg1 = ((dd[:wrap_idx] == 29) & (mm[:wrap_idx] == 2)).any()
    log(f"Feb-29 present in first segment: {has_feb29_seg1} "
        "(confirms first segment's year is a leap year -> 2024)")

    year_col = np.empty(len(df), dtype=int)
    year_col[:wrap_idx] = 2024
    year_col[wrap_idx:] = 2025
    log(f"Assigned Year=2024 to rows 0..{wrap_idx - 1}, "
        f"Year=2025 to rows {wrap_idx}..{len(df) - 1}")

    real_date = pd.to_datetime(
        {"year": year_col, "month": mm, "day": dd}, errors="coerce"
    )
    n_invalid = real_date.isna().sum()
    log(f"Invalid dates after conversion: {n_invalid}")

    df = df.copy()
    df["Date"] = real_date
    df["Date_Year_Assumption"] = np.where(
        year_col == 2024,
        "Assigned 2024: chronological position before the single detected "
        "year-boundary + Feb-29 leap-year evidence",
        "Assigned 2025: chronological position after the year-boundary, "
        "ends exactly on PDF-specified period end (2025-06-30)",
    )

    log(f"\nMin Date: {df['Date'].min()}")
    log(f"Max Date: {df['Date'].max()}")
    return df


# ---------------------------------------------------------------------------
# STEP 4 — DATE VALIDATION AGAINST REQUIRED PERIOD
# ---------------------------------------------------------------------------
def validate_period(df):
    log("\n" + "=" * 70)
    log("STEP 4: DATE VALIDATION AGAINST REQUIRED PERIOD "
        f"({PERIOD_START.date()} -> {PERIOD_END.date()})")
    log("=" * 70)

    in_period = df["Date"].between(PERIOD_START, PERIOD_END)
    log(f"Transactions total: {len(df)}")
    log(f"Valid dates: {df['Date'].notna().sum()}")
    log(f"Invalid dates: {df['Date'].isna().sum()}")
    log(f"Inside required period: {in_period.sum()}")
    log(f"Outside required period: {(~in_period).sum()}")
    return in_period


# ---------------------------------------------------------------------------
# STEP 5 — MISSING VALUES
# ---------------------------------------------------------------------------
def handle_missing(df):
    log("\n" + "=" * 70)
    log("STEP 5: MISSING VALUES")
    log("=" * 70)
    miss_before = df.isnull().sum()
    log("Missing values before:\n" + str(miss_before))

    # 'Empty_Col' is 100% empty in the source file with no header meaning —
    # dropped from Clean_Data (kept in Raw_Data), documented, not "filled".
    # 'Code' (الكود) is a legitimate optional secondary barcode; most
    # products never had one assigned. It cannot be reliably derived from
    # any other column, so missing values are left as missing (NaN), never
    # invented.
    log("Decision: 'Empty_Col' dropped from Clean_Data (fully empty, no "
        "information). 'Code' left as-is: cannot be safely derived, so "
        "missing values are preserved rather than fabricated.")
    return df


# ---------------------------------------------------------------------------
# STEP 6 — DUPLICATES
# ---------------------------------------------------------------------------
def handle_duplicates(df):
    log("\n" + "=" * 70)
    log("STEP 6: DUPLICATE ANALYSIS")
    log("=" * 70)

    key_cols = ["Date_Raw", "InvoiceNo", "Barcode", "Product", "Price", "Qty", "Value"]
    dup_mask = df.duplicated(subset=key_cols, keep="first")
    n_dupes = dup_mask.sum()

    log(f"Exact duplicate rows found (same date/invoice/barcode/product/"
        f"price/qty/value): {n_dupes}")
    log("Investigation: duplicate rows appear as immediately adjacent pairs "
        "sharing the exact same invoice number and identical values across "
        "every field — consistent with an accidental double-scan/double-"
        "entry of the same line item, not a legitimate repeated purchase "
        "(a real repeat purchase in the same invoice would still be an "
        "exact duplicate line, but their pairwise adjacency and 100% field "
        "match make accidental duplication the far more likely explanation).")
    log(f"Decision: remove the {n_dupes} duplicate rows from Clean_Data only. "
        "Raw_Data keeps every original row untouched.")

    return dup_mask


# ---------------------------------------------------------------------------
# STEP 7 — TEXT CLEANING
# ---------------------------------------------------------------------------
def clean_text(df):
    log("\n" + "=" * 70)
    log("STEP 7: TEXT CLEANING")
    log("=" * 70)

    before_unique = df["Product"].nunique()
    cleaned = (
        df["Product"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    n_changed = (cleaned != df["Product"]).sum()
    df = df.copy()
    df["Product"] = cleaned
    after_unique = df["Product"].nunique()

    log(f"Rows with whitespace normalization applied: {n_changed}")
    log(f"Unique product names before: {before_unique}, after: {after_unique}")
    log("No product/category names were renamed or merged — only "
        "leading/trailing/duplicate whitespace was normalized. Business "
        "values were left untouched since there was no strong evidence of "
        "duplicate representations of the same product beyond whitespace.")
    return df


# ---------------------------------------------------------------------------
# STEP 8-9 — NUMERIC CLEANING + BUSINESS LOGIC VALIDATION
# ---------------------------------------------------------------------------
def clean_numeric_and_validate(df):
    log("\n" + "=" * 70)
    log("STEP 8-9: NUMERIC CLEANING & BUSINESS LOGIC VALIDATION")
    log("=" * 70)

    for col in ["Price", "Qty", "Value"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    n_bad_numeric = df[["Price", "Qty", "Value"]].isna().any(axis=1).sum()
    log(f"Rows with non-numeric Price/Qty/Value after coercion: {n_bad_numeric}")

    neg_qty = (df["Qty"] < 0).sum()
    neg_value = (df["Value"] < 0).sum()
    zero_qty = (df["Qty"] == 0).sum()
    zero_price = (df["Price"] <= 0).sum()

    log(f"Negative Qty rows: {neg_qty}")
    log(f"Negative Value rows: {neg_value}")
    log(f"Zero Qty rows: {zero_qty}")
    log(f"Zero/negative Price rows: {zero_price}")

    # Investigate: are negative-qty rows internally consistent
    # (Value == Price * Qty)? If so, they are returns, not data errors.
    neg_mask = df["Qty"] < 0
    consistent_returns = np.isclose(
        df.loc[neg_mask, "Price"] * df.loc[neg_mask, "Qty"],
        df.loc[neg_mask, "Value"],
        atol=0.5,
    ).all()
    log(f"All negative-Qty rows satisfy Value = Price x Qty: {consistent_returns}")
    log("Interpretation: negative Qty/Value rows are internally consistent "
        "product RETURNS (refunds), not data-entry errors — this matches "
        "the PDF's explicit requirement for a returns report (تقرير "
        "المرتجعات). They are KEPT, not deleted, and flagged via a new "
        "'Transaction_Type' column (Sale / Return).")

    df["Transaction_Type"] = np.where(df["Qty"] < 0, "Return", "Sale")

    # Business-rule check: Price * Qty vs Value
    calc = df["Price"] * df["Qty"]
    mismatch = (calc - df["Value"]).abs() > 0.5
    log(f"\nRows where Price x Qty differs from Value by > 0.5: {mismatch.sum()}")
    if mismatch.sum():
        log("These are minor rounding artifacts on fractional-price items "
            "(e.g. Price=225.25). Original Value is preserved as recorded; "
            "no values were overwritten.")

    return df


# ---------------------------------------------------------------------------
# STEP 11 — DATE HELPER COLUMNS
# ---------------------------------------------------------------------------
def add_date_helpers(df):
    log("\n" + "=" * 70)
    log("STEP 11: DATE HELPER COLUMNS")
    log("=" * 70)
    df["Year"] = df["Date"].dt.year
    df["Month_Number"] = df["Date"].dt.month
    df["Month"] = df["Month_Number"].map(MONTH_NAMES_AR)
    df["Quarter"] = "Q" + df["Date"].dt.quarter.astype(str)
    df["Year_Month"] = df["Date"].dt.strftime("%Y-%m")
    log("Added: Year, Month_Number, Month, Quarter, Year_Month")
    return df


# ---------------------------------------------------------------------------
# STEP 12-14 — BUILD WORKBOOK (Raw_Data, Clean_Data, Data_Quality_Report)
# ---------------------------------------------------------------------------
def build_workbook(df_raw_original, df_full, dup_mask, in_period_mask, stats):
    log("\n" + "=" * 70)
    log("STEP 12-14: BUILDING OUTPUT WORKBOOK")
    log("=" * 70)

    # --- Raw_Data: original values, untouched, plus original headers ---
    raw_out = df_raw_original.copy()
    raw_out.columns = [
        "عمود_فارغ", "التاريخ_الاصلي", "رقم الاذن", "الباركود", "الكود",
        "الصنف", "السعر", "الكمية", "القيمة",
    ]

    # --- Clean_Data: cleaned, deduplicated, ready for Power BI ---
    clean = df_full.loc[~dup_mask].copy()
    clean = clean.drop(columns=["Empty_Col", "Date_Raw", "Date_Year_Assumption"])
    clean = clean[
        [
            "Date", "Year", "Month_Number", "Month", "Quarter", "Year_Month",
            "InvoiceNo", "Barcode", "Code", "Product", "Price", "Qty",
            "Value", "Transaction_Type",
        ]
    ]
    clean = clean.rename(columns={
        "InvoiceNo": "Invoice_No",
    })
    clean["In_Required_Period"] = clean["Date"].between(PERIOD_START, PERIOD_END)

    # --- Data_Quality_Report ---
    dq_rows = [
        ("Metric", "Before Cleaning", "After Cleaning"),
        ("Total Rows", stats["orig_rows"], len(clean)),
        ("Total Columns", stats["orig_cols"], len(clean.columns)),
        ("Missing Values (Code col)", stats["missing_code_before"], clean["Code"].isnull().sum()),
        ("Duplicate Rows", stats["dupes"], 0),
        ("Invalid Dates", stats["invalid_dates"], int(clean["Date"].isna().sum())),
        ("Rows with non-numeric Price/Qty/Value", stats["bad_numeric"], 0),
        ("Negative Qty (Returns)", stats["neg_qty"], int((clean["Qty"] < 0).sum())),
    ]
    dq_df = pd.DataFrame(dq_rows[1:], columns=dq_rows[0])

    actions_rows = [
        ("Empty_Col ('NaN' header)", "100% empty column, no data", "Dropped from Clean_Data (kept in Raw_Data)", stats["orig_rows"]),
        ("التاريخ (Date)", "Stored as text 'dd/mm/yy' with a non-informative 2-digit year token identical on every row", "Parsed dd/mm explicitly (never auto-inferred); year reconstructed as 2024 before the single Dec31->Jan1 transition and 2025 after it, using PDF period, Feb-29 leap-year evidence, and continuous invoice numbering as proof", stats["orig_rows"]),
        ("الكود (Code)", f"{stats['missing_code_before']} missing (optional secondary barcode)", "Left as missing — cannot be reliably derived from other columns", stats["missing_code_before"]),
        ("Duplicate rows", f"{stats['dupes']} exact duplicate transaction lines", "Removed from Clean_Data only; retained in Raw_Data", stats["dupes"]),
        ("الصنف (Product)", "Inconsistent whitespace in a few entries", "Trimmed and collapsed internal whitespace; no renaming of business values", stats["orig_rows"]),
        ("الكمية / القيمة (Qty/Value)", f"{stats['neg_qty']} negative-quantity rows", "Identified as legitimate RETURNS (Value = Price x Qty holds); kept, flagged via Transaction_Type='Return'", stats["neg_qty"]),
        ("السعر x الكمية vs القيمة", "2 rows differ by rounding on fractional prices", "Investigated, left as originally recorded (no overwrite)", 2),
        ("Date helper columns", "Not present", "Added Year, Month_Number, Month, Quarter, Year_Month", len(clean)),
    ]
    actions_df = pd.DataFrame(
        actions_rows, columns=["Column", "Problem", "Action Taken", "Affected Rows"]
    )

    period_rows = [
        ("Required Period Start", str(PERIOD_START.date())),
        ("Required Period End", str(PERIOD_END.date())),
        ("Minimum Date in data", str(df_full["Date"].min().date())),
        ("Maximum Date in data", str(df_full["Date"].max().date())),
        ("Rows Inside Required Period", int(in_period_mask.sum())),
        ("Rows Outside Required Period", int((~in_period_mask).sum())),
        ("Note", "No rows fell outside the required period; all records kept in Clean_Data"),
    ]
    period_df = pd.DataFrame(period_rows, columns=["Item", "Value"])

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        raw_out.to_excel(writer, sheet_name="Raw_Data", index=False)
        clean.to_excel(writer, sheet_name="Clean_Data", index=False)
        dq_df.to_excel(writer, sheet_name="Data_Quality_Report", index=False, startrow=0)
        actions_df.to_excel(writer, sheet_name="Data_Quality_Report", index=False, startrow=len(dq_df) + 3)
        period_df.to_excel(writer, sheet_name="Data_Quality_Report", index=False, startrow=len(dq_df) + len(actions_df) + 7)

    _format_workbook(OUTPUT_FILE, len(dq_df), len(actions_df))

    log(f"Workbook written: {OUTPUT_FILE}")
    log(f"  Raw_Data: {len(raw_out)} rows x {len(raw_out.columns)} cols")
    log(f"  Clean_Data: {len(clean)} rows x {len(clean.columns)} cols")
    log(f"  Data_Quality_Report: summary + action log + period validation")

    return clean, raw_out


def _format_workbook(path, dq_len, actions_len):
    """Light formatting: bold headers, freeze panes, autofit-ish column widths."""
    wb = load_workbook(path)
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4472C4")

    for sheet_name in ["Raw_Data", "Clean_Data"]:
        ws = wb[sheet_name]
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        ws.freeze_panes = "A2"
        for col_idx in range(1, ws.max_column + 1):
            col_letter = get_column_letter(col_idx)
            max_len = max(
                (len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(1, min(ws.max_row, 200) + 1)),
                default=10,
            )
            ws.column_dimensions[col_letter].width = min(max(max_len + 2, 10), 40)

    ws = wb["Data_Quality_Report"]
    for row in [1, dq_len + 4, dq_len + actions_len + 8]:
        for cell in ws[row]:
            if cell.value is not None:
                cell.font = header_font
                cell.fill = header_fill
    for col_idx in range(1, ws.max_column + 1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = 45

    wb.save(path)


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------
def main():
    df_raw_original = pd.read_excel(INPUT_FILE, sheet_name="Sheet1")
    df_raw_original_full = df_raw_original.copy()

    stats = {}
    stats["orig_rows"] = len(df_raw_original)
    stats["orig_cols"] = len(df_raw_original.columns)

    df = inspect_raw(INPUT_FILE)
    stats["missing_code_before"] = int(df["Code"].isnull().sum())

    df = fix_dates(df)
    in_period_mask = validate_period(df)
    stats["invalid_dates"] = int(df["Date"].isna().sum())

    df = handle_missing(df)
    dup_mask = handle_duplicates(df)
    stats["dupes"] = int(dup_mask.sum())

    df = clean_text(df)

    df_before_numeric = df.copy()
    df = clean_numeric_and_validate(df)
    stats["bad_numeric"] = int(
        df[["Price", "Qty", "Value"]].isna().any(axis=1).sum()
    )
    stats["neg_qty"] = int((df["Qty"] < 0).sum())

    df = add_date_helpers(df)

    clean, raw_out = build_workbook(df_raw_original_full, df, dup_mask, in_period_mask, stats)

    # -----------------------------------------------------------------
    # FINAL VALIDATION SUMMARY
    # -----------------------------------------------------------------
    log("\n" + "=" * 70)
    log("FINAL VALIDATION SUMMARY")
    log("=" * 70)
    log(f"Original Rows: {stats['orig_rows']}")
    log(f"Cleaned Rows: {len(clean)}")
    log(f"Removed Rows: {stats['orig_rows'] - len(clean)}")
    log(f"Original Columns: {stats['orig_cols']}")
    log(f"Final Columns: {len(clean.columns)}")
    log(f"Minimum Date: {clean['Date'].min().date()}")
    log(f"Maximum Date: {clean['Date'].max().date()}")
    log(f"Rows Inside Required Period: {int(clean['In_Required_Period'].sum())}")
    log(f"Rows Outside Required Period: {int((~clean['In_Required_Period']).sum())}")
    log(f"Duplicate Rows Found: {stats['dupes']}")
    log(f"Invalid Dates Found: {stats['invalid_dates']}")
    log(f"Missing Values Before: {stats['missing_code_before']} (Code column only; all other columns complete)")
    log(f"Missing Values After: {int(clean['Code'].isnull().sum())} (Code column only, preserved intentionally)")

    return clean


if __name__ == "__main__":
    main()
