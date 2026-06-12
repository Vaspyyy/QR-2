# DenseGrid v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete CLI tool that encodes arbitrary files into QR² dense-grid PNG images and decodes them back, using only Python stdlib.

**Architecture:** The system is split into focused modules: pixel-level encoding, grid layout construction, header metadata, minimal PNG I/O, and CLI entry points. Each module has a single responsibility and is independently testable. The encode pipeline reads a file, builds a header, maps bytes to a pixel grid, and writes a PNG. The decode pipeline reverses this.

**Tech Stack:** Python 3.14, zero external dependencies, pytest for testing.

**Spec:** `/home/ransom/Schreibtisch/QR².txt`

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/densegrid/__init__.py` | Package init, version string |
| `src/densegrid/pixel.py` | `encode_pixel(n) → (R,G,B)`, `decode_pixel((R,G,B)) → n` |
| `src/densegrid/grid.py` | Grid layout constants, finder/timing/quiet-zone generation, data-region coordinate mapping |
| `src/densegrid/header.py` | Header pack/unpack: magic, payload size, version, CRC32, grid dimensions |
| `src/densegrid/png.py` | Minimal PNG write (RGB, no alpha, filter=None) and read |
| `src/densegrid/encode.py` | Full encode pipeline: file → header → bitstream → grid → PNG |
| `src/densegrid/decode.py` | Full decode pipeline: PNG → finder detection → header → bitstream → file |
| `src/densegrid/cli.py` | argparse CLI with `dgencode` and `dgdecode` entry points |
| `tests/test_pixel.py` | Pixel encode/decode tests |
| `tests/test_grid.py` | Grid layout and data-region mapping tests |
| `tests/test_header.py` | Header pack/unpack and CRC32 tests |
| `tests/test_png.py` | PNG write/read roundtrip tests |
| `tests/test_roundtrip.py` | Full encode→decode identity tests |
| `tests/test_cli.py` | CLI subprocess tests |
| `pyproject.toml` | Package config, CLI entry points, pytest config |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/densegrid/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=80"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "densegrid"
version = "0.1.0"
description = "High-density 2D barcode format — QR²"
requires-python = ">=3.14"

[project.scripts]
dgencode = "densegrid.cli:encode_main"
dgdecode = "densegrid.cli:decode_main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create src/densegrid/__init__.py**

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Create tests/__init__.py**

```python
```

- [ ] **Step 4: Verify project loads**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest --collect-only`
Expected: collects 0 tests, no import errors

- [ ] **Step 5: Initialize git and commit**

```bash
git init
git add pyproject.toml src/densegrid/__init__.py tests/__init__.py
git commit -m "chore: scaffold densegrid project"
```

---

## Task 2: Pixel Encoding & Decoding

**Covers:** [S2] Multi-Level Pixel Encoding, [S4] Pixel Construction

**Files:**
- Create: `src/densegrid/pixel.py`
- Create: `tests/test_pixel.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_pixel.py
from densegrid.pixel import encode_pixel, decode_pixel

def test_encode_zero():
    assert encode_pixel(0) == (0, 0, 0)

def test_encode_max():
    assert encode_pixel(63) == (255, 255, 255)

def test_encode_red_only():
    # bits 5-4 = 01 (red=85), bits 3-2 = 00 (green=0), bits 1-0 = 00 (blue=0)
    assert encode_pixel(0b010000) == (85, 0, 0)

def test_encode_green_only():
    assert encode_pixel(0b000100) == (0, 85, 0)

def test_encode_blue_only():
    assert encode_pixel(0b000001) == (0, 0, 85)

def test_decode_all_levels():
    for level, value in enumerate([0, 85, 170, 255]):
        # Single channel: red bits only, green=0, blue=0
        n = level << 4
        assert decode_pixel((value, 0, 0)) == n

def test_roundtrip_all_values():
    for n in range(64):
        assert decode_pixel(encode_pixel(n)) == n

def test_decode_tolerance():
    # Values at exact levels should decode cleanly
    assert decode_pixel((170, 85, 255)) == 0b100111
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_pixel.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'densegrid.pixel'`

