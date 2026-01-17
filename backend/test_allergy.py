from fastapi.testclient import TestClient
from main import app
import sys

client = TestClient(app)

# Use a purely mocked user ID to avoid database lookups failing
# We just want to check if the route MATCHES (i.e. returns 200, 404 from inner logic, or 500)
# A 404 from the router means "Route not found". 
# A 404 from inside the function means "User not found".
# We want to distinguish these.

user_id = "7qL4PzrEfQe04tvpUems1L89ePg1"
allergy_name = "Peanuts"

print(f"Testing POST /user/allergies/{user_id}?allergy_name={allergy_name}")
response = client.post(f"/user/allergies/{user_id}?allergy_name={allergy_name}")

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 404 and "Profile not found" in response.json().get("detail", ""):
    print("SUCCESS: Route matched, but user profile not found (Expected).")
elif response.status_code == 200:
    print("SUCCESS: Route matched and executed.")
else:
    print("FAILURE: Unexpected response.")
