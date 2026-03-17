import requests
import pandas as pd
import time

# Bangladesh bounding box
BBOX = "20.5,88.0,26.7,92.7"  # south,west,north,east

def query_osm(amenity_type, extra_filter=""):  # <-- added extra_filter param
    query = f"""
    [out:json][timeout:90];
    node["amenity"="{amenity_type}"{extra_filter}]({BBOX});
    out body;
    """
    encoded_query = requests.utils.quote(query)
    url = f"https://overpass-api.de/api/interpreter?data={encoded_query}"

    response = requests.get(url, timeout=120)
    print(f"  {amenity_type}: status {response.status_code}", end=" ")

    if response.status_code == 200:
        data = response.json()
        elements = data.get('elements', [])
        print(f"→ {len(elements)} found")
        return elements
    else:
        print(f"→ failed: {response.text[:100]}")
        return []

def elements_to_df(elements, amenity_type):
    rows = []
    for el in elements:
        tags = el.get('tags', {})
        rows.append({
            'name':     tags.get('name:en') or tags.get('name', 'Unknown'),
            'amenity':  amenity_type,
            'lat':      el['lat'],
            'lon':      el['lon'],
            'district': tags.get('addr:district', None),
            'phone':    tags.get('phone', None),
            'beds':     tags.get('capacity:beds', None),
        })
    return pd.DataFrame(rows)

# Query each type with delay to avoid rate limit
print("Querying OpenStreetMap...")
time.sleep(2)
hospital_els = query_osm('hospital')
time.sleep(5)
clinic_els   = query_osm('clinic')
time.sleep(5)
# REMOVED: shelter_els — no official shelter data in OSM for Bangladesh
# PRIMARY SCHOOLS only as emergency shelters
school_els   = query_osm('school', '["isced:level"="1"]')  # <-- primary only
time.sleep(5)
# Fallback — all schools in case isced tag count is low
all_school_els = query_osm('school')

# Convert to DataFrames
hospitals = elements_to_df(hospital_els,   'hospital')
clinics   = elements_to_df(clinic_els,     'clinic')
schools   = elements_to_df(school_els,     'primary_school')
all_schools = elements_to_df(all_school_els, 'school')

print("\n--- Coverage Summary ---")
print(f"Hospitals             : {len(hospitals)}")
print(f"Clinics               : {len(clinics)}")
print(f"Primary schools (tagged): {len(schools)}")
print(f"All schools (fallback): {len(all_schools)}")

# Use primary tagged if count > 500, otherwise fall back to all schools
final_schools = schools if len(schools) > 500 else all_schools
print(f"\nUsing: {len(final_schools)} schools as emergency shelters")

# Save
hospitals.to_csv('../data/osm_hospitals.csv',  index=False)
clinics.to_csv('../data/osm_clinics.csv',      index=False)
final_schools.to_csv('../data/osm_schools.csv', index=False)  # REMOVED shelters

print("\nSaved to ../data/")