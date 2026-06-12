import os
import struct
import tempfile

from densegrid.encode import encode_file
from densegrid.decode import decode_file


def test_roundtrip_short_text():
    payload = b"Hello, QR2!"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        png_path = f.name
    try:
        encode_file(payload, png_path)
        result = decode_file(png_path)
        assert result == payload
    finally:
        os.unlink(png_path)


def test_roundtrip_binary_data():
    payload = bytes(range(256))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        png_path = f.name
    try:
        encode_file(payload, png_path)
        result = decode_file(png_path)
        assert result == payload
    finally:
        os.unlink(png_path)


def test_roundtrip_empty_file():
    payload = b""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        png_path = f.name
    try:
        encode_file(payload, png_path)
        result = decode_file(png_path)
        assert result == payload
    finally:
        os.unlink(png_path)


def test_roundtrip_max_single_image():
    # ~16KB payload — should fit in one image
    payload = os.urandom(16000)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        png_path = f.name
    try:
        encode_file(payload, png_path)
        result = decode_file(png_path)
        assert result == payload
    finally:
        os.unlink(png_path)


def test_png_is_valid():
    """Encoded output should be a valid PNG with expected dimensions."""
    payload = b"test"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        png_path = f.name
    try:
        encode_file(payload, png_path)
        with open(png_path, "rb") as f:
            data = f.read()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        # IHDR: width and height at offset 16
        width = struct.unpack(">I", data[16:20])[0]
        height = struct.unpack(">I", data[20:24])[0]
        assert width == 177
        assert height == 177
    finally:
        os.unlink(png_path)
