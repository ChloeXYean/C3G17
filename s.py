import requests

print("Fetching countries...")
c = requests.get("https://api.openaq.org/v3/countries").json()
print(c.keys())
print(type(c.get("data")))
print(len(c.get("data", [])))
print(c.get("data", [])[:3])

print("\nFetching locations...")
l = requests.get("https://api.openaq.org/v3/locations?limit=5&parameter=pm25").json()
print(l.keys())
print(type(l.get("data")))
print(len(l.get("data", [])))
print(l.get("data", [])[:1])
