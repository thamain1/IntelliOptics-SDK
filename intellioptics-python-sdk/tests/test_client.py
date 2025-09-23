import responses

from intellioptics import IntelliOptics


def test_get_image_query_normalizes():
    base = "https://api.example.com"
    iq_id = "iq_123"

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.get(
            f"{base}/v1/image-queries/{iq_id}",
            json={
                "id": iq_id,
                "status": "DONE",
                "result_type": "YESNO",
                "label": "YES",
                "confidence": 0.97,
            },
        )

        io = IntelliOptics(endpoint=base, api_token="t")
        iq = io.get_image_query(iq_id)

    assert iq.id == iq_id
    assert iq.status == "DONE"
    assert iq.label == "YES"
    assert iq.confidence == 0.97
