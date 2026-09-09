import pandas as pd

input_file = r"C:\Users\SRDC\Desktop\Alpha_earth\Models_separate_nepals\soil_cereal.csv"
output_file = r"nepal_soil_merged_dataset_without_buckwheat.csv"

# Read CSV
df = pd.read_csv(input_file)

# Show all columns containing "buckwheat"
buckwheat_columns = [
    col for col in df.columns
    if "buckwheat" in col.lower()
]

print("Buckwheat columns found:")
for col in buckwheat_columns:
    print(" -", repr(col))

# Remove them
df = df.drop(columns=buckwheat_columns)

# Save new CSV
df.to_csv(output_file, index=False)

print("\nDone!")
print("Removed:", len(buckwheat_columns), "columns")
print("Saved as:", output_file)
print("New shape:", df.shape)