from curl_cffi import requests
import pyairbnb.utils as utils
from urllib.parse import urlencode
import json

ep="https://www.airbnb.com/api/v3/StaysPdpReviewsQuery/dec1c8061483e78373602047450322fd474e79ba9afa8d3dbbc27f504030f91d/"

def get(product_id: str, api_key: str,proxy_url: str, locale: str = "en", currency: str = "USD") -> str:
    offset = 0
    all_reviews = []
    while True:
        reviews = get_from_offset(offset,product_id,api_key,proxy_url, locale, currency)
        offset=offset+50
        if len(reviews)==0:
            break
        all_reviews.extend(reviews)
    return all_reviews    

def get_from_offset(offset: int,product_id: str, api_key: str,proxy_url: str, locale: str = "en", currency: str = "USD") -> str:
    headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Airbnb-Api-Key": api_key,
    }
    variablesData={
            "id": product_id,
            "pdpReviewsRequest":{
            "fieldSelector": "for_p3_translation_only",
            "forPreview": False,
            "limit": 50,
            "offset": f"{offset}",
            "showingTranslationButton": False,
            "first": 50,
            "sortingPreference": "MOST_RECENT",
            "numberOfAdults": "1",
            "numberOfChildren": "0",
            "numberOfInfants": "0",
            "numberOfPets": "0",
            "after": None,
        }
    }
    entension={
        "persistedQuery": {
            "version":1,
            "sha256Hash": "dec1c8061483e78373602047450322fd474e79ba9afa8d3dbbc27f504030f91d",
        },
    }
    dataRawExtension = json.dumps(entension)
    dataRawVariables = json.dumps(variablesData)
    query = {
        "operationName": "StaysPdpReviewsQuery",
        "locale": locale,
        "currency": currency,
        "variables": dataRawVariables,
        "extensions": dataRawExtension,
    }
    url = f"{ep}?{urlencode(query)}"
    proxies = {}
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    response = requests.get(url, headers=headers, proxies=proxies, timeout=60)
    response.raise_for_status() 
    data = response.json()
    reviews = utils.get_nested_value(data,"data.presentation.stayProductDetailPage.reviews.reviews",{})
    return reviews