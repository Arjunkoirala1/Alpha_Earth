import ee
from ee_plugin import Map
import pandas as pd
import qgis.core

ee.Initialize()

layer = qgis.utils.iface.activeLayer()


features = []
for f in layer.getFeatures():
    geom = f.geometry().asJson()
    import json
    ee_geom = ee.Geometry(json.loads(geom))
    
    dist_name = f['district'] if 'district' in f.attributeMap() else f[0] 
    features.append(ee.Feature(ee_geom, {'district': dist_name}))

nepal_77_ee = ee.FeatureCollection(features)

alpha_earth = ee.ImageCollection('GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL')

years = [2019, 2020, 2021, 2022, 2023]
all_results = []

print("Processing Zonal Statistics for 77 districts across 5 years...")

for yr in years:
    print(f"Extracting Year {yr}...")
    start_date = f'{yr}-01-01'
    end_date = f'{yr}-12-31'
    
    img = alpha_earth.filter(ee.Filter.date(start_date, end_date)).mosaic()
    
   
    stats = img.reduceRegions(
        collection=nepal_77_ee,
        reducer=ee.Reducer.mean(),
        scale=100
    ).getInfo()
    
    for feat in stats['features']:
        props = feat['properties']
        row = {'district': props.get('district'), 'year': yr}
        
        for i in range(64):
            col_name = f'A{i:02d}'
            row[col_name] = props.get(col_name, None)
        all_results.append(row)


df = pd.DataFrame(all_results)
df_clean = df.sort_values(by=['district', 'year']).reset_index(drop=True)

output_path = "C:/Users/SRDC/Desktop/Alpha_earth/Nepal_77Districts_QGIS_AlphaEarth.csv"
df_clean.to_csv(output_path, index=False)

print(f"\nDONE! Exported {len(df_clean)} rows (77 districts x 5 years) to:")
print(output_path)