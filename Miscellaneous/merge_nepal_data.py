"""
Nepal crop yield dataset - corrected merge pipeline.

Fixes vs. the previous version:
  1. THE MAIN BUG: crop data is now loaded from ALL 5 year-files and joined
     on (district_key, Year_BS) -- not just district_key. The old script only
     ever read nepal_all_cereals_2078_79.csv, so every district's crop numbers
     were identical across all 5 years (2078/79's values copy-pasted 5x).
  2. Cereal source rows containing "N/A" are treated as missing (NaN), not
     as a real duplicate record.
  3. Exact duplicate (district, crop, year) rows in the raw cereal files are
     dropped before pivoting, so pivot_table can't silently pick one at random.
  4. Soil_Type is not touched/needed here since district_soil_data_cleaned.csv
     no longer contains it -- avoids the CSV-quoting bug from before entirely.
  5. Runs a validation pass at the end that would have caught the original bug:
     confirms crop values actually differ across years per district.
"""

import pandas as pd
import re
from pathlib import Path

IN_DIR = Path(__file__).resolve().parent
OUT_PATH = IN_DIR / "nepal_merged_dataset.csv"


def find_csv(filename: str) -> Path:
    direct = IN_DIR / filename
    if direct.exists():
        return direct
    matches = list(IN_DIR.rglob(filename))
    if matches:
        return matches[0]
    raise FileNotFoundError(
        f"\nCould not find '{filename}' anywhere under {IN_DIR}\n"
        f"Files currently visible there:\n"
        + "\n".join(f"  {p.relative_to(IN_DIR)}" for p in IN_DIR.rglob("*.csv"))
    )


DISTRICT_ALIASES = {
    "ILLAM": "ILAM",
    "RAMECHAP": "RAMECHHAP",
    "CHITWAN": "CHITAWAN",
    "MAKWANPUR": "MAKAWANPUR",
    "NAWALPARASI EAST": "NAWALPARASIEAST",
    "NAWALPARASI_E": "NAWALPARASIEAST",
    "NAWALPARASI WEST": "NAWALPARASIWEST",
    "NAWALPARASI_W": "NAWALPARASIWEST",
}


def normalize_district(name: str) -> str:
    if pd.isna(name):
        return name
    n = re.sub(r"\s+", " ", str(name).strip()).upper()
    n_nospace = n.replace(" ", "")
    if n in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[n]
    if n_nospace in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[n_nospace]
    return n_nospace


def clean_str_cols(df):
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].str.strip()
    return df


# ---------------------------------------------------------------------
# 1. Load each source
# ---------------------------------------------------------------------

# --- 1a. AlphaEarth embeddings (defines base grain: district x year) ---
alpha = pd.read_csv(find_csv("Nepal_77Districts_QGIS_AlphaEarth.csv"))
alpha.columns = [c.strip() for c in alpha.columns]
alpha = clean_str_cols(alpha)

district_col = next((c for c in alpha.columns if c.lower() in ["district", "district_key"]), alpha.columns[0])
alpha["district_key"] = alpha[district_col].apply(normalize_district)
if "District" not in alpha.columns:
    alpha = alpha.rename(columns={district_col: "District"})

year_col = next((c for c in alpha.columns if c in ["Year_AD", "year", "Year"]), "Year_AD")
if year_col != "Year_AD":
    alpha = alpha.rename(columns={year_col: "Year_AD"})
alpha["Year_BS"] = alpha["Year_BS"].str.strip()


# --- 1b. NPK / soil chemistry (static per district) ---
npk = pd.read_csv(find_csv("NPKPhOrganicmatter_csv.csv"))
npk.columns = [c.strip() for c in npk.columns]
npk = clean_str_cols(npk)
npk["district_key"] = npk["DISTRICT"].apply(normalize_district)
npk = npk.drop(columns=["DISTRICT", "STATE_CODE", "PR_NAME"], errors="ignore")
npk = npk.rename(columns={
    "_mean": "Potassium_mean",
    "Nitrogenmean": "Nitrogen_mean",
    "organicmean": "OrganicMatter_mean",
    "Phosphorousmean": "Phosphorous_mean",
    "Phvaluemean": "pH_mean",
})
for c in ["Potassium_mean", "Nitrogen_mean", "OrganicMatter_mean", "Phosphorous_mean", "pH_mean"]:
    npk[c] = pd.to_numeric(npk[c], errors="coerce")

npk_dupes = npk["district_key"].duplicated().sum()
if npk_dupes:
    raise ValueError(f"NPK source has {npk_dupes} duplicate district_key rows -- fix source before merging.")


# --- 1c. Landform / soil type (static per district) ---
soil = pd.read_csv(find_csv("district_soil_data_final_corrected.csv"), skipinitialspace=True)
soil.columns = [c.strip() for c in soil.columns]
soil = clean_str_cols(soil)
soil["district_key"] = soil["District"].apply(normalize_district)
soil = soil.drop(columns=["District"], errors="ignore")

soil_dupes = soil["district_key"].duplicated().sum()
if soil_dupes:
    raise ValueError(f"Soil source has {soil_dupes} duplicate district_key rows -- fix source before merging.")


