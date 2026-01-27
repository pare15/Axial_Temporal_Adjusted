import uproot
import pandas as pd
from pathlib import Path

ROOT_TREE = "/Users/2025/Documents/David/root_files/readimg28.root:Coincidences;1"
OUTPUT_XLSX = "/Users/2025/Documents/David/xlsx_files/coincidences.xlsx"
BRANCHES = None
EXCEL_MAX_ROWS = 1_048_576

print("Opening ROOT tree directly...")
tree = uproot.open(ROOT_TREE)   # <-- this IS the tree already

print("Reading into pandas DataFrame...")
df = tree.arrays(BRANCHES, library="pd") if BRANCHES else tree.arrays(library="pd")
print(f"Total rows read: {len(df):,}")

print("Writing to Excel...")
Path(OUTPUT_XLSX).parent.mkdir(parents=True, exist_ok=True)

with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
    if len(df) <= EXCEL_MAX_ROWS - 1:
        df.to_excel(writer, sheet_name="sheet1", index=False)
    else:
        rows_per_sheet = EXCEL_MAX_ROWS - 1
        n_sheets = (len(df) + rows_per_sheet - 1) // rows_per_sheet
        for i in range(n_sheets):
            start = i * rows_per_sheet
            end = min((i + 1) * rows_per_sheet, len(df))
            df.iloc[start:end].to_excel(writer, sheet_name=f"sheet{i+1}", index=False)

print(f"Done. Saved to {OUTPUT_XLSX}")
