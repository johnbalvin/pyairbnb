from datetime import datetime
from urllib.parse import urlencode
import pyairbnb.utils as utils
from curl_cffi import requests
import re

ep_autocomplete = "https://www.airbnb.com/api/v2/autocompletes-personalized"
ep_market = "https://www.airbnb.com/api/v2/user_markets"

treament = [
	"feed_map_decouple_m11_treatment",
	"stays_search_rehydration_treatment_desktop",
	"stays_search_rehydration_treatment_moweb",
	"selective_query_feed_map_homepage_desktop_treatment",
	"selective_query_feed_map_homepage_moweb_treatment",
]

headers_global = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en",
    "Cache-Control": "no-cache",
    "content-type": "application/json",
    "Connection": "close",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_stays_search_hash(proxy_url: str = "") -> str:
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    headers = {"User-Agent": headers_global["User-Agent"]}

    homepage = requests.get(
        "https://www.airbnb.com/",
        headers=headers,
        proxies=proxies,
        impersonate="chrome124",
    )
    homepage.raise_for_status()

    bundle_match = re.compile(
        r"https://a0\.muscache\.com/airbnb/static/packages/web/[^/]+/frontend/airmetro/browser/asyncRequire\.[^\"']+\.js"
    ).search(homepage.text)
    if not bundle_match:
        raise RuntimeError("Unable to locate StaysSearch bundle")

    bundle = requests.get(
        bundle_match.group(0), headers=headers, proxies=proxies, impersonate="chrome124"
    )
    bundle.raise_for_status()

    module_match = re.compile(
        r"common/frontend/stays-search/routes/StaysSearchRoute/StaysSearchRoute\.prepare\.[^\"']+\.js"
    ).search(bundle.text)
    if not module_match:
        raise RuntimeError("Unable to locate StaysSearchRoute module")

    module_url = f"https://a0.muscache.com/airbnb/static/packages/web/{module_match.group(0)}"
    module = requests.get(module_url, headers=headers, proxies=proxies, impersonate="chrome124")
    module.raise_for_status()

    hash_match = re.compile(r"operationId:['\"]([0-9a-f]{64})").search(module.text)
    if not hash_match:
        raise RuntimeError("Unable to extract StaysSearch operationId")

    return hash_match.group(1)

