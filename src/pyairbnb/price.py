from datetime import date
import json
from curl_cffi import requests
import pyairbnb.utils as utils
from urllib.parse import urlencode
import pyairbnb.api as api
import pyairbnb.standardize as standardize
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout


class UnavailableError(Exception):
    """Raised when the listing is unavailable for the specified dates."""
    pass


BASE_URL = "https://www.airbnb.com/api/v3/StaysPdpSections"
PERSISTED_QUERY_HASH = "80c7889b4b0027d99ffea830f6c0d4911a6e863a957cbe1044823f0fc746bf1f"


def _build_headers(api_key: str | None, proxy_url: str | None, timeout: Timeout = DEFAULT_TIMEOUT) -> dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # TO-DO randomize this later
        "X-Airbnb-Api-Key": api_key or api.get(proxy_url, timeout=timeout),
    }


def _build_query_extension() -> dict:
    return {"persistedQuery": {"version": 1, "sha256Hash": PERSISTED_QUERY_HASH}}


def _build_query_variables(
    room_id: str,
    check_in: date,
    check_out: date,
    adults: int = 1,
    impresion_id: str | None = None,
) -> dict:
    variables = {
        "id": standardize.encode_room_id(room_id=room_id, prefix="StayListing"),
        "demandStayListingId": standardize.encode_room_id(room_id=room_id, prefix="DemandStayListing"),
        "pdpSectionsRequest": {
            "adults": str(adults),
            "bypassTargetings": False,
            "categoryTag": None,
            "causeId": None,
            "children": None,
            "disasterId": None,
            "discountedGuestFeeVersion": None,
            "displayExtensions": None,
            "federatedSearchId": None,
            "forceBoostPriorityMessageType": None,
            "infants": None,
            "interactionType": None,
            "layouts": ["SIDEBAR", "SINGLE_COLUMN"],
            "pets": 0,
            "pdpTypeOverride": None,
            "photoId": None,
            "preview": False,
            "previousStateCheckIn": None,
            "previousStateCheckOut": None,
            "priceDropSource": None,
            "privateBooking": False,
            "promotionUuid": None,
            "relaxedAmenityIds": None,
            "searchId": None,
            "selectedCancellationPolicyId": None,
            "selectedRatePlanId": None,
            "splitStays": None,
            "staysBookingMigrationEnabled": False,
            "translateUgc": None,
            "useNewSectionWrapperApi": False,
            "sectionIds": ["BOOK_IT_FLOATING_FOOTER", "POLICIES_DEFAULT", "EDUCATION_FOOTER_BANNER_MODAL",
                           "BOOK_IT_SIDEBAR", "URGENCY_COMMITMENT_SIDEBAR", "BOOK_IT_NAV", "MESSAGE_BANNER", "HIGHLIGHTS_DEFAULT",
                           "EDUCATION_FOOTER_BANNER", "URGENCY_COMMITMENT", "BOOK_IT_CALENDAR_SHEET", "CANCELLATION_POLICY_PICKER_MODAL"],
            "checkIn": check_in.isoformat(),
            "checkOut": check_out.isoformat(),
        },
    }

    if impresion_id is not None:
        variables["pdpSectionsRequest"]["p3ImpressionId"] = impresion_id

    return variables


def _parse_price_response(data: dict) -> dict:
    # TO-DO need fix error when parsing ['raw']
    sections = utils.get_nested_value(data, "data.presentation.stayProductDetailPage.sections.sections", [])
    priceGroups = utils.get_nested_value(data, "data.presentation.stayProductDetailPage.sections.metadata.bookingPrefetchData.barPrice.explanationData.priceGroups", [])

    finalData = {"raw": priceGroups}

    for section in sections:
        if section.get("sectionId") != "BOOK_IT_SIDEBAR":
            continue

        if unavailability_message := utils.get_nested_value(section, "section.localizedUnavailabilityMessage"):
            raise UnavailableError(unavailability_message)

        _price_data = utils.get_nested_value(section, "section.structuredDisplayPrice", {})
        _details = utils.get_nested_value(_price_data, "explanationData.priceDetails", [])

        discounted_price = utils.get_nested_value(_price_data, "primaryLine.discountedPrice")
        original_price = utils.get_nested_value(_price_data, "primaryLine.originalPrice")
        qualifier = utils.get_nested_value(_price_data, "primaryLine.qualifier", {})
        details = {
            item.get("description"): item.get("priceString")
            for detail in _details
            for item in utils.get_nested_value(detail, "items", [])
            if isinstance(item, dict) and item.get("description")
        }
        
        finalData["main"] = {
            "price": discounted_price or original_price,
            "discountedPrice": discounted_price,
            "originalPrice": original_price,
            "qualifier": qualifier,
            "details": details
        }

        break

    return finalData


def get(
    room_id: str,
    check_in: date,
    check_out: date,
    adults: int = 1,
    currency: str = "USD",
    language: str = "en",
    impresion_id: str | None = None,
    api_key: str | None = None,
    cookies: list | None = None, 
    proxy_url: str | None = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> dict:
    extension = _build_query_extension()
    variables = _build_query_variables(
        room_id=room_id,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        impresion_id=impresion_id
    )
    query = {
        "operationName": "StaysPdpSections",
        "locale": language,
        "currency": currency,
        "variables": json.dumps(variables),
        "extensions": json.dumps(extension),
    }

    url = f"{BASE_URL}/{PERSISTED_QUERY_HASH}?{urlencode(query)}"
    headers = _build_headers(api_key, proxy_url, timeout=timeout)
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    with requests.Session() as session:
        session.cookies.update(cookies)
        response = session.get(url=url, headers=headers, proxies=proxies, timeout=timeout)
    
    response.raise_for_status()
    data = response.json()

    return _parse_price_response(data)

__all__ = ["get"]