- [ ] **Step 3: Implement pixel.py**

```python
# src/densegrid/pixel.py

LEVELS = (0, 85, 170, 255)


def encode_pixel(n: int) -> tuple[int, int, int]:
    """Encode a 0–63 value into an (R, G, B) pixel using 4-level intensity."""
    r = ((n >> 4) & 0b11) * 85
    g = ((n >> 2) & 0b11) * 85
    b = (n & 0b11) * 85
    return (r, g, b)


def decode_pixel(pixel: tuple[int, int, int]) -> int:
    """Decode an (R, G, B) pixel back to a 0–63 value."""
    r, g, b = pixel
    ri = round(r / 85)
    gi = round(g / 85)
    bi = round(b / 85)
    return (ri << 4) | (gi << 2) | bi
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_pixel.py -v`
Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/densegrid/pixel.py tests/test_pixel.py
git commit -m "feat: pixel encode/decode with 4-level RGB intensity"
```

---

## Task 3: Grid Layout

**Covers:** [S1] Visual Structure (QR-Like Layout)

**Files:**
- Create: `src/densegrid/grid.py`
- Create: `tests/test_grid.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_grid.py
from densegrid.grid import (
    GRID_SIZE,
    QUIET_ZONE,
    FINDER_SIZE,
    make_grid,
    get_data_pixels,
    is_finder_region,
    is_timing_pixel,
)

def test_grid_constants():
    assert GRID_SIZE == 177
    assert QUIET_ZONE == 4
    assert FINDER_SIZE == 7

def test_make_grid_dimensions():
    grid = make_grid()
    assert len(grid) == GRID_SIZE
    assert all(len(row) == GRID_SIZE for row in grid)

def test_finder_top_left():
    grid = make_grid()
    # Top-left finder: 7x7 nested squares
    # Outer border should be black (0,0,0)
    assert grid[4][4] == (0, 0, 0)  # top-left corner of finder
    # Inner 3x3 should be black (center)
    assert grid[7][7] == (0, 0, 0)

def test_quiet_zone_is_white():
    grid = make_grid()
    # Top-left quiet zone
    assert grid[0][0] == (255, 255, 255)
    assert grid[3][3] == (255, 255, 255)

def test_timing_pattern():
    grid = make_grid()
    # Row 6 (index): alternating black/white starting after finder
    # Column 6 (index): alternating black/white starting after finder
    # At position (6, 11) should be black (even offset from finder edge)
    assert grid[6][11] == (0, 0, 0)
    # At position (6, 12) should be white
    assert grid[6][12] == (255, 255, 255)

def test_data_pixel_count():
    data_pixels = get_data_pixels()
    # Data region: rows 8–176, cols 8–176 = 169×169 = 28561
    # Minus the header row (12 pixels) and structural overlaps
    assert len(data_pixels) > 20000
    assert len(data_pixels) < 30000

def test_data_pixels_not_in_structural_regions():
    data_pixels = get_data_pixels()
    for (r, c) in data_pixels:
        assert not is_finder_region(r, c)
        assert r >= QUIET_ZONE + FINDER_SIZE + 1  # below timing row
        assert c >= QUIET_ZONE + FINDER_SIZE + 1  # right of timing col
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_grid.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement grid.py**

