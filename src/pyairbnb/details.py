from curl_cffi import requests
import pyairbnb.parse as parse
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout
from urllib.parse import urlparse, urlunparse


def _airbnb_ca_fallback(room_url: str) -> str | None:
    parsed = urlparse(room_url)
    if parsed.hostname != "www.airbnb.com" and parsed.hostname != "airbnb.com":
        return None
    netloc = "www.airbnb.ca"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def get(room_url: str, language: str, proxy_url: str, timeout: Timeout = DEFAULT_TIMEOUT, cookies: dict | None = None):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": language,
        "Cache-Control": "no-cache",
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
    proxies = {}
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    candidate_urls = [room_url]
    fallback_url = _airbnb_ca_fallback(room_url)
    if fallback_url:
        candidate_urls.append(fallback_url)

    last_parse_error: Exception | None = None
    for candidate_url in candidate_urls:
        response = requests.get(
            candidate_url, headers=headers, proxies=proxies, timeout=timeout, cookies=cookies
        )
        response.raise_for_status()
        try:
            data_formatted, price_dependency_input = parse.parse_body_details_wrapper(
                response.text
            )
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
            last_parse_error = error
            continue
        return data_formatted, price_dependency_input, response.cookies

    raise last_parse_error or RuntimeError("Unable to parse Airbnb room details")
