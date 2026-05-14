from curl_cffi import requests
import json
import base64
from pyairbnb.utils import DEFAULT_TIMEOUT, Timeout

def get(api_key: str, cookies, host_id: str, language: str, proxy_url: str, timeout: Timeout = DEFAULT_TIMEOUT):
    # Encode the host ID to match Airbnb's required format
    host_id = 'User:' + host_id
    user_id = base64.b64encode(host_id.encode()).decode('utf-8')
    
    # Set up headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Airbnb-Api-Key": api_key,
    }
    
    # Set up parameters
    params = {
        'operationName': 'GetUserProfile',
        'locale': language,
        'currency': 'USD',
        'variables': json.dumps({
            "userId": user_id,
            "isPassportStampsEnabled": True,
            "mockIdentifier": None,
            "fetchCombinedSportsAndInterests": True
        }),
        'extensions': json.dumps({
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "a56d8909f271740ccfef23dd6c34d098f194f4a6e7157f244814c5610b8ad76a"
            }
        })
    }

    # Set up proxy if available
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else {}

    # Make the GET request
    response = requests.get(
        'https://www.airbnb.com/api/v3/GetUserProfile/a56d8909f271740ccfef23dd6c34d098f194f4a6e7157f244814c5610b8ad76a',
        params=params,
        headers=headers,
        cookies=cookies,
        proxies=proxies,
        timeout=timeout,
    )

    # Raise an exception if the request failed
    response.raise_for_status()
    
    # Parse the response JSON
    data = response.json()
    
    return data