```python
# src/densegrid/grid.py

GRID_SIZE = 177
QUIET_ZONE = 4
FINDER_SIZE = 7
HEADER_PIXELS = 12

# Finder pattern: 7x7 nested squares
# 0 = black, 1 = white
_FINDER_PATTERN = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0],
]

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def is_finder_region(r: int, c: int) -> bool:
    """Check if grid coordinates (r, c) fall within any finder pattern."""
    q = QUIET_ZONE
    f = FINDER_SIZE
    # Top-left
    if q <= r < q + f and q <= c < q + f:
        return True
    # Top-right
    if q <= r < q + f and GRID_SIZE - q - f <= c < GRID_SIZE - q:
        return True
    # Bottom-left
    if GRID_SIZE - q - f <= r < GRID_SIZE - q and q <= c < q + f:
        return True
    return False


def is_timing_pixel(r: int, c: int) -> bool:
    """Check if grid coordinates are on a timing pattern."""
    q = QUIET_ZONE
    f = FINDER_SIZE
    timing_row = q + f - 1  # row index 10 in absolute coords
    timing_col = q + f - 1  # col index 10 in absolute coords
    return r == timing_row or c == timing_col


def make_grid() -> list[list[tuple[int, int, int]]]:
    """Build the full 177×177 grid with finder patterns, timing, and quiet zone."""
    grid = [[WHITE for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    q = QUIET_ZONE

    # Place finder patterns
    def place_finder(start_r: int, start_c: int):
        for dr in range(FINDER_SIZE):
            for dc in range(FINDER_SIZE):
                val = _FINDER_PATTERN[dr][dc]
                color = BLACK if val == 0 else WHITE
                grid[start_r + dr][start_c + dc] = color

    place_finder(q, q)                              # top-left
    place_finder(q, GRID_SIZE - q - FINDER_SIZE)     # top-right
    place_finder(GRID_SIZE - q - FINDER_SIZE, q)     # bottom-left

    # Timing patterns (row and column connecting finders)
    timing_row = q + FINDER_SIZE - 1
    timing_col = q + FINDER_SIZE - 1
    for i in range(q + FINDER_SIZE, GRID_SIZE - q - FINDER_SIZE):
        color = BLACK if (i % 2 == 0) else WHITE
        grid[timing_row][i] = color  # horizontal
        grid[i][timing_col] = color  # vertical

    return grid


def get_data_pixels() -> list[tuple[int, int]]:
    """Return ordered list of (row, col) coordinates for data-region pixels.

    Order: left-to-right, top-to-bottom, skipping structural elements.
    First 12 pixels in the first data row are the header.
    """
    grid = make_grid()
    pixels = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] != WHITE:
                continue
            if is_finder_region(r, c):
                continue
            if is_timing_pixel(r, c):
                continue
            if r < QUIET_ZONE or c < QUIET_ZONE:
                continue
            if r >= GRID_SIZE - QUIET_ZONE or c >= GRID_SIZE - QUIET_ZONE:
                continue
            pixels.append((r, c))
    return pixels
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_grid.py -v`
Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/densegrid/grid.py tests/test_grid.py
git commit -m "feat: grid layout with finder patterns, timing, and data region mapping"
```

---

## Task 4: Header Encoding

**Covers:** [S3] Header Row (Metadata)

**Files:**
- Create: `src/densegrid/header.py`
- Create: `tests/test_header.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_header.py
import zlib
from densegrid.header import (
    MAGIC,
    FORMAT_VERSION,
    pack_header,
    unpack_header,
)

def test_magic_value():
    assert MAGIC == 0xD47

def test_pack_unpack_roundtrip():
    payload = b"Hello, QR2!"
    header = pack_header(len(payload), FORMAT_VERSION, payload)
    size, version, checksum, gw, gh = unpack_header(header)
    assert size == len(payload)
    assert version == FORMAT_VERSION
    assert checksum == zlib.crc32(payload)
    assert gw == 0
    assert gh == 0

def test_pack_header_length():
    header = pack_header(100, 1, b"x" * 100)
    assert len(header) == 12  # 12 pixels

def test_unpack_magic():
    header = pack_header(10, 1, b"test")
    # First two pixels encode magic
    from densegrid.pixel import decode_pixel
    p0 = decode_pixel(header[0])
    p1 = decode_pixel(header[1])
    magic = (p0 << 6) | p1
    assert magic == MAGIC

