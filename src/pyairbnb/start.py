import pyairbnb.details as details
import pyairbnb.reviews as reviews
import pyairbnb.price as price
import pyairbnb.api as api
import pyairbnb.search as search
import pyairbnb.utils as utils
import pyairbnb.standardize as standardize
import pyairbnb.experience as experience
import pyairbnb.calendarinfo as calendar
from pyairbnb.calendar_contract import (
    CalendarContractError,
    CalendarContractWarning,
)
from pyairbnb.models import CalendarMonth
from pyairbnb.parsers.calendar import parse_calendar
import pyairbnb.host_details as host_details
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout
from datetime import datetime
from typing import Any
from typing import Literal, overload
from urllib.parse import urlparse
import warnings


_UNSET = object()
_CURRENT_SEARCH_ARGUMENTS = (
    "price_min",
    "price_max",
    "place_type",
    "amenities",
    "free_cancellation",
    "adults",
    "children",
    "infants",
    "min_bedrooms",
    "min_beds",
    "min_bathrooms",
    "currency",
    "language",
    "proxy_url",
    "hash",
    "timeout",
)
_LEGACY_SEARCH_ARGUMENTS = (
    "currency",
    "place_type",
    "price_min",
    "price_max",
    "amenities",
    "language",
    "proxy_url",
)
_NUMERIC_SEARCH_ARGUMENTS = {
    "price_min",
    "price_max",
    "adults",
    "children",
    "infants",
    "min_bedrooms",
    "min_beds",
    "min_bathrooms",
}


def _search_defaults() -> dict[str, Any]:
    return {
        "price_min": 0,
        "price_max": 0,
        "place_type": "",
        "amenities": [],
        "free_cancellation": False,
        "adults": 0,
        "children": 0,
        "infants": 0,
        "min_bedrooms": 0,
        "min_beds": 0,
        "min_bathrooms": 0,
        "currency": "USD",
        "language": "en",
        "proxy_url": "",
        "hash": "",
        "timeout": DEFAULT_TIMEOUT,
    }


def _is_number(value: Any) -> bool:
    try:
        utils.coerce_number(value)
    except (TypeError, ValueError):
        return False
    return value is not None and value != ""


def _uses_legacy_search_order(
    positional_args: tuple[Any, ...], keyword_args: dict[str, Any]
) -> bool:
    if not positional_args:
        return False

    first = positional_args[0]
    if not isinstance(first, str) or first == "" or _is_number(first):
        return False

    if len(positional_args) >= 2 and _is_number(positional_args[1]):
        return False

    return len(positional_args) >= 2 or "price_min" in keyword_args


def _resolve_search_arguments(
    function_name: str,
    positional_args: tuple[Any, ...],
    keyword_args: dict[str, Any],
) -> dict[str, Any]:
    argument_names = (
        _LEGACY_SEARCH_ARGUMENTS
        if _uses_legacy_search_order(positional_args, keyword_args)
        else _CURRENT_SEARCH_ARGUMENTS
    )
    if len(positional_args) > len(argument_names):
        raise TypeError(
            f"{function_name}() received {len(positional_args)} positional search "
            f"arguments; expected at most {len(argument_names)}"
        )

    resolved = _search_defaults()
    assigned = set()
    for name, value in zip(argument_names, positional_args):
        resolved[name] = value
        assigned.add(name)

    for name, value in keyword_args.items():
        if name in assigned:
            raise TypeError(
                f"{function_name}() got multiple values for argument {name!r}"
            )
        resolved[name] = value

    for name in _NUMERIC_SEARCH_ARGUMENTS:
        resolved[name] = utils.coerce_number(resolved[name], name) or 0

    return resolved


@overload
def get_calendar(
    api_key: str = "",
    room_id: str = "",
    proxy_url: str = "",
    timeout: Timeout = DEFAULT_TIMEOUT,
    *,
    return_dataclass: Literal[False],
    on_dataclass_error: Literal["raise", "warn_return_dict"] = "warn_return_dict",
) -> list[dict[str, object]]: ...


@overload
def get_calendar(
    api_key: str = "",
    room_id: str = "",
    proxy_url: str = "",
    timeout: Timeout = DEFAULT_TIMEOUT,
    *,
    return_dataclass: Literal[True] = True,
    on_dataclass_error: Literal["raise"],
) -> list[CalendarMonth]: ...


@overload
def get_calendar(
    api_key: str = "",
    room_id: str = "",
    proxy_url: str = "",
    timeout: Timeout = DEFAULT_TIMEOUT,
    *,
    return_dataclass: Literal[True] = True,
    on_dataclass_error: Literal["warn_return_dict"] = "warn_return_dict",
) -> list[CalendarMonth] | list[dict[str, object]]: ...