def get(api_key:str, cursor:str, check_in:str, check_out:str, ne_lat:float, ne_long:float, sw_lat:float, sw_long:float, zoom_value:int, currency:str, place_type: str, price_min: int, price_max: int, amenities: list, free_cancellation: bool, language: str, proxy_url:str, hash:str):
    
    operationId = hash if hash else '9f945886dcc032b9ef4ba770d9132eb0aa78053296b5405483944c229617b00b'
    base_url = f"https://www.airbnb.com/api/v3/StaysSearch/{operationId}"

    query_params = {
        "operationName": "StaysSearch",
        "locale": language,
        "currency": currency,
    }
    url_parsed = f"{base_url}?{urlencode(query_params)}"
    rawParams=[
        {"filterName":"cdnCacheSafe","filterValues":["false"]},
        {"filterName":"channel","filterValues":["EXPLORE"]},
        {"filterName":"datePickerType","filterValues":["calendar"]},
        {"filterName":"flexibleTripLengths","filterValues":["one_week"]},
        {"filterName":"itemsPerGrid","filterValues":["50"]},#if you read this, this is items returned number, this can bex exploited  ;)
        {"filterName":"monthlyLength","filterValues":["3"]},
        {"filterName":"monthlyStartDate","filterValues":["2024-02-01"]},
        {"filterName":"neLat","filterValues":[str(ne_lat)]},
        {"filterName":"neLng","filterValues":[str(ne_long)]},
        {"filterName":"placeId","filterValues":["ChIJpTeBx6wjq5oROJeXkPCSSSo"]},
        {"filterName":"priceFilterInputType","filterValues":["0"]},
        {"filterName":"query","filterValues":["Galapagos Island, Ecuador"]},
        {"filterName":"screenSize","filterValues":["large"]},
        {"filterName":"refinementPaths","filterValues":["/homes"]},
        {"filterName":"searchByMap","filterValues":["true"]},
        {"filterName":"swLat","filterValues":[str(sw_lat)]},
        {"filterName":"swLng","filterValues":[str(sw_long)]},
        {"filterName":"tabId","filterValues":["home_tab"]},
        {"filterName":"version","filterValues":["1.8.3"]},
        {"filterName":"zoomLevel","filterValues":[str(zoom_value)]},
    ]

    if check_in is not None and len(check_in) > 0 and check_out is not None and len(check_out) > 0:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")

        difference = check_out_date - check_in_date
        days = difference.days
        rawParams.extend([
            {"filterName":"checkin","filterValues":[check_in]},
            {"filterName":"checkout","filterValues":[check_out]},
            {"filterName":"priceFilterNumNights","filterValues":[str(days)]},
        ])

    if place_type is not None and place_type in ("Private room","Entire home/apt"):
        rawParams.append({"filterName":"room_types","filterValues": [place_type]})
        rawParams.append({"filterName":"selected_filter_order","filterValues": ["room_types:"+place_type]})

    if price_min is not None and price_min > 0:
        rawParams.append({"filterName":"price_min","filterValues": [str(price_min)]})

    if price_max is not None and price_max > 0:
        rawParams.append({"filterName":"price_max","filterValues": [str(price_max)]})
        
    # Add amenities filtering if provided
    if amenities is not None and len(amenities) > 0:
        # Add each amenity as a separate filter
        amenity_str_values = [str(amenity_id) for amenity_id in amenities]
        rawParams.append({"filterName":"amenities","filterValues": amenity_str_values})
        
        # Add selected filter order for each amenity
        for amenity_id in amenities:
            rawParams.append({"filterName":"selected_filter_order","filterValues": [f"amenities:{amenity_id}"]})

    # Add free cancellation filtering if provided
    if free_cancellation is not None and free_cancellation:
        rawParams.append({"filterName":"flexible_cancellation","filterValues": ["true"]})
        rawParams.append({"filterName":"selected_filter_order","filterValues": ["flexible_cancellation:true"]})

    inputData = {
        "operationName":"StaysSearch",
        "extensions":{
            "persistedQuery": {
                "version": 1,
                "sha256Hash": operationId,
            },
        },
        "variables":{
            "skipExtendedSearchParams": False,
            "includeMapResults": True,
            "isLeanTreatment": False,
            "aiSearchEnabled": False, # required for dynamic StaysSearch hash
            "staysMapSearchRequestV2": {
                "cursor":cursor,
                "requestedPageType":"STAYS_SEARCH",
                "metadataOnly":False,
                "source":"structured_search_input_header",
                "searchType":"user_map_move",
                "treatmentFlags":treament,
                "rawParams":rawParams,
            },
            "staysSearchRequest": {
                "cursor":cursor,
                "maxMapItems": 9999,
                "requestedPageType":"STAYS_SEARCH",
                "metadataOnly":False,
                "source":"structured_search_input_header",
                "searchType":"user_map_move",
                "treatmentFlags":treament,
                "rawParams":rawParams,
            },
        },
    }
    headers_copy = headers_global.copy()
    headers_copy["X-Airbnb-Api-Key"] = api_key
    proxies = {}
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    response = requests.post(url_parsed, json = inputData, headers=headers_copy, proxies=proxies,  impersonate="chrome124")
    if response.status_code != 200:
        raise Exception("Not corret status code: ", response.status_code, " response body: ",response.text)
    data = response.json()
    return data

def get_markets(currency: str, locale: str, api_key: str, proxy_url: str):
    query_params = {
        "locale": locale,
        "currency": currency,
        "language": "en",
    }
    url_parsed = f"{ep_market}?{urlencode(query_params)}"
    headers_copy = headers_global.copy()
    headers_copy["X-Airbnb-Api-Key"] = api_key
    proxies = {}
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    response = requests.get(url_parsed, headers=headers_copy, proxies=proxies, impersonate="chrome124")
    if response.status_code != 200:
        raise Exception("Not corret status code: ", response.status_code, " response body: ",response.text)
    data = response.json()
    return data

def get_places_ids(country: str, location_name: str, currency: str, locale: str, config_token: str, api_key: str, proxy_url: str):
    query_params = {
        "currency": currency,
        "country": country,
        "key": api_key,
        "language": "en",
        "locale": locale,
        "num_results": 10,
        "user_input": location_name,
        "api_version": "1.2.0",
        "satori_config_token": config_token,
        "vertical_refinement": "experiences",
        "region": "-1",
        "options": "should_filter_by_vertical_refinement%7Chide_nav_results%7Cshould_show_stays%7Csimple_search%7Cflex_destinations_june_2021_launch_web_treatment"
    }
    url_parsed = f"{ep_autocomplete}?{urlencode(query_params)}"
    headers_copy = headers_global.copy()
    headers_copy["X-Airbnb-Api-Key"] = api_key
    proxies = {}
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    response = requests.get(url_parsed, headers=headers_copy, proxies=proxies, impersonate="chrome124")
    if response.status_code != 200:
        raise Exception("Not corret status code: ", response.status_code, " response body: ",response.text)
    data = response.json()
    to_return=utils.get_nested_value(data,"autocomplete_terms", [])
    return to_return
