from curl_cffi import requests
from urllib.parse import urlencode
import pyairbnb.utils as utils
import uuid
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout

ep_search = "https://www.airbnb.com/api/v3/ExperiencesSearch/fbbf9989cdf264a11fce48073008bb557f7f6b43961ccda5df6a8d988bd6ef36"
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en",
    "Cache-Control": "no-cache",
    "content-type": "application/json",
    "Connection": "close",
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
def search_by_place_id(cursor: str, place_id: str, location_name: str, currency:str, locale: str, check_in:str, check_out:str, api_key:str, proxy_url:str, timeout: Timeout = DEFAULT_TIMEOUT):
    query_params = {
        "operationName": "ExperiencesSearch",
        "locale": locale,
        "currency": currency,
    }
    url_parsed = f"{ep_search}?{urlencode(query_params)}"
    rawParams=[
        {"filterName":"cdnCacheSafe","filterValues":["false"]},
        {"filterName":"checkin","filterValues":[check_in]},
        {"filterName":"checkout","filterValues":[check_out]},
        {"filterName":"datePickerType","filterValues":["calendar"]},
        {"filterName":"federatedSearchSessionId","filterValues":[str(uuid.uuid4())]},
        {"filterName":"flexibleTripLengths","filterValues":["one_week"]},
        {"filterName":"isOnlineExperiences","filterValues":["false"]},
        {"filterName":"itemsPerGrid","filterValues":["24"]},
        {"filterName":"location","filterValues":[location_name]},
        {"filterName":"monthlyEndDate","filterValues":["2025-05-01"]},
        {"filterName":"monthlyLength","filterValues":["3"]},
        {"filterName":"monthlyStartDate","filterValues":["2025-02-01"]},
        {"filterName":"placeId","filterValues":[place_id]},
        {"filterName":"query","filterValues":[location_name]},
        {"filterName":"rankMode","filterValues":["default"]},
        {"filterName":"refinementPaths","filterValues":["/experiences"]},
        {"filterName":"screenSize","filterValues":["large"]},
        {"filterName":"searchType","filterValues":["filter_change"]},
        {"filterName":"source","filterValues":["structured_search_input_header"]},
        {"filterName":"tabId","filterValues":["experience_tab"]},
        {"filterName":"version","filterValues":["1.8.3"]}
    ]
    inputData = {
        "operationName":"ExperiencesSearch",
        "extensions":{
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "fbbf9989cdf264a11fce48073008bb557f7f6b43961ccda5df6a8d988bd6ef36",
            },
        },
        "variables":{
            "isLeanTreatment": False,
            "experiencesSearchRequest": {
                "metadataOnly": False,
                "rawParams": rawParams,
                "searchType": "filter_change",
                "source": "structured_search_input_header",
                "treatmentFlags":[
                    "stays_search_rehydration_treatment_desktop",
                    "stays_search_rehydration_treatment_moweb",
                    "experiences_search_feed_only_treatment",
                ]
            },
        },
    }
    if cursor!="":
        inputData["variables"]["experiencesSearchRequest"]["cursor"] = cursor
    headers_copy = headers.copy()
    headers_copy["X-Airbnb-Api-Key"] = api_key
    proxies = {}
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    response = requests.post(url_parsed, json = inputData, headers=headers_copy, proxies=proxies,  impersonate="chrome124", timeout=timeout)
    if response.status_code != 200:
        raise Exception("Not corret status code: ", response.status_code, " response body: ",response.text)
    data = response.json()
    to_return=utils.get_nested_value(data,"data.presentation.experiencesSearch.results.searchResults",{})
    cursor=utils.get_nested_value(data,"data.presentation.experiencesSearch.results.paginationInfo.nextPageCursor","")
    return to_return,cursor