@overload
def get_calendar(
    api_key: str = "",
    room_id: str = "",
    proxy_url: str = "",
    timeout: Timeout = DEFAULT_TIMEOUT,
    *,
    return_dataclass: bool = True,
    on_dataclass_error: Literal["raise", "warn_return_dict"] = "warn_return_dict",
) -> list[CalendarMonth] | list[dict[str, object]]: ...


def get_calendar(
    api_key: str = "",
    room_id: str = "",
    proxy_url: str = "",
    timeout: Timeout = DEFAULT_TIMEOUT,
    *,
    return_dataclass: bool = True,
    on_dataclass_error: Literal["raise", "warn_return_dict"] = "warn_return_dict",
) -> list[CalendarMonth] | list[dict[str, object]]:
    """
    Retrieves the calendar data for a specified room.

    Args:
        room_id (str): The room ID.
        api_key (str): The API key.
        proxy_url (str): The proxy URL.
        return_dataclass (bool): Return validated dataclasses when possible.
        on_dataclass_error (str): Raise on contract mismatches or warn and
            return the original dictionaries.

    Returns:
        list: Calendar months as dataclasses or raw dictionaries.
    """
    if type(return_dataclass) is not bool:
        raise TypeError("return_dataclass must be True or False")
    if on_dataclass_error not in ("raise", "warn_return_dict"):
        raise ValueError(
            'on_dataclass_error must be "raise" or "warn_return_dict"'
        )

    if not api_key:
        api_key = api.get(proxy_url, timeout=timeout)

    current_month = datetime.now().month
    current_year = datetime.now().year
    raw_calendar = calendar.get(
        api_key,
        room_id,
        current_month,
        current_year,
        proxy_url,
        timeout=timeout,
        require_calendar_path=return_dataclass,
    )
    if not return_dataclass:
        return raw_calendar

    try:
        return parse_calendar(raw_calendar)
    except CalendarContractError as error:
        if on_dataclass_error == "raise":
            raise
        warnings.warn(CalendarContractWarning(error.issues), stacklevel=2)
        return raw_calendar

def get_reviews(room_url: str ,language: str = "en", proxy_url: str = "", timeout: Timeout = DEFAULT_TIMEOUT):
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
    data, price_input, cookies = details.get(room_url, language, proxy_url, timeout=timeout)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]

    return reviews.get(api_key, product_id, "USD", language, proxy_url, timeout=timeout)

def get_details(room_url: str = None, room_id: int = None, domain: str = "www.airbnb.com", check_in: str = None, check_out: str = None, adults: int = 1, currency: str = "USD", language: str = "en", proxy_url: str = "", timeout: Timeout = DEFAULT_TIMEOUT):
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
    
    data, price_input, cookies = details.get(room_url, language, proxy_url, timeout=timeout)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]
    
    # Extract room_id from URL if not provided
    if room_id is None:
        parsed_url = urlparse(room_url)
        path = parsed_url.path
        room_id = path.split("/")[-1]
    
    # Get calendar and reviews data
    data["reviews"] = reviews.get(api_key, product_id, currency, language, proxy_url, timeout=timeout)
    data["calendar"] = get_calendar(
        api_key,
        str(room_id),
        proxy_url,
        timeout=timeout,
        return_dataclass=False,
    )
    
    # Get price data if check-in and check-out dates are provided
    if check_in and check_out:
        price_data = price.get(
            room_id=str(room_id),
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            currency=currency,
            language=language,
            impresion_id=price_input["impression_id"],
            api_key=api_key,
            cookies=cookies,
            proxy_url=proxy_url,
            timeout=timeout,
        )
        data["price"] = price_data
    
    # Get host details
    host_id = data["host"]["id"]
    data["host_details"] = host_details.get(api_key, cookies, host_id, language, proxy_url, timeout=timeout)
    
    return data

def _next_search_cursor(pagination_info: dict, cursor: str, fetched: set) -> str:
    """
    The cursor of the next search page, or "" when there is none.

    Airbnb used to send `nextPageCursor` on every page. Since November 2026
    StaysSearch lists every page up front in `pageCursors` instead and leaves
    `nextPageCursor` out, so following only the latter stops after page 1
    (40 results) without an error. Both shapes are followed here; `fetched`
    remembers what was requested so a cursor is never asked for twice.
    """
    fetched.add(cursor)
    page_cursors = pagination_info.get("pageCursors") or []
    if cursor == "" and page_cursors:
        # The first request has no cursor; page_cursors[0] is that same page.
        fetched.add(page_cursors[0])
    next_cursor = pagination_info.get("nextPageCursor") or next(
        (c for c in page_cursors if c not in fetched), ""
    )
    return "" if next_cursor in fetched else next_cursor


