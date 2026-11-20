import json
import re
from urllib.parse import urlencode

from curl_cffi import requests

import pyairbnb.utils as utils
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout

BASE_URL = "https://www.airbnb.com/api/v3/StaysPdpReviewsQuery"
DEFAULT_PERSISTED_QUERY_HASH = "cfdc3ffbe997a618795fc5a8f9a9b484054ce9be68c8788cd2ffda999934c5ae"
PERSISTED_QUERY_HASH = DEFAULT_PERSISTED_QUERY_HASH

_REVIEWS_PAGE_SIZE = 50

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  # TO-DO randomize this later

_ASYNC_REQUIRE_RE = re.compile(
    r"https://a0\.muscache\.com/airbnb/static/packages/web/[^/]+/frontend/airmetro/browser/asyncRequire\.[^\"']+\.js"
)
_HANDOFF_ACTION_RE = re.compile(r'<form[^>]+action="([^"]+)"')
_HANDOFF_PAYLOAD_RE = re.compile(r'<input[^>]+name="payload"[^>]+value="([^"]+)"')
_REVIEWS_MODULE_RE = re.compile(
    r"(?:common|[a-z]{2}(?:-[A-Za-z]{2,4})?)/frontend/gp-stays-pdp-sections/migrated-sections/ReviewsSection/ReviewsSection[^\"'\\\s<>]*\.js"
)
_REVIEWS_HASH_RE = re.compile(
    r"name:['\"]StaysPdpReviewsQuery['\"],type:['\"](?:query|mutation)['\"],operationId:['\"]([0-9a-f]{64})['\"]"
)


class _ReviewsResponseError(RuntimeError):
    """Raised when a response suggests the persisted-query hash is stale."""


def _build_headers(api_key: str) -> dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": _UA,
        "X-Airbnb-Api-Key": api_key,
        "X-Airbnb-Operation-Id": "StaysPdpReviewsQuery",
    }


def fetch_reviews_hash(
    proxy_url: str | None = None, timeout: Timeout = DEFAULT_TIMEOUT
) -> str:
    """Fetch the live StaysPdpReviewsQuery persisted-query hash from Airbnb web bundles."""
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    headers = {"User-Agent": _UA}

    homepage = requests.get(
        "https://www.airbnb.com/",
        headers=headers,
        proxies=proxies,
        impersonate="chrome124",
        timeout=timeout,
    )
    homepage.raise_for_status()

    bundle_match = _ASYNC_REQUIRE_RE.search(homepage.text)
    if not bundle_match:
        # Airbnb may return a domain-switch landing page instead of the actual homepage.
        handoff_match = _HANDOFF_ACTION_RE.search(homepage.text)
        payload_match = _HANDOFF_PAYLOAD_RE.search(homepage.text)
        if handoff_match and payload_match:
            homepage = requests.post(
                handoff_match.group(1),
                data={"version": "1", "payload": payload_match.group(1)},
                headers=headers,
                proxies=proxies,
                impersonate="chrome124",
                timeout=timeout,
            )
            homepage.raise_for_status()
            bundle_match = _ASYNC_REQUIRE_RE.search(homepage.text)

    if not bundle_match:
        raise RuntimeError("Unable to locate StaysPdpReviewsQuery asyncRequire bundle")

    bundle = requests.get(
        bundle_match.group(0),
        headers=headers,
        proxies=proxies,
        impersonate="chrome124",
        timeout=timeout,
    )
    bundle.raise_for_status()

    module_match = _REVIEWS_MODULE_RE.search(bundle.text)
    if not module_match:
        raise RuntimeError("Unable to locate StaysPdpReviewsQuery module chunk")

    chunk = requests.get(
        f"https://a0.muscache.com/airbnb/static/packages/web/{module_match.group(0)}",
        headers=headers,
        proxies=proxies,
        impersonate="chrome124",
        timeout=timeout,
    )
    chunk.raise_for_status()

    hash_match = _REVIEWS_HASH_RE.search(chunk.text)
    if not hash_match:
        raise RuntimeError("Unable to extract StaysPdpReviewsQuery operationId")

    return hash_match.group(1)


