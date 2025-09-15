import pyairbnb.details as details
import pyairbnb.reviews as reviews
import pyairbnb.price as price
import pyairbnb.api as api
import pyairbnb.search as search
import pyairbnb.utils as utils
import pyairbnb.standardize as standardize
import pyairbnb.experience as experience
import pyairbnb.calendarinfo as calendar
import pyairbnb.host_details as host_details
from datetime import datetime
from urllib.parse import urlparse

def get_calendar(api_key: str = "", room_id: str = "", proxy_url: str = ""):
    """
    Retrieves the calendar data for a specified room.

    Args:
        room_id (str): The room ID.
        api_key (str): The API key.
        proxy_url (str): The proxy URL.

    Returns:
        dict: Calendar data.
    """
    if not api_key:
        api_key = api.get(proxy_url)

    current_month = datetime.now().month
    current_year = datetime.now().year
    return calendar.get(api_key, room_id, current_month, current_year, proxy_url)

def get_reviews(room_url: str ,language: str = "en", proxy_url: str = ""):
    """
    Retrieves review data for a specified product.

    Args:
        room_url (str): The product room_url.
        proxy_url (str): The proxy URL.
        language (str): The language (default is 'en').
        currency (str): The currency (default is 'USD').

    Returns:
        dict: Reviews data.
    """
    data, price_input, cookies = details.get(room_url, language, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]

    return reviews.get(api_key, product_id, "USD", language, proxy_url)

def get_details(room_url: str = None, room_id: int = None, domain: str = "www.airbnb.com", check_in: str = None, check_out: str = None, adults: int = 1, currency: str = "USD", language: str = "en", proxy_url: str = ""):
    """
    Retrieves all details (calendar, reviews, price, and host details) for a specified room.

    Args:
        room_url (str): The room URL (optional if room_id is provided).
        room_id (int): The room ID (optional if room_url is provided).
        domain (str): The domain (default is 'www.airbnb.com').
        currency (str): Currency for pricing information.
        check_in (str): Check-in date for price information.
        check_out (str): Check-out date for price information.
        language (str): The language (default is 'en').
        proxy_url (str): Proxy URL.

    Returns:
        dict: A dictionary with all room details.
    """
    if not room_url and room_id is None:
        raise ValueError("Either room_url or room_id must be provided.")
    
    if not room_url:
        room_url = f"https://{domain}/rooms/{room_id}"
    
    data, price_input, cookies = details.get(room_url, language, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]
    
    # Extract room_id from URL if not provided
    if room_id is None:
        parsed_url = urlparse(room_url)
        path = parsed_url.path
        room_id = path.split("/")[-1]
    
    # Get calendar and reviews data
    data["reviews"] = reviews.get(api_key, product_id, currency, language, proxy_url)
    data["calendar"] = get_calendar(api_key, room_id, proxy_url)
    
    # Get price data if check-in and check-out dates are provided
    if check_in and check_out:
        price_data = price.get(
            api_key, cookies, price_input["impression_id"], product_id, check_in, check_out, adults, 
            currency, language, proxy_url
        )
        data["price"] = price_data
    
    # Get host details
    host_id = data["host"]["id"]
    data["host_details"] = host_details.get(api_key, cookies, host_id, language, proxy_url)
    
    return data

def search_all(check_in: str, check_out: str, ne_lat: float, ne_long: float, sw_lat: float, sw_long: float,
               zoom_value: int, price_min: int, price_max: int, place_type: str = "", amenities: list = [], free_cancellation: bool = False, currency: str = "USD", language: str = "en", proxy_url: str = "", hash: str = ""):
    """
    Performs a paginated search for all rooms within specified geographic bounds.

    Args:
        check_in (str): Check-in date.
        check_out (str): Check-out date.
        ne_lat (float): Latitude of northeast corner.
        ne_long (float): Longitude of northeast corner.
        sw_lat (float): Latitude of southwest corner.
        sw_long (float): Longitude of southwest corner.
        zoom_value (int): Zoom level.
        currency (str): Currency for pricing information.
        amenities (list): List of amenity IDs to filter
        free_cancellation (bool): Filter for listings with free cancellation
        language (str): language to use for example en,es,tr ..etc
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of all search results.
    """
    api_key = api.get(proxy_url)
    all_results = []
    cursor = ""
    while True:
        results_raw = search.get(
            api_key, cursor, check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, 
            currency, place_type, price_min, price_max, amenities, free_cancellation, language, proxy_url, hash
        )
        paginationInfo = utils.get_nested_value(results_raw,"data.presentation.staysSearch.results.paginationInfo",{})
        results = standardize.from_search(results_raw)
        all_results.extend(results)
        if not results or "nextPageCursor" not in paginationInfo or paginationInfo["nextPageCursor"] is None:
            break
        cursor = paginationInfo["nextPageCursor"]
    return all_results