def _extend_unique_search_results(
    all_results: list, results: list, seen_room_ids: set
) -> None:
    """Append results in page order without repeating the same listing."""
    for result in results:
        room_id = result.get("room_id") if isinstance(result, dict) else None
        if room_id is not None:
            if room_id in seen_room_ids:
                continue
            seen_room_ids.add(room_id)
        all_results.append(result)


def search_all(
    check_in: str,
    check_out: str,
    ne_lat: float,
    ne_long: float,
    sw_lat: float,
    sw_long: float,
    zoom_value: int,
    *search_args: Any,
    price_min: Any = _UNSET,
    price_max: Any = _UNSET,
    place_type: str = _UNSET,
    amenities: list = _UNSET,
    free_cancellation: bool = _UNSET,
    adults: Any = _UNSET,
    children: Any = _UNSET,
    infants: Any = _UNSET,
    min_bedrooms: Any = _UNSET,
    min_beds: Any = _UNSET,
    min_bathrooms: Any = _UNSET,
    currency: str = _UNSET,
    language: str = _UNSET,
    proxy_url: str = _UNSET,
    hash: str = _UNSET,
    timeout: Timeout = _UNSET,
):
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
        adults (int): Number of adults
        children (int): Number of children
        infants (int): Number of infants
        min_bedrooms (int): Minimum number of bedrooms
        min_beds (int): Minimum number of beds
        min_bathrooms (int): Minimum number of bathrooms
        language (str): language to use for example en,es,tr ..etc
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of all search results.
    """
    keyword_args = {
        name: value
        for name, value in {
            "price_min": price_min,
            "price_max": price_max,
            "place_type": place_type,
            "amenities": amenities,
            "free_cancellation": free_cancellation,
            "adults": adults,
            "children": children,
            "infants": infants,
            "min_bedrooms": min_bedrooms,
            "min_beds": min_beds,
            "min_bathrooms": min_bathrooms,
            "currency": currency,
            "language": language,
            "proxy_url": proxy_url,
            "hash": hash,
            "timeout": timeout,
        }.items()
        if value is not _UNSET
    }
    params = _resolve_search_arguments("search_all", search_args, keyword_args)

    proxy_url = params["proxy_url"]
    timeout = params["timeout"]
    api_key = api.get(proxy_url, timeout=timeout)
    all_results = []
    seen_room_ids = set()
    cursor = ""
    fetched = set()
    while True:
        results_raw = search.get(
            api_key=api_key,
            cursor=cursor,
            check_in=check_in,
            check_out=check_out,
            ne_lat=ne_lat,
            ne_long=ne_long,
            sw_lat=sw_lat,
            sw_long=sw_long,
            zoom_value=zoom_value,
            timeout=params["timeout"],
            **{name: params[name] for name in _CURRENT_SEARCH_ARGUMENTS if name != "timeout"},
        )
        paginationInfo = utils.get_nested_value(results_raw,"data.presentation.staysSearch.results.paginationInfo",{})
        results = standardize.from_search(results_raw)
        _extend_unique_search_results(all_results, results, seen_room_ids)
        cursor = _next_search_cursor(paginationInfo, cursor, fetched)
        if not results or not cursor:
            break
    return all_results

def search_first_page(
    check_in: str,
    check_out: str,
    ne_lat: float,
    ne_long: float,
    sw_lat: float,
    sw_long: float,
    zoom_value: int,
    *search_args: Any,
    price_min: Any = _UNSET,
    price_max: Any = _UNSET,
    place_type: str = _UNSET,
    amenities: list = _UNSET,
    free_cancellation: bool = _UNSET,
    adults: Any = _UNSET,
    children: Any = _UNSET,
    infants: Any = _UNSET,
    min_bedrooms: Any = _UNSET,
    min_beds: Any = _UNSET,
    min_bathrooms: Any = _UNSET,
    currency: str = _UNSET,
    language: str = _UNSET,
    proxy_url: str = _UNSET,
    hash: str = _UNSET,
    timeout: Timeout = _UNSET,
):
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
        adults (int): Number of adults
        children (int): Number of children
        infants (int): Number of infants
        min_bedrooms (int): Minimum number of bedrooms
        min_beds (int): Minimum number of beds
        min_bathrooms (int): Minimum number of bathrooms
        language (str): language to use for example en,es,tr ..etc
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of search results from the first page.
    """
    keyword_args = {
        name: value
        for name, value in {
            "price_min": price_min,
            "price_max": price_max,
            "place_type": place_type,
            "amenities": amenities,
            "free_cancellation": free_cancellation,
            "adults": adults,
            "children": children,
            "infants": infants,
            "min_bedrooms": min_bedrooms,
            "min_beds": min_beds,
            "min_bathrooms": min_bathrooms,
            "currency": currency,
            "language": language,
            "proxy_url": proxy_url,
            "hash": hash,
            "timeout": timeout,
        }.items()
        if value is not _UNSET
    }
    params = _resolve_search_arguments("search_first_page", search_args, keyword_args)

    proxy_url = params["proxy_url"]
    timeout = params["timeout"]
    api_key = api.get(proxy_url, timeout=timeout)
    results_raw = search.get(
        api_key=api_key,
        cursor="",
        check_in=check_in,
        check_out=check_out,
        ne_lat=ne_lat,
        ne_long=ne_long,
        sw_lat=sw_lat,
        sw_long=sw_long,
        zoom_value=zoom_value,
        timeout=timeout,
        **{name: params[name] for name in _CURRENT_SEARCH_ARGUMENTS if name != "timeout"},
    )

    results = standardize.from_search(results_raw)
    return results