def _build_query_variables(product_id: str, offset: int) -> dict:
    return {
        "id": product_id,
        "pdpReviewsRequest": {
            "fieldSelector": "for_p3_translation_only",
            "forPreview": False,
            "limit": _REVIEWS_PAGE_SIZE,
            "offset": f"{offset}",
            "showingTranslationButton": False,
            "first": _REVIEWS_PAGE_SIZE,
            "sortingPreference": "MOST_RECENT",
            "numberOfAdults": "1",
            "numberOfChildren": "0",
            "numberOfInfants": "0",
            "numberOfPets": "0",
            "after": None,
        },
    }


def get(
    api_key: str = "",
    product_id: str = "",
    currency: str = "USD",
    language: str = "en",
    proxy_url: str | None = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> list:
    offset = 0
    all_reviews = []
    while True:
        reviews = get_from_offset(
            api_key, offset, product_id, currency, language, proxy_url, timeout=timeout
        )
        all_reviews.extend(reviews)
        if len(reviews) < _REVIEWS_PAGE_SIZE:
            break
        offset += _REVIEWS_PAGE_SIZE
    return all_reviews


def get_from_offset(
    api_key: str,
    offset: int,
    product_id: str,
    currency: str = "USD",
    language: str = "en",
    proxy_url: str | None = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> list:
    global PERSISTED_QUERY_HASH

    headers = _build_headers(api_key)
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    query_hash = PERSISTED_QUERY_HASH
    last_error: Exception | None = None
    for attempt in range(2):
        if attempt == 1:
            # Airbnb rotates the persisted-query hash; refresh it once and retry
            try:
                refreshed_hash = fetch_reviews_hash(proxy_url=proxy_url, timeout=timeout)
            except Exception as refresh_error:
                raise last_error or RuntimeError(
                    "StaysPdpReviewsQuery hash refresh failed"
                ) from refresh_error
            if refreshed_hash == query_hash:
                raise last_error or RuntimeError("StaysPdpReviewsQuery failed")
            PERSISTED_QUERY_HASH = refreshed_hash
            query_hash = refreshed_hash

        query = {
            "operationName": "StaysPdpReviewsQuery",
            "locale": language,
            "currency": currency,
            "variables": json.dumps(_build_query_variables(product_id, offset)),
            "extensions": json.dumps(
                {"persistedQuery": {"version": 1, "sha256Hash": query_hash}}
            ),
        }
        url = f"{BASE_URL}/{query_hash}/?{urlencode(query)}"

        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)

            if response.status_code in (400, 404):
                raise _ReviewsResponseError(
                    f"StaysPdpReviewsQuery rejected the request with HTTP {response.status_code}"
                )

            response.raise_for_status()
            data = response.json()

            reviews = (
                utils.get_nested_value(
                    data, "data.presentation.stayProductDetailPage.reviews.reviews", None
                )
                if isinstance(data, dict)
                else None
            )
            if isinstance(reviews, list):
                return reviews

            errors = data.get("errors") if isinstance(data, dict) else None
            if isinstance(errors, list) and errors and isinstance(errors[0], dict):
                first_error = errors[0]
                message = first_error.get("message") or "unknown error"
                error_type = utils.get_nested_value(first_error, "extensions.errorType", "")
                if error_type == "NOT_FOUND":
                    raise RuntimeError(f"StaysPdpReviewsQuery failed (NOT_FOUND): {message}")
                raise _ReviewsResponseError(f"StaysPdpReviewsQuery failed: {message}")

            raise _ReviewsResponseError("StaysPdpReviewsQuery returned no reviews payload")
        except _ReviewsResponseError as error:
            last_error = error
            if attempt == 0:
                continue
            raise

    raise last_error if last_error else RuntimeError("StaysPdpReviewsQuery failed")


__all__ = ["get", "get_from_offset", "fetch_reviews_hash"]
