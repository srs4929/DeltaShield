import pandas as pd
import geopandas as gpd

bangladesh = gpd.read_file('../data/bangladesh_district.json')
pop_df = pd.read_csv('../data/population/bgd_admpop_adm2_2022.csv')

# See both name lists side by side
geo_names = sorted(bangladesh['NAME_2'].str.strip().str.title().tolist())
pop_names = sorted(pop_df['ADM2_NAME'].str.strip().str.title().tolist())

print("GeoJSON districts:", geo_names)
print("\nCSV districts:", pop_names)

# Find mismatches
geo_set = set(geo_names)
pop_set = set(pop_names)

print("\n--- In GeoJSON but NOT in CSV ---")
print(geo_set - pop_set)

print("\n--- In CSV but NOT in GeoJSON ---")
print(pop_set - geo_set)