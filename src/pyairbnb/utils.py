import math
import re
from typing import TypeAlias
from urllib.parse import quote


Timeout: TypeAlias = int | float | tuple[int | float, int | float] | None
DEFAULT_TIMEOUT: Timeout = 60

regex_space = re.compile(r'[\s ]+')
regx_price = re.compile(r'\d+(?:\.\d+)?')

def coerce_number(value, name: str = "value") -> int | float | None:
    """Convert a numeric filter value, preserving integer values as ints."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number; got {value!r}") from error

    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number; got {value!r}")

    return int(number) if number.is_integer() else number

def remove_space(value:str):
    return regex_space.sub(' ', value.strip())

def get_nested_value(dic, key_path, default=None):
    keys = key_path.split(".")
    current = dic
    for key in keys:
        current = current.get(key, {})
        if current == {} or current is None:
            return default
    return current

def parse_price_symbol(price_raw: str):
    price_raw = price_raw.replace(",", "")

    
    price_number_match = regx_price.search(price_raw)
    
    if price_number_match is None:
        return 0,""
    
    price_number = price_number_match.group(0)
    
    price_currency = price_raw.replace(price_number, "").replace(" ", "").replace("-", "")
    
    price_converted = float(price_number)
    if price_raw.startswith("-"):
        price_converted *= -1
    
    return price_converted, price_currency

def parse_proxy(ip_or_domain: str,port: str, username: str, password: str) -> (str):
    encoded_username = quote(username)
    encoded_password = quote(password)
    proxy_url = f"http://{encoded_username}:{encoded_password}@{ip_or_domain}:{port}"
    return proxy_url
