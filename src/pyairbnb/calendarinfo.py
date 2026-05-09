from curl_cffi import requests
import pyairbnb.utils as utils
from urllib.parse import urlencode
import json
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout

ep = "https://www.airbnb.com/api/v3/PdpAvailabilityCalendar/8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade/"
 

def get(api_key: str, room_id: str, month: int, year: int, proxy_url: str, timeout: Timeout = DEFAULT_TIMEOUT) -> str:
    headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Airbnb-Api-Key": api_key,
    }
    variablesData={
        "request":{
            "count":12,
            "listingId":room_id,
            "month":month,
            "year":year,
        },
    }
    entension={
        "persistedQuery": {
            "version":1,
            "sha256Hash": "8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade",
        },
    }
    dataRawExtension = json.dumps(entension)
    dataRawVariables = json.dumps(variablesData)
    query = {
        "operationName": "PdpAvailabilityCalendar",
        "locale": "en",
        "currency": "USD",
        "variables": dataRawVariables,
        "extensions": dataRawExtension,
    }
    url = f"{ep}?{urlencode(query)}"
    proxies = {}
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
    response.raise_for_status() 
    data = response.json()
    calendar = utils.get_nested_value(data,"data.merlin.pdpAvailabilityCalendar.calendarMonths",[])
    return calendar