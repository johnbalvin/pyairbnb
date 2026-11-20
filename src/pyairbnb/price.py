import random
import re
import string
import time
import uuid
from datetime import date
import json
from curl_cffi import requests
import pyairbnb.utils as utils
import pyairbnb.api as api
import pyairbnb.standardize as standardize
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout


class UnavailableError(Exception):
    """Raised when the listing is unavailable for the specified dates."""
    pass


BASE_URL = "https://www.airbnb.com/api/v3/StaysPdpSections"
DEFAULT_PERSISTED_QUERY_HASH = "14623240152ebb78334527fc8c97b63c0c37729df8d1e7abeec6a0aa57dbf4f9"
PERSISTED_QUERY_HASH = DEFAULT_PERSISTED_QUERY_HASH

_CLIENT_VERSION = "1c7fabdcdf93caaf2354e7e22f2e367207f81450"


def _build_headers(api_key: str | None, proxy_url: str | None, referer: str = "https://www.airbnb.com/", timeout: Timeout = DEFAULT_TIMEOUT) -> dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # TO-DO randomize this later
        "X-Airbnb-Api-Key": api_key or api.get(proxy_url, timeout=timeout),
        "X-Airbnb-Operation-Id": "StaysPdpSections",
        "X-Airbnb-GraphQL-Platform": "web",
        "X-Airbnb-GraphQL-Platform-Client": "minimalist-niobe",
        "X-Client-Version": _CLIENT_VERSION,
        "X-Airbnb-Supports-Airlock-V2": "true",
        "X-CSRF-Without-Token": "1",
        "X-CSRF-Token": "",
        "X-Client-Request-Id": uuid.uuid4().hex[:25],
        "X-Airbnb-Client-Trace-Id": uuid.uuid4().hex + uuid.uuid4().hex[:17],
        "Referer": referer,
    }


def fetch_pdp_sections_hash(proxy_url: str = "", timeout: Timeout = DEFAULT_TIMEOUT) -> str:
    """Fetch the live StaysPdpSections persisted-query hash from airbnb.ca bundles."""
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    # airbnb.com serves a geo-handoff form for HTML pages; airbnb.ca serves the real app bundle
    homepage = requests.get(
        "https://www.airbnb.ca/",
        headers=headers,
        proxies=proxies,
        impersonate="chrome124",
        timeout=timeout,
    )
    homepage.raise_for_status()

    bundle_match = re.compile(
        r"https://a0\.muscache\.com/airbnb/static/packages/web/[^/]+/frontend/airmetro/browser/asyncRequire\.[^\"']+\.js"
    ).search(homepage.text)
    if not bundle_match:
        raise RuntimeError("Unable to locate StaysPdpSections asyncRequire bundle")

    bundle = requests.get(
        bundle_match.group(0), headers=headers, proxies=proxies, impersonate="chrome124", timeout=timeout
    )
    bundle.raise_for_status()

    module_match = re.compile(
        r"(?:common|[a-z]{2}(?:-[A-Za-z]{2,4})?)/frontend/gp-stays-pdp-route/routes/PdpPlatformRoute[^\"'\\\s<>]*\.js"
    ).search(bundle.text)
    if not module_match:
        raise RuntimeError("Unable to locate StaysPdpSections module chunk")

    chunk = requests.get(
        f"https://a0.muscache.com/airbnb/static/packages/web/{module_match.group(0)}",
        headers=headers,
        proxies=proxies,
        impersonate="chrome124",
        timeout=timeout,
    )
    chunk.raise_for_status()

    hash_match = re.compile(
        r"name:['\"]StaysPdpSections['\"],type:['\"](?:query|mutation)['\"],operationId:['\"]([0-9a-f]{64})['\"]"
    ).search(chunk.text)
    if not hash_match:
        raise RuntimeError("Unable to extract StaysPdpSections operationId")

    return hash_match.group(1)


def _new_p3_impression_id() -> str:
    return f"p3_{int(time.time() * 1000)}_" + "".join(random.choices(string.ascii_letters + string.digits, k=15))


