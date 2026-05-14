from curl_cffi import requests
import pyairbnb.parse as parse
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout



def get(room_url: str, language: str, proxy_url: str, timeout: Timeout = DEFAULT_TIMEOUT):
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
    response = requests.get(room_url, headers=headers, proxies=proxies, timeout=timeout)
    response.raise_for_status()
    data_formatted, price_dependency_input=parse.parse_body_details_wrapper(response.text)
    cookies = response.cookies
    return data_formatted, price_dependency_input, cookies