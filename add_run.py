import pandas as pd
import sys
import os
from datetime import datetime

# Check command-line arguments
if len(sys.argv) != 2:
    print("Usage: add_run.py [filepath]")
    sys.exit(1)

run_file = sys.argv[1]

# Check file existence and extension
if not os.path.exists(run_file) or not run_file.endswith('.csv'):
    print("Error: File does not exist or is not a CSV.")
    sys.exit(1)

date = os.path.basename(run_file).replace(".csv", "")

try:
    datetime.strptime(date, "%Y-%m,%d")
except ValueError:
    print("Error: Filename must be in YYYY-MM-DD format.")

try:
    df = pd.read_csv(run_file)
except Exception as e:
    print(f"Error reading CSV: {e}")
    sys.exit(1)

if df.empty:
    print("Error: The CSV file is empty.")
    sys.exit(1)


# Validate rating input
while True:
    rating = input("How did you feel? (1-10): ")
    try:
        rating_int = int(rating)
        if 1 <= rating_int <= 10:
            break
        else:
            print("Please enter a number between 1 and 10.")
    except ValueError:
        print("Please enter a valid integer.")

notes = input("Any notes about the run? ").strip()

summary_row = df.iloc[-1]

# Check for required columns
required_cols = [
    "Distancekm", "Cumulative Time", "Avg Pacemin/km",
    "Avg HRbpm", "Avg Run Cadencespm", "Total Ascentm"
]
for col in required_cols:
    if col not in summary_row:
        print(f"Error: Missing column '{col}' in summary row.")
        sys.exit(1)

run_row = {
    "date": date,
    "distance": summary_row["Distancekm"],
    "time": summary_row["Cumulative Time"],
    "avg pace": summary_row["Avg Pacemin/km"],
    "avg hr": summary_row["Avg HRbpm"],
    "avg cadence": summary_row["Avg Run Cadencespm"],
    "total ascent": summary_row["Total Ascentm"],
    "rating": rating_int,
    "notes": notes,
}

row_df = pd.DataFrame([run_row])
row_df.to_csv("data/runs.csv", header=False, mode='a', index=False)
print("Run added successfully!")