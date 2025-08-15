from fourward.intellioptics.client import IntelliOptics

<<<<<<< HEAD
def test_sdk_init():
    client = IntelliOptics(api_token="fake-token")
    assert client.api_token == "fake-token"
=======
def test_init():
    client = IntelliOptics(api_token="test-token")
    assert client.api_token == "test-token"
>>>>>>> 5f1bbe5 (Initial commit of IntelliOptics SDK)
