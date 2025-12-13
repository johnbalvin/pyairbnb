import pyairbnb
import json

# Define search parameters
currency = "MXN"  # Currency for the search
check_in = "2026-01-01"  # Check-in date
check_out = "2026-01-04"  # Check-out date
ne_lat = -0.6747456399483214 # North-East latitude
ne_long = -90.30058677891441  # North-East longitude
sw_lat = -0.7596840340260731  # South-West latitude
sw_long = -90.36727562895442  # South-West longitude
zoom_value = 2  # Zoom level for the map
price_min = 1000
price_max = 0
place_type = "Private room" #or "Entire home/apt" or empty
amenities = [4, 7]  # Example: Filter for listings with WiFi and Pool or leave empty
free_cancellation = False  # Filter for listings with free/flexible cancellation
language = "th"
proxy_url = ""

# Search listings within specified coordinates and date range using keyword arguments
search_results = pyairbnb.search_all(
    check_in=check_in,
    check_out=check_out,
    ne_lat=ne_lat,
    ne_long=ne_long,
    sw_lat=sw_lat,
    sw_long=sw_long,
    zoom_value=zoom_value,
    price_min=price_min,
    price_max=price_max,
    place_type=place_type,
    amenities=amenities,
    free_cancellation=free_cancellation,
    currency=currency,
    language=language,
    proxy_url=proxy_url
)

# Save the search results as a JSON file
with open('search_results.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(search_results))  # Convert results to JSON and write to file