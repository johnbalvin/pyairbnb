import pyairbnb
import json
#
check_in = "2026-05-15"
check_out = "2026-05-17"
currency = "EUR"
user_input_text = "Luxembourg"
locale = "pt"
proxy_url = ""  # Proxy URL (if needed)
zoom_value=2
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
print("place_id: ",place_id)
print("location_name: ",location_name)
bb=place_ids_results[0]["location"]["bounding_box"]
ne_lat = bb["ne_lat"]
ne_long = bb["ne_lng"]
sw_lat = bb["sw_lat"]
sw_long = bb["sw_lng"]
price_min = 0
price_max = 0
place_type = ""
amenities = []
free_cancellation = False
currency = currency
language = "en"
proxy_url = ""

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
with open('search_results1.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(search_results))  # Convert results to JSON and write to file

room_url = "https://www.airbnb.com/rooms/51752186"  # Listing URL
currency = "USD"  # Currency for the listing details
check_in = "2026-05-15"
check_out = "2026-05-17"
# Retrieve listing details without including the price information (no check-in/check-out dates)
data = pyairbnb.get_details(room_url=room_url, currency=currency,adults=4,check_in=check_in,check_out=check_out)

# Save the retrieved details to a JSON file
with open('details_data.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(data))  # Convert the data to JSON and save it

# Dynamically fetching operationId
dynamic_hash = pyairbnb.fetch_stays_search_hash()
# Test search_all_from_url using a sample Airbnb URL with various filters.
results = pyairbnb.search_all_from_url(
    "https://www.airbnb.com/s/Luxembourg--Luxembourg/homes?checkin=2026-05-15&checkout=2026-05-16&ne_lat=49.765370668280966&ne_lng=6.560570632398054&sw_lat=49.31155139251553&sw_lng=6.0326271739902495&zoom=10&price_min=22&price_max=200&room_types%5B%5D=Entire%20home%2Fapt&amenities%5B%5D=4&amenities%5B%5D=5&flexible_cancellation=true",
    currency="USD",
    proxy_url="",
    hash=dynamic_hash,
)

with open('search_results_from_url.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(results))  # Convert the data to JSON and save it

print(f"Retrieved {len(results)} listings from URL search.")