from __future__ import annotations

from io import BytesIO

from PIL import Image

from intellioptics._img import to_jpeg_bytes


def _make_image_bytes(fmt: str, color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (10, 10), color=color)
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def test_jpeg_bytes_passthrough():
    jpeg_bytes = _make_image_bytes("JPEG")
    assert to_jpeg_bytes(jpeg_bytes) == jpeg_bytes


def test_png_bytes_are_transcoded_to_jpeg():
    png_bytes = _make_image_bytes("PNG")
    jpeg_bytes = to_jpeg_bytes(png_bytes)

    with Image.open(BytesIO(jpeg_bytes)) as result:
        assert result.format == "JPEG"


def test_png_stream_is_transcoded_and_rewound():
    png_bytes = _make_image_bytes("PNG")
    stream = BytesIO(png_bytes)

    jpeg_bytes = to_jpeg_bytes(stream)

    # Stream is rewound if possible so callers can reuse it.
    assert stream.tell() == 0

    with Image.open(BytesIO(jpeg_bytes)) as result:
        assert result.format == "JPEG"


def test_png_path_is_transcoded(tmp_path):
    png_path = tmp_path / "example.png"
    png_path.write_bytes(_make_image_bytes("PNG"))

    jpeg_bytes = to_jpeg_bytes(str(png_path))

    with Image.open(BytesIO(jpeg_bytes)) as result:
        assert result.format == "JPEG"