def search_first_page(check_in: str, check_out: str, ne_lat: float, ne_long: float, sw_lat: float, sw_long: float,
               zoom_value: int, price_min: int, price_max: int, place_type: str = "", amenities: list = [], free_cancellation: bool = False, currency: str = "USD", language: str = "en", proxy_url: str = "", hash: str = ""):
    """
    Searches the first page of results within specified geographic bounds.

    Args:
        check_in (str): Check-in date.
        check_out (str): Check-out date.
        ne_lat (float): Latitude of northeast corner.
        ne_long (float): Longitude of northeast corner.
        sw_lat (float): Latitude of southwest corner.
        sw_long (float): Longitude of southwest corner.
        zoom_value (int): Zoom level.
        currency (str): Currency for pricing information.
        amenities (list): List of amenity IDs to filter
        free_cancellation (bool): Filter for listings with free cancellation
        language (str): language to use for example en,es,tr ..etc
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of search results from the first page.
    """
    api_key = api.get(proxy_url)
    results_raw = search.get(
        api_key, "", check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, 
        currency, place_type, price_min, price_max, amenities, free_cancellation, language, proxy_url, hash=hash
    )

    results = standardize.from_search(results_raw.get("searchResults", []))
    return results


def search_experience_by_taking_the_first_inputs_i_dont_care(user_input_text: str, currency:str, locale: str, check_in:str, check_out:str, api_key:str, proxy_url:str):
    markets_data = search.get_markets(currency,locale,api_key,proxy_url)
    markets = utils.get_nested_value(markets_data,"user_markets", [])
    if len(markets)==0:
        raise Exception("markets are empty")
    config_token = utils.get_nested_value(markets[0],"satori_parameters", "")
    country_code = utils.get_nested_value(markets[0],"country_code", "")
    if config_token=="" or country_code=="":
        raise Exception("config_token or country_code are empty")
    place_ids_results = search.get_places_ids(country_code, user_input_text, currency, locale, config_token, api_key, proxy_url)
    if len(place_ids_results)==0:
        raise Exception("empty places ids")
    place_id = utils.get_nested_value(place_ids_results[0],"location.google_place_id", "")
    location_name = utils.get_nested_value(place_ids_results[0],"location.location_name", "")
    if place_id=="" or location_name=="":
        raise Exception("place_id or location_name are empty")
    [result,cursor] = experience.search_by_place_id("", place_id, location_name, currency, locale, check_in, check_out, api_key, proxy_url)
    while cursor!="":
        [result_tmp,cursor] = experience.search_by_place_id(cursor, place_id, location_name, currency, locale, check_in, check_out, api_key, proxy_url)
        if len(result_tmp)==0:
            break
        result = result + result_tmp
    return result

def search_all_from_url(url: str, currency: str = "USD", language: str = "en", proxy_url: str = "", hash: str = ""):
    """
    Wrapper that parses an Airbnb search URL and delegates to search_all.
    """
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    # Extract required parameters
    check_in = qs.get("checkin", [None])[0]
    check_out = qs.get("checkout", [None])[0]
    ne_lat = float(qs.get("ne_lat", [0])[0])
    ne_long = float(qs.get("ne_lng", [0])[0])
    sw_lat = float(qs.get("sw_lat", [0])[0])
    sw_long = float(qs.get("sw_lng", [0])[0])

    # Determine zoom value
    zoom_str = qs.get("zoom_level", qs.get("zoom", [0]))[0]
    zoom_value = int(float(zoom_str))

    # Price filters
    price_min = int(qs.get("price_min", [0])[0])
    price_max = int(qs.get("price_max", [0])[0])

    # Place type filter
    place_type = qs.get("room_types[]", [None])[0]

    # Amenities list
    amenities = []
    for a in qs.get("amenities[]", []):
        try:
            amenities.append(int(a))
        except ValueError:
            continue

    # Free cancellation filter
    free_cancellation = qs.get("flexible_cancellation", ["false"])[0].lower() == "true"

    # Delegate to existing search_all
    return search_all(
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
        proxy_url=proxy_url,
        hash=hash
    )