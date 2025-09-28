# IntelliOptics Python SDK (drop-in Groundlight-style client)
from intellioptics import IntelliOptics

# Example:
# io = IntelliOptics()  # reads INTELLIOPTICS_API_TOKEN & INTELLIOPTICS_BASE_URL
# det = io.create_detector("Door open?", "binary", "Is the door open?", threshold=0.8)
# ans = io.ask_image(det.id, "frame.jpg")
# print(ans.answer, ans.confidence)
