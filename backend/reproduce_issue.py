import requests
import json

url = "http://10.156.65.50:8000/nearby-hospitals"
payload = {
    "lat": 28.6139,
    "lng": 77.2090, 
    "radius": 5000,
    "limit": 5
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    try:
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
