import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def write_png(pixels: list[list[tuple[int, int, int]]]) -> bytes:
    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = _make_chunk(b"IHDR", ihdr_data)

    raw = bytearray()
    for row in pixels:
        raw.append(0)  # filter byte: None
        for r, g, b in row:
            raw.extend((r, g, b))
    idat = _make_chunk(b"IDAT", zlib.compress(bytes(raw)))

    iend = _make_chunk(b"IEND", b"")

    return PNG_SIGNATURE + ihdr + idat + iend


def read_png(data: bytes) -> list[list[tuple[int, int, int]]]:
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("Not a valid PNG file")
    pos = 8
    width = height = 0
    idat_data = b""

    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length

        if chunk_type == b"IHDR":
            width, height = struct.unpack(">II", chunk_data[:8])
        elif chunk_type == b"IDAT":
            idat_data += chunk_data

    raw = zlib.decompress(idat_data)
    pixels = []
    row_bytes = width * 3
    for y in range(height):
        offset = y * (row_bytes + 1)
        if raw[offset] != 0:
            raise ValueError(f"Unsupported PNG filter: {raw[offset]}")
        row = []
        for x in range(width):
            i = offset + 1 + x * 3
            row.append((raw[i], raw[i + 1], raw[i + 2]))
        pixels.append(row)

    return pixels
