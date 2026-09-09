

import pandas as pd

files = [r"C:\Users\SRDC\Desktop\Alpha_earth\ridge_results.csv", r"C:\Users\SRDC\Desktop\Alpha_earth\random_forest_results.csv", r"C:\Users\SRDC\Desktop\Alpha_earth\xgboost_results.csv"]
dfs = [pd.read_csv(f) for f in files]
combined = pd.concat(dfs, ignore_index=True)
combined = combined.sort_values(["Crop", "CV_Scheme", "Model"]).reset_index(drop=True)
combined.to_csv("crop_yield_full_validation_results.csv", index=False)
print("Saved crop_yield_full_validation_results.csv --", combined.shape)
