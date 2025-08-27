from intellioptics import IntelliOptics

io = IntelliOptics(
    endpoint="https://intellioptics-api-37558.azurewebsites.net",
    api_token="rnGT87T8Fevu0x248gUq3QLk0KlVDc+dRHw/tZB3VV2mzAxoc0qSO2XkQZbm8/fx",
)

det = io.create_detector(
    name="smoke-detector-test",
    mode="binary",
    query="Is there a person in the image?",
    confidence_threshold=0.75,
)

print(det)
