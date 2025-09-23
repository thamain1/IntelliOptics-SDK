from intellioptics.client import IntelliOptics


def test_init_sets_authorization_header():
    client = IntelliOptics(endpoint="https://api.example.test", api_token="test-token")

    assert client._http.headers["Authorization"] == "Bearer test-token"
