# Intelli)ptics SDK v0.2
Now with ask(), list_detectors(), and more.

An AI-powered computer vision SDK designed for IntelliOptics's capabilities — privately hosted and controlled by **4WardMotion**.

## 🚀 Features (v0.2)
- ✅ `create_detector()`
- ✅ `list_detectors()`
- ✅ `delete_detector()`
- ✅ `submit_image_query()`
- ✅ `get_image_query()`
- ✅ `ask()` - one-shot query
- ✅ `ask_confident()` - one-shot with confidence check
- ✅ `wait_for_confident_result()`
- ✅ `add_label()`
- 🔬 `ExperimentalApi` stub for alert/rule expansion

## 🧪 Quickstart

### Install locally (in development mode)
```bash
pip install -e .
Use in Python
python
Always show details

Copy
from fourward.intellioptics.client import IntelliOptics

client = IntelliOptics(api_token="your-api-key")

# Create detector
detector = client.create_detector("Safety Hat", "Is the person wearing a helmet?")

# Ask a question
result = client.ask_confident(detector.id, "images/frame1.jpg", threshold=0.85)
print(result)
🛠️ Configuration
INTELLIOPTICS_API_TOKEN – your API key

INTELLIOPTICS_ENDPOINT – base URL of your backend (default: http://localhost:8000)

🤖 API Compatibility
Designed to work with fourward-intellioptics-backend FastAPI server:

 /api/detectors

 /api/image-query

 /api/image-query/{id}

 /api/image-query/{id}/label

⚙️ Testing
To run tests locally:

bash
Always show details

Copy
export PYTHONPATH=.
pytest tests
🧩 Coming Soon
ROI (Region of Interest) support

Video stream input

Alerting rules via Experimental API

Human-in-the-loop labeling UI

Azure Blob & SQL integration

📄 License
MIT License (c) 2025 4WardMotion
