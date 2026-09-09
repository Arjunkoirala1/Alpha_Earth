import csv
import pandas as pd

# ==========================
# File Paths
# ==========================

input_file = r"C:\Users\SRDC\Desktop\Alpha_earth\soil_chemicals(NPK)information_csv\districtwise_and_municipalitywise_soilfeatures_csv\districtwise_soiltypeand_chemicals\soiltype\districtwise_soiltype.csv"

output_file = r"C:\Users\SRDC\Desktop\Alpha_earth\soil_data_cleaned.csv"

# ==========================
# Read CSV using csv module
# ==========================

rows = []

with open(input_file, "r", encoding="utf-8", newline="") as f:
    reader = csv.reader(
        f,
        delimiter=",",
        quotechar='"',
        skipinitialspace=True
    )

    for row in reader:
        rows.append(row)

# ==========================
# Convert to DataFrame
# ==========================

header = [h.strip() for h in rows[0]]
data = rows[1:]

df = pd.DataFrame(data, columns=header)

# ==========================
# Keep required columns
# ==========================

columns = [
    "DISTRICT",
    "PR_NAME",
    "SQKM",
    "Elev_min",
    "Elev_max",
    "Slope_med",
    "Relief_med",
    "Landform",
    "Parent_Mat",
    "Dominant_S",
    "NAME"
]

df = df[columns]

# ==========================
# Rename
# ==========================

df.rename(columns={
    "DISTRICT":"District",
    "PR_NAME":"Province",
    "SQKM":"Area_sqkm",
    "Elev_min":"Elevation_Min",
    "Elev_max":"Elevation_Max",
    "Slope_med":"Slope_Median",
    "Relief_med":"Relief_Median",
    "Landform":"Landform",
    "Parent_Mat":"Parent_Material",
    "Dominant_S":"Dominant_Soil",
    "NAME":"Rock_Type"
}, inplace=True)

# ==========================
# Clean spaces
# ==========================

for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].str.strip()

# ==========================
# Save
# ==========================

df.to_csv(output_file, index=False)

print("Done!")
print(df.head())
print(f"\nSaved to:\n{output_file}")