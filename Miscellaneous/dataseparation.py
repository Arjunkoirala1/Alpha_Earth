import pandas as pd

# Load the dataset
df = pd.read_csv(r"C:\Users\SRDC\Desktop\Alpha_earth\merged_dataset\nepal_merged_dataset.csv")
df.columns = df.columns.str.strip()  # clean up whitespace in headers

# Common identifier columns you'll want in both files
id_cols = ["District_Key", "District", "Year_AD", "Year_BS", "Province"]

# AlphaEarth embedding columns (A00 to A63)
alpha_cols = [f"A{str(i).zfill(2)}" for i in range(64)]

# Soil / terrain / geo columns (everything else that isn't AlphaEarth or crop data)
soil_cols = [
    "Elevation_Min", "Elevation_Max", "Slope_Median", "Landform",
    "Parent_Material", "Dominant_Soil", "area", "longitude", "latitude",
    "Potassium_mean", "Nitrogen_mean", "OrganicMatter_mean",
    "Phosphorous_mean", "pH_mean"
]

# Cereal/crop columns — grab all Area_Ha, Production_Mt, Yield_MtHa columns automatically
crop_cols = [c for c in df.columns if any(k in c for k in ["Area_Ha", "Production_Mt", "Yield_MtHa"])]

# Sanity check: make sure nothing's missing/mismatched
missing_alpha = [c for c in alpha_cols if c not in df.columns]
missing_soil = [c for c in soil_cols if c not in df.columns]
print("Missing AlphaEarth cols:", missing_alpha)
print("Missing soil cols:", missing_soil)
print("Crop cols found:", crop_cols)

# File 1: AlphaEarth + cereal data
alpha_df = df[id_cols + alpha_cols + crop_cols]
alpha_df.to_csv("alphaearth_cereal.csv", index=False)

# File 2: Soil/terrain + cereal data (no AlphaEarth)
soil_df = df[id_cols + soil_cols + crop_cols]
soil_df.to_csv("soil_cereal.csv", index=False)

print("Done. Shapes:", alpha_df.shape, soil_df.shape)