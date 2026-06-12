import zlib

from densegrid.grid import GRID_SIZE, get_data_pixels
from densegrid.header import unpack_header, HEADER_LENGTH
from densegrid.pixel import decode_pixel
from densegrid.png import read_png


def decode_file(input_path: str) -> bytes:
    """Decode a QR² PNG image back to the original byte payload."""
    with open(input_path, "rb") as f:
        png_data = f.read()

    pixels = read_png(png_data)

    if len(pixels) != GRID_SIZE or len(pixels[0]) != GRID_SIZE:
        raise ValueError(
            f"Expected {GRID_SIZE}x{GRID_SIZE} grid, got {len(pixels[0])}x{len(pixels)}"
        )

    data_pixels = get_data_pixels()

    header_pixel_values = []
    for r, c in data_pixels[:HEADER_LENGTH]:
        header_pixel_values.append(pixels[r][c])

    payload_size, version, checksum = unpack_header(header_pixel_values)

    body_pixels = data_pixels[HEADER_LENGTH:]
    bits = ""
    for r, c in body_pixels:
        if len(bits) >= payload_size * 8:
            break
        chunk = decode_pixel(pixels[r][c])
        bits += f"{chunk:06b}"

    bits = bits[: payload_size * 8]

    payload = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i : i + 8]
        if len(byte_bits) < 8:
            byte_bits += "0" * (8 - len(byte_bits))
        payload.append(int(byte_bits, 2))

    payload = bytes(payload)

    actual_crc = zlib.crc32(payload) & 0xFFFFFF
    if actual_crc != checksum:
        raise ValueError(
            f"CRC32 mismatch: expected 0x{checksum:06X}, got 0x{actual_crc:06X}"
        )

    return payload
