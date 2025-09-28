"""Image helpers for the IntelliOptics SDK."""

from __future__ import annotations

from io import BufferedIOBase, BytesIO
from pathlib import Path
from typing import IO, Any, Union

try:  # pragma: no cover - optional dependency
    from PIL import Image
except Exception:  # pragma: no cover - pillow may be absent during tests
    Image = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore[assignment]


ImageLike = Union[str, bytes, bytearray, IO[bytes], BufferedIOBase, "Image.Image", "np.ndarray"]


def _looks_like_jpeg(data: bytes) -> bool:
    return len(data) >= 2 and data[0:2] == b"\xff\xd8"


def _ensure_jpeg_bytes(data: bytes) -> bytes:
    if _looks_like_jpeg(data):
        return data

    if Image is None:
        raise RuntimeError("Pillow is required to convert non-JPEG inputs to JPEG")

    with Image.open(BytesIO(data)) as pil_image:  # type: ignore[attr-defined]
        return _encode_with_pillow(pil_image)


def _read_file_like(stream: Any) -> bytes:
    data = stream.read()
    if not isinstance(data, bytes):
        raise TypeError("File-like objects must return bytes when read()")

    if hasattr(stream, "seek") and callable(stream.seek):
        try:  # pragma: no cover - best effort rewind
            stream.seek(0)
        except Exception:
            pass

    return data


def _encode_with_pillow(pil_image: "Image.Image") -> bytes:
    buffer = BytesIO()
    pil_image.convert("RGB").save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def _encode_numpy(array: "np.ndarray") -> bytes:
    if array.ndim not in (2, 3):
        raise ValueError("numpy array must have 2 or 3 dimensions")
    if array.ndim == 3 and array.shape[2] not in (1, 3):
        raise ValueError("numpy array must have shape (H, W, 3) or (H, W, 1)")
    if Image is None:
        raise RuntimeError("Pillow is required to encode numpy arrays to JPEG")

    if array.ndim == 3 and array.shape[2] == 3:
        rgb = array.astype("uint8")
    else:  # grayscale
        rgb = array.squeeze().astype("uint8")

    image = Image.fromarray(rgb)
    return _encode_with_pillow(image)


def to_jpeg_bytes(image: ImageLike) -> bytes:
    """Normalise supported image inputs into a JPEG byte payload."""

    if Image is not None and isinstance(image, Image.Image):  # type: ignore[arg-type]
        return _encode_with_pillow(image)

    if np is not None and isinstance(image, np.ndarray):  # type: ignore[attr-defined]
        return _encode_numpy(image)

    if isinstance(image, (bytes, bytearray)):
        return _ensure_jpeg_bytes(bytes(image))

    if hasattr(image, "read") and callable(image.read):  # file-like object
        data = _read_file_like(image)
        return _ensure_jpeg_bytes(data)

    if isinstance(image, (str, Path)):
        data = Path(image).read_bytes()
        return _ensure_jpeg_bytes(data)

    raise TypeError("Unsupported image type")

