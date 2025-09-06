import respx, httpx
from intellioptics import IntelliOptics

@respx.mock
def test_get_image_query_normalizes():
    base = "https://api.example.com"; iq_id = "iq_123"
    respx.get(f"{base}/v1/image-queries/{iq_id}").mock(
        return_value=httpx.Response(200, json={
            "id": iq_id, "done_processing": True, "result_type": "YESNO",
            "result": {"label": "YES", "confidence": 0.97}
        })
    )
    io = IntelliOptics(endpoint=base, api_token="t")
    iq = io.get_image_query(iq_id)
    assert iq.done_processing and iq.result.label == "YES"