# --- 1d. Crop yield data: THE FIX -- load ALL 5 year-files, not just one ---
CEREAL_FILES = [
    "nepal_cereals_2075_76.csv",
    "nepal_cereals_2076_77.csv",
    "nepal_all_cereals_2078_79.csv",
    "nepal_cereals_2079_80.csv",
    "nepal_cereals_2080_81.csv",
]

cereal_frames = []
for fname in CEREAL_FILES:
    df = pd.read_csv(find_csv(fname))
    df.columns = [c.strip() for c in df.columns]
    df = clean_str_cols(df)
    df["district_key"] = df["District"].apply(normalize_district)
    df["Crop"] = df["Crop"].str.strip()
    df["Year_BS"] = df["Year_BS"].str.strip()

    # "N/A" strings -> real NaN so they don't get treated as valid duplicate rows
    for c in ["Area_Ha", "Production_Mt", "Yield_MtHa"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Drop fully-empty junk rows (e.g. the MAHOTTARI Barley N/A row in 2075/76)
    df = df.dropna(subset=["Area_Ha", "Production_Mt", "Yield_MtHa"], how="all")

    # Drop exact duplicate (district, crop, year) rows (e.g. KAILALI Barley in 2079/80)
    before = len(df)
    df = df.drop_duplicates(subset=["district_key", "Crop", "Year_BS"], keep="first")
    if len(df) != before:
        print(f"  [{fname}] dropped {before - len(df)} duplicate (district, crop) row(s)")

    cereal_frames.append(df[["district_key", "Year_BS", "Crop", "Area_Ha", "Production_Mt", "Yield_MtHa"]])

cereals_all = pd.concat(cereal_frames, ignore_index=True)

# Sanity: at most one row per (district, crop, year) after cleanup above
dup_check = cereals_all.duplicated(subset=["district_key", "Year_BS", "Crop"]).sum()
if dup_check:
    raise ValueError(f"Still have {dup_check} duplicate (district, crop, year) rows after cleanup -- investigate.")

# Pivot to wide format: one column per metric per crop, grain = district x year
cereals_wide = cereals_all.pivot_table(
    index=["district_key", "Year_BS"],
    columns="Crop",
    values=["Area_Ha", "Production_Mt", "Yield_MtHa"],
    aggfunc="first",
)
cereals_wide.columns = [f"{crop}_{metric}" for metric, crop in cereals_wide.columns]
cereals_wide = cereals_wide.reset_index()


# ---------------------------------------------------------------------
# 2. Merge datasets onto base (district x year grain)
# ---------------------------------------------------------------------
merged = alpha.merge(soil, on="district_key", how="left", validate="many_to_one")
merged = merged.merge(npk, on="district_key", how="left", validate="many_to_one")
# THE FIX: join crop data on BOTH district_key and Year_BS, not district_key alone
merged = merged.merge(cereals_wide, on=["district_key", "Year_BS"], how="left", validate="many_to_one")

id_cols = [c for c in ["district_key", "District", "Year_AD", "Year_BS", "Province"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in id_cols]
merged = merged[id_cols + other_cols]
merged = merged.rename(columns={"district_key": "District_Key"})

merged = merged.sort_values(["Year_AD", "District_Key"]).reset_index(drop=True)


# ---------------------------------------------------------------------
# 3. Validation
# ---------------------------------------------------------------------
print("\nFinal Shape:", merged.shape)
print("Districts:", merged["District_Key"].nunique(), "| Years:", sorted(merged["Year_AD"].unique()))

missing_soil = merged[merged["Province"].isna()]["District_Key"].unique() if "Province" in merged.columns else []
missing_npk = merged[merged["Nitrogen_mean"].isna()]["District_Key"].unique() if "Nitrogen_mean" in merged.columns else []
crop_test_col = next((c for c in merged.columns if "Yield_MtHa" in c), None)
missing_crop = merged[merged[crop_test_col].isna()]["District_Key"].unique() if crop_test_col else []

print("Districts missing soil match:", list(missing_soil))
print("Districts missing NPK match:", list(missing_npk))
print("Districts missing crop match:", list(missing_crop))

# This check would have caught the original bug: crop values must vary by year.
crop_cols = [c for c in merged.columns if any(c.endswith(m) for m in ("_Area_Ha", "_Production_Mt", "_Yield_MtHa"))]
static_districts = []
for dist, g in merged.groupby("District_Key"):
    if all(g[c].nunique(dropna=True) <= 1 for c in crop_cols):
        static_districts.append(dist)

if static_districts:
    print(f"\nWARNING: {len(static_districts)} districts have IDENTICAL crop values across all years "
          f"(this is the bug from before -- something's still wrong): {static_districts}")
else:
    print("\nOK: crop values vary by year for all districts (year-join bug is fixed).")

merged.to_csv(OUT_PATH, index=False, na_rep="N/A")
print(f"\nSUCCESS: Saved merged dataset to {OUT_PATH}")
print("Note: missing values are written as the literal text 'N/A' (not blank cells).")
print("When loading this file back for modeling, tell pandas to treat 'N/A' as missing, e.g.:")
print('    pd.read_csv("nepal_merged_dataset.csv", na_values=["N/A"])')
