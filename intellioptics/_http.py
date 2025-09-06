import requests
from .errors import IntelliOpticsClientError

class HttpClient:
    def __init__(self, base_url: str, api_token: str, verify: bool = True, timeout: float = 30.0):
        if not base_url:
            raise IntelliOpticsClientError("Missing INTELLIOPTICS_ENDPOINT")
        self.base = base_url.rstrip("/")
        self.verify = verify
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_token}"}

    def post_json(self, path, **kw):
        r = requests.post(self.base + path, headers=self.headers, timeout=self.timeout, verify=self.verify, **kw)
        if not r.ok:
            raise IntelliOpticsClientError(f"POST {path} {r.status_code} {r.text}")
        return r.json()

    def get_json(self, path, **kw):
        r = requests.get(self.base + path, headers=self.headers, timeout=self.timeout, verify=self.verify, **kw)
        if not r.ok:
            raise IntelliOpticsClientError(f"GET {path} {r.status_code} {r.text}")
        return r.json()
