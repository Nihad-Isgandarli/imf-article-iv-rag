"""Explore the structure of the Reinhart-Rogoff Global Crises Excel file."""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRISES_XLSX = PROJECT_ROOT / "data" / "crises_raw.xlsx"


def main() -> None:
    # Read the only sheet with no header guess to see raw structure
    df = pd.read_excel(CRISES_XLSX, sheet_name="Sheet1", header=None)
    print(f"Shape: {df.shape}  (rows, columns)\n")

    # Show first 15 rows so we can see headers + first data
    print("=== First 15 rows ===")
    print(df.head(15).to_string())
    print()

    # Show last 5 rows so we see how it ends
    print("=== Last 5 rows ===")
    print(df.tail(5).to_string())


if __name__ == "__main__":
    main()