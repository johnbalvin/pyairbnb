from curl_cffi import requests
from urllib.parse import urlencode
import pyairbnb.utils as utils
import json
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout

ep = "https://www.airbnb.com/api/v3/UserProfileBeehiveListingQuery/529ca816b8be0619618d48b31bf46c379543e297fd68c0a953922927e5497b43"

extension = {
    "persistedQuery": {
        "version": 1,
        "sha256Hash": "529ca816b8be0619618d48b31bf46c379543e297fd68c0a953922927e5497b43",
    }
}

extensionRaw = json.dumps(extension)
        
def get_listings_from_user(userId: int, api_key: str, proxy_url: str, timeout: Timeout = DEFAULT_TIMEOUT):
    offset = 0
    all_listings = []
    while True:
        listings = get_listings_from_offset(offset, userId, api_key, proxy_url, timeout=timeout)
        offset = offset + len(listings)
        if len(listings)==0:
            break
        all_listings = all_listings + listings
    return all_listings

def get_listings_from_offset(offset: int, userId: int, api_key: str, proxy_url: str, timeout: Timeout = DEFAULT_TIMEOUT) -> str:
    variables = {
        "userId": userId,
        "limit": 12,
        "offset": offset,
    }
    variablesRaw = json.dumps(variables)
    query_params = {
            "operationName": "UserProfileBeehiveListingQuery",
            "locale": "en",
            "currency":"USD",
            "variables":variablesRaw,
            "extensions":extensionRaw,
    }
    url_parsed = f"{ep}?{urlencode(query_params)}"
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
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
        "X-Airbnb-Api-Key": api_key,
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url_parsed, headers=headers, proxies=proxies, timeout=timeout)
    response.raise_for_status() 
    data = response.json()
    listings = utils.get_nested_value(data,"data.beehive.getListOfListings.listings",[])
    return listings