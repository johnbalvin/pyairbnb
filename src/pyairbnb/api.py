from curl_cffi import requests
import re
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout

ep = "https://www.airbnb.com"

regx_api_key = re.compile(r'"api_config":{"key":".+?"')

# Airbnb's long-lived public web client key, used as a last resort when the homepage parse fails.
FALLBACK_API_KEY = "d306zoyjsyarp7ifhu67rjxn52tv0t20"

def get(proxy_url: str, timeout: Timeout = DEFAULT_TIMEOUT) -> str:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en",
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

    response = requests.get(ep, headers=headers, proxies=proxies, timeout=timeout)
    response.raise_for_status()

    body = response.text
    api_key_match = regx_api_key.search(body)

    if not api_key_match:
        # Airbnb may return a domain-switch landing page instead of the actual homepage.
        handoff_match = re.search(r'<form[^>]+action="([^"]+)"', body)
        payload_match = re.search(r'<input[^>]+name="payload"[^>]+value="([^"]+)"', body)

        if handoff_match and payload_match:
            handoff_url = handoff_match.group(1)
            payload_value = payload_match.group(1)
            response = requests.post(
                handoff_url,
                data={"version": "1", "payload": payload_value},
                headers=headers,
                proxies=proxies,
                timeout=60,
            )
            response.raise_for_status()
            body = response.text
            api_key_match = regx_api_key.search(body)

    if not api_key_match:
        return FALLBACK_API_KEY

    api_key = api_key_match.group()
    api_key = api_key.replace('"api_config":{"key":"', '')
    api_key = api_key.replace('"', "")
    return api_key