def test_large_payload_size():
    payload = b"\x00" * 100000
    header = pack_header(len(payload), 1, payload)
    size, version, checksum, _, _ = unpack_header(header)
    assert size == 100000
    assert checksum == zlib.crc32(payload)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_header.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement header.py**

```python
# src/densegrid/header.py

import zlib
import struct
from densegrid.pixel import encode_pixel, decode_pixel

MAGIC = 0xD47
FORMAT_VERSION = 1
HEADER_LENGTH = 12  # pixels


def pack_header(
    payload_size: int,
    version: int,
    payload: bytes,
) -> list[tuple[int, int, int]]:
    """Pack metadata into 12 encoded pixels.

    Layout (each value is split across one or more 6-bit pixel slots):
    - Pixels 0-1:  magic (12 bits)
    - Pixels 2-5:  payload size in bytes (24 bits)
    - Pixels 6-7:  format version (12 bits)
    - Pixels 8-11: CRC32 of payload (24 bits used out of 32 available)
    """
    checksum = zlib.crc32(payload) & 0xFFFFFFFF

    values = []
    # Magic: 12 bits split into two 6-bit values
    values.append((MAGIC >> 6) & 0x3F)
    values.append(MAGIC & 0x3F)

    # Payload size: 24 bits split into four 6-bit values
    values.append((payload_size >> 18) & 0x3F)
    values.append((payload_size >> 12) & 0x3F)
    values.append((payload_size >> 6) & 0x3F)
    values.append(payload_size & 0x3F)

    # Version: 12 bits split into two 6-bit values
    values.append((version >> 6) & 0x3F)
    values.append(version & 0x3F)

    # CRC32: 24 bits (low 24 bits of the 32-bit CRC) split into four 6-bit values
    values.append((checksum >> 18) & 0x3F)
    values.append((checksum >> 12) & 0x3F)
    values.append((checksum >> 6) & 0x3F)
    values.append(checksum & 0x3F)

    return [encode_pixel(v) for v in values]


def unpack_header(
    pixels: list[tuple[int, int, int]],
) -> tuple[int, int, int, int, int]:
    """Unpack 12 header pixels into (payload_size, version, crc32, grid_w, grid_h).

    Returns:
        (payload_size, version, crc32_checksum, grid_width, grid_height)
        grid_width and grid_height are 0 for default (square) grids.
    """
    values = [decode_pixel(p) for p in pixels]

    # Magic
    magic = (values[0] << 6) | values[1]
    if magic != MAGIC:
        raise ValueError(f"Invalid magic: 0x{magic:03X} (expected 0x{MAGIC:03X})")

    # Payload size
    payload_size = (
        (values[2] << 18)
        | (values[3] << 12)
        | (values[4] << 6)
        | values[5]
    )

    # Version
    version = (values[6] << 6) | values[7]

    # CRC32
    checksum = (
        (values[8] << 18)
        | (values[9] << 12)
        | (values[10] << 6)
        | values[11]
    )

    return payload_size, version, checksum, 0, 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_header.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/densegrid/header.py tests/test_header.py
git commit -m "feat: header pack/unpack with magic, size, version, CRC32"
```

---

## Task 5: Minimal PNG Encoder/Decoder

**Covers:** [S5] Pixel Extraction (step 1: load image as raw RGB)

**Files:**
- Create: `src/densegrid/png.py`
- Create: `tests/test_png.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_png.py
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
    # Simulate a small grid
    pixels = [[(i % 4 * 85, 0, 0) for _ in range(177)] for i in range(177)]
    data = write_png(pixels)
    result = read_png(data)
    assert len(result) == 177
    assert len(result[0]) == 177
    assert result == pixels
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_png.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement png.py**

```python
# src/densegrid/png.py

import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
    chunk = chunk_type + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)


