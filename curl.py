import requests

url = "https://gql.tokopedia.com/graphql/Searching"

headers = {
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "tkpd-userid": "1502705",
    "X-Version": "77e0648",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "content-type": "application/json",
    "accept": "*/*",
    "Referer": "https://www.tokopedia.com/flight/search/?r=CGK.DPS&d=20240317&a=1&c=0&i=0&k=1",
    "X-Source": "tokopedia-lite",
    "X-Tkpd-Lite-Service": "test",
    "sec-ch-ua-platform": '"macOS"',
}

payload = """
[{"operationName":"Searching","variables":{"data":{"Departure":"CGK","Arrival":"DPS","Date":"2024-03-17","Adult":1,"Child":0,"Infant":0,"Class":1,"ExcludedAirlines":[],"IPAddress":"","RequestID":""}},"query":"query Searching($data: SearchSingleArgs) {\n  flightSearch(input: $data) {\n    data {\n      id\n      term\n      departureAirportID\n      departureTime\n      departureTimeInt\n      departureTerminal\n      arrivalAirportID\n      arrivalTime\n      arrivalTimeInt\n      arrivalTerminal\n      totalTransit\n      addDayArrival\n      totalStop\n      duration\n      durationMinute\n      durationLong\n      showSpecialPriceTag\n      total\n      totalNumeric\n      beforeTotal\n      label1\n      label2\n      routes {\n        airlineID\n        departureAirportID\n        departureTime\n        arrivalAirportID\n        arrivalTime\n        duration\n        layover\n        flightNumber\n        stop\n        operatingAirlineID\n        amenities {\n          icon\n          label\n          __typename\n        }\n        stopDetail {\n          code\n          city\n          __typename\n        }\n        infos {\n          label\n          value\n          __typename\n        }\n        __typename\n      }\n      fare {\n        adult\n        child\n        infant\n        adultNumeric\n        childNumeric\n        infantNumeric\n        __typename\n      }\n      __typename\n    }\n    included {\n      type\n      id\n      attributes {\n        shortName\n        logo\n        name\n        city\n        __typename\n      }\n      __typename\n    }\n    meta {\n      needRefresh\n      refreshTime\n      maxRetry\n      adult\n      child\n      infant\n      requestID\n      internationalTransitTag\n      backgroundRefreshTime\n      __typename\n    }\n    error {\n      id\n      status\n      title\n      __typename\n    }\n    __typename\n  }\n}\n"}]"""

response = requests.post(url, headers=headers, data=payload)

if response.status_code == 200:
    print("Response:")
    print(response.text)
else:
    print("Failed to retrieve data. Status code:", response.status_code)