def _build_query_variables(
    room_id: str,
    check_in: date,
    check_out: date,
    adults: int = 1,
    impresion_id: str | None = None,
) -> dict:
    check_in_str = check_in.isoformat() if hasattr(check_in, "isoformat") else str(check_in)
    check_out_str = check_out.isoformat() if hasattr(check_out, "isoformat") else str(check_out)
    p3_impression_id = impresion_id if impresion_id is not None else _new_p3_impression_id()

    variables = {
        "id": standardize.encode_room_id(room_id=room_id, prefix="StayListing"),
        "demandStayListingId": standardize.encode_room_id(room_id=room_id, prefix="DemandStayListing"),
        "pdpSectionsRequest": {
            "adults": str(adults),
            "amenityFilters": None,
            "bypassTargetings": False,
            "categoryTag": None,
            "causeId": None,
            "children": None,
            "disasterId": None,
            "discountedGuestFeeVersion": None,
            "federatedSearchId": None,
            "forceBoostPriorityMessageType": None,
            "guestAges": None,
            "hostPreview": False,
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
            "partner": None,
            "partnerProgram": None,
            "directBookingParams": None,
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
            "sectionIds": ["BOOK_IT_FLOATING_FOOTER", "POLICIES_DEFAULT", "BOOK_IT_SIDEBAR",
                           "BOOK_IT_NAV", "BOOK_IT_CALENDAR_SHEET", "CANCELLATION_POLICY_PICKER_MODAL"],
            "checkIn": check_in_str,
            "checkOut": check_out_str,
            "p3ImpressionId": p3_impression_id,
            "targetPromotion": None,
            "logPricingViewEvent": True,
        },
        "categoryTag": None,
        "federatedSearchId": None,
        "federatedSearchSessionId": None,
        "p3ImpressionId": p3_impression_id,
        "photoId": None,
        "includePdpLayoutPipelineInputs": False,
        "amenityIds": None,
        "causeId": None,
        "dateRange": {"startDate": check_in_str, "endDate": check_out_str},
        "guestCounts": {"numberOfAdults": adults},
        "targetPromotion": None,
        "numberOfChildren": None,
        "numberOfInfants": None,
        "numberOfPets": None,
        "includePdpMigrationBookItNavFragment": True,
        "includeGpBookItFragment": True,
        "includePdpMigrationBookItFloatingFooterFragment": True,
        "includePdpMigrationBookItSidebarFragment": True,
        "includePdpMigrationBookItCalendarSheetFragment": True,
        "includePdpMigrationPropertyAvailableRoomsFragment": False,
        "includeGpPropertyAvailableRoomsFragment": False,
        "includePdpOffers": False,
    }

    return variables


def _build_request_body(room_id: str, check_in: date, check_out: date, adults: int = 1, impresion_id: str | None = None) -> dict:
    return {
        "operationName": "StaysPdpSections",
        "variables": _build_query_variables(
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            impresion_id=impresion_id,
        ),
        "extensions": {"persistedQuery": {"version": 1, "sha256Hash": PERSISTED_QUERY_HASH}},
    }


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
    global PERSISTED_QUERY_HASH

    body = _build_request_body(
        room_id=room_id,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        impresion_id=impresion_id,
    )
    url = f"{BASE_URL}/{PERSISTED_QUERY_HASH}?operationName=StaysPdpSections&locale={language}&currency={currency}"
    headers = _build_headers(api_key, proxy_url, timeout=timeout)
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    last_error: Exception | None = None
    for attempt in range(2):
        if attempt == 1:
            # Airbnb rotates the persisted-query hash; refresh it once and retry
            try:
                PERSISTED_QUERY_HASH = fetch_pdp_sections_hash(proxy_url=proxy_url, timeout=timeout)
            except Exception:
                pass
            body["extensions"]["persistedQuery"]["sha256Hash"] = PERSISTED_QUERY_HASH
            url = f"{BASE_URL}/{PERSISTED_QUERY_HASH}?operationName=StaysPdpSections&locale={language}&currency={currency}"

        try:
            with requests.Session() as session:
                if cookies:
                    session.cookies.update(cookies)
                response = session.post(url=url, headers=headers, json=body, proxies=proxies, timeout=timeout)

            response.raise_for_status()
            data = response.json()

            if not utils.get_nested_value(data, "data.presentation"):
                errors = data.get("errors") or []
                message = errors[0].get("message", "unknown error") if errors else "empty response"
                raise RuntimeError(f"StaysPdpSections failed: {message}")

            return _parse_price_response(data)
        except UnavailableError:
            raise
        except Exception as error:
            last_error = error

    raise last_error if last_error else RuntimeError("StaysPdpSections failed")


__all__ = ["get", "UnavailableError"]
