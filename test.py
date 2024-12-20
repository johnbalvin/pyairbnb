import pyairbnb
import json
from urllib.parse import urlparse, parse_qs


def test0():
    room_id=668146487515150072
    currency="MXN"
    check_in = "2024-11-04"
    check_out = "2024-11-10"
    data = pyairbnb.get_details(room_id=room_id, 
                                currency=currency,
                                check_in=check_in,
                                check_out=check_out)
    with open('details.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data))


def test1():
    room_id=668146487515150072
    currency="MXN"
    check_in = "2024-11-02"
    check_out = "2024-11-10"
    proxy_url = pyairbnb.parse_proxy("[IP or domain]","[port]","[user name]","[password]")
    data = pyairbnb.get_details(room_id=room_id,
                                currency=currency,
                                check_in=check_in,
                                check_out=check_out,
                                proxy_url=proxy_url)
    with open('details.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data))

def test11():
    room_url="https://www.airbnb.com/rooms/762251620189545147"
    currency="MXN"
    check_in = "2024-11-02"
    check_out = "2024-11-10"
    data = pyairbnb.get_details(room_url=room_url,
                                currency=currency,
                                check_in=check_in,
                                check_out=check_out)
    with open('details.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data))


def test2():
    currency="MXN"
    check_in = "2024-11-04"
    check_out = "2024-11-10"
    ne_lat = -1.03866277790021
    ne_long = -77.53091734683608
    sw_lat = -1.1225978433925647
    sw_long = -77.59713412765507
    zoom_value = 2
    results = pyairbnb.search_all(check_in,check_out,ne_lat,ne_long,sw_lat,sw_long,zoom_value, currency,"")
    with open('search_all.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(results))

def test3():
    calendar_data = pyairbnb.get_calendar("762251620189545147","")
    with open('calendar_data.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(calendar_data))