def search_experience_by_taking_the_first_inputs_i_dont_care(user_input_text: str, currency:str, locale: str, check_in:str, check_out:str, api_key:str, proxy_url:str, timeout: Timeout = DEFAULT_TIMEOUT):
    markets_data = search.get_markets(currency,locale,api_key,proxy_url, timeout=timeout)
    markets = utils.get_nested_value(markets_data,"user_markets", [])
    if len(markets)==0:
        raise Exception("markets are empty")
    config_token = utils.get_nested_value(markets[0],"satori_parameters", "")
    country_code = utils.get_nested_value(markets[0],"country_code", "")
    if config_token=="" or country_code=="":
        raise Exception("config_token or country_code are empty")
    place_ids_results = search.get_places_ids(country_code, user_input_text, currency, locale, config_token, api_key, proxy_url, timeout=timeout)
    if len(place_ids_results)==0:
        raise Exception("empty places ids")
    place_id = utils.get_nested_value(place_ids_results[0],"location.google_place_id", "")
    location_name = utils.get_nested_value(place_ids_results[0],"location.location_name", "")
    if place_id=="" or location_name=="":
        raise Exception("place_id or location_name are empty")
    [result,cursor] = experience.search_by_place_id("", place_id, location_name, currency, locale, check_in, check_out, api_key, proxy_url, timeout=timeout)
    while cursor!="":
        [result_tmp,cursor] = experience.search_by_place_id(cursor, place_id, location_name, currency, locale, check_in, check_out, api_key, proxy_url, timeout=timeout)
        if len(result_tmp)==0:
            break
        result = result + result_tmp
    return result

def search_all_from_url(url: str, currency: str = "USD", language: str = "en", proxy_url: str = "", hash: str = "", timeout: Timeout = DEFAULT_TIMEOUT):
    """
    Parses an Airbnb search URL and forwards all recognizable filters to
    Airbnb's StaysSearch API. The URL is the source of truth: any URL
    parameter (known or unknown) is passed through.
    """
    raw_params = search.url_to_raw_params(url)
    api_key = api.get(proxy_url)
    all_results = []
    seen_room_ids = set()
    cursor = ""
    fetched = set()
    # search.get's structured-args are ignored when raw_params is supplied,
    # but they're still required by the signature. Pass them by name so this
    # call doesn't break if their positional order ever changes.
    call_kwargs = {
        "currency": currency, "language": language,
        "proxy_url": proxy_url, "hash": hash,
        "raw_params": raw_params,
        "check_in": None, "check_out": None,
        "ne_lat": 0, "ne_long": 0, "sw_lat": 0, "sw_long": 0,
        "zoom_value": 0, "place_type": "",
        "price_min": 0, "price_max": 0, "amenities": [],
        "free_cancellation": False,
        "adults": 0, "children": 0, "infants": 0,
        "min_bedrooms": 0, "min_beds": 0, "min_bathrooms": 0,
    }
    while True:
        results_raw = search.get(api_key=api_key, cursor=cursor, timeout=timeout, **call_kwargs)
        paginationInfo = utils.get_nested_value(
            results_raw, "data.presentation.staysSearch.results.paginationInfo", {}
        )
        results = standardize.from_search(results_raw)
        _extend_unique_search_results(all_results, results, seen_room_ids)
        cursor = _next_search_cursor(paginationInfo, cursor, fetched)
        if not results or not cursor:
            break
    return all_results