def write_png(pixels: list[list[tuple[int, int, int]]]) -> bytes:
    """Write a 2D grid of (R, G, B) tuples to PNG bytes (no filter, no interlace)."""
    height = len(pixels)
    width = len(pixels[0])

    # Build raw image data: filter byte (0) + RGB row
    raw = b""
    for row in pixels:
        raw += b"\x00"  # filter: None
        for r, g, b in row:
            raw += struct.pack("BBB", r, g, b)

    compressed = zlib.compress(raw)

    # Build PNG
    result = PNG_SIGNATURE
    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    result += _make_chunk(b"IHDR", ihdr_data)
    # IDAT
    result += _make_chunk(b"IDAT", compressed)
    # IEND
    result += _make_chunk(b"IEND", b"")
    return result


def read_png(data: bytes) -> list[list[tuple[int, int, int]]]:
    """Read PNG bytes and return 2D grid of (R, G, B) tuples."""
    assert data[:8] == PNG_SIGNATURE, "Not a valid PNG"

    chunks = {}
    pos = 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        # Skip CRC
        pos += 12 + length
        chunks[chunk_type] = chunk_data

    # Parse IHDR
    ihdr = chunks[b"IHDR"]
    width, height = struct.unpack(">II", ihdr[:8])

    # Decompress IDAT
    raw = zlib.decompress(chunks[b"IDAT"])

    # Parse pixels
    pixels = []
    idx = 0
    for _ in range(height):
        filter_byte = raw[idx]
        idx += 1
        assert filter_byte == 0, f"Unsupported filter: {filter_byte}"
        row = []
        for _ in range(width):
            r, g, b = struct.unpack("BBB", raw[idx:idx + 3])
            row.append((r, g, b))
            idx += 3
        pixels.append(row)

    return pixels
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_png.py -v`
Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/densegrid/png.py tests/test_png.py
git commit -m "feat: minimal PNG encoder/decoder (RGB, no filter, stdlib only)"
```

---

## Task 6: Encode Pipeline + Decode Pipeline

**Covers:** [S4] Pixel Construction (Encoding), [S5] Pixel Extraction (Decoding)

**Files:**
- Create: `src/densegrid/encode.py`
- Create: `src/densegrid/decode.py`
- Create: `tests/test_roundtrip.py`

- [ ] **Step 1: Write failing roundtrip tests**

```python
# tests/test_roundtrip.py
import os
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
    import struct
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_roundtrip.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement encode.py**

```python
# src/densegrid/encode.py

from densegrid.grid import make_grid, get_data_pixels, HEADER_LENGTH
from densegrid.header import pack_header, FORMAT_VERSION
from densegrid.png import write_png


def encode_file(payload: bytes, output_path: str) -> None:
    """Encode a byte payload into a QR² PNG image."""
    grid = make_grid()
    data_pixels = get_data_pixels()

    # First HEADER_LENGTH pixels are reserved for the header
    header_pixels = data_pixels[:HEADER_LENGTH]
    body_pixels = data_pixels[HEADER_LENGTH:]

    # Pack header
    header = pack_header(len(payload), FORMAT_VERSION, payload)

    # Build bitstream from payload
    bits = _bytes_to_bits(payload)

    # Map header pixels
    for i, pixel in enumerate(header_pixels):
        grid[pixel[0]][pixel[1]] = header[i]

    # Map payload bits to body pixels (6 bits per pixel)
    bit_idx = 0
    for r, c in body_pixels:
        if bit_idx + 6 <= len(bits):
            chunk = int(bits[bit_idx:bit_idx + 6], 2)
            bit_idx += 6
        else:
            # Remaining bits (pad with zeros)
            remaining = bits[bit_idx:]
            remaining += "0" * (6 - len(remaining))
            chunk = int(remaining, 2)
            bit_idx = len(bits)
        from densegrid.pixel import encode_pixel
        grid[r][c] = encode_pixel(chunk)

    # Write PNG
    png_data = write_png(grid)
    with open(output_path, "wb") as f:
        f.write(png_data)


