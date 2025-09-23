import os
import io
import json
import typing as _t
from httpx import Timeout
from ._http import make_httpx_client

# ----- generated imports (present after codegen) -----
try:
    from .generated.openapi.client import AuthenticatedClient
    from .generated.openapi.api.default.healthz_healthz_get import sync as _healthz_sync
    from .generated.openapi.api.default.create_detector_v1_detectors_post import sync as _create_detector_sync
    from .generated.openapi.api.default.get_detector_v1_detectors_detector_id_get import sync as _get_detector_sync
    from .generated.openapi.api.default.list_detectors_v1_detectors_get import sync as _list_detectors_sync
    from .generated.openapi.api.default.get_current_user_v1_users_me_get import sync as _get_current_user_sync
    from .generated.openapi.api.default.create_label_v1_labels_post import sync as _create_label_sync
    from .generated.openapi.api.default.image_query_json_v1_image_queries_json_post import sync as _image_query_json_sync
    from .generated.openapi.api.default.get_image_query_v1_image_queries_iq_id_get import sync as _get_image_query_sync
    from .generated.openapi.api.default.feedback_v1_feedback_post import sync as _feedback_sync

    from .generated.openapi.models.detector_create import DetectorCreate
    from .generated.openapi.models.detector_out import DetectorOut
    from .generated.openapi.models.detector_list import DetectorList
    from .generated.openapi.models.user_identity import UserIdentity
    from .generated.openapi.models.label_create import LabelCreate
    from .generated.openapi.models.label_record import LabelRecord
    from .generated.openapi.models.image_query_json import ImageQueryJson
    from .generated.openapi.models.feedback_in import FeedbackIn
except Exception:
    AuthenticatedClient = _t.Any  # type: ignore[misc,assignment]
    _healthz_sync = None  # type: ignore[assignment]
    _create_detector_sync = None  # type: ignore[assignment]
    _get_detector_sync = None  # type: ignore[assignment]
    _list_detectors_sync = None  # type: ignore[assignment]
    _get_current_user_sync = None  # type: ignore[assignment]
    _create_label_sync = None  # type: ignore[assignment]
    _image_query_json_sync = None  # type: ignore[assignment]
    _get_image_query_sync = None  # type: ignore[assignment]
    _feedback_sync = None  # type: ignore[assignment]
    DetectorCreate = _t.Any  # type: ignore[assignment]
    DetectorOut = _t.Any  # type: ignore[assignment]
    DetectorList = _t.Any  # type: ignore[assignment]
    UserIdentity = _t.Any  # type: ignore[assignment]
    LabelCreate = _t.Any  # type: ignore[assignment]
    LabelRecord = _t.Any  # type: ignore[assignment]
    ImageQueryJson = _t.Any  # type: ignore[assignment]
    FeedbackIn = _t.Any  # type: ignore[assignment]

# Optional deps for image conversion helpers
try:
    from PIL import Image as _PIL_Image  # type: ignore
except Exception:
    _PIL_Image = None  # type: ignore

try:
    import numpy as _np  # type: ignore
except Exception:
    _np = None  # type: ignore


def _to_jpeg_bytes(image: _t.Union[str, bytes, "io.BytesIO", "io.BufferedReader", "_PIL_Image.Image", "_np.ndarray"]) -> bytes:
    if isinstance(image, str):
        with open(image, "rb") as f:
            return f.read()
    if isinstance(image, (bytes, bytearray)):
        return bytes(image)
    if isinstance(image, (io.BytesIO, io.BufferedReader)):
        return image.read()
    if _PIL_Image is not None and isinstance(image, _PIL_Image.Image):  # type: ignore[attr-defined]
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    if _np is not None and isinstance(image, _np.ndarray):  # type: ignore[attr-defined]
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("numpy array must have shape (H, W, 3)")
        arr = image[:, :, ::-1].astype("uint8")
        if _PIL_Image is None:
            raise RuntimeError("Pillow not installed; cannot encode numpy array to JPEG")
        img = _PIL_Image.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    raise TypeError("Unsupported image type for submit_image_query().")


