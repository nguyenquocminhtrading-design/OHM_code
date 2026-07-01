import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = "OHM_KeHoachXoayVon.xlsx"
try:
    xl = pd.ExcelFile(file_path)
    for sheet in ['1. Chi Phí Sản Xuất', '2. Giá Bán & Margin']:
        if sheet in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=15)
            print(f"\n--- Sheet: {sheet} ---")
            for i, row in df.iterrows():
                print(f"Row {i}: {row.to_dict()}")
except Exception as e:
    print(f"Error reading file {file_path}: {e}")
