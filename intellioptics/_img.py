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


def _coerce_file_like(image: ImageLike) -> bytes | None:
    if isinstance(image, (bytes, bytearray)):
        return bytes(image)

    if hasattr(image, "read") and callable(image.read):  # file-like object
        data = image.read()
        if isinstance(data, bytes):
            return data
        raise TypeError("File-like objects must return bytes when read()")

    if isinstance(image, (str, Path)):
        path = Path(image)
        return path.read_bytes()

    return None


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

    data = _coerce_file_like(image)
    if data is not None:
        return data

    if Image is not None and hasattr(image, "__class__") and image.__class__.__module__.startswith("PIL"):  # type: ignore[attr-defined]
        return _encode_with_pillow(image)  # type: ignore[arg-type]

    if np is not None and isinstance(image, np.ndarray):  # type: ignore[attr-defined]
        return _encode_numpy(image)

    raise TypeError("Unsupported image type")

