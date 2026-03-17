import requests
import pandas as pd
import time

BBOX = "20.5,88.0,26.7,92.7"

def query_osm(amenity_type, retries=3):
    query = f"""
    [out:json][timeout:90];
    node["amenity"="{amenity_type}"]({BBOX});
    out body;
    """
    encoded_query = requests.utils.quote(query)
    url = f"https://overpass-api.de/api/interpreter?data={encoded_query}"

    for attempt in range(retries):
        print(f"  {amenity_type}: attempt {attempt+1}...", end=" ")
        response = requests.get(url, timeout=120)
        print(f"status {response.status_code}", end=" ")

        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            print(f"→ {len(elements)} found")
            return elements
        elif response.status_code == 429:
            wait = 30 * (attempt + 1)   # 30s, 60s, 90s
            print(f"→ rate limited, waiting {wait}s...")
            time.sleep(wait)
        else:
            print(f"→ failed: {response.text[:80]}")
            return []

    print(f"  {amenity_type}: all retries failed")
    return []

def elements_to_df(elements, label):
    rows = []
    for el in elements:
        tags = el.get('tags', {})
        rows.append({
            'name':     tags.get('name:en') or tags.get('name', 'Unknown'),
            'amenity':  label,
            'lat':      el['lat'],
            'lon':      el['lon'],
            'district': tags.get('addr:district', None),
            'phone':    tags.get('phone', None),
            'beds':     tags.get('capacity:beds', None),
        })
    return pd.DataFrame(rows)

print("Querying OpenStreetMap...")

# hospitals and clinics already saved — skip them
# Only fetch school with long wait first
print("Waiting 60s before school query to reset rate limit...")
time.sleep(60)
school_els = query_osm('school')

print("\n--- Result ---")
print(f"Schools: {len(school_els)}")

if len(school_els) > 0:
    schools = elements_to_df(school_els, 'school')
    schools.to_csv('../data/osm_schools.csv', index=False)
    print("Saved to ../data/osm_schools.csv")
    print(schools.head(3))
else:
    print("Still failed — use the alternative below")