def _bytes_to_bits(data: bytes) -> str:
    """Convert bytes to a string of '0' and '1' characters."""
    return "".join(f"{byte:08b}" for byte in data)
```

- [ ] **Step 4: Run tests to verify they fail (decode not yet implemented)**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_roundtrip.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'densegrid.decode'`

- [ ] **Step 5: Implement decode.py**

```python
# src/densegrid/decode.py

import zlib
from densegrid.grid import (
    GRID_SIZE,
    QUIET_ZONE,
    FINDER_SIZE,
    HEADER_LENGTH,
    is_finder_region,
    is_timing_pixel,
)
from densegrid.header import unpack_header, MAGIC
from densegrid.pixel import decode_pixel
from densegrid.png import read_png


def decode_file(input_path: str) -> bytes:
    """Decode a QR² PNG image back to the original byte payload."""
    with open(input_path, "rb") as f:
        png_data = f.read()

    pixels = read_png(png_data)
    width = len(pixels[0])
    height = len(pixels)

    # Extract data pixels in order
    data_pixels = _get_data_pixels_from_grid(pixels)

    # Read header
    header_pixel_values = []
    for r, c in data_pixels[:HEADER_LENGTH]:
        header_pixel_values.append(pixels[r][c])

    payload_size, version, checksum, _, _ = unpack_header(header_pixel_values)

    # Read payload pixels
    body_pixels = data_pixels[HEADER_LENGTH:]
    bits = ""
    for r, c in body_pixels:
        if len(bits) >= payload_size * 8:
            break
        chunk = decode_pixel(pixels[r][c])
        bits += f"{chunk:06b}"

    # Trim to exact payload size
    bits = bits[:payload_size * 8]

    # Convert bits to bytes
    payload = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        if len(byte_bits) < 8:
            byte_bits += "0" * (8 - len(byte_bits))
        payload.append(int(byte_bits, 2))

    payload = bytes(payload)

    # Verify CRC32
    actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_crc != checksum:
        raise ValueError(
            f"CRC32 mismatch: expected 0x{checksum:08X}, got 0x{actual_crc:08X}"
        )

    return payload


def _get_data_pixels_from_grid(
    pixels: list[list[tuple[int, int, int]]],
) -> list[tuple[int, int]]:
    """Extract data pixel coordinates from an actual pixel grid.

    Unlike grid.get_data_pixels() which builds a fresh grid, this reads
    from the decoded image to handle any orientation.
    """
    result = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if is_finder_region(r, c):
                continue
            r_abs = r - QUIET_ZONE
            c_abs = c - QUIET_ZONE
            if r_abs < FINDER_SIZE and c_abs < FINDER_SIZE:
                continue
            if r < QUIET_ZONE or c < QUIET_ZONE:
                continue
            if r >= GRID_SIZE - QUIET_ZONE or c >= GRID_SIZE - QUIET_ZONE:
                continue
            # Skip timing pattern pixels
            timing_row = QUIET_ZONE + FINDER_SIZE - 1
            timing_col = QUIET_ZONE + FINDER_SIZE - 1
            if r == timing_row or c == timing_col:
                continue
            result.append((r, c))
    return result
```

- [ ] **Step 6: Run roundtrip tests**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_roundtrip.py -v`
Expected: all 5 tests PASS

- [ ] **Step 7: Run full test suite**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest -v`
Expected: all tests PASS

- [ ] **Step 8: Commit**

```bash
git add src/densegrid/encode.py src/densegrid/decode.py tests/test_roundtrip.py
git commit -m "feat: encode and decode pipelines with CRC32 verification"
```

---

## Task 7: CLI Entry Points

**Covers:** [S9] CLI Interface

