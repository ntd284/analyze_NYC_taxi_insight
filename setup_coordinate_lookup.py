#setup_coordinate_lookup.py
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

df_lookup = pd.read_csv("output_data/taxi_zone_lookup.csv")
geolocator = Nominatim(user_agent="Geopy Library")
geocode = RateLimiter(geolocator.geocode)

# Function to get coordinates for a given zone
def get_coordinates(zone):
    max_retries = 100
    for amount in range(max_retries):
        try:
            location = geocode(zone)
            print(location)
            break
        except:
            max_retries-=1
            time.sleep(1)
        
    return (location.latitude, location.longitude) if location else (None, None)
df_lookup['zone'] = df_lookup['zone'].apply(lambda x: x.split('/')[0] if isinstance(x, str) else x)

df_lookup['latitude'], df_lookup['longitude'] = zip(*df_lookup['zone'].apply(get_coordinates))
df_lookup.to_csv("output_data/taxi_lookup.csv")
