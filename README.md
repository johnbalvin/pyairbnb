# Airbnb scraper in Python

## Overview
This project is an open-source tool developed in Python for extracting product information from Airbnb. It's designed to be easy to use, making it an ideal solution for developers looking for Airbnb product data.

## Features
- Extract prices, available dates, reviews, host details and others
- Full search support with filtering by amenities and free cancellation
- Extracts detailed product information from Airbnb
- Implemented in Python just because it's popular
- Easy to integrate with existing Python projects

## Legacy
- This was a project first implemented on:[https://github.com/johnbalvin/pybnb](https://github.com/johnbalvin/pybnb) but was moved to [https://github.com/johnbalvin/pyairbnb](https://github.com/johnbalvin/pyairbnb)
to match the name with pip name

## Important
- With the new airbnb changes, if you want to get the price from a room url you need to specify the date range
the date range should be on the format year-month-day, if you leave the date range empty, you will get the details but not the price


### Install

```bash
$ pip install pyairbnb
```
## Examples

### Example for Searching Listings

```python
import pyairbnb
import json

# Define search parameters
currency = "MXN"  # Currency for the search
check_in = "2025-10-01"  # Check-in date
check_out = "2025-10-04"  # Check-out date
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
```

### Example: Searching via a full Airbnb URL

```python
import pyairbnb
import json

# Define an Airbnb search URL using only the supported parameters (including free cancellation)
url = "https://www.airbnb.com/s/Luxembourg--Luxembourg/homes?checkin=2026-02-09&checkout=2026-02-16&ne_lat=49.76537&ne_lng=6.56057&sw_lat=49.31155&sw_lng=6.03263&zoom=10&price_min=154&price_max=700&room_types%5B%5D=Entire%20home%2Fapt&amenities%5B%5D=4&amenities%5B%5D=5&flexible_cancellation=true"

# Fetches the live StaysSearch hash first so
# the persisted query id matches airbnb website.
dynamic_hash = pyairbnb.fetch_stays_search_hash()
# Use the URL wrapper
results = pyairbnb.search_all_from_url(
    url,
    currency="EUR",
    language="es",
    proxy_url="",
    hash=dynamic_hash, # optional, fallbacks to predefined hash
)

# Save results and print count
with open('search_from_url.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Found {len(results)} listings from URL search.")
```

### Retrieving Details for Listings

### Getting price
```python
room_url="https://www.airbnb.com/rooms/30931885"
check_in = "2025-10-10"
check_out = "2025-10-12"
proxy_url = ""  # Proxy URL (if needed)
language="de"
data, price_input, cookies = details.get(room_url, language, proxy_url)
product_id = price_input["product_id"]
api_key = price_input["api_key"]
currency = "USD"
adults=1
data = price.get(api_key, cookies, price_input["impression_id"], product_id, 
            check_in, check_out, adults, currency, language, proxy_url)

with open('price.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(data))
```


### Getting listings from user id
```Python
import pyairbnb
import json
host_id = 656454528
api_key = pyairbnb.get_api_key("")
listings = pyairbnb.get_listings_from_user(host_id,api_key,"")
with open('listings.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(listings))
```

### Getting details from user id
```Python
import pyairbnb
import json
host_id = "656454528"
language = "en"
api_key = pyairbnb.get_api_key("")
listings = pyairbnb.get_host_details(api_key, None, host_id, language, "")
with open('listings.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(listings))
```

### Getting experiences by just taking the first autocompletions that you would normally do manually on the website
```Python
import pyairbnb
import json
check_in = "2025-10-10"
check_out = "2025-10-12"
currency = "EUR"
user_input_text = "Estados Unidos"
locale = "es"
proxy_url = ""  # Proxy URL (if needed)
api_key = pyairbnb.get_api_key("")
experiences = pyairbnb.experience_search(user_input_text, currency, locale, check_in, check_out, api_key, proxy_url)
with open('experiences.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(experiences))
```

### Getting experiences by first getting the autocompletions
```Python
import pyairbnb
import json
check_in = "2025-10-06"
check_out = "2025-10-10"
currency = "USD"
user_input_text = "cuenca"
locale = "pt"
proxy_url = ""  # Proxy URL (if needed)
api_key = pyairbnb.get_api_key("")
markets_data = pyairbnb.get_markets(currency,locale,api_key,proxy_url)
markets = pyairbnb.get_nested_value(markets_data,"user_markets", [])
if len(markets)==0:
    raise Exception("markets are empty")
config_token = pyairbnb.get_nested_value(markets[0],"satori_parameters", "")
country_code = pyairbnb.get_nested_value(markets[0],"country_code", "")
if config_token=="" or country_code=="":
    raise Exception("config_token or country_code are empty")
place_ids_results = pyairbnb.get_places_ids(country_code, user_input_text, currency, locale, config_token, api_key, proxy_url)
if len(place_ids_results)==0:
    raise Exception("empty places ids")
place_id = pyairbnb.get_nested_value(place_ids_results[0],"location.google_place_id", "")
location_name = pyairbnb.get_nested_value(place_ids_results[0],"location.location_name", "")
if place_id=="" or location_name=="":
    raise Exception("place_id or location_name are empty")
[result,cursor] = pyairbnb.experience_search_by_place_id("", place_id, location_name, currency, locale, check_in, check_out, api_key, proxy_url)
while cursor!="":
    [result_tmp,cursor] = pyairbnb.experience_search_by_place_id(cursor, place_id, location_name, currency, locale, check_in, check_out, api_key, proxy_url)
    if len(result_tmp)==0:
        break
    result = result + result_tmp
with open('experiences.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(result))
```

### Getting available/unavailable homes along with metadata
```Python
import pyairbnb
import json

# Define listing URL and parameters
room_url = "https://www.airbnb.com/rooms/51752186"  # Listing URL
currency = "USD"  # Currency for the listing details
checkin = "2025-10-12"
checkout = "2025-10-17"
# Retrieve listing details without including the price information (no check-in/check-out dates)
data = pyairbnb.get_details(room_url=room_url, currency=currency,adults=2, language="ja")

# Save the retrieved details to a JSON file
with open('details_data.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(data))  # Convert the data to JSON and save it
```

#### Retrieve Details Using Room ID with Proxy
You can also use `get_details` with a room ID and an optional proxy.

```python
import pyairbnb
from urllib.parse import urlparse
import json

# Define listing parameters
room_id = 18039593  # Listing room ID
currency = "MXN"  # Currency for the listing details
proxy_url = ""  # Proxy URL (if needed)

# Retrieve listing details by room ID with a proxy
checkin = "2025-10-12"
checkout = "2025-10-17"
data = pyairbnb.get_details(room_id=room_id, currency=currency, proxy_url=proxy_url,adults=3, language="ko")

# Save the retrieved details to a JSON file
with open('details_data.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(data))  # Convert the data to JSON and save it
```

### Retrieve Reviews for a Listing
Use `get_reviews` to extract reviews and metadata for a specific listing.

```python
import pyairbnb
import json

# Define listing URL and proxy URL
room_url = "https://www.airbnb.com/rooms/30931885"  # Listing URL
proxy_url = ""  # Proxy URL (if needed)
language = "fr"
# Retrieve reviews for the specified listing
reviews_data = pyairbnb.get_reviews(room_url, language, proxy_url)

# Save the reviews data to a JSON file
with open('reviews.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(reviews_data))  # Extract reviews and save them to a file
```

### Retrieve Availability for a Listing
The `get_calendar` function provides availability information for specified listings.

```python
import pyairbnb
import json

# Define listing parameters
room_id = "44590727"  # Listing room ID
proxy_url = ""  # Proxy URL (if needed)

# Retrieve availability for the specified listing
calendar_data = pyairbnb.get_calendar(room_id, "", proxy_url)

# Save the calendar data (availability) to a JSON file
with open('calendar.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(calendar_data))  # Extract calendar data and save it to a file
```