**Files:**
- Create: `src/densegrid/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

```python
# tests/test_cli.py
import os
import subprocess
import tempfile

def test_encode_help():
    result = subprocess.run(
        ["python", "-m", "densegrid.cli", "encode", "--help"],
        capture_output=True, text=True,
        cwd="/home/ransom/Projekte/QR²",
    )
    assert result.returncode == 0
    assert "input" in result.stdout.lower() or "file" in result.stdout.lower()

def test_decode_help():
    result = subprocess.run(
        ["python", "-m", "densegrid.cli", "decode", "--help"],
        capture_output=True, text=True,
        cwd="/home/ransom/Projekte/QR²",
    )
    assert result.returncode == 0

def test_encode_decode_roundtrip_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "input.txt")
        png_file = os.path.join(tmpdir, "output.png")
        output_file = os.path.join(tmpdir, "recovered.txt")

        with open(input_file, "wb") as f:
            f.write(b"Hello from CLI!")

        # Encode
        result = subprocess.run(
            ["python", "-m", "densegrid.cli", "encode", input_file, "-o", png_file],
            capture_output=True, text=True,
            cwd="/home/ransom/Projekte/QR²",
        )
        assert result.returncode == 0, f"Encode failed: {result.stderr}"
        assert os.path.exists(png_file)

        # Decode
        result = subprocess.run(
            ["python", "-m", "densegrid.cli", "decode", png_file, "-o", output_file],
            capture_output=True, text=True,
            cwd="/home/ransom/Projekte/QR²",
        )
        assert result.returncode == 0, f"Decode failed: {result.stderr}"
        assert os.path.exists(output_file)

        with open(output_file, "rb") as f:
            assert f.read() == b"Hello from CLI!"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError` or CLI not found

- [ ] **Step 3: Implement cli.py**

```python
# src/densegrid/cli.py

import argparse
import sys
from densegrid.encode import encode_file
from densegrid.decode import decode_file


def encode_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dgencode",
        description="Encode a file into a QR² dense-grid PNG image.",
    )
    parser.add_argument("input", help="Input file to encode")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    args = parser.parse_args(argv)

    with open(args.input, "rb") as f:
        payload = f.read()

    encode_file(payload, args.output)
    print(f"Encoded {len(payload)} bytes → {args.output}")


def decode_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dgdecode",
        description="Decode a QR² dense-grid PNG image back to the original file.",
    )
    parser.add_argument("input", help="Input PNG file to decode")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    args = parser.parse_args(argv)

    payload = decode_file(args.input)

    with open(args.output, "wb") as f:
        f.write(payload)

    print(f"Decoded {args.input} → {len(payload)} bytes")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "decode":
        decode_main(sys.argv[2:])
    else:
        encode_main(sys.argv[1:] if len(sys.argv) > 1 else None)
```

- [ ] **Step 4: Run CLI tests**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest tests/test_cli.py -v`
Expected: all 3 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /home/ransom/Projekte/QR² && python -m pytest -v`
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/densegrid/cli.py tests/test_cli.py
git commit -m "feat: CLI entry points (dgencode/dgdecode)"
```

---

## Self-Review Checklist

| Spec Section | Covered By |
|-------------|-----------|
| [S1] Visual Structure | Task 3 (grid.py) |
| [S2] Multi-Level Pixel Encoding | Task 2 (pixel.py) |
| [S3] Header Row | Task 4 (header.py) |
| [S4] Pixel Construction (Encoding) | Task 2 + Task 6 (encode.py) |
| [S5] Pixel Extraction (Decoding) | Task 5 (png.py) + Task 6 (decode.py) |
| [S6] Multi-Image Sequences | **Out of scope** — v1 is single-image only |
| [S7] Digital environment advantage | N/A (design rationale, not implementable) |
| [S8] Future density expansion | **Out of scope** — Phase 2 |
| [S9] CLI Interface | Task 7 (cli.py) |
