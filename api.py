import requests


def get_dummy_json_data():
    url = "https://dummyjson.com/products/1"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None


# Call the function to get the data
dummy_data = get_dummy_json_data()
if dummy_data:
    print(dummy_data)
