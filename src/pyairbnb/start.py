
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

def get_calendar(room_id: str ,api_key: str = "", proxy_url: str = ""):
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
    return calendar.get(room_id, current_month, current_year, api_key, proxy_url)

def get_reviews(room_url: str , api_key: str = "", proxy_url: str = ""):
    """
    Retrieves review data for a specified product.

    Args:
        room_url (str): The product room_url.
        api_key (str): The API key.
        proxy_url (str): The proxy URL.

    Returns:
        dict: Reviews data.
    """
    data, price_input, cookies = details.get(room_url, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]

    return reviews.get(product_id, api_key, proxy_url)

def get_details(room_url: str = None, room_id: int = None, domain: str = "www.airbnb.com",
                currency: str = None, check_in: str = None, check_out: str = None, proxy_url: str = None):
    """
    Retrieves all details (calendar, reviews, price, and host details) for a specified room.

    Args:
        room_url (str): The room URL (optional if room_id is provided).
        room_id (int): The room ID (optional if room_url is provided).
        domain (str): The domain (default is 'www.airbnb.com').
        currency (str): Currency for pricing information.
        check_in (str): Check-in date for price information.
        check_out (str): Check-out date for price information.
        proxy_url (str): Proxy URL.

    Returns:
        dict: A dictionary with all room details.
    """
    if not room_url and room_id is None:
        raise ValueError("Either room_url or room_id must be provided.")
    
    if not room_url:
        room_url = f"https://{domain}/rooms/{room_id}"
    
    data, price_input, cookies = details.get(room_url, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]
    
    # Extract room_id from URL if not provided
    if room_id is None:
        parsed_url = urlparse(room_url)
        path = parsed_url.path
        room_id = path.split("/")[-1]
    
    # Get calendar and reviews data
    data["calendar"] = get_calendar(room_id, api_key, proxy_url)
    data["reviews"] = get_reviews(room_url, api_key, proxy_url)
    
    # Get price data if check-in and check-out dates are provided
    if check_in and check_out:
        price_data = price.get(
            product_id, price_input["impression_id"], api_key, currency, cookies,
            check_in, check_out, proxy_url
        )
        data["price"] = price_data
    
    # Get host details
    host_id = data["host"]["id"]
    data["host_details"] = host_details.get(host_id, api_key, proxy_url, cookies)
    
    return data

def search_all(check_in: str, check_out: str, ne_lat: float, ne_long: float, sw_lat: float, sw_long: float,
               zoom_value: int, currency: str, proxy_url: str):
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
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of all search results.
    """
    api_key = api.get(proxy_url)
    all_results = []
    cursor = ""
    while True:
        results_raw = search.get(
            check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value,
            cursor, currency, api_key, proxy_url
        )
        results = standardize.from_search(results_raw.get("searchResults", []))
        all_results.extend(results)
        if not results or "nextPageCursor" not in results_raw["paginationInfo"] or results_raw["paginationInfo"]["nextPageCursor"] is None:
            break
        cursor = results_raw["paginationInfo"]["nextPageCursor"]
    return all_results

def search_first_page(check_in: str, check_out: str, ne_lat: float, ne_long: float,
                      sw_lat: float, sw_long: float, zoom_value: int, currency: str, proxy_url: str):
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
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of search results from the first page.
    """
    api_key = api.get(proxy_url)
    results_raw = search.get(
        check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value,
        "", currency, api_key, proxy_url
    )
    return standardize.from_search(results_raw)


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