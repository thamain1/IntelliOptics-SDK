from fourward.intellioptics.client import IntelliOptics

def test_sdk_init():
    client = IntelliOptics(api_token="fake-token")
    assert client.api_token == "fake-token"
