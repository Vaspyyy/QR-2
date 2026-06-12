from densegrid.grid import make_grid, get_data_pixels
from densegrid.header import pack_header, FORMAT_VERSION, HEADER_LENGTH
from densegrid.png import write_png
from densegrid.pixel import encode_pixel


def encode_file(payload: bytes, output_path: str) -> None:
    """Encode a byte payload into a QR² PNG image."""
    grid = make_grid()
    data_pixels = get_data_pixels()

    header_pixels = data_pixels[:HEADER_LENGTH]
    body_pixels = data_pixels[HEADER_LENGTH:]

    header = pack_header(len(payload), FORMAT_VERSION, payload)

    bits = _bytes_to_bits(payload)

    for i, pixel in enumerate(header_pixels):
        grid[pixel[0]][pixel[1]] = header[i]

    bit_idx = 0
    for r, c in body_pixels:
        if bit_idx + 6 <= len(bits):
            chunk = int(bits[bit_idx:bit_idx + 6], 2)
            bit_idx += 6
        else:
            remaining = bits[bit_idx:]
            remaining += "0" * (6 - len(remaining))
            chunk = int(remaining, 2)
            bit_idx = len(bits)
        grid[r][c] = encode_pixel(chunk)

    png_data = write_png(grid)
    with open(output_path, "wb") as f:
        f.write(png_data)


def _bytes_to_bits(data: bytes) -> str:
    """Convert bytes to a string of '0' and '1' characters."""
    return "".join(f"{byte:08b}" for byte in data)
