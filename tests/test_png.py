import struct
from densegrid.png import write_png, read_png


def test_write_read_roundtrip():
    pixels = [
        [(0, 0, 0), (85, 170, 255)],
        [(255, 170, 85), (0, 0, 0)],
    ]
    data = write_png(pixels)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG signature
    result = read_png(data)
    assert result == pixels


def test_single_pixel():
    pixels = [[(255, 0, 0)]]
    data = write_png(pixels)
    result = read_png(data)
    assert result == pixels


def test_all_white():
    pixels = [[(255, 255, 255) for _ in range(10)] for _ in range(10)]
    data = write_png(pixels)
    result = read_png(data)
    assert result == pixels


def test_177x177_grid():
    pixels = [[(i % 4 * 85, 0, 0) for _ in range(177)] for i in range(177)]
    data = write_png(pixels)
    result = read_png(data)
    assert len(result) == 177
    assert len(result[0]) == 177
    assert result == pixels
