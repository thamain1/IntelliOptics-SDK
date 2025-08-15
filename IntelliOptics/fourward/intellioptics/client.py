import os
<<<<<<< HEAD
import time
=======
>>>>>>> 5f1bbe5 (Initial commit of IntelliOptics SDK)
import requests
from .models import Detector, ImageQuery
from .exceptions import APIError
from .config import get_headers

class IntelliOptics:
    def __init__(self, endpoint=None, api_token=None, verify_tls=True):
        self.endpoint = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT", "http://localhost:8000")
        self.api_token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
        self.verify_tls = verify_tls
        if not self.api_token:
            raise ValueError("API token is required for IntelliOptics SDK")

    def create_detector(self, name, query, **kwargs):
        payload = {
            "name": name,
            "query": query,
            "confidence_threshold": kwargs.get("confidence_threshold", 0.9),
            "metadata": kwargs.get("metadata", {}),
        }
        response = requests.post(f"{self.endpoint}/api/detectors", json=payload, headers=get_headers(self.api_token), verify=self.verify_tls)
        if response.status_code != 201:
            raise APIError(response)
        return Detector(**response.json())

<<<<<<< HEAD
    def list_detectors(self):
        response = requests.get(f"{self.endpoint}/api/detectors", headers=get_headers(self.api_token), verify=self.verify_tls)
        if response.status_code != 200:
            raise APIError(response)
        return [Detector(**d) for d in response.json()]

    def delete_detector(self, detector_id):
        response = requests.delete(f"{self.endpoint}/api/detectors/{detector_id}", headers=get_headers(self.api_token), verify=self.verify_tls)
        if response.status_code != 204:
            raise APIError(response)
        return {"status": "deleted"}

=======
>>>>>>> 5f1bbe5 (Initial commit of IntelliOptics SDK)
    def submit_image_query(self, detector_id, image_path, wait=True):
        with open(image_path, "rb") as img_file:
            files = {"image": img_file}
            data = {"detector_id": detector_id, "wait": wait}
            response = requests.post(f"{self.endpoint}/api/image-query", headers=get_headers(self.api_token), files=files, data=data, verify=self.verify_tls)
        if response.status_code != 200:
            raise APIError(response)
        return ImageQuery(**response.json())

    def get_image_query(self, query_id):
        response = requests.get(f"{self.endpoint}/api/image-query/{query_id}", headers=get_headers(self.api_token), verify=self.verify_tls)
        if response.status_code != 200:
            raise APIError(response)
        return ImageQuery(**response.json())

    def add_label(self, query_id, label):
        payload = {"label": label}
        response = requests.post(f"{self.endpoint}/api/image-query/{query_id}/label", json=payload, headers=get_headers(self.api_token), verify=self.verify_tls)
        if response.status_code != 200:
            raise APIError(response)
        return {"status": "Label added"}
<<<<<<< HEAD

    def wait_for_confident_result(self, query_id, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            query = self.get_image_query(query_id)
            if query.result:
                return query
            time.sleep(1)
        raise TimeoutError("Timed out waiting for result")

    def ask(self, detector_id, image_path):
        query = self.submit_image_query(detector_id, image_path, wait=True)
        return query.result

    def ask_confident(self, detector_id, image_path, threshold=0.9):
        result = self.ask(detector_id, image_path)
        if result and result.get("confidence", 0) >= threshold:
            return result
        raise ValueError("Result not confident enough")
=======
>>>>>>> 5f1bbe5 (Initial commit of IntelliOptics SDK)
