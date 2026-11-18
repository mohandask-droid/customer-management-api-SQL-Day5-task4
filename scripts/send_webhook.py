import hashlib, hmac, json, requests

SECRET = "my-super-secret"   # same as .env
URL = "http://127.0.0.1:8000/webhooks/customer-events"

body = json.dumps({"event": "customer.created", "id": 1}).encode()
sig = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()

r = requests.post(URL, data=body, headers={"X-Signature": sig})
print("valid   :", r.status_code, r.json())

r = requests.post(URL, data=body + b"x", headers={"X-Signature": sig})
print("tampered:", r.status_code, r.json())

r = requests.post(URL, data=body)
print("missing :", r.status_code)