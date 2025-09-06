from typing import Union, IO
from io import BytesIO
from PIL import Image
try:
    import numpy as np  # type: ignore
except Exception:
    np = None  # type: ignore

def to_jpeg_bytes(image: Union[str, bytes, IO[bytes], "Image.Image", "np.ndarray"]) -> bytes:  # type: ignore[name-defined]
    if isinstance(image, bytes):
        return image
    if hasattr(image, "read"):
        return image.read()  # type: ignore[return-value]
    if isinstance(image, str):
        with open(image, "rb") as f:
            return f.read()
    try:
        if isinstance(image, Image.Image):
            buf = BytesIO()
            image.save(buf, format="JPEG", quality=95)
            return buf.getvalue()
    except Exception:
        pass
    if np is not None and isinstance(image, np.ndarray):  # type: ignore[attr-defined]
        img = Image.fromarray(image[:, :, :3]) if image.ndim == 3 else Image.fromarray(image)  # type: ignore[index]
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    raise TypeError("Unsupported image type")
