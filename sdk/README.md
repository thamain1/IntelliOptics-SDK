# IntelliOptics Python SDK 
from intellioptics import IntelliOptics

# Example:

# io = IntelliOptics()  # reads INTELLOPTICS_API_TOKEN & INTELLOPTICS_BASE_URL
# det = io.create_detector("Door open?", labels=["open", "closed"])

# io = IntelliOptics()  # reads INTELLIOPTICS_API_TOKEN & INTELLIOPTICS_BASE_URL
# det = io.create_detector("Door open?", "binary", "Is the door open?", threshold=0.8)

# ans = io.ask_image(det.id, "frame.jpg")
# print(ans.answer, ans.confidence)