class IntelliOptics:
    """
    High-level IntelliOptics Python SDK.

    Implemented so far:
      - Auth setup
      - health() / health_generated()
      - create_detector(...)
      - get_detector(detector_id)
      - submit_image_query(...)      (multipart)
      - submit_image_query_json(...) (JSON body)
      - get_image_query(iq_id)
      - submit_feedback(**kwargs)
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_token: str | None = None,
        disable_tls_verification: bool | None = None,
        timeout: float = 30.0,
    ) -> None:
        token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
        if not token:
            raise ValueError("Missing INTELLIOPTICS_API_TOKEN (set env var or pass api_token=)")
        base_url = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT") or "http://localhost:8000"

        disable_env = os.getenv("DISABLE_TLS_VERIFY") == "1"
        disable_flag = bool(disable_tls_verification) if disable_tls_verification is not None else False
        verify = not (disable_flag or disable_env)

        self._base_url = base_url
        self._token = token
        self._headers = {"Authorization": f"Bearer {token}"}
        self._http = make_httpx_client(base_url=base_url, verify=verify, timeout=Timeout(timeout))

        try:
            self._client = AuthenticatedClient(
                base_url=base_url,
                token=token,
                verify_ssl=verify,
                timeout=timeout,
            )
        except Exception:
            self._client = None

    # ---- health ----
    def health(self) -> bool:
        resp = self._http.get("/healthz", headers=self._headers)
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception:
            return resp.status_code == 200
        return bool(data) or resp.status_code == 200

    def health_generated(self) -> bool:
        if self._client is None or _healthz_sync is None:
            return self.health()
        try:
            _ = _healthz_sync(client=self._client)
            return True
        except Exception:
            return self.health()

    # ---- detectors ----
    def create_detector(self, **kwargs) -> "DetectorOut":
        if self._client is None or _create_detector_sync is None or DetectorCreate is _t.Any:
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        body = DetectorCreate(**kwargs)
        return _create_detector_sync(client=self._client, body=body)

    def get_detector(self, detector_id: str) -> "DetectorOut":
        if self._client is None or _get_detector_sync is None:
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        return _get_detector_sync(client=self._client, detector_id=detector_id)

    def list_detectors(self) -> list["DetectorOut"]:
        if (
            self._client is None
            or _list_detectors_sync is None
            or DetectorList is _t.Any
            or DetectorOut is _t.Any
        ):
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        result = _list_detectors_sync(client=self._client)
        if isinstance(result, DetectorList):
            return list(result.items)
        raise RuntimeError(f"Unexpected response from API: {result!r}")

    # ---- image queries ----
    def submit_image_query(
        self,
        detector: _t.Union[str, "DetectorOut"],
        image: _t.Union[str, bytes, "io.BytesIO", "io.BufferedReader", "_PIL_Image.Image", "_np.ndarray"],
        *,
        wait: float | None = None,
        confidence_threshold: float | None = None,
        human_review: str | None = None,
        metadata: _t.Union[dict, str, None] = None,
        inspection_id: str | None = None,
    ) -> _t.Any:
        det_id = detector.id if hasattr(detector, "id") else str(detector)
        jpg = _to_jpeg_bytes(image)
        data: dict[str, str] = {"detector_id": det_id}
        if wait is not None:
            data["wait"] = str(float(wait))
        if confidence_threshold is not None:
            data["confidence_threshold"] = str(float(confidence_threshold))
        if human_review is not None:
            data["human_review"] = str(human_review)
        if inspection_id is not None:
            data["inspection_id"] = inspection_id
        if metadata is not None:
            data["metadata"] = json.dumps(metadata) if isinstance(metadata, dict) else str(metadata)
        files = {"image": ("image.jpg", jpg, "image/jpeg")}
        resp = self._http.post("/v1/image-queries", headers=self._headers, data=data, files=files)
        resp.raise_for_status()
        return resp.json()

    def submit_image_query_json(self, **kwargs) -> _t.Any:
        if self._client is None or _image_query_json_sync is None or ImageQueryJson is _t.Any:
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        body = ImageQueryJson(**kwargs)
        return _image_query_json_sync(client=self._client, body=body)

    def get_image_query(self, iq_id: str) -> _t.Any:
        """Fetch an image query by ID."""
        if self._client is None or _get_image_query_sync is None:
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        return _get_image_query_sync(client=self._client, iq_id=iq_id)

    def submit_feedback(self, **kwargs) -> _t.Any:
        """
        Submit feedback on a prior image query.
        kwargs must match FeedbackIn schema (e.g., iq_id=..., correct_label=..., bboxes=[...], notes=...).
        """
        if self._client is None or _feedback_sync is None or FeedbackIn is _t.Any:
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        body = FeedbackIn(**kwargs)
        return _feedback_sync(client=self._client, body=body)

    # ---- users ----
    def whoami(self) -> "UserIdentity":
        if self._client is None or _get_current_user_sync is None or UserIdentity is _t.Any:
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        result = _get_current_user_sync(client=self._client)
        if isinstance(result, UserIdentity):
            return result
        raise RuntimeError(f"Unexpected response from API: {result!r}")

    # ---- labels ----
    def add_label(self, **kwargs) -> "LabelRecord":
        if self._client is None or _create_label_sync is None or LabelCreate is _t.Any or LabelRecord is _t.Any:
            raise RuntimeError("Generated client not available; re-run codegen or check installation.")
        body = LabelCreate(**kwargs)
        result = _create_label_sync(client=self._client, body=body)
        if isinstance(result, LabelRecord):
            return result
        raise RuntimeError(f"Unexpected response from API: {result!r}")

    def close(self) -> None:
        try:
            self._http.close()
        except Exception:
            pass
