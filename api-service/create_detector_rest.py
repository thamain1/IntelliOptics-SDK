import requests

API = "https://intellioptics-api-37558.azurewebsites.net"
TOKEN = "rnGT87T8Fevu0x248gUq3QLk0KlVDc+dRHw/tZB3VV2mzAxoc0qSO2XkQZbm8/fx"

payload = {
    "name": "smoke-detector-test",
    "mode": "binary",
    "query": "Is there a person in the image?",
    "confidence_threshold": 0.75
}

resp = requests.post(
    f"{API}/v1/detectors",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json=payload,
)

print(resp.status_code, resp.json())
